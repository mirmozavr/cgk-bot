from dataclasses import dataclass


@dataclass
class CGKConfig:
    TIME_LIMIT_CAPITAN: int = 5
    TIME_LIMIT_ANSWER: int = 5
    TIME_LIMIT_DISC_MAIN: int = 5
    TIME_LIMIT_DISC_EXTRA: int = 5
    menu: dict = None

    def __init__(self):
        self.menu = {
            "about": (
                "This is a Chto Gde Kogda host.\n"
                "IMPORTANT! Give me Admin rights so I can see messages\n"
                "Send /rules to read the game rules\n"
                "Send /team_up to form a team\n"
                "Send /start_game to start game\n"
                "Send /end_game anytime to end the game\n"
                "Send /group_stats to see group statistic\n"
                "Send /player_stats to see personal statistic\n"
            ),
            "rules": (
                f"Game is played up to 6 points. {self.TIME_LIMIT_DISC_MAIN+self.TIME_LIMIT_DISC_EXTRA} sec to discuss"
                "Randomly selected capitan will choose the player, who will answer"
                "If answer is correct, team will gain 1 point, otherwise host will gain 1 point."
                "Also if capitan spent too much time choosing player, or answering player"
                "spent too much time answering, host will gain 1 point"
                "\nGood luck!"
            ),
        }


@dataclass
class CGKState:
    OFF: str = "off"
    TEAM_UP: str = "team_up"
    DISCUSSION: str = "discussion"
    CAPITAN: str = "capitan"
    ANSWER: str = "answer"
    WAIT: str = "wait"
