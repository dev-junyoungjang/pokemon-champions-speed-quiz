import os

os.environ.setdefault("POKEMON_SPECIES_SOURCE", "local")

from fastapi.testclient import TestClient

from app.main import app
from app.repositories import pokemon_species


client = TestClient(app)


def test_pokemon_species_lookup_by_korean_name() -> None:
    response = client.get("/api/v1/pokemon/species", params={"query": "피카츄"})

    assert response.status_code == 200
    species = response.json()["species"]
    assert species["pokemonId"] == "pikachu"
    assert species["nameKo"] == "피카츄"
    assert species["nationalDexNumber"] == 25
    assert species["baseStats"]["spe"] == 90
    assert species["types"] == ["electric"]
    assert any(ability["abilityId"] == "static" and ability["nameKo"] == "정전기" for ability in species["availableAbilities"])
    assert any(move["moveId"] == "thunderbolt" and move["nameKo"] == "10만볼트" for move in species["availableMoves"])
    assert species["imageAssets"]["primaryArtworkUrl"].endswith("/025.png")


def test_pokemon_species_lookup_can_return_mega_form() -> None:
    response = client.get("/api/v1/pokemon/species", params={"query": "메가리자몽X"})

    assert response.status_code == 200
    species = response.json()["species"]
    assert species["pokemonId"] == "charizard-mega-x"
    assert species["nameKo"] == "메가리자몽X"
    assert species["types"] == ["fire", "dragon"]
    assert species["baseStats"] == {"hp": 78, "atk": 130, "def": 111, "spa": 130, "spd": 85, "spe": 100}
    assert any(ability["abilityId"] == "tough-claws" for ability in species["availableAbilities"])
    assert any(move["moveId"] == "flamethrower" for move in species["availableMoves"])


def test_inferred_meowstic_female_mega_species_lookup() -> None:
    response = client.get("/api/v1/pokemon/species", params={"query": "메가냐오닉스♀"})

    assert response.status_code == 200
    species = response.json()["species"]
    assert species["pokemonId"] == "meowstic-female-mega"
    assert species["nameKo"] == "메가냐오닉스♀"
    assert species["types"] == ["psychic"]
    assert species["baseStats"] == {"hp": 74, "atk": 48, "def": 76, "spa": 143, "spd": 101, "spe": 124}
    assert any(ability["abilityId"] == "trace" for ability in species["availableAbilities"])


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


def test_dynamodb_species_loader_reads_pokemon_species_table(monkeypatch) -> None:
    pokemon_species.load_dynamodb_regulation_species.cache_clear()
    item = {
        "pk": pokemon_species.REGULATION_SPECIES_PK,
        "sk": "POKEMON#pikachu",
        "pokemonId": "pikachu",
        "nameEn": "Pikachu",
        "nameKo": "피카츄",
        "speciesId": "pikachu",
        "speciesNameEn": "Pikachu",
        "speciesNameKo": "피카츄",
        "nationalDexNumber": 25,
        "pokemonChampionsCode": "0025-000",
        "baseStats": {"hp": 35, "atk": 55, "def": 40, "spa": 50, "spd": 50, "spe": 90},
        "imageAssets": {
            "primaryArtworkUrl": "https://assets.pokemon.com/assets/cms2/img/pokedex/full/025.png",
            "fallbackArtworkUrl": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png",
            "spriteUrl": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png",
        },
        "types": ["electric"],
    }

    options_item = {
        "pk": pokemon_species.REGULATION_OPTIONS_PK,
        "sk": "POKEMON#pikachu",
        "pokemonId": "pikachu",
        "availableAbilities": [
            {"abilityId": "static", "nameEn": "Static", "nameKo": "정전기", "slot": 1, "hidden": False}
        ],
        "availableMoves": [
            {"moveId": "thunderbolt", "nameEn": "Thunderbolt", "nameKo": "10만볼트", "type": "electric"}
        ],
    }

    class FakeTable:
        def __init__(self, items):
            self.items = items

        def query(self, **kwargs):
            assert kwargs["KeyConditionExpression"] is not None
            return {"Items": self.items}

    class FakeDynamodb:
        def Table(self, table_name: str):
            if table_name == "pokemon-species":
                return FakeTable([item])
            if table_name == "pokemon-options":
                return FakeTable([options_item])
            raise AssertionError(f"unexpected table {table_name}")

    monkeypatch.setattr(pokemon_species.boto3, "resource", lambda *args, **kwargs: FakeDynamodb())

    species = pokemon_species.load_dynamodb_regulation_species("pokemon-species", "ap-northeast-2", "pokemon-options")

    assert len(species) == 1
    assert species[0].pokemon_id == "pikachu"
    assert species[0].name_ko == "피카츄"
    assert species[0].available_abilities[0].ability_id == "static"
    assert species[0].available_moves[0].move_id == "thunderbolt"
