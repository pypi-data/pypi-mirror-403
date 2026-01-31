import random
import time
from typing import Any, cast
from urllib.parse import urlparse

from .types import Proxy, ProxyStrategy


class ProxyPool:
    def __init__(
        self, proxies: list[Proxy | str], strategy: ProxyStrategy = "round_robin"
    ):
        self.proxies = [p if isinstance(p, Proxy) else Proxy(url=p) for p in proxies]
        self.strategy = strategy
        self._index = 0
        self._domain_map: dict[str, Proxy] = {}

    def get(
        self,
        url: str | None = None,
        location: str | None = None,
        vendor: str | None = None,
        proxy_type: str | None = None,
    ) -> Proxy | None:
        if not self.proxies:
            return None

        now = time.time()

        # Filter by criteria
        candidates = self.proxies
        if location:
            candidates = [p for p in candidates if p.location == location]
        if vendor:
            candidates = [
                p
                for p in candidates
                if p.vendor == vendor or p.provider == vendor
            ]
        if proxy_type:
            candidates = [
                p for p in candidates if p.proxy_type == proxy_type
            ]

        if not candidates:
            return None

        # Filter out cool-down proxies (Health Check)
        healthy_candidates = [p for p in candidates if p.cooldown_until <= now]

        # Fail-Open: If all candidates are on cool-down, use the ones expiring soonest
        if not healthy_candidates:
            # Sort by cooldown_until ascending
            candidates.sort(key=lambda p: p.cooldown_until)
            # Take the top 20% or at least 1 to distribute load among recovering proxies
            take_count = max(1, len(candidates) // 5)
            healthy_candidates = candidates[:take_count]

        # Apply strategy on healthy candidates
        match self.strategy:
            case "round_robin":
                # We need to maintain index stability relative to the original list or just pick from healthy?
                # Simple round-robin on filtered list is tricky because it changes every time.
                # Let's fallback to random on filtered list for simplicity, or maintain a global index.
                # Global index is unstable with filtering. Let's increment global but wrap to len(healthy).
                proxy = healthy_candidates[self._index % len(healthy_candidates)]
                self._index += 1
                return proxy

            case "random":
                return random.choice(healthy_candidates)

            case "geo_match":
                # already handled by filter above
                return random.choice(healthy_candidates)

            case "sticky" if url:
                domain = urlparse(url).netloc
                # Check if we have a sticky proxy for this domain
                if domain in self._domain_map:
                    p = self._domain_map[domain]
                    # Respect cool-down? If sticky proxy is dead, we should probably re-assign.
                    if p.cooldown_until <= now:
                        return p

                # Assign new sticky
                proxy = random.choice(healthy_candidates)
                self._domain_map[domain] = proxy
                return proxy

            case "failover":
                # Prefer those with 0 failures, else least failures
                healthy_candidates.sort(key=lambda p: p.failures)
                return healthy_candidates[0]

            case _:
                return random.choice(healthy_candidates)

    def mark_failed(self, proxy: Proxy) -> None:
        proxy.failures += 1
        
        # Exponential backoff: 30s * 2^(failures-1)
        # 1st fail: 30s
        # 2nd fail: 60s
        # 3rd fail: 120s
        # Cap at 1 hour (3600s)
        base_delay = 30.0
        backoff = min(3600.0, base_delay * (2 ** (proxy.failures - 1)))
        proxy.cooldown_until = time.time() + backoff

    def mark_success(self, proxy: Proxy) -> None:
        proxy.failures = 0
        proxy.cooldown_until = 0.0
        proxy.last_used = time.time()

    @classmethod
    def from_locations(
        cls, mapping: dict[str, list[str]], **kwargs: Any
    ) -> "ProxyPool":
        proxies = [
            Proxy(url=url, location=loc)
            for loc, urls in mapping.items()
            for url in urls
        ]
        return cls(cast(list[Proxy | str], proxies), **kwargs)
