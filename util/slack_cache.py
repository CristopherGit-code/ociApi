'''
Need to store:

for each channel ID
    - Ch name
    - Ch messages
    - Last checked time

for each user:
    - User name
    - User main channels
    - User top n channels
    - Last time checked
'''

import logging

logger = logging.getLogger(f'slackbot.{__name__}')

class Cache():
    def __init__(self):
        self.ch_messages = {}
        self.ch_summaries = {}
        self.user_channels = {}
        self.user_recent_channels = {}
        self.user_relevant_channels = 3 # default

    def store_channel_messages(self, channel_id, messages, timestamp):
        self.ch_messages[channel_id] = [messages,timestamp]

    def store_user_channels(self, user_id, channels):
        self.user_channels[user_id] = channels

    # For get latest messages in a channel
    def update_user_recent_ch(self, user_id, channel_id):
        if user_id not in self.user_recent_channels:
            self.user_recent_channels[user_id] = [channel_id]
        else:
            ch_list = self.user_recent_channels[user_id]
            if channel_id not in ch_list:
                if len(ch_list) == self.user_relevant_channels:
                    ch_list.pop()
                    ch_list.insert(0,channel_id)
                else:
                    ch_list.insert(0,channel_id)
            else:
                ch_list.remove(channel_id)
                ch_list.insert(0,channel_id)
        logger.debug(self.user_recent_channels[user_id])
        return self.user_recent_channels[user_id]
    
    def get_latest_channels(self, user_id):
        return self.user_recent_channels[user_id]
    
    def update_channel_limit(self, limit):
        self.user_relevant_channels = limit