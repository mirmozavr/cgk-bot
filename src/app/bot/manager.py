import asyncio
import typing as t
from pprint import pprint

from sqlalchemy.exc import IntegrityError

from src.app.bot.cgk_config import CGKConfig, CGKState
from src.app.bot.models import GameModel, PlayerModel
from src.app.store.tg_api.dataclasses import Message, Update, CallbackQuery

if t.TYPE_CHECKING:
    from src.app.web.app import Application

cgk_config = CGKConfig()
cgk_state = CGKState()


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_update(self, update: Update):
        pprint(update)
        if update.message:
            await self.handle_message(update.message)
        elif update.callback_query:
            await self.handle_callback_query(update.callback_query)

    async def handle_message(self, message: Message):
        # Get a Game object if game in database, else create new Game and add to database
        game = await self.app.store.tg_api.get_game_by_message(message)
        if game is None:
            game = await self.app.store.tg_api.create_game_by_message(message)

        print("at start")
        pprint(game)

        # skip messages if in discussion
        if game.status == cgk_state.DISCUSSION and message.text[1:] != "end_game":
            return
        # handle menu commands
        elif self.extract_command(message) in cgk_config.menu:
            await self.app.store.tg_api.send_message(
                game.id, cgk_config.menu[self.extract_command(message)]
            )
            return
        elif self.extract_command(message) == "group_stats":
            await self.app.store.tg_api.send_message(game.id, game.statistic)
        elif self.extract_command(message) == "player_stats":
            player = await self.app.store.tg_api.get_player_by_id(message.user.id)
            await self.app.store.tg_api.send_message(game.id, player.statistic)

        # Handle commands
        # Send join team inline buttons
        elif (
            game.status == cgk_state.OFF and self.extract_command(message) == "team_up"
        ):
            game.status = cgk_state.TEAM_UP
            await self.app.store.tg_api.send_inline_button(message, "join")

        # start_game, start sending questions
        elif (
            game.status == cgk_state.TEAM_UP
            and self.extract_command(message) == "start_game"
            and game.team_size > 0
        ):
            game.shuffle_team()
            # declare a capitan to the group
            capitan = await self.app.store.tg_api.get_capitan(game)
            await self.app.store.tg_api.send_message(
                game.id, f"{capitan.first_name} is a capitan of the team"
            )
            await asyncio.sleep(1)
            await self.send_question(game)

        # end_game, clear game
        elif self.extract_command(message) == "end_game":
            game.canceled += 1
            await self.app.store.tg_api.remove_buttons(
                game, f"Game ended by {message.user.first_name}"
            )
            game.clear_game()

        # CAPITAN choose the responder
        elif game.status == cgk_state.CAPITAN:
            time_spent = message.date - game.update_time
            if time_spent > cgk_config.TIME_LIMIT_CAPITAN:
                game.score_host += 1
                await self.app.store.tg_api.remove_buttons(
                    game, f"Player select is late! Round lost\n{game.score}"
                )
                game.status = cgk_state.WAIT
            elif (
                time_spent <= cgk_config.TIME_LIMIT_CAPITAN
                and message.user.id == game.cap_id
            ):
                responder = await self.app.store.tg_api.get_player_by_name(
                    game, message.text
                )
                print("responder", responder)
                if responder:
                    game.responder_id = responder.id
                    game.status = cgk_state.ANSWER
                    update_time = await self.app.store.tg_api.remove_buttons(
                        game,
                        f"{responder.first_name}, send your answer in {cgk_config.TIME_LIMIT_ANSWER} sec!!!",
                    )
                    game.update_time = update_time

        # RESPONDER is answering
        elif game.status == cgk_state.ANSWER:
            time_spent = message.date - game.update_time
            responder = await self.app.store.tg_api.get_player_by_id(message.user.id)
            if time_spent > cgk_config.TIME_LIMIT_ANSWER:
                game.score_host += 1
                game.status = cgk_state.WAIT
                responder.ans_late += 1
                await self.app.store.tg_api.send_message(
                    game.id, f"Answer is late! Round lost\n{game.score}"
                )

            elif (
                time_spent <= cgk_config.TIME_LIMIT_ANSWER
                and message.user.id == game.responder_id
            ):
                last_question = await self.app.store.quiz.get_question_by_id(
                    game.last_question_id
                )
                if last_question.check_answer(message.text):
                    game.score_team += 1
                    game.status = cgk_state.WAIT
                    responder.ans_correct += 1
                    await self.app.store.tg_api.send_message(
                        game.id, f"Correct!!!\n{game.score}"
                    )
                else:
                    game.score_host += 1
                    game.status = cgk_state.WAIT
                    responder.ans_wrong += 1
                    await self.app.store.tg_api.send_message(
                        game.id,
                        f"Wrong!!! Correct answer: {last_question.answer}\n{game.score}",
                    )
            await self.update_player_db(responder)
        # check if game finished
        await self.check_game_finished(game)
        # update db with game object
        await self.update_game_db(game)

        # at the end check if need to send next question
        print("At end")
        pprint(game)
        if game.status == cgk_state.WAIT:
            await self.send_question(game)

    async def send_question(self, game: GameModel) -> None:
        """
        Send question
        :param game: GameModel object
        :return:
        """
        game.status = cgk_state.DISCUSSION
        question = await self.app.store.quiz.get_question_for_game(game)
        game.add_question_to_history(question.id)
        await self.app.store.tg_api.send_message(game.id, question.title)
        await asyncio.sleep(cgk_config.TIME_LIMIT_DISC_MAIN)
        await self.app.store.tg_api.send_message(
            game.id, f"{cgk_config.TIME_LIMIT_DISC_EXTRA} seconds remaining"
        )
        await asyncio.sleep(cgk_config.TIME_LIMIT_DISC_EXTRA)
        game.status = cgk_state.CAPITAN
        update_time = await self.app.store.tg_api.send_choose_responder_buttons(
            game,
            f"Cap, who will answer?\n{cgk_config.TIME_LIMIT_CAPITAN} sec to choose",
        )
        game.update_time = update_time

        await self.update_game_db(game)

    async def handle_callback_query(self, cq: CallbackQuery):
        game = await self.app.store.tg_api.get_game_by_message(cq.message)

        if not (game.status == cgk_state.TEAM_UP and cq.data == "join"):
            # handle random cq requests
            await self.app.store.tg_api.answer_cq(cq, "")
            return

        if game.team_size >= 6:
            await self.app.store.tg_api.answer_cq(cq, "Team is full :(")
            return
        if game.check_player_in_team(cq.user.id):
            await self.app.store.tg_api.answer_cq(cq, "You already in the team")
            return

        try:
            await self.app.store.tg_api.create_player_by_message(cq)
        except IntegrityError:
            pass

        game.add_player_to_team(cq.user.id)
        usr = f"@{cq.user.username}" if cq.user.username else cq.user.first_name
        await self.app.store.tg_api.answer_cq(cq, "You are in the team")
        await self.app.store.tg_api.send_message(game.id, f"{usr} joined the team!")
        if game.team_size == 6:
            await self.app.store.tg_api.send_message(game.id, "Team is full")

        await self.update_game_db(game)
        print("After CQ")
        pprint(game)

    async def check_game_finished(self, game: GameModel):
        if 6 not in (game.score_team, game.score_host):
            return
        if game.score_host == 6:
            game.loses += 1
            await self.app.store.tg_api.send_message(
                game.id, f"Host won.\n{game.score}"
            )
        elif game.score_team == 6:
            game.wins += 1
            await self.app.store.tg_api.send_message(
                game.id, f"Team won. Congrats!\n{game.score}"
            )
        game.clear_game()

    async def update_game_db(self, game: GameModel):
        async with self.app.database.session.begin() as session:
            session.add(game)

    async def update_player_db(self, player: PlayerModel):
        async with self.app.database.session.begin() as session:
            session.add(player)

    @staticmethod
    def extract_command(message: Message):
        return message.text.split("@")[0][1:]
