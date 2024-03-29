import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from src.app.quiz.models import Question, QuestionModel
from src.app.quiz.schemes import QuestionSchema
from src.app.store import Store
from src.tests.utils import check_empty_table_exists
from src.tests.utils import ok_response


class TestQuestionsStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "questions")
        await check_empty_table_exists(cli, "players")
        await check_empty_table_exists(cli, "games")

    async def test_create_question(self, cli, store: Store):
        question_title, question_answer = "title", "answer"
        question = await store.quiz.create_question(question_title, question_answer)
        assert type(question) is Question

        async with cli.app.database.session() as session:
            res = await session.execute(select(QuestionModel))
            questions = res.scalars().all()

        assert len(questions) == 1, "Length is not 1"
        db_question = questions[0]

        assert db_question.title == question_title, "Wrong title"
        assert db_question.answer == question_answer, "Wrong answer"

    async def test_create_question_miss_field(self, cli, store: Store):
        question_title, question_answer = "title", "answer"
        with pytest.raises(IntegrityError) as exc_info:
            await store.quiz.create_question(question_title, None)
        assert exc_info.value.orig.pgcode == "23502"

        with pytest.raises(IntegrityError) as exc_info:
            await store.quiz.create_question(None, question_answer)
        assert exc_info.value.orig.pgcode == "23502"

    async def test_create_question_unique_title_constraint(
        self, cli, store: Store, question_1: Question
    ):
        with pytest.raises(IntegrityError) as exc_info:
            await store.quiz.create_question(question_1.title, question_1.answer)
        assert exc_info.value.orig.pgcode == "23505"

    async def test_get_question_by_title(self, cli, store: Store, question_1: Question):
        assert question_1 == await store.quiz.get_question_by_title(question_1.title)

    async def test_list_questions(
        self, cli, store: Store, question_1: Question, question_2: Question
    ):
        questions = await store.quiz.list_questions()
        assert questions == [question_1, question_2]


class TestQuestionAddView:
    async def test_success(self, authed_cli):
        question_title, question_answer = "title", "answer"
        resp = await authed_cli.post(
            "/quiz.add_question",
            json={"title": question_title, "answer": question_answer},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response({"title": question_title, "answer": question_answer})

    async def test_unauthorized(self, cli):
        resp = await cli.post(
            "/quiz.add_question",
            json={"title": "How many legs does an octopus have?", "answer": "8"},
        )
        assert resp.status == 401
        data = await resp.json()
        assert data["status"] == "unauthorized"


class TestQuestionListView:
    async def test_unauthorized(self, cli):
        resp = await cli.get("/quiz.list_questions")
        assert resp.status == 401
        data = await resp.json()
        assert data["status"] == "unauthorized"

    async def test_empty(self, authed_cli):
        resp = await authed_cli.get("/quiz.list_questions")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(data={"questions": []})

    async def test_one_question(self, authed_cli, question_1):
        resp = await authed_cli.get("/quiz.list_questions")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            data={"questions": [QuestionSchema().dump(question_1, many=False)]}
        )

    async def test_several_questions(
        self, authed_cli, question_1: Question, question_2
    ):
        resp = await authed_cli.get("/quiz.list_questions")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            data={
                "questions": QuestionSchema().dump([question_1, question_2], many=True)
            }
        )
