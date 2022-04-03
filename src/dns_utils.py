from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from dns import exception as dns_exception
from dns import inet, resolver
from yarl import URL

from core import cl, logger

resolver = resolver.Resolver()

resolver.nameservers = [
    "1.1.1.1",
    "1.0.0.1",
    "8.8.8.8",
    "8.8.4.4",
    "208.67.222.222",
    "208.67.220.220",
]


# TODO: handle multiple IPs
@lru_cache(maxsize=128)
def resolve_host(url):
    host = URL(url).host
    if inet.is_address(host):
        return host
    answer = resolver.resolve(host)
    return answer[0].to_text()


def get_resolvable_targets(targets):
    targets = list(set(targets))
    with ThreadPoolExecutor(min(len(targets), 10)) as executor:
        future_to_target = {executor.submit(resolve_host, target): target for target in targets}
        for future in as_completed(future_to_target):
            target = future_to_target[future]
            try:
                future.result()
                yield target
            except dns_exception.DNSException:
                logger.warning(f"{cl.RED}Ціль {target} не резолвиться і не буде атакована{cl.RESET}")
