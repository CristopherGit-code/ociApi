from slack_bolt import App
import logging, re
from util.slack_metadata import Slack_Metadata
from .llm_client import LLM_Client
from datetime import datetime

logger = logging.getLogger(f'slackbot.{__name__}')

class HomeManager:
    def __init__(self, app:App, bot_client, user_client, cache):
        self.app = app
        self.slack_metadata = Slack_Metadata(bot_client,user_client)
        self.slack_cache = cache # Fix object inheritance, missing
        self.user_top_channels = {}
        self.user_active_channel = {}
        self.command_summary = ''
        self.is_in_summary = False
        self.summary_ch_reference = ''
        self.user_days = 7
        self.user_instructions = ''
        self.user_m_limit = 100
        self.custom_user_ch = 3

        self.llm_client = LLM_Client()
    
    def update_u_top_channels(self, user_id):
        channels = []
        try:
            u_channels = self.slack_cache.get_latest_channels(user_id)
        except Exception as e:
            u_channels = self.slack_metadata.get_user_channels(user_id)
            self.user_top_channels[user_id] = u_channels
            return u_channels[:self.custom_user_ch] #only lastest channels
        
        for ch in u_channels:
            name = self.slack_metadata.get_channel_name(ch)
            channels.append((ch,name))
        self.user_top_channels[user_id] = channels

        return channels[:self.custom_user_ch] #channels set in settings

    # Update messages only if there has been a minute
    def check_channel_messages(self, channel_id, timestamp):
        messages = ''
        if channel_id not in self.slack_cache.ch_messages:
            messages = self.slack_metadata.get_messages(channel_id,self.user_days,self.user_m_limit)
            self.slack_cache.ch_messages[channel_id] = [messages,timestamp]
        else:
            storage = int(self.slack_cache.ch_messages[channel_id][1])
            difference = timestamp - storage
            if difference > 120: # around 1 minute
                messages = self.slack_metadata.get_messages(channel_id,self.user_days,self.user_m_limit)
                now = str(datetime.now().timestamp())
                time_mark = int(now[:10])
                self.slack_cache.ch_messages[channel_id] = [messages,time_mark]
            else:
                messages = self.slack_cache.ch_messages[channel_id]
        return messages

    def build_home_blocks(self, channels='example', channel_name='test', summary_text=None):
        blocks = [{'type':'section', 'text': {'type':'mrkdwn','text':'*Top channels summary*'}}]
        button_row = []
        for idx,ch in enumerate(channels):
            button_row.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"#{ch[1]}", #name channel
                    },
                    "style": "primary",
                    "action_id": f"channel_{idx}",
                    "value": ch[0] #channel ID
                }
            )
        button_row.append({
            "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Settings",
                    },
                    "style": "primary",
                    "action_id": "open_settings",
                    "value": 'settings'
        })
        blocks.append({'type':'actions', 'elements': button_row})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*This is the summary of the channel: * {channel_name}"
                },
            }
        )
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary_text
                }
            }
        )
        logger.debug(f'This is loger #{channel_name}')
        return blocks

    def update_home_tab(self, client, c_user_id='0', channel_id = '', channel_name=''):
        #update channel and user data
        channels = self.update_u_top_channels(c_user_id)
        now = str(datetime.now().timestamp())
        time_mark = int(now[:10])
        ch_messages = self.check_channel_messages(channel_id,time_mark)

        #maybe add to the prompt the name conversions instead of parsing in the function
        prompt = f'summarize the following conversation from a channel in less than 6 bullet points: {ch_messages}.'
        summary_text = self.llm_client.botConversation(prompt, self.user_instructions)
        blocks = self.build_home_blocks(channels, channel_name, summary_text)
        client.views_publish(user_id=c_user_id, view={'type': 'home', 'blocks': blocks})

    def manage_handlers(self):
        @self.app.event("app_home_opened")
        def handle_home_opened(client, event):
            user_id = event['user']
            channels = self.update_u_top_channels(user_id)
            channel_id = channels[0][0]
            channel_name = f'#{channels[0][1]}'
            self.user_active_channel[user_id] = (channel_id, channel_name)

            client.views_publish(user_id=user_id, view={'type': 'home', 'blocks': [{'type':'section', 'text': {'type':'mrkdwn','text':'*Getting channels...*'}}]})
            self.update_home_tab(client, user_id, channel_id, channel_name)
        
        @self.app.action(re.compile('channel_\\d+'))
        def handle_channel_button(ack, client, body, action):
            ack()
            user_id = body['user']['id']
            channel_id = action['value']
            channel_name = action['text']['text']

            logger.debug(f'Sumary of the home button at {channel_id}')
            client.views_publish(user_id=user_id, view={'type': 'home', 'blocks': [{'type':'section', 'text': {'type':'mrkdwn','text':'*Getting channels from button...*'}}]})
            self.update_home_tab(client, user_id, channel_id, channel_name)

        @self.app.action('open_settings')
        def handle_settings(ack, body, client):
            ack()
            client.views_open(
                trigger_id = body['trigger_id'],
                view={
                    "type": "modal",
                    "callback_id": "settings_submit",
                    "title": {"type": "plain_text", "text": "Settings"},
                    "submit": {"type": "plain_text", "text": "Save"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "limit_messages",
                            "label": {"type": "plain_text", "text": "Limit messages to:"},
                            "element": {
                                "type": "static_select",
                                "action_id": "limit_select",
                                "options": [
                                    {"text": {"type": "plain_text", "text": "200"}, "value": "200"},
                                    {"text": {"type": "plain_text", "text": "100"}, "value": "100"},
                                    {"text": {"type": "plain_text", "text": "50"}, "value": "50"}
                                ]
                            }
                        },
                        {
                            "type": "input",
                            "block_id": "number_channels",
                            "label": {"type": "plain_text", "text": "Top channels to show"},
                            "element": {
                                "type": "static_select",
                                "action_id": "top_select",
                                "options": [
                                    {"text": {"type": "plain_text", "text": "3"}, "value": "3"},
                                    {"text": {"type": "plain_text", "text": "4"}, "value": "4"},
                                    {"text": {"type": "plain_text", "text": "5"}, "value": "5"}
                                ]
                            }
                        },
                        {
                            "type": "input",
                            "block_id": "summary_days",
                            "label": {"type": "plain_text", "text": "Days of channel history to summarize"},
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "days_input",
                                "initial_value": "1"
                            }
                        },
                        {
                            "type": "input",
                            "block_id": "system_prompt",
                            "label": {"type": "plain_text", "text": "System Prompt"},
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "prompt_input",
                                "multiline": True
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Refresh Top Channels"},
                                    "action_id": "refresh_top_channels",
                                    "value": "refresh"
                                }
                            ]
                        }
                    ]
                }
            )

        @self.app.view('settings_submit')
        def submit_settings(ack, body, view):
            ack()
            user_id = body['user']['id']
            values = view['state']['values']
            self.user_days = int(values['summary_days']['days_input']['value'])
            self.user_instructions = values['system_prompt']['prompt_input']['value'] # missing go to LLM object
            self.user_m_limit = int(values['limit_messages']['limit_select']['selected_option']['value'])
            self.custom_user_ch = int(values['number_channels']['top_select']['selected_option']['value'])
            self.slack_cache.update_channel_limit(self.custom_user_ch)

        # Summarize and respond to specific channel information
        @self.app.command("/summary")
        def answerPrivate(ack, command, say, respond):
            ack()
            respond('Getting the summary')
            ch_name = command['text'].replace(' ','-')
            user_id = command['user_id']
            channels = []
            channels = self.slack_metadata.get_user_channels(user_id)
            self.user_top_channels[user_id] = channels
            
            # Check if the user is part of that channel
            for id,name in channels:
                if ch_name == name:
                    now = str(datetime.now().timestamp())
                    time_mark = int(now[:10])
                    ch_messages = self.check_channel_messages(id,time_mark)
                    self.summary_ch_reference = ch_messages
                    prompt = f'summarize the following conversation from a channel in less than 6 bullet points: {ch_messages}.'
                    self.command_summary = self.llm_client.botConversation(prompt)
                    break

            if not self.command_summary or not self.summary_ch_reference:
                say('channel not found, try:\n/summary name of channel\n/summary name-of-channel')
            else:
                say(f'Summary of channel #{ch_name}:\n{self.command_summary}')

            # Chat only about the channel when true
            self.is_in_summary = True
        
        # Reset bot conversation
        @self.app.command("/backconversation")
        def answerAll(ack, command, say):
            ack()
            say("Back to normal chat")
            # Back to the general configuration, 
            # reset chat history to clean any system instructions
            self.is_in_summary = False
            self.llm_client.reset_chat(command['user_id'])