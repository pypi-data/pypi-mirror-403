from abc import abstractmethod, ABC

from devbricksx.development.log import info, debug
from devbricksxai.generativeai.roles.character import Character, Role


class Advisor(Character, ABC):
    PARAM_PROMPT = 'prompt'
    PARAM_HISTORIES = 'histories'
    PARAM_SESSION = 'session'

    ROLE_USER = 'user'
    ROLE_ADVISOR = 'advisor'

    def __init__(self, name, provider):
        super().__init__(name, provider, Role.ADVISOR)

    @abstractmethod
    def ask(self, prompt, **kwargs):
        pass

    @staticmethod
    def format_prompt(prompt):
        if isinstance(prompt, str):
            result = prompt
        elif isinstance(prompt, list):
            result = ", ".join(prompt)
        else:
            result = str(prompt)
        return result

    def craft(self, **kwargs):
        prompt = kwargs.pop(Advisor.PARAM_PROMPT)
        if prompt is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Advisor.PARAM_PROMPT}] in arguments.")

        formatted_prompt = self.format_prompt(prompt)
        debug(f"formatted prompt: {formatted_prompt}")

        return self.ask(formatted_prompt, **kwargs)

def init_advisors():
    from devbricksxai.generativeai.roles.character import register_character
    from devbricksxai.generativeai.roles.advisors.chatgpt import ChatGPTAdvisor
    from devbricksxai.generativeai.roles.advisors.gemini import GeminiAdvisor

    register_character(ChatGPTAdvisor())
    register_character(GeminiAdvisor())