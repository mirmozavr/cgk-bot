from dataclasses import dataclass
from random import sample

from sqlalchemy import Integer, Column, String, BigInteger

from src.app.store.database.sqlalchemy_base import Base


@dataclass
class Game:
    id: int
    status: str = "off"
    score_host: int = 0
    score_team: int = 0
    team: str = ""
    q_history: str = ""
    update_time: int = None


class GameModel(Base):
    __tablename__ = "games"
    id = Column(BigInteger, primary_key=True)
    status = Column(String, default="off", nullable=False)
    score_host = Column(Integer, default=0, nullable=False)
    score_team = Column(Integer, default=0, nullable=False)
    team = Column(String, default="", nullable=False)
    q_history = Column(String, default="", nullable=False)
    update_time = Column(Integer, nullable=True)
    responder_id = Column(Integer, nullable=True)
    wins = Column(Integer, default=0, nullable=False)
    loses = Column(Integer, default=0, nullable=False)
    canceled = Column(Integer, default=0, nullable=False)

    def q_history_to_list(self):
        return [item for item in self.q_history.split()]

    def list_to_q_history(self, lst: list):
        self.q_history = " ".join(lst)

    def add_question_to_history(self, question_id):
        lst = self.q_history_to_list()
        lst.append(str(question_id))
        self.list_to_q_history(lst)

    def check_question_in_history(self, question_id):
        return str(question_id) in self.q_history_to_list()

    def clear_history(self):
        self.q_history = ""

    @property
    def last_question_id(self):
        return self.q_history_to_list()[-1] if self.q_history else None

    def team_to_list(self):
        return [item for item in self.team.split()]

    def list_to_team(self, lst: list):
        self.team = " ".join(lst)

    def add_player_to_team(self, player_id):
        lst = self.team_to_list()
        lst.append(str(player_id))
        self.list_to_team(lst)

    def check_player_in_team(self, player_id):
        return str(player_id) in self.team_to_list()

    def shuffle_team(self):
        lst = self.team_to_list()
        self.list_to_team(sample(lst, len(lst)))

    @property
    def cap_id(self):
        return int(self.team_to_list()[0]) if self.team_size > 0 else None

    @property
    def team_size(self):
        return len(self.team_to_list())

    def clear_team(self):
        self.team = ""

    def clear_game(self):
        self.status = "off"
        self.team = ""
        self.responder_id = None
        self.score_team = self.score_host = 0

    @property
    def score(self):
        return f"TEAM: {self.score_team}\nHOST: {self.score_host}"

    @property
    def statistic(self):
        return f"Group stats:\nWins: {self.wins}\nLoses: {self.loses}\nCanceled: {self.canceled}"

    def __repr__(self):
        return (
            f"{self.__class__.__name__} (id: {self.id}\n"
            f"status: {self.status}\n"
            f"score_host: {self.score_host}\n"
            f"score_team: {self.score_team}\n"
            f"team: {self.team}\n"
            f"q_history: {self.q_history}\n"
            f"responder_id: {self.responder_id}\n"
            f"update_time: {self.update_time})\n"
        )


class PlayerModel(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    ans_correct = Column(Integer, nullable=False, default=0)
    ans_wrong = Column(Integer, nullable=False, default=0)
    ans_late = Column(Integer, nullable=False, default=0)

    @property
    def statistic(self):
        return (
            f"Personal stats:\nCorrect answers: {self.ans_correct}\n"
            f"Wrong answers: {self.ans_wrong}\n"
            f"Late answers: {self.ans_late}"
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__} ({self.id}\n"
            f"username: {self.username}\n"
            f"first_name: {self.first_name}\n"
        )
