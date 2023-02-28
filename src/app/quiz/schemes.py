from marshmallow import fields, Schema


class QuestionSchema(Schema):
    id = fields.Int(required=False, load_only=True)
    title = fields.Str(required=True)
    answer = fields.Str(required=True)


class ListQuestionSchema(Schema):
    questions = fields.Nested(QuestionSchema, many=True)
