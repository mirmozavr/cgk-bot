## Chto Gde Kogda simulator telegram bot

### Setup
1) Install python 3.8 or higher
2) Create new virtual environment `python -m venv venv`
3) Activate created environment `source venv/bin/activate`
4) Install dependencies `pip install requirements.txt`
5) Create environment configuration file `dev.env.yaml` for development
or `prod.env.yaml` in `src/env` directory
6) Production and development environment is regulated by `dev_config` parameter (at `main.py` entrypoint)
7) Env file example:  
   ```
   bot:
     token: bot_token_from_botfather
   
   database:
     host: 0.0.0.0
     port: 5432
     user: db_username
     password: db_password
     db_name: db_name
   
   session:
     key: session_key_by_fernet
   
   admin:
     email: admin@admin.com
     password: admin
   ```
    * bot token: telegram bot API token, received from BotFather
    * session key: generate this key using fernet from cryptography module
   ```
   from cryptography import fernet
   fernet.Fernet.generate_key().decode()
   ```
   * database: postgres database parameters
   * admin: admin credentials for admin API
8) Prepare database and run migrations via alembic
9) Adjust time limits for in-game decision-making with TIME_LIMIT variables at `src/app/bot/cgk_config.py`
### Run
To run server on localhost run `python3 ./src/main.py` from project directory

### Admin API

Admin API provides following methods:
* /admin.login - Authorize user
* /admin.current - Get current user (authorization required)
* /quiz.add_question - Add new question (authorization required)
* /quiz.list_questions - Get list of all questions (authorization required)
Documentation on methods and schemas is provided via api-spec library at `/docs`

### Chto? Gde? Kogda? Game rules

After team is formed and capitan is randomly selected amongst team. 
After every question team will have some time to discuss the answer. After discussion time capitan must 
choose the player, that will give an answer. If answer is correct, team will gain 1 point, 
otherwise host will gain 1 point. Also, if capitan spent too much time choosing player, or answering player 
spent too much time answering, host will gain 1 point. Game is played up to 6 points, if team reaches 6 points 
before host does, team wins. Otherwise, host wins.

#### Bot commands
 * /about to get command list and information
 * /rules to read the game rules
 * /team_up to form a team
 * /start_game to start game
 * /end_game anytime to end the game
 * /group_stats to see group statistic
 * /player_stats to see personal statistic

#### Hot wo play
1) Create a telegram group
2) Add the bot to group via mention @cgkhost_bot or [Telegram URL](https::/t.me/cghhost_bot)
3) Give the bot administrator permissions, or he will not see any messages and won't work
4) Invite your friends to group
5) Firstly initiate team by using /team_up command (available to everyone)
6) Inline button will be sent to group chat. Players, who want to play, should press that button. Max team size
is 6 players. Team should have at least 1 player, or it will not start
7) Use /start_game to start getting questions
8) Capitan of the team will be randomly selected by host and declared in chat
9) After receiving the question team will have time to discuss
10) Then capitan of the team will have some time to choose the player, that will send the answer.
That will be done by reply buttons with players names on them. Time to select player is limited!
11) When answering player is selected, he will have limited time to send his answer. After checking the 
answer for correctness, the scores will be updated and announced
12) The goal is to reach 6 points for the win. After that game will end, and you should repeat this algorythm again 
from step 4.
13) Send /end_game anytime to finish the game. It will count as cancelled game in group statistics.
14) You can check your group stats by /group_stats or personal stats overall all groups you are in by /player_stats