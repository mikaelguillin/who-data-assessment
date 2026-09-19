from pathlib import Path

from fastapi.testclient import TestClient

from tests.helpers import write_csv_a, write_json_c, write_xlsx_b


def test_empty_overview_and_countries(client: TestClient) -> None:
    overview = client.get("/api/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["expenditure_count"] == 0
    assert payload["countries"] == []

    countries = client.get("/api/countries")
    assert countries.status_code == 200
    assert countries.json() == []


def test_ingest_upload_creates_country(client: TestClient, tmp_path: Path) -> None:
    path = write_csv_a(tmp_path / "kenya.csv")
    response = client.post(
        "/api/ingest",
        data={"country_name": "Kenya"},
        files={"file": ("kenya.csv", path.read_bytes(), "text/csv")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["country_code"] == "KENYA"
    assert body["record_count"] == 1
    assert body["source_format"] == "csv"
    assert body["replaced"] is False

    countries = client.get("/api/countries").json()
    assert countries == [
        {
            "country_code": "KENYA",
            "country_name": "Kenya",
            "primary_currency": "KES",
            "language": "en",
        }
    ]
    overview = client.get("/api/overview").json()
    assert overview["expenditure_count"] == 1
    assert overview["countries"][0]["country_name"] == "Kenya"


def test_ingest_rejects_unknown_layout(client: TestClient) -> None:
    response = client.post(
        "/api/ingest",
        data={"country_name": "Mystery"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_ingest_second_country_and_replace(client: TestClient, tmp_path: Path) -> None:
    kenya = write_csv_a(tmp_path / "kenya.csv")
    rwanda = write_json_c(tmp_path / "rwanda.json")
    first = client.post(
        "/api/ingest",
        data={"country_name": "Kenya"},
        files={"file": ("kenya.csv", kenya.read_bytes(), "text/csv")},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/ingest",
        data={"country_name": "Rwanda"},
        files={"file": ("rwanda.json", rwanda.read_bytes(), "application/json")},
    )
    assert second.status_code == 200
    codes = {item["country_code"] for item in client.get("/api/countries").json()}
    assert codes == {"KENYA", "RWANDA"}
    assert client.get("/api/overview").json()["expenditure_count"] == 2

    replacement = write_csv_a(
        tmp_path / "kenya2.csv",
        [
            {
                "TXN_ID": "KE-9",
                "DATE": "04/02/2024",
                "MINISTRY_CODE": "MOH",
                "MINISTRY_NAME": "Health",
                "ACCOUNT_CODE": "2211102",
                "DESCRIPTION": "Contraceptives",
                "VENDOR": "Vendor",
                "AMOUNT_KES": "10.00",
                "PAYMENT_METHOD": "BANK",
            }
        ],
    )
    again = client.post(
        "/api/ingest",
        data={"country_name": "Kenya", "country_code": "KENYA"},
        files={"file": ("kenya2.csv", replacement.read_bytes(), "text/csv")},
    )
    assert again.status_code == 200
    assert again.json()["replaced"] is True
    assert again.json()["record_count"] == 1
    overview = client.get("/api/overview").json()
    assert overview["expenditure_count"] == 2
    kenya_summary = next(item for item in overview["countries"] if item["country_code"] == "KENYA")
    assert kenya_summary["record_count"] == 1


def test_ingest_xlsx_upload(client: TestClient, tmp_path: Path) -> None:
    path = write_xlsx_b(tmp_path / "senegal.xlsx")
    response = client.post(
        "/api/ingest",
        data={"country_name": "Senegal"},
        files={
            "file": (
                "senegal.xlsx",
                path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["country_code"] == "SENEGAL"
    assert body["source_format"] == "xlsx"
    assert body["layout_id"] == "xlsx_b"
    countries = client.get("/api/countries").json()
    assert countries == [
        {
            "country_code": "SENEGAL",
            "country_name": "Senegal",
            "primary_currency": "XOF",
            "language": "fr",
        }
    ]


def test_ingest_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/ingest",
        data={"country_name": "Kenya"},
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_ingest_rejects_blank_country_name(client: TestClient, tmp_path: Path) -> None:
    path = write_csv_a(tmp_path / "kenya.csv")
    response = client.post(
        "/api/ingest",
        data={"country_name": "   "},
        files={"file": ("kenya.csv", path.read_bytes(), "text/csv")},
    )
    assert response.status_code == 400
    assert "country_name is required" in response.json()["detail"]


def test_ingest_rejects_csv_wrong_layout(client: TestClient) -> None:
    response = client.post(
        "/api/ingest",
        data={"country_name": "Mystery"},
        files={"file": ("other.csv", b"id,amount\n1,2\n", "text/csv")},
    )
    assert response.status_code == 400
    assert "TXN_ID" in response.json()["detail"]
