from backend.config_reader import config
test_bot = int(config.test_bot_id.get_secret_value())
local_domain = "http://127.0.0.1"
global_domain = config.global_domain.get_secret_value()


BOT_TOKEN = config.bot_token.get_secret_value()
BOT_LOGIN = config.bot_login.get_secret_value()

BOT_ID = test_bot
BOT_DOMAIN = global_domain

print(BOT_DOMAIN, BOT_ID, BOT_LOGIN, BOT_TOKEN)