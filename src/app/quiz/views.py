from aiohttp_apispec import request_schema, response_schema

from src.app.quiz.schemes import QuestionSchema, ListQuestionSchema
from src.app.web.app import View
from src.app.web.mixins import AuthRequiredMixin
from src.app.web.utils import json_response


class QuestionAddView(AuthRequiredMixin, View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        data = self.data
        title, answer = data["title"], data["answer"]
        question = await self.store.quiz.create_question(title, answer)
        return json_response(data=QuestionSchema().dump(question))


class QuestionListView(AuthRequiredMixin, View):
    @response_schema(ListQuestionSchema)
    async def get(self):
        questions = await self.request.app.store.quiz.list_questions()
        return json_response(
            data={"questions": QuestionSchema().dump(questions, many=True)}
        )
