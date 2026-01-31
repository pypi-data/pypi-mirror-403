import asyncio
import json
import os
from typing import Any, Literal, cast

from loguru import logger

from .cache import Cache, FileSystemCache
from .engines import CDPEngine, CurlEngine
from .pool import ProxyPool
from .telemetry import get_tracer
from .types import (
    Action,
    Cookie,
    EngineType,
    Proxy,
    ProxyStrategy,
    Response,
)

tracer = get_tracer()


class Fetcher:
    """
    Main entry point for PhantomFetch.
    """

    def __init__(
        self,
        # Proxy config
        proxies: list[str | Proxy] | None = None,
        proxy_strategy: ProxyStrategy = "round_robin",
        # Browser engine selection
        browser_engine: Literal["cdp", "baas"] = "cdp",
        # CDP options
        cdp_endpoint: str | None = None,
        headless: bool = True,
        # General options
        timeout: float = 30.0,
        browser_timeout: float = 60.0,
        max_retries: int = 3,
        max_concurrent: int = 50,
        max_concurrent_browser: int = 10,
        # Cache
        cache: Cache | bool | None = None,
        # Advanced CDP
        cdp_use_existing_page: bool = True,
    ):
        """
        Initialize the Fetcher.

        Args:
            proxies: List of proxy URLs or Proxy objects
            proxy_strategy: Strategy for proxy selection
            browser_engine: "cdp" (local/remote Playwright) or "baas" (HTTP API)
            cdp_endpoint: Optional CDP WebSocket URL (e.g. ws://localhost:3000)
            headless: Run browser in headless mode (CDP only)
            baas_endpoints: List of BaaS endpoints
            timeout: Default timeout for curl requests
            browser_timeout: Default timeout for browser requests
            max_retries: Max retries for curl requests
            max_concurrent: Max concurrent curl requests
            max_concurrent_browser: Max concurrent browser requests
            cache: Cache implementation (e.g. FileSystemCache)
            cdp_use_existing_page: Reuse existing page in remote CDP (default: True)
        """
        # Cache
        self.cache: Cache | None = None
        if cache is True:
            from .cache import FileSystemCache

            self.cache = FileSystemCache()
        elif cache is False:
            self.cache = None
        else:
            self.cache = cache

        # Proxy pool
        if isinstance(proxies, ProxyPool):
            self.proxy_pool = proxies
        else:
            self.proxy_pool = ProxyPool(proxies or [], strategy=proxy_strategy)

        # Curl engine
        self._curl = CurlEngine(
            timeout=timeout,
            max_retries=max_retries,
        )
        
        if browser_engine == "baas":
            raise ValueError("BaaSEngine has been removed. Please use 'cdp' engine or contact support.")

        # Browser engine
        # Always use CDPEngine now
        self._cdp_engine = CDPEngine(
            cdp_endpoint=cdp_endpoint,
            headless=headless,
            timeout=browser_timeout,
            cache=self.cache,
            use_existing_page=cdp_use_existing_page,
        )
        self._browser = self._cdp_engine

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_open_browsers = max_concurrent_browser
        self._browser_semaphore = asyncio.Semaphore(max_concurrent_browser)

        # Session persistence
        self.session_data: dict[str, Any] | None = None

        # Defaults
        self.timeout = timeout
        self.browser_timeout = browser_timeout
        self.max_retries = max_retries

    async def __aenter__(self) -> "Fetcher":
        await self._browser.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._browser.disconnect()

    async def start(self) -> None:
        """
        Start the browser engine.
        """
        if self._browser:
            await self._browser.start()

    async def stop(self) -> None:
        """
        Stop the browser engine.
        """
        if self._browser:
            await self._browser.stop()

    def save_session(self, path: str) -> None:
        """
        Save the current session storage (cookies, localStorage) to a file.

        Args:
            path: Path to save the session JSON file.
        """
        if not self.session_data:
            logger.warning("No session data to save. Run a browser fetch first.")
            return

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, indent=2)

    def load_session(self, path: str) -> None:
        """
        Load session storage (cookies, localStorage) from a file.

        Args:
            path: Path to load the session JSON file from.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Session file not found: {path}")

        with open(path, encoding="utf-8") as f:
            self.session_data = json.load(f)

    def _normalize_actions(self, actions: list[Action | dict]) -> list[Action]:
        """Normalize action shorthands to Action objects."""
        normalized_actions: list[Action] = []
        for a in actions:
            if isinstance(a, Action):
                normalized_actions.append(a)
            elif isinstance(a, dict):
                normalized_actions.append(Action(**a))
            elif isinstance(a, str):
                # Parse string shorthand
                # "wait_for_load"
                # "click:#selector"
                # "wait:2000"
                # "screenshot"
                # "screenshot:filename.png"
                if ":" in a:
                    action_type, value = a.split(":", 1)
                    if action_type == "click":
                        normalized_actions.append(
                            Action(action="click", selector=value)
                        )
                    elif action_type == "wait":
                        # Check if value is number (timeout) or selector
                        if value.isdigit():
                            normalized_actions.append(
                                Action(action="wait", timeout=int(value))
                            )
                        else:
                            normalized_actions.append(
                                Action(action="wait", selector=value)
                            )
                    elif action_type == "input":
                        # input:#selector:value - might be too complex for simple split
                        # Let's support simple input:#selector=value
                        if "=" in value:
                            sel, val = value.split("=", 1)
                            normalized_actions.append(
                                Action(action="input", selector=sel, value=val)
                            )
                        else:
                            # Fallback or error? Let's assume just selector focus? No, input needs value.
                            # Maybe just don't support complex input in shorthand.
                            pass
                    elif action_type == "screenshot":
                        normalized_actions.append(
                            Action(action="screenshot", value=value)
                        )
                    elif action_type == "scroll":
                        normalized_actions.append(
                            Action(action="scroll", selector=value)
                        )
                    elif action_type == "hover":
                        normalized_actions.append(
                            Action(action="hover", selector=value)
                        )
                # No arguments
                elif a == "wait_for_load":
                    normalized_actions.append(Action(action="wait_for_load"))
                elif a == "screenshot":
                    normalized_actions.append(Action(action="screenshot"))
        return normalized_actions

    async def fetch(
        self,
        url: str,
        *,
        engine: EngineType = "curl",
        proxy: Proxy | str | None = None,
        location: str | None = None,
        actions: list[Action | dict | str] | None = None,
        cookies: dict[str, str] | list[Cookie] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_on: set[int] | None = None,
        retry_backoff: float | None = None,
        referer: str | None = None,
        allow_redirects: bool = True,
        wait_until: str = "domcontentloaded",
        block_resources: list[str] | None = None,
        wait_for_url: str | None = None,
        stealth: bool = False,
    ) -> Response:
        """
        Fetch a URL.

        Args:
            url: Target URL
            engine: "curl" (default) or "browser"
            proxy: Specific proxy to use (overrides pool)
            location: Geo location for proxy selection
            actions: List of `Action` objects or dicts (implies engine="browser")
            
            ...
        """
        # Normalize actions - implies browser
        normalized_actions: list[Action] | None = None
        if actions:
            normalized_actions = self._normalize_actions(actions)
            engine = "browser"

        # Start OTel span
        with tracer.start_as_current_span("phantomfetch.fetch") as span:
            span.set_attribute("url.full", url)
            span.set_attribute("phantomfetch.engine", engine)
            span.set_attribute("phantomfetch.cache.enabled", bool(self.cache))

            # Enhanced OTel attributes
            if timeout:
                span.set_attribute("phantomfetch.config.timeout", float(timeout))
            if wait_until:
                span.set_attribute("phantomfetch.config.wait_until", wait_until)
            if block_resources:
                span.set_attribute(
                    "phantomfetch.config.block_resources", block_resources
                )
            if wait_for_url:
                span.set_attribute("phantomfetch.config.wait_for_url", wait_for_url)

            if normalized_actions:
                span.set_attribute(
                    "phantomfetch.actions.count", len(normalized_actions)
                )
                try:
                    # Serialize actions to JSON for debugging
                    # We only serialize the 'action' and 'selector' to keep it concise
                    actions_summary = [
                        {"action": a.action, "selector": a.selector, "value": a.value}
                        for a in normalized_actions
                    ]
                    span.set_attribute(
                        "phantomfetch.actions.json", json.dumps(actions_summary)
                    )
                except Exception:
                    pass

            # Check cache
            if self.cache and self.cache.should_cache_request("document"):
                # Cache key generation: engine + url + location + proxy
                # This ensures geo-targeted requests are cached separately
                cache_key_parts = [engine, url]
                if location:
                    cache_key_parts.append(f"loc={location}")
                
                # Use proxy URL for cache key if explicit proxy is used
                # Note: We rely on the proxy *argument* (manual override) for this separation.
                # If using pool, we typically don't split cache by specific pool proxy, 
                # UNLESS location was requested (handled above).
                if proxy: 
                    # If manual proxy string/object provided, include it
                    p_url = proxy if isinstance(proxy, str) else proxy.url
                    # Sanitize sensitive info? user:pass might be sensitive, 
                    # but for cache key uniqueness it's needed. 
                    # Since MD5 is used downstream, it's somewhat obscured.
                    cache_key_parts.append(f"proxy={p_url}")

                cache_key = ":".join(cache_key_parts)
                
                cached_resp = await self.cache.get(cache_key)
                if cached_resp:
                    cached_resp.from_cache = True
                    span.set_attribute("phantomfetch.cache.hit", True)
                    return cached_resp

            span.set_attribute("phantomfetch.cache.hit", False)

            # Get proxy
            # 1. Manual override
            selected_proxy: Proxy | None = None
            if proxy:
                if isinstance(proxy, str):
                    selected_proxy = Proxy(url=proxy, metadata={"source": "manual_override"})
                else:
                    selected_proxy = proxy
            
            # 2. From Pool (if no override)
            if not selected_proxy:
                selected_proxy = self.proxy_pool.get(url=url, location=location)

            if selected_proxy:
                span.set_attribute("phantomfetch.proxy", selected_proxy.url)
                if selected_proxy.vendor:
                    span.set_attribute("phantomfetch.proxy.vendor", selected_proxy.vendor)
                if selected_proxy.proxy_type:
                    span.set_attribute("phantomfetch.proxy.type", selected_proxy.proxy_type)
                if selected_proxy.location:
                    span.set_attribute("phantomfetch.proxy.location", selected_proxy.location)
                if selected_proxy.provider:
                    span.set_attribute("phantomfetch.proxy.provider", selected_proxy.provider)

            # Route to engine
            if engine == "browser":
                resp = await self._fetch_browser(
                    url=url,
                    proxy=selected_proxy,

                    headers=headers,
                    cookies=cookies,
                    actions=normalized_actions,
                    timeout=timeout or self.browser_timeout,
                    location=location,
                    wait_until=wait_until,
                    block_resources=block_resources,
                    wait_for_url=wait_for_url,
                    storage_state=self.session_data,  # Pass current session
                    stealth=stealth,
                )
            else:
                resp = await self._fetch_curl(
                    url=url,
                    proxy=proxy,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout or self.timeout,
                    max_retries=max_retries or self.max_retries,
                    retry_on=retry_on,
                    retry_backoff=retry_backoff,
                    referer=referer,
                    allow_redirects=allow_redirects,
                )

            # Update session data from response if present
            if resp.storage_state:
                self.session_data = resp.storage_state

            # Update proxy stats (ONLY if it came from the pool, or generally?)
            # If manual override, we might NOT want to impact the pool stats unless the manual proxy IS in the pool?
            # For simplicity, if we have a pool, and this proxy matches one in the pool, we could update it.
            # But the 'selected_proxy' might be a new instance specific to this request (manual override).
            # The pool.mark_* methods take a Proxy object.
            
            # Logic: If 'proxy' argument was None, it came from pool -> Update stats.
            # If 'proxy' argument was set -> Do NOT update pool stats (it's a manual override).
            if not proxy and selected_proxy:
                if resp.ok:
                    self.proxy_pool.mark_success(selected_proxy)
                elif resp.error:
                    self.proxy_pool.mark_failed(selected_proxy)

            # Cache response
            if self.cache and resp.ok and self.cache.should_cache_request("document"):
                # Re-generate key (same logic as above)
                cache_key_parts = [engine, url]
                if location:
                    cache_key_parts.append(f"loc={location}")
                if proxy: 
                    p_url = proxy if isinstance(proxy, str) else proxy.url
                    cache_key_parts.append(f"proxy={p_url}")
                
                cache_key = ":".join(cache_key_parts)
                await self.cache.set(cache_key, resp)

            return resp

    # ... (other methods)

    async def _fetch_browser(
        self,
        url: str,
        proxy: Proxy | None,
        headers: dict[str, str] | None,
        actions: list[Action] | None,
        timeout: float,
        location: str | None,
        wait_until: str,
        cookies: dict[str, str] | list[Cookie] | None = None,
        block_resources: list[str] | None = None,
        wait_for_url: str | None = None,
        storage_state: dict[str, Any] | None = None,
        stealth: bool = False,
    ) -> Response:
        async with self._semaphore:
            async with self._browser_semaphore:
                # Direct CDP usage (BaaSEngine removed)
                if not self._cdp_engine:
                     # Lazy init if not done (though currently init in __init__)
                     # But wait, logic in __init__ was: 
                     # self._cdp_engine = CDPEngine(...) if browser_engine == "cdp"
                     # Since we removed engine selection, we should ensure it's initialized.
                     # In __init__ I see: self._cdp_engine: CDPEngine | None = None
                     # And the constructor logic for it was tied to the "if browser_engine == 'cdp'" block which I might have messed up or need to fix.
                     # Let's check __init__ again.
                     pass 

                # Actually, looking at the previous file content, I removed the 'if browser_engine ==' logic in __init__? 
                # No, I only updated the arguments. I need to make sure __init__ initializes _cdp_engine unconditionally.
                # Let's assume I fix __init__ in a separate recursive step if needed, or I can fix it here if I see it.
                # In the previous `view_file` output (Step 356), lines 87-101 show the old init logic. 
                # I need to clean that up too! 
                
                # Let's just assume _browser attribute is now _cdp_engine.
                # Wait, the __init__ logic was:
                # self._browser = CDPEngine(...)
                # So here I should just use self._browser (which is typed as CDPEngine in the new world).
                
                # Correct implementation for _fetch_browser:
                return await self._cdp_engine.fetch(
                    url=url,
                    proxy=proxy,
                    headers=headers,
                    cookies=cookies,
                    actions=actions,
                    timeout=timeout,
                    location=location,
                    wait_until=wait_until,
                    block_resources=block_resources,
                    wait_for_url=wait_for_url,
                    storage_state=storage_state,
                    stealth=stealth,
                )

    async def _fetch_curl(
        self,
        url: str,
        proxy: Proxy | None,
        headers: dict[str, str] | None,
        cookies: dict[str, str] | list[Cookie] | None,
        timeout: float,
        max_retries: int,
        retry_on: set[int] | None,
        retry_backoff: float | None,
        referer: str | None,
        allow_redirects: bool,
    ) -> Response:
        async with self._semaphore:
            return await self._curl.fetch(
                url=url,
                proxy=proxy,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                max_retries=max_retries,
                retry_on=retry_on,
                retry_backoff=retry_backoff,
                referer=referer,
                allow_redirects=allow_redirects,
            )
