from app.repositories.in_memory import DEFAULT_TEAM
from app.repositories.user_pokemon_data import UserPokemonDataRepository


def test_user_pokemon_data_repository_persists_team(monkeypatch) -> None:
    writes = []

    class FakeTable:
        def get_item(self, Key):
            return {}

        def put_item(self, Item):
            writes.append(Item)

    class FakeDynamodb:
        def Table(self, table_name: str):
            assert table_name == "user-pokemon-data"
            return FakeTable()

    monkeypatch.setattr("app.repositories.user_pokemon_data.boto3.resource", lambda *args, **kwargs: FakeDynamodb())

    repository = UserPokemonDataRepository("user-pokemon-data", "ap-northeast-2", "local")
    saved = repository.save_team(DEFAULT_TEAM)

    assert saved.team_name == "main"
    assert writes[0]["pk"] == "USER#local"
    assert writes[0]["sk"] == "TEAM#main"
    assert writes[0]["entityType"] == "UserPokemonTeam"
    assert writes[0]["team"]["teamName"] == "main"
