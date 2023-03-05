import asyncio
import typing as t
from pprint import pprint

from sqlalchemy.exc import IntegrityError

from src.app.bot.models import GameModel
from src.app.store.tg_api.dataclasses import Message, Update, CallbackQuery

if t.TYPE_CHECKING:
    from src.app.web.app import Application

menu = {"about": "This is a Chto Gde Kogda host", "rules": "Game rules...."}


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_update(self, update: Update):
        print("# " * 30)
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
        if game.status == "discussion" and message.text[1:] != "end_game":
            return
        # handle menu commands
        elif message.text[1:] in menu:
            await self.app.store.tg_api.send_message(
                chat_id=game.id, text=menu[message.text[1:]]
            )
            return

        # Handle commands
        # Send join team inline buttons
        elif message.text[1:] == "team_up" and game.status == "off":
            game.status = "team_up"
            await self.app.store.tg_api.send_inline_button(message, "join")

        # start game, start sending questions
        elif (
            message.text[1:] == "start_game"
            and game.status == "team_up"
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
        elif message.text[1:] == "end_game":
            await self.app.store.tg_api.remove_buttons(game, f"Game ended by {message.user.first_name}")
            game.clear_game()

        # CAPITAN choose the responder
        elif game.status == "capitan" and message.user.id == game.cap_id:
            choose_time_spent = message.date - game.update_time
            print("CHOOSE TIME SPENT", choose_time_spent)
            if choose_time_spent > 10:
                game.score_host += 1
                await self.app.store.tg_api.remove_buttons(
                    game, f"Player select is late! Round lost\n{game.score}"
                )
                game.status = "wait"
            else:
                responder = await self.app.store.tg_api.get_player_by_name(
                    game, message.text
                )
                print("responder", responder)
                if responder:
                    game.responder_id = responder.id
                    game.status = "answer"
                    update_time = await self.app.store.tg_api.remove_buttons(
                        game, f"{responder.first_name}, send your answer in 10 sec!!!"
                    )
                    game.update_time = update_time

                # else:
                #     await self.app.store.tg_api.reply_to_message(
                #         message, f"Don't get it..."
                #     )

        # RESPONDER is answering
        elif game.status == "answer" and message.user.id == game.responder_id:
            answer_time_spent = message.date - game.update_time
            print(
                "answer TIME SPENT", answer_time_spent, game.update_time, message.date
            )
            if answer_time_spent > 10:
                game.score_host += 1
                game.status = "wait"
                await self.app.store.tg_api.send_message(
                    game.id, f"Answer is late! Round lost\n{game.score}"
                )

            else:
                last_question = await self.app.store.quiz.get_question_by_id(
                    game.last_question_id
                )
                if last_question.check_answer(message.text):
                    game.score_team += 1
                    game.status = "wait"
                    await self.app.store.tg_api.send_message(
                        game.id, f"Correct!!!\n{game.score}"
                    )
                else:
                    game.score_host += 1
                    game.status = "wait"
                    await self.app.store.tg_api.send_message(
                        game.id,
                        f"Wrong!!! Correct answer: {last_question.answer}\n{game.score}",
                    )
        # check if game finished
        await self.check_game_finished(game)
        # update db with game object
        async with self.app.database.session.begin() as session:
            session.add(game)

        # at the end check if need to send next question
        print("At end")
        pprint(game)
        if game.status == "wait":
            print("At finish status is WAIT")
            await self.send_question(game)

    async def send_question(self, game: GameModel) -> None:
        """
        Send question
        :param game: GameModel object
        :return:
        """
        print("Send question")
        game.status = "discussion"
        question = await self.app.store.quiz.get_question_for_game(game)
        game.add_question_to_history(question.id)
        await self.app.store.tg_api.send_message(game.id, question.title)
        await asyncio.sleep(3)
        await self.app.store.tg_api.send_message(game.id, "20 seconds remaining")
        await asyncio.sleep(3)
        game.status = "capitan"
        update_time = await self.app.store.tg_api.send_choose_responder_buttons(
            game, "Cap, who will answer?\n10 sec to choose"
        )
        game.update_time = update_time

        async with self.app.database.session.begin() as session:
            session.add(game)

    async def handle_callback_query(self, cq: CallbackQuery):
        game = await self.app.store.tg_api.get_game_by_message(cq.message)

        if cq.data == "join" and game.status == "team_up":
            if game.team_size >= 6:
                await self.app.store.tg_api.answer_cq(cq, "Team is full :(")
            elif game.check_player_in_team(cq.user.id):
                await self.app.store.tg_api.answer_cq(cq, "You already in the team")
            else:
                try:
                    await self.app.store.tg_api.create_player_by_message(cq)
                except IntegrityError:
                    pass

                game.add_player_to_team(cq.user.id)
                usr = f"@{cq.user.username}" if cq.user.username else cq.user.first_name
                await self.app.store.tg_api.answer_cq(cq, "You are in the team")
                await self.app.store.tg_api.send_message(
                    cq.message.chat.id, f"{usr} joined the team!"
                )
                if game.team_size == 6:
                    await self.app.store.tg_api.send_message(
                        cq.message.chat.id, "Team is full"
                    )

        else:
            # handle random cq requests
            await self.app.store.tg_api.answer_cq(cq, "")
        async with self.app.database.session.begin() as session:
            session.add(game)
        print("After CQ")
        pprint(game)

    async def check_game_finished(self, game: GameModel):
        if 6 not in (game.score_team, game.score_host):
            return
        if game.score_host == 6:
            await self.app.store.tg_api.send_message(
                game.id, f"Host won.\n{game.score}"
            )
        elif game.score_team == 6:
            await self.app.store.tg_api.send_message(
                game.id, f"Team won. Congrats!\n{game.score}"
            )
        game.clear_game()
