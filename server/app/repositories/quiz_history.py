from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, cast
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.models.domain import AnswerResult, QuizQuestion
from app.repositories.user_pokemon_data import current_user_session_id

USER_PK_PREFIX = "USER"
SESSION_SK_PREFIX = "QUIZ_SESSION"
ANSWER_SK_PREFIX = "QUIZ_ANSWER"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class QuizHistoryRepository:
    def __init__(self) -> None:
        self._sessions_by_user: dict[str, list[dict[str, Any]]] = {}
        self._answers_by_user: dict[str, list[dict[str, Any]]] = {}

    @property
    def user_id(self) -> str:
        return current_user_session_id.get()

    @property
    def user_pk(self) -> str:
        return f"{USER_PK_PREFIX}#{self.user_id}"

    def create_session(self, *, difficulty: str, team_name: str, questions: list[QuizQuestion]) -> str:
        session_id = str(uuid4())
        created_at = utc_now_iso()
        item = {
            "pk": self.user_pk,
            "sk": f"{SESSION_SK_PREFIX}#{created_at}#{session_id}",
            "entityType": "QuizSession",
            "userId": self.user_id,
            "sessionId": session_id,
            "createdAt": created_at,
            "difficulty": difficulty,
            "teamName": team_name,
            "questionCount": len(questions),
            "questions": [question.model_dump(by_alias=True) for question in questions],
        }
        self._sessions_by_user.setdefault(self.user_id, []).append(deepcopy(item))
        return session_id

    def record_answer(
        self,
        *,
        session_id: str | None,
        question: QuizQuestion,
        selected_answer: bool,
        result: AnswerResult,
    ) -> None:
        answered_at = utc_now_iso()
        item = {
            "pk": self.user_pk,
            "sk": f"{ANSWER_SK_PREFIX}#{session_id or 'unknown'}#{answered_at}#{question.id}",
            "entityType": "QuizAnswer",
            "userId": self.user_id,
            "sessionId": session_id,
            "questionId": question.id,
            "answeredAt": answered_at,
            "selectedAnswer": selected_answer,
            "correct": result.correct,
            "correctAnswer": result.correct_answer,
            "subjectPokemonId": question.subject.build.pokemon_id,
            "opponentPokemonId": question.opponent.build.pokemon_id,
            "subjectSpeed": result.subject_speed,
            "opponentSpeed": result.opponent_speed,
            "question": question.model_dump(by_alias=True),
            "result": result.model_dump(by_alias=True),
        }
        self._answers_by_user.setdefault(self.user_id, []).append(deepcopy(item))

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        sessions = sorted(self._sessions_by_user.get(self.user_id, []), key=lambda item: item["createdAt"], reverse=True)
        return deepcopy(sessions[:limit])


class DynamoDbQuizHistoryRepository(QuizHistoryRepository):
    def __init__(self, table_name: str, region_name: str) -> None:
        super().__init__()
        self.table_name = table_name
        self.region_name = region_name

    def _table(self) -> Any:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.region_name,
            config=Config(connect_timeout=1, read_timeout=2, retries={"max_attempts": 1}),
        )
        return cast(Any, dynamodb).Table(self.table_name)

    def create_session(self, *, difficulty: str, team_name: str, questions: list[QuizQuestion]) -> str:
        session_id = str(uuid4())
        created_at = utc_now_iso()
        item = {
            "pk": self.user_pk,
            "sk": f"{SESSION_SK_PREFIX}#{created_at}#{session_id}",
            "entityType": "QuizSession",
            "userId": self.user_id,
            "sessionId": session_id,
            "createdAt": created_at,
            "difficulty": difficulty,
            "teamName": team_name,
            "questionCount": len(questions),
            "questions": [question.model_dump(by_alias=True) for question in questions],
        }
        try:
            self._table().put_item(Item=item)
        except (BotoCoreError, ClientError, TimeoutError):
            self._sessions_by_user.setdefault(self.user_id, []).append(deepcopy(item))
        return session_id

    def record_answer(
        self,
        *,
        session_id: str | None,
        question: QuizQuestion,
        selected_answer: bool,
        result: AnswerResult,
    ) -> None:
        answered_at = utc_now_iso()
        item = {
            "pk": self.user_pk,
            "sk": f"{ANSWER_SK_PREFIX}#{session_id or 'unknown'}#{answered_at}#{question.id}",
            "entityType": "QuizAnswer",
            "userId": self.user_id,
            "sessionId": session_id,
            "questionId": question.id,
            "answeredAt": answered_at,
            "selectedAnswer": selected_answer,
            "correct": result.correct,
            "correctAnswer": result.correct_answer,
            "subjectPokemonId": question.subject.build.pokemon_id,
            "opponentPokemonId": question.opponent.build.pokemon_id,
            "subjectSpeed": result.subject_speed,
            "opponentSpeed": result.opponent_speed,
            "question": question.model_dump(by_alias=True),
            "result": result.model_dump(by_alias=True),
        }
        try:
            self._table().put_item(Item=item)
        except (BotoCoreError, ClientError, TimeoutError):
            self._answers_by_user.setdefault(self.user_id, []).append(deepcopy(item))

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        try:
            response = self._table().query(
                KeyConditionExpression=Key("pk").eq(self.user_pk) & Key("sk").begins_with(f"{SESSION_SK_PREFIX}#"),
                ScanIndexForward=False,
                Limit=limit,
            )
        except (BotoCoreError, ClientError, TimeoutError):
            return super().list_sessions(limit)
        return response.get("Items", [])
