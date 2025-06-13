import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from util.home_manager import HomeManager
from util.llm_client import LLM_Client
from util.slack_cache import Cache
from slack_sdk.web.client import WebClient
from config import (
    SLACK_SIGNIN_SECRET_KEY,
    SLACK_APP,
    SLACK_BOT_LEVEL_KEY,
    SLACK_USER_LEVEL_KEY
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(f'slackbot.{__name__}')

class SlackInnoBot:
    def __init__(self):
        self.app = App(token=SLACK_BOT_LEVEL_KEY, signing_secret=SLACK_SIGNIN_SECRET_KEY)
        self.user_client = WebClient(token=SLACK_USER_LEVEL_KEY)
        self.user_bot = WebClient(token=SLACK_BOT_LEVEL_KEY)

        #Start bot home
        self.ll_client = LLM_Client()
        self.slack_cache = Cache()
        self.bot_home = HomeManager(self.app, self.user_bot, self.user_client, self.slack_cache)
        self.main_handlers()
        self.bot_home.manage_handlers()

    def Main_Start(self):
        SocketModeHandler(self.app, SLACK_APP).start()

    def main_handlers(self):
        @self.app.event('message')
        def handle_message(message,say,event,body):
            if message['channel_type'] == 'im':
                if self.bot_home.is_in_summary:
                    question = message['text']
                    ch_summary = self.bot_home.command_summary
                    instructions = f'Respond using ONLY the information and context from the following conversation: {self.bot_home.summary_ch_reference} and the summary: {ch_summary}'
                    response = self.process_chat_request(question, instructions)
                    say(response)
                else:
                    say(f"{self.process_chat_request(message['text'])}")
            elif message['channel_type'] == 'channel':
                self.slack_cache.update_user_recent_ch(event['user'],event['channel'])
            else:
                pass
        # Answer a message in-place (to the channel requested)
        @self.app.shortcut("ans_message")
        def ansMessageSc(ack, shortcut, say):
            ack()
            say(f"{self.process_chat_request(shortcut['message']['text'])}")

        #global shortcut to start a chat (DM) with the bot
        @self.app.shortcut("chat_global")
        def chatGlobal(ack,shortcut,say):
            ack()
            say(text=f"{self.process_chat_request("Hello, what can you help me with?")}",channel=shortcut['user']['id'])

        #Mention the app to chat -----------------------------
        @self.app.event("app_mention")
        def answerMention(event,say):
            say(f"{self.process_chat_request(event['text'])}")
        #-----------------------------------------------------

    def process_chat_request(self, prompt, instructions = ''):
        return self.ll_client.botConversation(prompt, instructions)

if __name__== '__main__':
    logger.debug(f'Starting App...')
    bot = SlackInnoBot()
    bot.Main_Start()