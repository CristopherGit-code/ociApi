from dotenv import load_dotenv
import os

#Use .env file to set

load_dotenv()

#Slack App variables
SLACK_APP = os.environ["SLACK_APP_LEVEL_KEY"]
SLACK_BOT_LEVEL_KEY = os.getenv("SLACK_BOT_LEVEL_KEY")
SLACK_USER_LEVEL_KEY = os.getenv("SLACK_USER_LEVEL_KEY")
SLACK_SIGNIN_SECRET_KEY = os.getenv("SLACK_SIGNIN_SECRET_KEY")

#Error handling
if not SLACK_APP:
  raise ValueError("Not Slack App Level Key set")

if not SLACK_BOT_LEVEL_KEY:
  raise ValueError("Not Slack Bot Level Key set")

if not SLACK_USER_LEVEL_KEY:
  raise ValueError("Not Slack User Level Key set")

if not SLACK_SIGNIN_SECRET_KEY:
  raise ValueError("Not Slack Secret Key set")