"""Unit tests for brewery parsing and helpers."""

from __future__ import annotations

from datetime import datetime

import pytest
from bs4 import BeautifulSoup
from httpx import HTTPStatusError
from untappd_scraper import brewery as brewery_mod
from untappd_scraper.brewery import Brewery, brewery_activity, brewery_details
from utpd_models_web.constants import UNTAPPD_BASE_URL


class FakeHTTPStatusError(HTTPStatusError):
    def __init__(self, *args, **kwargs):
        # Avoid calling HTTPStatusError.__init__ which requires specific args
        Exception.__init__(self, "fake http status")


# ----- brewery_details -----


def test_brewery_details_full() -> None:
    html = f"""
    <html>
      <head>
        <link rel="canonical" href="{UNTAPPD_BASE_URL}brewery/123"/>
      </head>
      <body>
        <div class="name">
          <h1>Test Brewery</h1>
          <p class="style">Ale</p>
          <p class="brewery">123 Test Road</p>
        </div>
        <div class="desc">
          <div class="beer-descrption-read-less">A lovely brewery <a class="read-less">Show Less</a></div>
        </div>
        <div class="details">
          <p class="count">5 beers</p>
          <div class="caps" data-rating="4.2"></div>
        </div>
      </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")

    details = brewery_details(soup, brewery_id=123)

    assert details.brewery_id == 123
    assert details.name == "Test Brewery"
    assert details.style == "Ale"
    assert details.address == "123 Test Road"
    assert details.description == "A lovely brewery"
    assert details.num_beers == 5
    assert details.rating == 4.2
    assert details.brewery_url == "brewery/123"


def test_brewery_details_no_desc_or_rating():
    html = """
    <html>
      <body>
        <div class="name">
          <h1>Anon Brewery</h1>
          <p class="style">Lager</p>
          <p class="brewery">Somewhere</p>
        </div>
        <div class="details">
          <p class="count">no beers</p>
        </div>
      </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")

    details = brewery_details(soup, brewery_id=777)

    assert details.description == ""
    assert details.rating is None
    assert details.num_beers == 0


# ----- brewery_activity -----


def test_brewery_activity_full():
    html = """
    <div class="activity">
      <div class="item" data-checkin-id="123">
        <div class="top">
          <div class="text">
            <a href="/user/abc">User</a>
            <a href="/beer/10">The Beer</a>
            <a href="/brewery/111">Brewery Name</a>
            <a href="/venue/222">Venue</a>
          </div>
        </div>
        <div class="bottom">
          <span class="time">2021-01-01 00:00:00</span>
        </div>
        <a class="label"><img src="/static/label.jpg"/></a>
        <p class="purchased"><a href="/place/222">Place</a></p>
        <div class="rating-serving"><div class="caps" data-rating="3.5"></div></div>
        <div class="tagged-friends"><a href="/user/f1"></a><a href="/user/f2"></a></div>
        <p class="comment-text">Nice</p>
        <p class="serving">On Tap</p>
      </div>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")

    activity = brewery_activity(soup, brewery_id=111)

    assert len(activity) == 1
    item = activity[0]
    assert item.checkin_id == 123
    assert item.beer_id == 10
    assert item.beer_label_url.endswith("label.jpg")
    assert item.user_name == "abc"
    assert item.location_id == 222
    assert item.purchased_at == "Place"
    assert item.purchased_id == 222
    assert item.comment == "Nice"
    assert item.serving == "On Tap"
    assert item.user_rating == 3.5
    assert item.friends == ["f1", "f2"]


def test_brewery_activity_missing_time_and_friends():
    html = """
    <div class="activity">
      <div class="item" data-checkin-id="0">
        <div class="top">
          <div class="text">
            <a href="/user/zzz">UserZ</a>
            <a href="/beer/0">Zero Beer</a>
            <a href="/brewery/11">X</a>
          </div>
        </div>
        <!-- no time element -->
      </div>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")

    activity = brewery_activity(soup, brewery_id=11)

    assert len(activity) == 1
    item = activity[0]
    assert item.checkin == datetime.min
    assert item.friends is None


# ----- Brewery.from_name and from_url -----


def test_from_name_success_and_no_result(monkeypatch):
    # a positive search result
    html_ok = """
    <div class="details brewery"><a href="/444/beer">beers</a></div>
    """
    soup_ok = BeautifulSoup(html_ok, "html.parser")

    monkeypatch.setattr(brewery_mod, "make_soup", lambda url: (soup_ok, True))

    # prevent real __post_init__ behaviour when constructing instance
    orig_init = Brewery.__init__

    def fake_init(self, brewery_id: int):
        self.brewery_id = brewery_id

    monkeypatch.setattr(Brewery, "__init__", fake_init)

    try:
        res = Brewery.from_name("anything")
        assert res is not None
        assert res.brewery_id == 444

        # a negative search result
        soup_none = BeautifulSoup("<div></div>", "html.parser")
        monkeypatch.setattr(brewery_mod, "make_soup", lambda url: (soup_none, True))
        res2 = Brewery.from_name("nope")
        assert res2 is None
    finally:
        monkeypatch.setattr(Brewery, "__init__", orig_init)


def test_from_url_success_and_errors(monkeypatch):
    # success path
    html_ok = """
    <p class="rss"><a href="/rss/555"></a></p>
    """
    soup_ok = BeautifulSoup(html_ok, "html.parser")
    monkeypatch.setattr(brewery_mod, "make_soup", lambda url: (soup_ok, True))

    orig_init = Brewery.__init__

    def fake_init(self, brewery_id: int):
        self.brewery_id = brewery_id

    monkeypatch.setattr(Brewery, "__init__", fake_init)

    try:
        res = Brewery.from_url("some-url")
        assert res is not None
        assert res.brewery_id == 555

        # no rss/href -> None
        soup_no_rss = BeautifulSoup("<p></p>", "html.parser")
        monkeypatch.setattr(brewery_mod, "make_soup", lambda url: (soup_no_rss, True))
        res2 = Brewery.from_url("some-url")
        assert res2 is None

        # make_soup raises HTTP error -> None
        monkeypatch.setattr(
            brewery_mod, "make_soup", lambda url: (_ for _ in ()).throw(FakeHTTPStatusError())
        )
        res3 = Brewery.from_url("some-url")
        assert res3 is None
    finally:
        monkeypatch.setattr(Brewery, "__init__", orig_init)


def test_post_init_http_error(monkeypatch):
    # make_soup raises HTTPStatusError -> constructor will raise ValueError
    monkeypatch.setattr(
        brewery_mod, "make_soup", lambda url: (_ for _ in ()).throw(FakeHTTPStatusError())
    )

    with pytest.raises(ValueError, match="Invalid brewery ID"):
        Brewery(9999)
