from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Integer, Column, String

from src.app.store.database import Base


@dataclass
class Question:
    id: Optional[int]
    title: str
    answer: str


class QuestionModel(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    answer = Column(String, unique=False, nullable=False)

    def __repr__(self):
        return f"QuestionModel(id={self.id!r}, title={self.title!r}, answer={self.answer!r})"
