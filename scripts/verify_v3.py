from __future__ import annotations

import ast
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    for path in [ROOT / "app_v3.py", *sorted((ROOT / "src").glob("*.py"))]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    from src.product_intelligence import analyze_product

    profile = analyze_product("保温钉")
    assert profile.product_name_en == "Insulation Anchor"
    assert profile.category == "建筑五金"
    assert "hardware store" in profile.buyer_types
    assert "insulation materials distributor" in profile.buyer_types

    generic_profile = analyze_product(
        "工业脚轮",
        product_name_en="Industrial Caster Wheel",
        category="其他",
    )
    assert "Industrial Caster Wheel distributor" in generic_profile.buyer_types
    override_profile = analyze_product(
        "定制产品",
        product_name_en="Custom Product",
        buyer_types="specialist dealer, regional importer",
        end_user_types="assembly factory",
        exclude_terms="consumer toy",
    )
    assert override_profile.buyer_types == [
        "specialist dealer", "regional importer"
    ]
    assert override_profile.end_user_types == ["assembly factory"]
    assert override_profile.exclude_terms == ["consumer toy"]

    from src.market_data import (
        REGION_COUNTRIES,
        get_cities_for_country,
        get_country_english_name,
        get_subregions_for_country,
        search_keywords_template,
    )

    assert get_country_english_name("泰国") == "Thailand"

    queries = search_keywords_template(
        ",".join(profile.keywords_en),
        "阿联酋",
        "Dubai",
        profile.category,
        "中东",
        ",".join(profile.buyer_types),
        ",".join(profile.end_user_types),
    )
    assert any("hardware store" in query for query in queries)
    assert any("insulation anchor" in query for query in queries)
    assert any("EIFS contractor" in query for query in queries)
    assert len(queries) == len(set(queries))
    thailand_queries = search_keywords_template(
        ",".join(profile.keywords_en),
        get_country_english_name("泰国"),
        "",
        profile.category,
        "东南亚",
        ",".join(profile.buyer_types),
        ",".join(profile.end_user_types),
    )
    assert all("泰国" not in query for query in thailand_queries)
    assert any("Thailand" in query for query in thailand_queries)
    configured_countries = {
        country_name
        for countries in REGION_COUNTRIES.values()
        for _, country_name in countries
    }
    assert all(get_cities_for_country(country) for country in configured_countries)
    assert len(get_cities_for_country("泰国")) >= 7
    assert any(
        name_en == "Chon Buri Province"
        for name_en, _ in get_subregions_for_country("泰国")
    )
    province_queries = search_keywords_template(
        ",".join(profile.keywords_en),
        "Thailand",
        "Pattaya",
        profile.category,
        "东南亚",
        ",".join(profile.buyer_types),
        ",".join(profile.end_user_types),
        subregion_en="Chon Buri Province",
    )
    assert all("Pattaya Chon Buri Province Thailand" in query for query in province_queries)

    from src.qualification import qualify_lead

    qualification_product = {
        "id": 1,
        "product_name_cn": "保温钉",
        "product_name_en": profile.product_name_en,
        "category": profile.category,
        "sub_category": profile.sub_category,
        "keywords_en": ", ".join(profile.keywords_en),
        "buyer_types": ", ".join(profile.buyer_types),
        "end_user_types": ", ".join(profile.end_user_types),
        "exclude_terms": ", ".join(profile.exclude_terms),
    }
    distributor_result = qualify_lead(
        {
            "company_name": "EIFS Supply Thailand",
            "website": "https://eifs.example",
            "email": "sales@eifs.example",
            "phone": "+66 2 555 1000",
            "business_summary": (
                "Leading importer and distributor of EIFS anchors, "
                "thermal insulation fixing and facade systems."
            ),
        },
        qualification_product,
        {"website_alive": 1, "has_product_page": 1},
    )
    assert distributor_result.buyer_role == "channel_partner"
    assert distributor_result.verdict == "qualified"
    assert distributor_result.product_fit_score >= 50

    end_user_result = qualify_lead(
        {
            "company_name": "Facade Build",
            "website": "https://facade.example",
            "email": "procurement@facade.example",
            "business_summary": (
                "Facade contractor delivering thermal insulation projects "
                "using insulation anchors."
            ),
        },
        qualification_product,
        {"website_alive": 1, "has_product_page": 1},
    )
    assert end_user_result.buyer_role == "end_user"
    assert end_user_result.verdict == "qualified"
    assert end_user_result.demand_signal_score > 0

    rejected_result = qualify_lead(
        {
            "company_name": "Beauty Nail Salon",
            "website": "https://beauty.example",
            "business_summary": "Beauty nail salon selling artificial nails.",
        },
        qualification_product,
        {"website_alive": 1},
    )
    assert rejected_result.verdict == "rejected"
    assert rejected_result.rejection_reasons

    from src.diligence import run_diligence

    homepage_response = Mock(
        status_code=200,
        apparent_encoding="utf-8",
        text=(
            "<html><head><title>EIFS Supply</title></head><body>"
            '<a href="/products">Products</a>'
            '<a href="/about">About</a>'
            '<a href="/contact">Contact</a>'
            "</body></html>"
        ),
    )
    product_response = Mock(
        status_code=200,
        apparent_encoding="utf-8",
        text=(
            "<html><body><h1>Insulation Anchor</h1>"
            "<p>EIFS anchor and thermal insulation fixing distributor.</p>"
            "</body></html>"
        ),
    )
    about_response = Mock(
        status_code=200,
        apparent_encoding="utf-8",
        text="<html><body>Building materials importer and distributor.</body></html>",
    )
    contact_response = Mock(
        status_code=200,
        apparent_encoding="utf-8",
        text="<html><body>Email: sales@eifs-supply.com</body></html>",
    )

    def fake_diligence_request(url: str, timeout: int):
        if "/products" in url:
            return product_response
        if "/about" in url:
            return about_response
        if "/contact" in url:
            return contact_response
        return homepage_response

    with patch(
        "src.diligence._request",
        side_effect=fake_diligence_request,
    ), patch("src.diligence.time.sleep", return_value=None):
        diligence_result = run_diligence(
            1,
            "https://eifs.example",
            target_keywords="insulation anchor, EIFS anchor",
        )
    assert "insulation anchor" in diligence_result["matched_product_terms"].lower()
    assert diligence_result["has_product_page"] == 1

    from src.acquisition_channels import (
        ChannelLead,
        _nominatim_bbox,
        brave_web_search,
        foursquare_places_search,
        google_places_search,
        opencorporates_search,
        pdl_company_search,
    )

    with patch(
        "src.acquisition_channels.requests.get",
        side_effect=RuntimeError("network must not be used"),
    ):
        assert _nominatim_bbox("Bangkok", "Thailand", "TH") == (
            "13.5500", "13.9500", "100.3500", "100.9000"
        )

    fake_brave = Mock()
    fake_brave.raise_for_status.return_value = None
    fake_brave.json.return_value = {
        "web": {"results": [{"title": "Dubai Hardware", "url": "https://hardware.ae", "description": "Tools"}]}
    }
    with patch.dict("os.environ", {"BRAVE_SEARCH_API_KEY": "test"}), patch(
        "src.acquisition_channels.requests.get", return_value=fake_brave
    ):
        assert brave_web_search("hardware Dubai")[0].domain == "hardware.ae"

    fake_places = Mock()
    fake_places.raise_for_status.return_value = None
    fake_places.json.return_value = {
        "places": [{
            "displayName": {"text": "Dubai Building Materials"},
            "formattedAddress": "Dubai, UAE",
            "websiteUri": "https://materials.ae",
            "internationalPhoneNumber": "+971 4 000 0000",
            "googleMapsUri": "https://maps.google.com/example",
        }]
    }
    with patch.dict("os.environ", {"GOOGLE_MAPS_API_KEY": "test"}), patch(
        "src.acquisition_channels.requests.post", return_value=fake_places
    ):
        place = google_places_search("building materials Dubai", "AE")[0]
        assert place.phone == "+971 4 000 0000"
        assert place.domain == "materials.ae"

    fake_foursquare = Mock()
    fake_foursquare.raise_for_status.return_value = None
    fake_foursquare.json.return_value = {
        "results": [{
            "fsq_place_id": "fsq-1",
            "name": "Bangkok Hardware",
            "website": "bangkok-hardware.example",
            "tel": "+66 2 555 0100",
            "location": {
                "formatted_address": "Bangkok, Thailand",
            },
            "categories": [{"name": "Hardware Store"}],
        }]
    }
    with patch.dict("os.environ", {"FOURSQUARE_API_KEY": "test"}), patch(
        "src.acquisition_channels.requests.get", return_value=fake_foursquare
    ):
        foursquare = foursquare_places_search(
            "hardware store", "Bangkok, Thailand"
        )[0]
        assert foursquare.domain == "bangkok-hardware.example"
        assert foursquare.phone == "+66 2 555 0100"
        assert foursquare.address == "Bangkok, Thailand"

    fake_opencorporates = Mock()
    fake_opencorporates.raise_for_status.return_value = None
    fake_opencorporates.json.return_value = {
        "results": {
            "companies": [{
                "company": {
                    "name": "THAI BUILDING SUPPLY CO LTD",
                    "company_number": "0105550000000",
                    "current_status": "Active",
                    "registered_address_in_full": "Bangkok, Thailand",
                    "opencorporates_url": "https://opencorporates.com/companies/th/example",
                }
            }]
        }
    }
    with patch.dict("os.environ", {"OPENCORPORATES_API_TOKEN": "test"}), patch(
        "src.acquisition_channels.requests.get",
        return_value=fake_opencorporates,
    ):
        company = opencorporates_search("building supply", "TH")[0]
        assert company.address == "Bangkok, Thailand"
        assert "Active" in company.business_summary
        assert company.source_channel == "OpenCorporates 企业注册"

    fake_pdl = Mock()
    fake_pdl.raise_for_status.return_value = None
    fake_pdl.json.return_value = {
        "status": 200,
        "data": [{
            "name": "Thailand Fastener Distribution",
            "website": "https://fastener.example",
            "industry": "Building Materials",
            "summary": "Fastener distributor",
            "size": "51-200",
            "location": {"name": "Bangkok, Thailand"},
            "linkedin_url": "https://linkedin.com/company/example",
        }],
    }
    with patch.dict("os.environ", {"PDL_API_KEY": "test"}), patch(
        "src.acquisition_channels.requests.get", return_value=fake_pdl
    ):
        pdl_company = pdl_company_search(
            "fastener distributor", "Thailand"
        )[0]
        assert pdl_company.domain == "fastener.example"
        assert "Fastener distributor" in pdl_company.business_summary

    from src.provider_gateway import provider_request

    fake_gateway = Mock()
    with patch.dict(
        "os.environ",
        {
            "TRADELEAD_API_GATEWAY_URL": "https://gateway.example/api/gateway",
            "TRADELEAD_API_GATEWAY_TOKEN": "gateway-secret",
            "TRADELEAD_GATEWAY_SERVICES": "serpapi,pdl",
        },
    ), patch(
        "src.provider_gateway.requests.request",
        return_value=fake_gateway,
    ) as gateway_request:
        assert provider_request(
            "serpapi",
            "GET",
            "https://serpapi.com/search.json",
            params={"q": "hardware", "api_key": "must-not-leak"},
        ) is fake_gateway
        gateway_call = gateway_request.call_args.kwargs
        assert gateway_call["params"]["service"] == "serpapi"
        assert gateway_call["params"]["q"] == "hardware"
        assert "api_key" not in gateway_call["params"]
        assert (
            gateway_call["headers"]["X-TradeLead-Gateway-Token"]
            == "gateway-secret"
        )

    import src.db_v3 as db

    with tempfile.TemporaryDirectory() as tmp:
        db.DB_DIR = Path(tmp)
        db.DB_PATH = Path(tmp) / "verify_v3.sqlite3"
        db.init_db()
        product_id = db.add_product(
            {
                "product_name_cn": "保温钉",
                "product_name_en": profile.product_name_en,
                "category": profile.category,
                "sub_category": profile.sub_category,
                "keywords_en": ", ".join(profile.keywords_en),
                "buyer_types": ", ".join(profile.buyer_types),
                "end_user_types": ", ".join(profile.end_user_types),
                "exclude_terms": ", ".join(profile.exclude_terms),
                "analysis_reasoning": profile.reasoning,
            }
        )
        saved = db.get_product(product_id)
        assert saved and "hardware store" in saved["buyer_types"]
        assert any(
            column["name"] == "address" for column in db.query("PRAGMA table_info(leads)")
        )
        assert any(
            column["name"] == "subregion"
            for column in db.query("PRAGMA table_info(leads)")
        )
        assert any(
            column["name"] == "subregion"
            for column in db.query("PRAGMA table_info(acquisition_tasks)")
        )
        assert db.query(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='lead_qualifications'"
        )

        from src.scraper import run_acquisition

        osm_lead = ChannelLead(
            company_name="Verified Hardware",
            website="https://verified.example",
            phone="+66 2 123 4567",
            business_summary="Hardware store",
            source_url="https://www.openstreetmap.org/node/1",
            source_channel="OpenStreetMap",
        )
        diligence = {
            "lead_id": 1,
            "website_alive": 1,
            "website_title": "Verified Hardware",
            "about_text": "Distributor of construction fasteners.",
            "products_found": "fasteners",
            "email_count": 1,
            "phone_count": 1,
            "has_whatsapp": 1,
            "has_product_page": 1,
            "has_contact_page": 1,
            "summary": "官网可访问",
            "emails": ["sales@verified.example"],
            "phones": ["+66 2 123 4567"],
            "whatsapps": ["https://wa.me/6621234567"],
        }
        with patch(
            "src.acquisition_channels.openstreetmap_search",
            return_value=[osm_lead],
        ), patch("src.diligence.run_diligence", return_value=diligence):
            result = run_acquisition(
                product_id,
                ",".join(profile.keywords_en),
                "东南亚",
                "泰国",
                "Bangkok",
                ["osm"],
                profile.category,
                ",".join(profile.buyer_types),
                ",".join(profile.end_user_types),
            )
        assert result == {"osm": 1}
        enriched = db.query(
            "SELECT email, phone, whatsapp, business_summary FROM leads "
            "WHERE company_name='Verified Hardware'"
        )[0]
        assert enriched["email"] == "sales@verified.example"
        assert enriched["whatsapp"] == "https://wa.me/6621234567"
        assert "Distributor" in enriched["business_summary"]

        registry_lead = ChannelLead(
            company_name="Registered Building Supply",
            address="Bangkok, Thailand",
            business_summary="注册状态: Active",
            source_url="https://opencorporates.com/companies/th/example-2",
            source_channel="OpenCorporates 企业注册",
        )
        pdl_lead = ChannelLead(
            company_name="PDL Fastener Distributor",
            phone="+66 2 555 0200",
            business_summary="Building Materials",
            source_channel="People Data Labs",
        )
        foursquare_lead = ChannelLead(
            company_name="Foursquare Tool Shop",
            address="Bangkok, Thailand",
            phone="+66 2 555 0300",
            source_channel="Foursquare Places",
        )
        with patch(
            "src.acquisition_channels.foursquare_places_search",
            return_value=[foursquare_lead],
        ), patch(
            "src.acquisition_channels.opencorporates_search",
            return_value=[registry_lead],
        ), patch(
            "src.acquisition_channels.pdl_company_search",
            return_value=[pdl_lead],
        ):
            commercial_result = run_acquisition(
                product_id,
                ",".join(profile.keywords_en),
                "东南亚",
                "泰国",
                "Bangkok",
                ["foursquare", "opencorporates", "pdl"],
                profile.category,
                ",".join(profile.buyer_types),
                ",".join(profile.end_user_types),
                subregion_en="Bangkok",
            )
        assert commercial_result == {
            "foursquare": 1,
            "opencorporates": 1,
            "pdl": 1,
        }
        assert db.query(
            "SELECT COUNT(*) AS count FROM leads WHERE subregion='Bangkok'"
        )[0]["count"] == 3
        assert db.query(
            "SELECT COUNT(*) AS count FROM lead_qualifications"
        )[0]["count"] == 4

    print("TradeLead V3 verification passed.")


if __name__ == "__main__":
    main()
