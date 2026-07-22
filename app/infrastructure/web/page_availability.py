from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PageAvailability:
    is_available: bool
    is_gone: bool = False
    is_verification_blocked: bool = False
    status_code: int | None = None
    error: str | None = None


def check_page_availability(url: str, *, timeout_seconds: float = 5.0) -> PageAvailability:
    request = Request(url, method="HEAD", headers={"User-Agent": "gite-agent/0.1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.status
    except HTTPError as exc:
        if exc.code == 405:
            return _check_with_get(url, timeout_seconds=timeout_seconds)
        return _from_http_error(exc)
    except URLError as exc:
        return PageAvailability(is_available=False, error=str(exc.reason))
    return PageAvailability(is_available=status_code < 400, status_code=status_code)


def _check_with_get(url: str, *, timeout_seconds: float) -> PageAvailability:
    request = Request(url, method="GET", headers={"User-Agent": "gite-agent/0.1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.status
    except HTTPError as exc:
        return _from_http_error(exc)
    except URLError as exc:
        return PageAvailability(is_available=False, error=str(exc.reason))
    return PageAvailability(is_available=status_code < 400, status_code=status_code)


def _from_http_error(exc: HTTPError) -> PageAvailability:
    return PageAvailability(
        is_available=False,
        is_gone=exc.code in {404, 410},
        is_verification_blocked=exc.code in {401, 403, 429},
        status_code=exc.code,
        error=str(exc.reason),
    )
