import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference import models
from .config import Settings

# Use config file to set, include OCI parameters

# General Model (DEFAULT) variables --------------------------
MAX_TOKENS = 600
TEMPERATURE = 1
FREQ_PENALTY = 0
TOP_P = 0.75
TOP_K = 0
PREAMBLE = 'Answer in maximum, 200 words, '
MESSAGE = ''

class LLM_Client:
    def __init__(self):
        self.credentials = Settings() #Get OCI credentials
        self.config = oci.config.from_file(self.credentials.config_path, self.credentials.config_profile)
        self.client = GenerativeAiInferenceClient(
            config=self.config, 
            service_endpoint=self.credentials.endpoint, 
            retry_strategy=oci.retry.NoneRetryStrategy(), 
            timeout=(10,240))
        
        self.chat_detail = models.ChatDetails()
        self.chat_detail.serving_mode = models.OnDemandServingMode(model_id=self.credentials.model_id)
        self.chat_detail.compartment_id = self.credentials.compartiment

        self.message_db = {} #Store history for each user
        self.message_history = [] # user

        self.chat_request = models.CohereChatRequest()
        self.chat_request.preamble_override = PREAMBLE # user
        self.chat_request.message = MESSAGE #user
        self.chat_request.max_tokens = MAX_TOKENS
        self.chat_request.temperature = TEMPERATURE
        self.chat_request.frequency_penalty = FREQ_PENALTY
        self.chat_request.top_p = TOP_P
        self.chat_request.top_k = TOP_K
        self.chat_request.chat_history = self.message_history #user    
        
    def get_chat_details(self):
        self.chat_detail.chat_request = self.get_chat_request()

        return self.chat_detail
    
    # Chat parameters
    def get_chat_request(self):
        return self.chat_request
    
    def set_chat_request(self, prompt, instructions):
        self.chat_request.preamble_override = PREAMBLE+instructions # user (keep 200 word limit)
        self.chat_request.message = prompt #user
    
    def botConversation(self,u_prompt, sys_instructions=''):
        self.message_history.append(models.CohereUserMessage(message=u_prompt))
        self.set_chat_request(u_prompt, sys_instructions)
        client_config = self.get_chat_details()
        chat_response = self.client.chat(client_config)
        generated_response = chat_response.data.chat_response.text
        self.message_history.append(models.CohereChatBotMessage(message=generated_response))

        return generated_response
    
    # TODO: Set each user to particular history, missing
    def reset_chat(self,user):
        self.message_db[user] = []
        self.message_history = []