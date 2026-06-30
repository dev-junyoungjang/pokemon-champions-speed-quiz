from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_held_items_include_champions_battle_items() -> None:
    response = client.get("/api/v1/items")

    assert response.status_code == 200
    items = response.json()["items"]
    item_ids = {item["itemId"] for item in items}
    assert "choice-scarf" in item_ids
    assert "leftovers" in item_ids
    assert "garchompite" in item_ids


def test_held_items_can_be_searched_by_korean_name() -> None:
    response = client.get("/api/v1/items", params={"query": "구애스카프"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["itemId"] == "choice-scarf"
    assert items[0]["nameKo"] == "구애스카프"
