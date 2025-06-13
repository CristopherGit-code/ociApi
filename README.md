# Slack InnoLab Bot lite

Slack App chatbot able to suumarize slack channels based on history metadata and answer questions

## Features

- Fetch latest channels from user and display top channels with respective summary in app home
- Adjust relevant channels, number of messages, message retrieval limit and bot system instructions
- Real-time chat 
- Channel-based chat
- Commands and shortcuts to respond in place questions, try app mention in channel and ask a question

## Setup

1. Get the necessary dependencies:
    - slack_bolt
    - slack_sdk
    - python-dotenv
    - oci
    - oracledb
2. Create .env file to set the environmet variables for slack
    - Ensure Event suscriptions, OAuth permissions form Slack App
3. Fill config file in /util with the LLM client variables
    - Access to AI igui SandBox required for credentials
    - Make sure OCI config path is set
4. Run form ```Main```

## Basic walkthrough

- Use ```llm_client``` to tune the model from SandBox
- API calls to gather user and channel information in ```slack_metadata```
- Home logic to show summary and commands in ```home_manager```