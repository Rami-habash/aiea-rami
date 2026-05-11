import json
from llm.base import chat, chat_json, get_msg
import os
from configparser import ConfigParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI
# Read configuration file
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config.ini").replace("\\", "/")
cf = ConfigParser()
cf.read(file_path, encoding="utf-8")
MODEL = cf.get("API", "MODEL")
Temperature  = cf.get("API", "TEMPERATURE")
class AgentBase:
    def __init__(self):
        global cf
        # Initialize some variables or configuration
        self.chat_msg = ""
        self.json_msg = ""
        self.temperature = 0.7
        self.max_retry = cf.getint("API", "MAX_RETRY")
        # For json conversation
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=cf.get("API", "BASE_URL"),
        )
        self.llm = ChatOpenAI(
            model=MODEL,
            temperature=Temperature,
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=cf.get("API", "BASE_URL"),
        )

    async def chat(self, prompt: str) -> tuple:
        """
        Receive user input prompt, call the chat method in base, and return the response content
        """
        response = await self.chat_text(prompt, self.chat_msg, self.temperature)
        return await self.extract_json(response), response

    async def extract_json(self, prompt: str) -> dict:
        """
        Receive user input prompt, call the chat_json method in base, return JSON formatted response
        """
        json_response = await self.chat_json(prompt, self.json_msg, self.temperature)
        return json_response
    # For sending messages, normal conversation
    async def chat_text(self,prompt:str, system_msg:str = "", temperature=0.7):
        cur = 0
        while cur < self.max_retry:
            try:
                res = await self.llm.ainvoke(get_msg(prompt, system_msg))
                return res.content
            except Exception as e:
                print(f"chat error {cur + 1}attempts: {e}")
                cur += 1
        return ""
    # For sending messages, json conversation
    async def chat_json(self,prompt:str, system_msg:str = "", temperature=0.7):
        cur = 0
        messages = [{"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}]
        response = None
        while cur < self.max_retry:
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    response_format={
                        'type': 'json_object'
                    }
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"Current JSON prompt:\n{prompt}\nCurrent JSON format requirement:\n{system_msg}\n")
                if response:
                    print(f"Current answer:\n{response}")
                print(f"chat_json error {cur + 1}attempts: {e}")
                cur += 1
        return {}