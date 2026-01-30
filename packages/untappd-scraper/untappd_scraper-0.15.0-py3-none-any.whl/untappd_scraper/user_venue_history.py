"""Untappd user venue history functions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin

from utpd_models_web.constants import UNTAPPD_BASE_URL
from utpd_models_web.venue import WebUserHistoryVenue

from untappd_scraper.web import (
    date_from_data_href,
    id_from_href,
    make_soup,
    parsed_value,
    url_of,
)

if TYPE_CHECKING:  # pragma: no cover
    from bs4 import Tag


def load_user_venue_history(user_id: str) -> list[WebUserHistoryVenue]:
    """Load all availble recent venues for a user.

    Args:
        user_id (str): user ID to load

    Returns:
        Collection[WebUserHistoryVenue]: last 15 (or so) visited venues
    """
    url = url_of(user_id, page="venues", query={"sort": "recent"})
    soup, _from_cache = make_soup(url)

    return [recent_venue_details(checkin) for checkin in soup.select(".venue-item")]


def recent_venue_details(recent: Tag) -> WebUserHistoryVenue:
    """Extract venue details from a venue history entry.

    Args:
        recent (Element): single venue

    Returns:
        WebUserHistoryVenue: Interesting details for a venue
    """
    category_el = recent.select_one(".category")
    address_el = recent.select_one(".address")
    name_el = recent.select_one(".name a")
    details = recent.select_one(".details")

    assert category_el is not None, recent
    assert address_el is not None, recent
    assert name_el is not None, recent
    assert details is not None, recent

    is_verified = recent.select_one(".verified") is not None

    first_visit = date_from_data_href(details, ":firstVisit", date_only=True)
    last_visit = date_from_data_href(details, ":lastVisit", date_only=True)
    assert last_visit is not None, recent

    first_visit_el = details.select_one('.date [data-href=":firstVisit"]')
    first_checkin = id_from_href(first_visit_el) if first_visit_el else None
    last_visit_el = details.select_one('.date [data-href=":lastVisit"]')
    last_checkin = id_from_href(last_visit_el) if last_visit_el else None
    assert last_checkin is not None, details

    checkins_el = details.select_one(".check-ins")
    assert checkins_el is not None, details
    checkins_text = checkins_el.get_text(" ", strip=True)
    parsed_checkins = parsed_value("Check-ins: {:d}", checkins_text)
    checkins = int(parsed_checkins) if parsed_checkins is not None else 0

    href = str(name_el.get("href", ""))
    venue_id_attr = recent.attrs.get("data-venue-id", "0")
    venue_id_str = venue_id_attr[0] if isinstance(venue_id_attr, list) else str(venue_id_attr)
    venue_id = int(venue_id_str)

    return WebUserHistoryVenue(
        venue_id=venue_id,
        name=name_el.get_text(strip=True),
        url=urljoin(UNTAPPD_BASE_URL, href),
        category=category_el.get_text(strip=True),
        address=address_el.get_text(strip=True),
        is_verified=is_verified,
        first_visit=first_visit,
        last_visit=last_visit,
        num_checkins=checkins,
        first_checkin_id=first_checkin,
        last_checkin_id=last_checkin,
    )
