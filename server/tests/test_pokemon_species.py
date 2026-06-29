from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_pokemon_species_lookup_by_korean_name() -> None:
    response = client.get("/api/v1/pokemon/species", params={"query": "피카츄"})

    assert response.status_code == 200
    species = response.json()["species"]
    assert species["pokemonId"] == "pikachu"
    assert species["nameKo"] == "피카츄"
    assert species["nationalDexNumber"] == 25
    assert species["baseStats"]["spe"] == 90
    assert species["imageAssets"]["primaryArtworkUrl"].endswith("/025.png")


def test_pokemon_species_lookup_by_english_name() -> None:
    response = client.get("/api/v1/pokemon/species", params={"query": "Charizard"})

    assert response.status_code == 200
    species = response.json()["species"]
    assert species["pokemonId"] == "charizard"
    assert species["nameKo"] == "리자몽"
    assert species["baseStats"] == {"hp": 78, "atk": 84, "def": 78, "spa": 109, "spd": 85, "spe": 100}


def test_pokemon_species_lookup_returns_404_for_unknown_name() -> None:
    response = client.get("/api/v1/pokemon/species", params={"query": "not-a-pokemon"})

    assert response.status_code == 404
