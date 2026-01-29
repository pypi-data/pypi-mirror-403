from abc import abstractmethod, ABC
from typing import Optional

from devbricksxai.generativeai.roles.character import Character, Role

SKILL_EXCERPTING = "excerpting"
SKILL_PAINTING = "painting"
SKILL_RECORDING = "recording"
SKILL_ESCORTING = "escorting"
SKILL_ANALYZING = "analyzing"
SKILL_COMPOSING_MUSIC = "composing music"

class Artisan(Character, ABC):
    skill: str

    def __init__(self, name, provider, skill):
        super().__init__(name, provider, Role.ARTISAN)
        self.skill = skill
    def __repr__(self):
        return f"{super().__repr__()}&skill={self.skill}"

    @abstractmethod
    def craft(self, **kwargs) -> Optional[object]:
        pass

