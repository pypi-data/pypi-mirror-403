from abc import ABC, abstractmethod

from devbricksxai.generativeai.roles.artisan import Artisan, SKILL_COMPOSING_MUSIC


class Musician(Artisan, ABC):
    PARAM_PROMPT = 'prompt'

    def __init__(self, name, provider):
        super().__init__(name, provider, SKILL_COMPOSING_MUSIC)

    @abstractmethod
    def compose(self, prompt, **kwargs):
        pass

    def craft(self, **kwargs):
        prompt = kwargs.pop(Musician.PARAM_PROMPT)
        if prompt is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Musician.PARAM_PROMPT}] in arguments.")

        return self.compose(prompt, **kwargs)



def init_musicians():
    from generativeai.roles.character import register_character
    from generativeai.roles.artisans.musicians.suno_musician import SunoMusician

    register_character(SunoMusician())