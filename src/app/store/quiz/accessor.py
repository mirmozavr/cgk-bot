from sqlalchemy import select

from src.app.bot.models import GameModel
from src.app.store.base.base_accessor import BaseAccessor
from src.app.quiz.models import QuestionModel, Question


class QuizAccessor(BaseAccessor):
    async def create_question(self, title: str, answer: str) -> Question:
        async with self.app.database.session.begin() as session:
            question = QuestionModel(
                title=title,
                answer=answer,
            )
            session.add(question)
            return Question(id=question.id, title=title, answer=answer)

    async def get_question_by_title(self, title: str) -> Question | None:
        stmt = select(QuestionModel).where(QuestionModel.title == title)
        async with self.app.database.session.begin() as session:
            result = await session.execute(stmt)
            data = result.scalars().all()
            if data:
                data = data[0]
                return Question(data.id, data.title, data.answer)

    async def get_question_by_id(self, id: int) -> QuestionModel | None:
        stmt = select(QuestionModel).where(QuestionModel.id == int(id))
        async with self.app.database.session.begin() as session:
            result = await session.scalars(stmt)
            return result.one_or_none()

    async def list_questions(self) -> list[Question]:
        stmt = select(QuestionModel)

        async with self.app.database.session.begin() as session:
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

    async def get_question_for_game(self, game: GameModel):
        stmt = (
            select(QuestionModel)
            .where(QuestionModel.id.notin_(list(map(int, game.q_history_to_list()))))
            .limit(1)
        )
        async with self.app.database.session.begin() as session:
            result = await session.scalars(stmt)
            question = result.one_or_none()
            if question is None:
                game.clear_history()
                return await self.get_question_for_game(game)
            return question



