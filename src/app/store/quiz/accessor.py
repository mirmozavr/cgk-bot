from sqlalchemy import select

from src.app.store.base.base_accessor import BaseAccessor
from src.app.quiz.models import QuestionModel, Question


class QuizAccessor(BaseAccessor):
    async def create_question(self, title: str, answer: str) -> Question:
        async with self.app.database.session as session:
            question = QuestionModel(
                title=title,
                answer=answer,
            )
            session.add(question)
            return Question(id=question.id, title=title, answer=answer)

    async def get_question_by_title(self, title: str) -> Question | None:
        stmt = select(QuestionModel).where(QuestionModel.title == title)
        async with self.app.database.session as session:
            result = await session.execute(stmt)
            data = result.scalars().all()
            if data:
                data = data[0]
                return Question(data.id, data.title, data.answer)

    async def list_questions(self) -> list[Question]:
        stmt = select(QuestionModel)

        async with self.app.database.session as session:
            result = await session.execute(stmt)
            questions = result.scalars().all()
            return [
                Question(
                    q.id,
                    q.title,
                    q.answer,
                )
                for q in questions
            ]
