from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import get_settings
from app.models.domain import (
    AnswerRequest,
    AnswerResult,
    Difficulty,
    GenerateQuizRequest,
    QuizQuestionCandidate,
    RenderQuestionRequest,
    UserTeam,
    ValidatedQuizQuestion,
)
from app.repositories.in_memory import InMemoryRepository
from app.services.quiz_service import QuizService

repository = InMemoryRepository()
quiz_service = QuizService(repository)

app = FastAPI(title="Pokémon Champions Speed Quiz API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/ai/config")
def ai_config() -> dict[str, object]:
    settings = get_settings()
    return {
        "openaiConfigured": settings.openai_configured,
        "candidateModel": settings.openai_candidate_model,
        "renderModel": settings.openai_render_model,
        "questionGenerationEnabled": settings.ai_question_generation_enabled,
        "questionRenderingEnabled": settings.ai_question_rendering_enabled,
        "candidateBatchMultiplier": settings.ai_candidate_batch_multiplier,
        "maxGenerationAttempts": settings.ai_max_generation_attempts,
    }


@app.get("/api/v1/difficulties")
def difficulties() -> list[dict[str, str]]:
    return [
        {"id": Difficulty.easy, "label": "Easy", "description": "Base Speed tier only"},
        {"id": Difficulty.normal, "label": "Normal", "description": "Level 50 stat with EV and nature"},
        {"id": Difficulty.hard, "label": "Hard", "description": "Items and speed stages"},
        {"id": Difficulty.expert, "label": "Expert", "description": "Weather and abilities"},
        {"id": Difficulty.master, "label": "Master", "description": "Mixed battle conditions"},
    ]


@app.get("/api/v1/teams/me", response_model=UserTeam)
def get_my_team() -> UserTeam:
    return repository.get_team("main")


@app.put("/api/v1/teams/me", response_model=UserTeam)
def save_my_team(team: UserTeam) -> UserTeam:
    return repository.save_team(team)


@app.post("/api/v1/quiz/question-candidates")
def generate_question_candidates(request: GenerateQuizRequest) -> dict[str, object]:
    candidates = quiz_service.generate_candidates(request)
    return {"candidates": candidates}


@app.post("/api/v1/quiz/questions/validate", response_model=ValidatedQuizQuestion)
def validate_question_candidate(candidate: QuizQuestionCandidate) -> ValidatedQuizQuestion:
    return quiz_service.validate_candidate(candidate)


@app.post("/api/v1/quiz/questions/render")
def render_question(request: RenderQuestionRequest) -> dict[str, object]:
    question = quiz_service.render_question(request)
    return {"question": question}


@app.post("/api/v1/quiz/questions")
def generate_questions(request: GenerateQuizRequest) -> dict[str, object]:
    questions = quiz_service.generate_questions(request)
    return {"questions": questions}


@app.post("/api/v1/quiz/answers", response_model=AnswerResult)
def submit_answer(request: AnswerRequest) -> AnswerResult:
    question = quiz_service.get_question(request.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found or expired")
    return AnswerResult(
        correct=request.answer == question.correct_answer,
        correctAnswer=question.correct_answer,
        explanation=question.explanation,
        subjectSpeed=question.subject.speed.effective_speed,
        opponentSpeed=question.opponent.speed.effective_speed,
    )
