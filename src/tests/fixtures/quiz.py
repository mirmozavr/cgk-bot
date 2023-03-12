import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.quiz.models import (
    Question,
    QuestionModel,
)


@pytest.fixture
async def question_1(db_session: AsyncSession) -> Question:
    title = "how are you?"
    answer = "fine"
    async with db_session.begin() as session:
        question = QuestionModel(title=title, answer=answer)

        session.add(question)

    return Question(id=question.id, title=title, answer=answer)


@pytest.fixture
async def question_2(db_session: AsyncSession) -> Question:
    title = "are you fine?"
    answer = "yes"
    async with db_session.begin() as session:
        question = QuestionModel(title=title, answer=answer)

        session.add(question)

    return Question(id=question.id, title=title, answer=answer)
