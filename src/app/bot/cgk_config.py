from dataclasses import dataclass


@dataclass
class CGKConfig:
    cap_choose_player_time: int = 10
    wait_answer_time: int = 10
    discussion_first: int = 5
    discussion_second: int = 3
    menu: dict = None

    def __init__(self):
        self.menu = {
            "about": (
                "This is a Chto Gde Kogda host.\n"
                "IMPORTANT! Give me Admin rights so I can see messages\n"
                "Send /team_up command to form a team\n"
                "Send /start_game to start game\n"
                "Send /end_game anytime to end the game\n"
            ),
            "rules": "Game rules....",
        }


@dataclass
class CGKState:
    OFF: str = "off"
    TEAM_UP: str = "team_up"
    DISCUSSION: str = "discussion"
    CAPITAN: str = "capitan"
    ANSWER: str = "answer"
    WAIT: str = "wait"
