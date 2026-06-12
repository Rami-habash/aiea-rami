import json
import logging
import traceback
import os
from configparser import ConfigParser
from openai import OpenAI
from openai.types.chat import ChatCompletion
from utils.text import remove_markdown
from config.Settings import config
import traceback
class AgentBase:
    def __init__(self,model_type,data_type):
        self.data_type = data_type
        self.example = ""
        if self.data_type:
            # get llm file path
            llm_dir = os.path.dirname(os.path.abspath(__file__))
            # get prompt path
            prompt_path = os.path.join(llm_dir, "prompt",f"{model_type}_{self.data_type}.txt")
            # check for existence
            if os.path.exists(prompt_path):
               with open(prompt_path, 'r', encoding='utf-8') as f:
                     self.example = f.read()
        # Initialize some variables or configuration
        self.max_retry = 3
        self.json_msg = None
        self.prompt = None
        self.last_usage = None  # populated after each chat() call; piggybacked onto sample JSONL
        # for normal conversation
        self.llm = OpenAI(
            api_key=config["agent"][model_type]["api_key"],
            base_url=config["agent"][model_type]["base_url"],
        )
        self.chat_model = config["agent"][model_type]["model"]
        self.temperature = config["agent"][model_type]["temperature"]
        self.reasoning_effort = config["agent"][model_type].get("reasoning_effort") # initalizing reasoning
        # for JSON format conversation
        self.json_llm = OpenAI(
            api_key=config["agent"]["extra"]["api_key"],
            base_url=config["agent"]["extra"]["base_url"],
        )

    def chat(self, prompt: str, system_msg: str = "", json_mode = True) -> tuple:
        """
        Normal text chat mode: receives user input prompt, returns text response, and attempts to parse JSON.
        """
        logging.debug(prompt)
        response_text = ""
        cur = 0
        messages = [{"role": "user", "content": prompt}]
        if system_msg:
            messages.insert(0, {"role": "system", "content": system_msg})
        while cur < self.max_retry:
            try:
                logging.debug(messages)
                # only temp and max_tokens for inference
                response = self.llm.chat.completions.create(
                    model=self.chat_model,
                    messages=messages,
                    timeout=600,
                    **({"reasoning_effort": self.reasoning_effort}
                    if self.reasoning_effort
                    else {"temperature": float(self.temperature)}),
                )

                logging.info(response)
                u = response.usage
                r = getattr(u.completion_tokens_details, "reasoning_tokens", 0) if u.completion_tokens_details else 0
                self.last_usage = {"in": u.prompt_tokens, "out": u.completion_tokens, "reasoning": r}
                response_text = self.get_content(response)
                if not response_text:
                    return {}
                response_text = remove_markdown(response_text)
                break
            except Exception as e:
                err_msg = f"chat error attempt {cur + 1}: {e} {traceback.format_exc()}"
                logging.error(err_msg)
                cur += 1
        # if response obtained, attempt to parse JSON
        if response_text:
            logging.info(response_text)
            if json_mode:
                # update: bypass extractor if already formatted properly
                # deployed in non-cot LTRAG
                parsed = None
                start, end = response_text.find("{"), response_text.rfind("}")
                if start != -1 and end > start:
                    try:
                        parsed = json.loads(response_text[start:end + 1])
                    except (json.JSONDecodeError, TypeError):
                        parsed = None
                json_data = parsed if isinstance(parsed, dict) else self.extract_json(response_text)
            else:
                json_data = {}
            return json_data, response_text
        return {}, ""

    def extract_json(self, prompt: str) -> dict:
        """
        Receives text response, attempts to extract JSON format content.
        """
        cur = 0
        messages = [{"role": "user", "content": prompt}]
        if self.json_msg:
            messages.insert(0, {"role": "system", "content": self.json_msg})
        while cur < self.max_retry:
            try:
                logging.debug(prompt)
                response = self.json_llm.chat.completions.create(
                    model=config["agent"]["extra"]["model"],
                    temperature=config["agent"]["extra"]["temperature"],
                    messages=messages,
                    response_format={'type': 'json_object'}
                )
                # adding extractor call to LTRAG's costs
                u = response.usage
                r = getattr(u.completion_tokens_details, "reasoning_tokens", 0) if u.completion_tokens_details else 0
                if isinstance(self.last_usage, dict):
                    self.last_usage["in"] += u.prompt_tokens
                    self.last_usage["out"] += u.completion_tokens
                    self.last_usage["reasoning"] += r
                msg = self.get_content(response)
                if not msg:
                    return {}
                logging.debug(msg)
                json_data = json.loads(msg)
                logging.debug(f"extract_json complete: {json_data}")
                return json_data
            except Exception as e:
                tb_info = traceback.format_exc()
                logging.error(f"extract_json error attempt {cur + 1}: {e}\n{tb_info}")
                cur += 1
        return {}  # if max retries exceeded, return empty dictionary
    @staticmethod
    def get_content(response: ChatCompletion) -> str:
        try:
            # check and get content property
            if not response.choices:
                logging.error(f"response has no choices: {response}")
                return ""

            first_choice = response.choices[0] if response.choices else None
            if not first_choice:
                logging.error(f"choices has no first element: {response}")
                return ""

            message = first_choice.message if first_choice.message else None
            if not message:
                logging.error(f"first choice has no message: {response}")
                return ""

            content = message.content if message.content else message.reasoning_content
            if not content:
                logging.error(f"message has no content: {response}")
                return ""
            return content
        except Exception as e:
            tb_info = traceback.format_exc()
            logging.error(f"get_content {e}\n{tb_info} \n {response}")

if __name__ == "__main__":
    print(config)
