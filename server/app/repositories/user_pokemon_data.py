from __future__ import annotations

from contextvars import ContextVar, Token
from copy import deepcopy
from typing import Any, cast

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.models.domain import UserTeam
from app.repositories.in_memory import DEFAULT_TEAM, InMemoryRepository

USER_PK_PREFIX = "USER"
TEAM_SK_PREFIX = "TEAM"
DEFAULT_SESSION_USER_ID = "anonymous"
current_user_session_id: ContextVar[str] = ContextVar("current_user_session_id", default=DEFAULT_SESSION_USER_ID)


def set_current_user_session_id(user_session_id: str) -> Token[str]:
    return current_user_session_id.set(user_session_id.strip() or DEFAULT_SESSION_USER_ID)


def reset_current_user_session_id(token: Token[str]) -> None:
    current_user_session_id.reset(token)


class UserPokemonDataRepository(InMemoryRepository):
    """Persist user-owned Pokémon/team data to a DynamoDB pk/sk table.

    Authentication is not wired yet. The frontend generates an anonymous session
    id, stores it in localStorage, and sends it as `X-User-Session-Id`; this
    repository uses that id as the DynamoDB user partition suffix.
    """

    def __init__(self, table_name: str, region_name: str) -> None:
        super().__init__()
        self.table_name = table_name
        self.region_name = region_name

    @property
    def user_id(self) -> str:
        return current_user_session_id.get()

    @property
    def user_pk(self) -> str:
        return f"{USER_PK_PREFIX}#{self.user_id}"

    @staticmethod
    def team_sk(team_name: str) -> str:
        return f"{TEAM_SK_PREFIX}#{team_name}"

    def _table(self) -> Any:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.region_name,
            config=Config(connect_timeout=1, read_timeout=2, retries={"max_attempts": 1}),
        )
        return cast(Any, dynamodb).Table(self.table_name)

    def get_team(self, team_name: str = "main") -> UserTeam:
        try:
            response = self._table().get_item(Key={"pk": self.user_pk, "sk": self.team_sk(team_name)})
        except (BotoCoreError, ClientError, TimeoutError):
            return super().get_team(team_name)

        item = response.get("Item")
        if not item:
            return deepcopy(DEFAULT_TEAM if team_name == "main" else super().get_team(team_name))
        return UserTeam.model_validate(item["team"])

    def save_team(self, team: UserTeam) -> UserTeam:
        ordered = sorted(team.members, key=lambda member: member.slot)
        saved = team.model_copy(update={"members": ordered})
        item = {
            "pk": self.user_pk,
            "sk": self.team_sk(saved.team_name),
            "entityType": "UserPokemonTeam",
            "userId": self.user_id,
            "teamName": saved.team_name,
            "team": saved.model_dump(by_alias=True),
        }
        self._table().put_item(Item=item)
        self._teams[saved.team_name] = deepcopy(saved)
        return deepcopy(saved)
