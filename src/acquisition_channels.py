"""External lead acquisition channel adapters for TradeLead V3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
import re
from urllib.parse import urlparse

import requests

from src.provider_gateway import provider_configured, provider_request


@dataclass
class ChannelLead:
    company_name: str
    website: str = ""
    domain: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    whatsapp: str = ""
    social_links: str = ""
    business_summary: str = ""
    source_url: str = ""
    source_channel: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


DIRECTORY_SITES = {
    "阿联酋": ["yellowpages-uae.com", "atninfo.com", "reachuae.com"],
    "尼日利亚": ["businesslist.com.ng", "finelib.com"],
    "南非": ["yellowpages.co.za", "africanadvice.com"],
    "肯尼亚": ["businesslist.co.ke", "yellowpageskenya.com"],
    "印度": ["exportersindia.com", "indiamart.com"],
    "土耳其": ["turkishexporter.net", "turkish-manufacturers.com"],
    "泰国": ["yellowpages.co.th", "thaibusinesslisting.com"],
}

GLOBAL_DIRECTORY_SITES = ["europages.com", "kompass.com"]

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Offline bounding boxes for frequently used trade cities. This keeps normal
# searches independent from Nominatim, which is occasionally unreachable from
# mainland-China networks. Format: south, north, west, east.
CITY_BBOXES: dict[str, tuple[str, str, str, str]] = {
    "bangkok": ("13.5500", "13.9500", "100.3500", "100.9000"),
    "dubai": ("24.7900", "25.4200", "54.8900", "55.7000"),
    "abu dhabi": ("24.2200", "24.6900", "54.2000", "54.8500"),
    "riyadh": ("24.3500", "25.0500", "46.3000", "47.2000"),
    "jeddah": ("21.2500", "21.8500", "38.8500", "39.5500"),
    "istanbul": ("40.8000", "41.3500", "28.4500", "29.5500"),
    "lagos": ("6.3500", "6.7500", "3.0500", "3.7500"),
    "nairobi": ("-1.4800", "-1.1000", "36.6500", "37.0500"),
    "johannesburg": ("-26.4000", "-25.9500", "27.7000", "28.3500"),
    "cairo": ("29.8000", "30.2500", "31.0500", "31.6500"),
    "almaty": ("43.0500", "43.4500", "76.6500", "77.2000"),
    "tashkent": ("41.1500", "41.4500", "69.0500", "69.5000"),
    "jakarta": ("-6.4500", "-5.9500", "106.5500", "107.1000"),
    "ho chi minh city": ("10.5500", "11.1500", "106.3500", "107.0500"),
    "hanoi": ("20.8000", "21.2500", "105.5500", "106.0500"),
    "manila": ("14.3500", "14.8500", "120.8000", "121.2000"),
    "kuala lumpur": ("2.9500", "3.3500", "101.4500", "101.9500"),
    "dhaka": ("23.5500", "24.0500", "90.1500", "90.6500"),
    "karachi": ("24.6500", "25.2000", "66.7500", "67.5000"),
    "mumbai": ("18.8500", "19.3500", "72.7500", "73.1000"),
    "sao paulo": ("-24.0500", "-23.3000", "-46.9500", "-46.3000"),
    "mexico city": ("19.1500", "19.6500", "-99.4000", "-98.9000"),
    "moscow": ("55.4500", "56.0500", "37.1500", "38.0500"),
}


def directory_sites_for_country(country: str) -> list[str]:
    return DIRECTORY_SITES.get(country, []) + GLOBAL_DIRECTORY_SITES


def brave_web_search(query: str, limit: int = 10) -> list[ChannelLead]:
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not provider_configured("brave", "BRAVE_SEARCH_API_KEY"):
        raise RuntimeError("未配置 BRAVE_SEARCH_API_KEY")
    response = provider_request(
        "brave",
        "GET",
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
        params={"q": query, "count": min(limit, 20), "safesearch": "moderate"},
        timeout=30,
    )
    response.raise_for_status()
    items = response.json().get("web", {}).get("results", [])
    return [
        ChannelLead(
            company_name=item.get("title", "")[:150],
            website=item.get("url", ""),
            domain=_domain(item.get("url", "")),
            business_summary=_clean_html(item.get("description", ""))[:500],
            source_url=item.get("url", ""),
            source_channel="Brave Web Search",
        )
        for item in items[:limit]
        if item.get("url")
    ]


def google_places_search(query: str, country_code: str = "", limit: int = 20) -> list[ChannelLead]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not provider_configured("google_places", "GOOGLE_MAPS_API_KEY"):
        raise RuntimeError("未配置 GOOGLE_MAPS_API_KEY")
    payload: dict = {"textQuery": query, "pageSize": min(limit, 20), "languageCode": "en"}
    if country_code:
        payload["regionCode"] = country_code.upper()
    response = provider_request(
        "google_places",
        "POST",
        "https://places.googleapis.com/v1/places:searchText",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.displayName,places.formattedAddress,places.websiteUri,"
                "places.internationalPhoneNumber,places.googleMapsUri,"
                "places.businessStatus,places.primaryTypeDisplayName"
            ),
        },
        json_payload=payload,
        timeout=30,
    )
    response.raise_for_status()
    leads: list[ChannelLead] = []
    for place in response.json().get("places", []):
        website = place.get("websiteUri", "")
        type_text = place.get("primaryTypeDisplayName", {}).get("text", "")
        status = place.get("businessStatus", "")
        summary = " · ".join(value for value in [type_text, status] if value)
        leads.append(
            ChannelLead(
                company_name=place.get("displayName", {}).get("text", "")[:150],
                website=website,
                domain=_domain(website),
                address=place.get("formattedAddress", ""),
                phone=place.get("internationalPhoneNumber", ""),
                business_summary=summary,
                source_url=place.get("googleMapsUri", ""),
                source_channel="Google Places",
            )
        )
    return leads


def foursquare_places_search(
    query: str,
    location: str,
    limit: int = 20,
) -> list[ChannelLead]:
    api_key = os.getenv("FOURSQUARE_API_KEY", "").strip()
    if not provider_configured("foursquare", "FOURSQUARE_API_KEY"):
        raise RuntimeError("未配置 FOURSQUARE_API_KEY")
    response = provider_request(
        "foursquare",
        "GET",
        "https://places-api.foursquare.com/places/search",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-Places-Api-Version": "2025-06-17",
        },
        params={"query": query, "near": location, "limit": min(limit, 50)},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    items = payload.get("results") or payload.get("places") or []
    leads: list[ChannelLead] = []
    for item in items:
        location_data = item.get("location") or {}
        website = _normalize_url(
            item.get("website") or item.get("url") or item.get("link") or ""
        )
        categories = item.get("categories") or []
        category_names = [
            category.get("name", "") for category in categories
            if isinstance(category, dict) and category.get("name")
        ]
        address = (
            location_data.get("formatted_address")
            or location_data.get("formattedAddress")
            or ", ".join(
                value for value in [
                    location_data.get("address", ""),
                    location_data.get("locality", ""),
                    location_data.get("region", ""),
                    location_data.get("country", ""),
                ] if value
            )
        )
        fsq_id = item.get("fsq_place_id") or item.get("fsq_id") or item.get("id") or ""
        source_url = item.get("link") or (
            f"https://foursquare.com/place/{fsq_id}" if fsq_id else ""
        )
        leads.append(
            ChannelLead(
                company_name=(item.get("name") or "")[:150],
                website=website,
                domain=_domain(website),
                address=address,
                phone=item.get("tel") or item.get("telephone") or item.get("phone") or "",
                email=item.get("email") or "",
                business_summary=" · ".join(category_names),
                source_url=source_url,
                source_channel="Foursquare Places",
            )
        )
    return [lead for lead in leads if lead.company_name]


def opencorporates_search(
    query: str,
    country_code: str,
    limit: int = 30,
) -> list[ChannelLead]:
    api_token = os.getenv("OPENCORPORATES_API_TOKEN", "").strip()
    if not provider_configured("opencorporates", "OPENCORPORATES_API_TOKEN"):
        raise RuntimeError("未配置 OPENCORPORATES_API_TOKEN")
    params = {
        "q": query,
        "country_code": country_code.lower(),
        "inactive": "false",
        "order": "score",
        "per_page": min(limit, 100),
        "api_token": api_token,
    }
    if not api_token:
        params.pop("api_token")
    response = provider_request(
        "opencorporates",
        "GET",
        "https://api.opencorporates.com/v0.4/companies/search",
        params=params,
        headers={"Accept": "application/json"},
        timeout=35,
    )
    response.raise_for_status()
    companies = (
        response.json().get("results", {}).get("companies", [])
    )
    leads: list[ChannelLead] = []
    for wrapper in companies:
        company = wrapper.get("company", wrapper)
        status = company.get("current_status") or (
            "Inactive" if company.get("inactive") else "Status unknown"
        )
        company_number = company.get("company_number", "")
        company_type = company.get("company_type", "")
        incorporation_date = company.get("incorporation_date", "")
        summary = " · ".join(
            value for value in [
                f"注册状态: {status}",
                f"注册号: {company_number}" if company_number else "",
                company_type,
                f"成立: {incorporation_date}" if incorporation_date else "",
            ] if value
        )
        source_url = company.get("opencorporates_url") or company.get("registry_url") or ""
        leads.append(
            ChannelLead(
                company_name=(company.get("name") or "")[:150],
                address=company.get("registered_address_in_full") or "",
                business_summary=summary,
                source_url=source_url,
                source_channel="OpenCorporates 企业注册",
            )
        )
    return [lead for lead in leads if lead.company_name]


def pdl_company_search(
    query: str,
    country: str,
    limit: int = 20,
    subregion: str = "",
) -> list[ChannelLead]:
    api_key = os.getenv("PDL_API_KEY", "").strip()
    if not provider_configured("pdl", "PDL_API_KEY"):
        raise RuntimeError("未配置 PDL_API_KEY")
    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": ["name", "summary", "industry", "tags"],
            }
        },
        {"match": {"location.country": country.lower()}},
    ]
    if subregion:
        must_clauses.append({"match": {"location.region": subregion.lower()}})
    es_query = {"query": {"bool": {"must": must_clauses}}}
    response = provider_request(
        "pdl",
        "GET",
        "https://api.peopledatalabs.com/v5/company/search",
        headers={"Accept": "application/json", "X-api-key": api_key},
        params={
            "query": json.dumps(es_query, ensure_ascii=False),
            "size": min(limit, 100),
            "titlecase": "true",
        },
        timeout=35,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") not in (None, 200):
        raise RuntimeError(payload.get("error", {}).get("message") or "PDL 查询失败")
    leads: list[ChannelLead] = []
    for company in payload.get("data", []):
        website = _normalize_url(
            company.get("website") or company.get("domain") or ""
        )
        location_data = company.get("location") or {}
        if isinstance(location_data, str):
            address = location_data
        else:
            address = location_data.get("name") or ", ".join(
                value for value in [
                    location_data.get("locality", ""),
                    location_data.get("region", ""),
                    location_data.get("country", ""),
                ] if value
            )
        phone = company.get("phone") or ""
        if isinstance(phone, list):
            phone = ", ".join(str(value) for value in phone[:3])
        summary = " · ".join(
            str(value) for value in [
                company.get("industry", ""),
                company.get("summary", ""),
                f"规模: {company.get('size')}" if company.get("size") else "",
            ] if value
        )
        social_links = [
            company.get("linkedin_url", ""),
            company.get("facebook_url", ""),
            company.get("twitter_url", ""),
        ]
        leads.append(
            ChannelLead(
                company_name=(company.get("display_name") or company.get("name") or "")[:150],
                website=website,
                domain=_domain(website),
                address=address,
                phone=phone,
                email=company.get("email") or "",
                social_links=json.dumps(
                    [link for link in social_links if link], ensure_ascii=False
                ),
                business_summary=summary[:1000],
                source_url=company.get("linkedin_url") or website,
                source_channel="People Data Labs",
            )
        )
    return [lead for lead in leads if lead.company_name]


def openstreetmap_search(
    buyer_terms: list[str],
    country: str,
    city: str = "",
    country_code: str = "",
    limit: int = 50,
) -> list[ChannelLead]:
    """Search public OpenStreetMap business tags through Overpass."""
    terms = [term for term in buyer_terms if term][:4]
    if not terms:
        return []
    location = city or country
    elements: list[dict] = []
    successful_tiles = 0
    errors: list[str] = []

    known_bbox = CITY_BBOXES.get(location.strip().lower())
    if not known_bbox and country_code:
        try:
            elements.extend(
                _fetch_overpass_area(location, country_code, min(limit, 100))
            )
            successful_tiles += 1
        except Exception as exc:
            errors.append(str(exc))

    if known_bbox or not successful_tiles:
        try:
            bbox = known_bbox or _nominatim_bbox(
                location, country, country_code
            )
        except RuntimeError as exc:
            errors.append(str(exc))
            bbox = None
        for tile in _split_bbox(bbox) if bbox else []:
            bounds = f"({tile[0]},{tile[2]},{tile[1]},{tile[3]})"
            query = f"""
            [out:json][timeout:18];
            nwr["shop"~"hardware|doityourself|building_materials|electrical|paint"]{bounds};
            out center {min(limit, 100)};
            """
            try:
                elements.extend(_fetch_overpass(query))
                successful_tiles += 1
            except Exception as exc:
                errors.append(str(exc))

    if not successful_tiles:
        detail = errors[-1] if errors else "所有公共实例均不可用"
        raise RuntimeError(f"OpenStreetMap 查询失败：{detail}")

    leads: list[ChannelLead] = []
    seen_osm_ids: set[tuple[str, int]] = set()
    for element in elements:
        osm_identity = (element.get("type", ""), element.get("id", 0))
        if osm_identity in seen_osm_ids:
            continue
        seen_osm_ids.add(osm_identity)
        tags = element.get("tags", {})
        native_name = tags.get("name") or tags.get("brand")
        english_name = tags.get("name:en") or tags.get("brand:en")
        if not native_name and not english_name:
            continue
        if english_name and native_name and english_name != native_name:
            name = f"{english_name} ({native_name})"
        else:
            name = english_name or native_name
        website = _normalize_url(tags.get("contact:website") or tags.get("website") or "")
        phone = tags.get("contact:phone") or tags.get("phone") or ""
        email = tags.get("contact:email") or tags.get("email") or ""
        whatsapp = tags.get("contact:whatsapp") or tags.get("whatsapp") or ""
        social_links = [
            tags.get("contact:facebook", ""),
            tags.get("contact:instagram", ""),
            tags.get("contact:line", ""),
        ]
        address = _osm_address(tags)
        osm_url = f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}"
        description = (
            tags.get("description:en")
            or tags.get("description")
            or tags.get("operator")
            or tags.get("brand")
            or ""
        )
        shop_type = tags.get("shop", tags.get("office", ""))
        summary_parts = ["OpenStreetMap 商家", shop_type, description]
        leads.append(
            ChannelLead(
                company_name=name[:150],
                website=website,
                domain=_domain(website),
                address=address,
                phone=phone,
                email=email,
                whatsapp=whatsapp,
                social_links=json.dumps(
                    [link for link in social_links if link], ensure_ascii=False
                ),
                business_summary=" · ".join(part for part in summary_parts if part),
                source_url=osm_url,
                source_channel="OpenStreetMap",
            )
        )
    return leads[:limit]


def _domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().removeprefix("www.")


def _normalize_url(url: str) -> str:
    value = (url or "").strip()
    if value and "://" not in value:
        return f"https://{value}"
    return value


def _clean_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "").strip()


def _escape_ql(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _osm_address(tags: dict) -> str:
    if tags.get("addr:full"):
        return tags["addr:full"]
    parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:street", ""),
        tags.get("addr:city", ""),
        tags.get("addr:state", ""),
        tags.get("addr:country", ""),
    ]
    return ", ".join(part for part in parts if part)


def _nominatim_bbox(
    location: str,
    country: str,
    country_code: str,
) -> tuple[str, str, str, str] | None:
    known = CITY_BBOXES.get(location.strip().lower())
    if known:
        return known
    try:
        response = requests.get(
            os.getenv("NOMINATIM_API_URL", "https://nominatim.openstreetmap.org/search"),
            params={
                "q": f"{location}, {country}",
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": country_code.lower() if country_code else "",
            },
            headers={"User-Agent": "TradeLeadIntel/3.0 (business research tool)"},
            timeout=20,
        )
        response.raise_for_status()
        items = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(
            f"城市“{location}”未配置本地坐标，且在线地理编码不可用"
        ) from exc
    if not items or len(items[0].get("boundingbox", [])) != 4:
        return None
    south, north, west, east = items[0]["boundingbox"]
    return south, north, west, east


def _split_bbox(
    bbox: tuple[str, str, str, str],
) -> list[tuple[float, float, float, float]]:
    south, north, west, east = (float(value) for value in bbox)
    middle_lat = (south + north) / 2
    middle_lon = (west + east) / 2
    return [
        (south, middle_lat, west, middle_lon),
        (south, middle_lat, middle_lon, east),
        (middle_lat, north, west, middle_lon),
        (middle_lat, north, middle_lon, east),
    ]


def _fetch_overpass(query: str) -> list[dict]:
    configured = os.getenv("OVERPASS_API_URL", "").strip()
    endpoints = [configured] if configured else []
    endpoints.extend(endpoint for endpoint in OVERPASS_ENDPOINTS if endpoint != configured)
    failures: list[str] = []
    for endpoint in endpoints:
        try:
            response = requests.get(
                endpoint,
                params={"data": query},
                headers={"User-Agent": "TradeLeadIntel/3.0 (business research tool)"},
                timeout=25,
            )
            if response.status_code in (429, 502, 503, 504):
                failures.append(f"{endpoint} HTTP {response.status_code}")
                continue
            response.raise_for_status()
            return response.json().get("elements", [])
        except (requests.RequestException, ValueError) as exc:
            failures.append(f"{endpoint}: {exc}")
    raise RuntimeError("；".join(failures))


def _fetch_overpass_area(
    location: str,
    country_code: str,
    limit: int,
) -> list[dict]:
    """Search an administrative area without depending on Nominatim."""
    aliases = [location.strip()]
    shortened = re.sub(
        r"\s+(Province|State|Region|Governorate|County|Oblast|Krai|"
        r"Voivodeship|Division|Territory)$",
        "",
        location.strip(),
        flags=re.IGNORECASE,
    )
    if shortened and shortened.lower() != location.strip().lower():
        aliases.append(shortened)
    name_pattern = "|".join(re.escape(alias) for alias in aliases)
    escaped_pattern = _escape_ql(f"^({name_pattern})$")
    escaped_country = _escape_ql(country_code.upper())
    query = f"""
    [out:json][timeout:25];
    area["ISO3166-1"="{escaped_country}"][admin_level="2"]->.countryArea;
    (
      area(area.countryArea)["boundary"="administrative"]["name"~"{escaped_pattern}",i];
      area(area.countryArea)["boundary"="administrative"]["name:en"~"{escaped_pattern}",i];
    )->.searchArea;
    nwr["shop"~"hardware|doityourself|building_materials|electrical|paint"](area.searchArea);
    out center {min(limit, 100)};
    """
    return _fetch_overpass(query)
