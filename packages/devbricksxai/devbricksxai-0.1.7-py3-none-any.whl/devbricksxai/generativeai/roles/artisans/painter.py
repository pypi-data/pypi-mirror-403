from abc import abstractmethod, ABC

from PIL import Image

from devbricksxai.generativeai.roles.artisan import Artisan, SKILL_PAINTING
from devbricksx.development.log import debug

class Painter(Artisan, ABC):
    PARAM_PROMPT = 'prompt'
    PARAM_MODEL = 'model'
    PARAM_WIDTH = 'width'
    PARAM_HEIGHT = 'height'

    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 512

    def __init__(self,
                 name,
                 provider):
        super().__init__(name, provider, SKILL_PAINTING)

    @abstractmethod
    def generate(self,
                 prompt,
                 model=None,
                 width=1024,
                 height=512,
                 **kwargs):
        pass

    @abstractmethod
    def get_default_model(self):
        pass

    def craft(self, **kwargs) -> str:
        kwargs.update(self.parameters)
        prompt = kwargs.pop(Painter.PARAM_PROMPT)
        debug(f"prompt: {prompt}")
        if prompt is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Painter.PARAM_PROMPT}] in arguments.")

        composed_prompt = self.compose_prompt(prompt)
        debug(f"composed_prompt: {composed_prompt}")

        model = kwargs.pop(Painter.PARAM_MODEL, self.get_default_model())
        if model is None:
            raise ValueError(
                f"no model is provider by mode parameter of get_default_mode() of {self.__class__.__name__}.")

        width = kwargs.pop(Painter.PARAM_WIDTH, Painter.DEFAULT_WIDTH)
        height = kwargs.pop(Painter.PARAM_HEIGHT, Painter.DEFAULT_HEIGHT)

        return self.generate(composed_prompt, model, width, height, **kwargs)

    def compose_prompt(self, prompt):
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list):
            contents = []
            for obj in prompt:
                if isinstance(obj, dict) and 'content' in obj:
                    contents.append(obj['content'])
                else:
                    contents.append(None)
            return ' '.join(c for c in contents)
        else:
            return None

    @staticmethod
    def resize_image(src_file, dest_file, targe_width, target_height):
        with Image.open(src_file) as img:
            img_resized = img.resize((targe_width, target_height))

            img_resized.save(dest_file)
    @staticmethod
    def compress_image(src_file, dest_file, quality):
        with Image.open(src_file) as img:
            img_resized = img.convert("RGB")

            img_resized.save(dest_file, 'JPEG', quality=quality)

def init_painters():
    from devbricksxai.generativeai.roles.character import register_character
    from devbricksxai.generativeai.roles.artisans.painters.dalle import DallEPainter

    register_character(DallEPainter())