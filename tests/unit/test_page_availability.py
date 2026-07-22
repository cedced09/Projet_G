from urllib.error import HTTPError

import pytest

from app.infrastructure.web import page_availability


def test_check_page_availability_treats_403_as_blocked_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> object:
        raise HTTPError(
            url="https://example.invalid/listing",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(page_availability, "urlopen", fake_urlopen)

    availability = page_availability.check_page_availability("https://example.invalid/listing")

    assert availability.is_available is False
    assert availability.is_gone is False
    assert availability.is_verification_blocked is True
    assert availability.status_code == 403


def test_check_page_availability_treats_404_as_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> object:
        raise HTTPError(
            url="https://example.invalid/listing",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(page_availability, "urlopen", fake_urlopen)

    availability = page_availability.check_page_availability("https://example.invalid/listing")

    assert availability.is_available is False
    assert availability.is_gone is True
    assert availability.is_verification_blocked is False
    assert availability.status_code == 404
