from app.repositories.in_memory import DEFAULT_TEAM
from app.repositories.user_pokemon_data import (
    UserPokemonDataRepository,
    reset_current_user_session_id,
    set_current_user_session_id,
)


def test_user_pokemon_data_repository_persists_team_for_current_session(monkeypatch) -> None:
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

    token = set_current_user_session_id("session-abc")
    try:
        repository = UserPokemonDataRepository("user-pokemon-data", "ap-northeast-2")
        saved = repository.save_team(DEFAULT_TEAM)
    finally:
        reset_current_user_session_id(token)

    assert saved.team_name == "main"
    assert writes[0]["pk"] == "USER#session-abc"
    assert writes[0]["sk"] == "TEAM#main"
    assert writes[0]["entityType"] == "UserPokemonTeam"
    assert writes[0]["userId"] == "session-abc"
    assert writes[0]["team"]["teamName"] == "main"
