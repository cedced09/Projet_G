from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PageDownloadError(RuntimeError):
    pass


def download_page_html(url: str, *, timeout_seconds: float = 10.0) -> str:
    request = Request(
        url,
        method="GET",
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "gite-agent/0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read()
            charset = str(response.headers.get_content_charset() or "utf-8")
    except HTTPError as exc:
        raise PageDownloadError(f"HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise PageDownloadError(str(exc.reason)) from exc
    decoded_payload: str = payload.decode(charset, errors="replace")
    return decoded_payload
