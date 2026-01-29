import openai

from devbricksxai.generativeai.roles.artisans.painter import Painter
from devbricksxai.generativeai.settings.aisettings import get_ai_settings
from devbricksx.development.log import info, debug, error

PAINTER_DALL_E = 'Dall·E'
__PAINTER_PROVIDER__ = 'OpenAI.com'

__SUPPORTED_DIMENSIONS__ = [
    (1024, 1024),
    (1792, 1024),
    (1024, 1792)
]

class DallEPainter(Painter):

    MODEL_DALL_E_2 = "dall-e-2"
    MODEL_DALL_E_3 = "dall-e-3"

    PARAM_SEED = "seed"

    def __init__(self):
        super().__init__(PAINTER_DALL_E, __PAINTER_PROVIDER__)

    def get_default_model(self):
        return DallEPainter.MODEL_DALL_E_3

    def generate(self, prompt,
                 model=None,
                 width=1024, height=1024,
                 **kwargs):
        debug("[{}] be asked to generate: {}".format(model, prompt))
        input_dimension = (width, height)

        seed = kwargs.get(self.PARAM_SEED, None)
        debug(f"generating image using seed [{seed}]")

        if not input_dimension in __SUPPORTED_DIMENSIONS__:
            width, height = __SUPPORTED_DIMENSIONS__[0]
            info("({}, {}) is NOT supported. Use default one: {}".format(
                width, height, __SUPPORTED_DIMENSIONS__[0]
            ))

        return text_to_image_dall_e(prompt,
                                    get_ai_settings().dall_e_model,
                                    width, height,
                                    seed
                                    )

def text_to_image_dall_e(prompt, model, width, height, seed=None):
    openai.api_key = get_ai_settings().open_ai_apikey

    if seed is not None:
        prompt = f"{prompt}. Seed: {seed}"
        debug(f"update prompt with seed [{seed}]: {prompt}")

    try:
        generation_of_cover_image = openai.Image.create(
            prompt=prompt,
            model=model,
            n=1,
            size="{}x{}".format(width, height),
        )
    except Exception as e:
        error(f"failed to create image with prompt {prompt}: {e}")
        return None

    return generation_of_cover_image['data'][0]['url']

