from slack_sdk.web.client import WebClient
from slack_sdk.errors import SlackApiError
import logging, time
from datetime import datetime, timedelta

logger = logging.getLogger(f'slackbot.{__name__}')

class Slack_Metadata:
    def __init__(self, bot_client: WebClient, user_client: WebClient):
        self.messages = []
        self._bot_client = bot_client
        self._user_client = user_client

    def get_user_name(self, user_id):
        response = self._bot_client.users_info(user=user_id) #bot access to the user info, profile, name, channels, etc.
        profile = response['user']['profile']
        real_name = profile.get('display_name') or profile.get('real_name') or user_id ## get the information from bot client
        return real_name
    
    def get_channel_name(self, channel_id):
        response = self._user_client.conversations_info(channel=channel_id)
        ch_profile = response['channel']['name']
        return ch_profile
    
    def get_user_channels(self, user_id):
        u_channels = []
        cursor = None
        
        while True:
            response = self._bot_client.users_conversations(
                user=user_id,
                types='public_channel',
                cursor=cursor,
                limit = 100
            )
            if 'channels' in response and isinstance(response['channels'],list):
                u_channels.extend(response['channels'] or [])
            if not cursor:
                break
            time.sleep(0.5)
        return [(channel['id'],channel['name']) for channel in u_channels]
    
    def _get_messages(self, channel_id, days, limit):
        if not days:
            days = 30 # default

        now = datetime.now()
        past_days = now - timedelta(days=days)
        timestamp = str(past_days.timestamp())

        if not limit:
            limit = 1000

        messages = []
        cursor = None

        while len(messages) < limit:
            try:
                result = self._user_client.conversations_history(
                    channel=channel_id,
                    oldest=timestamp,
                    limit=min(limit-len(messages),1000),
                    cursor=cursor,
                    include_all_metadata=False,
                    inclusive=False
                )
                messages.extend(result.get('messages',[]))
                if result['response_metadata']:
                    cursor = result['response_metadata'].get('next_cursor', None)
                else:
                    break
            except SlackApiError as v:
                # In case of API not responding, fix the rate limits
                logger.debug(f'Loop exception: {v} \n------------------------------\n')
                break
            time.sleep(0.5)

        return messages
    
    # Missing to implement thread messages
    def get_thread_replies(self, channel_id, thread_ts):
        result = self._user_client.conversations_replies(channel=channel_id, ts=thread_ts)
        messagess = result.get('messages', [])

        return messagess

    def get_messages(self, channel_id, days, limit, thread_ts = None):
        # missing to retrieve messages from threads
        if thread_ts:
            replies = self.get_thread_replies(channel_id,thread_ts)
            header = f'Thread history for message: {thread_ts}[{len(replies)}]:\n'
            parts = [
                f'-<@{self.get_user_name(m.get('user','unknown'))}>: {m.get('text','no text')}' for m in replies
            ]
        
        messages = self._get_messages(channel_id, days, limit)
        thread_replies = []

        for message in messages:
            replies = [message]
            header = ''
            parts = [
            f'-<@{self.get_user_name(m.get('user'))}> : {m.get('text','[no text]')}' for m in replies
            ]
            thread_replies.append(header + '\n'.join(parts))
        return thread_replies