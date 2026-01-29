import json
from dataclasses import dataclass

from devbricksx.common.json_convert import JsonConvert
from devbricksx.development.log import debug

DEFAULT_AI_SETTINGS_FILE = "private/genai.json"

@dataclass
class AISettings:
    providers: {}
    characters: {}
    members: {}

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def from_dict(data):
        return AISettings(**data)

    def __str__(self):
        return f"{json.dumps(self.__dict__, indent=4, ensure_ascii=False)}"

ai_settings = {}

def init_ai_settings(ai_settings_file):
    global ai_settings
    debug(f"Loading AI settings from[{ai_settings_file}] ... ")
    ai_settings_dict = JsonConvert.from_file_to_dict(ai_settings_file)
    ai_settings = AISettings.from_dict(ai_settings_dict)
    debug("Loaded AI settings: {}".format(ai_settings))

def get_ai_settings():
    return ai_settings