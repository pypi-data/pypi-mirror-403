from google import genai
from devbricksxai.generativeai.roles.advisor import Advisor
from devbricksxai.generativeai.settings.aisettings import get_ai_settings
from devbricksx.development.log import info, debug, error

ADVISOR_GEMINI = 'Gemini'
__ADVISOR_PROVIDER__ = 'Google.com'

class GeminiAdvisor(Advisor):

    PARAM_CONTEXT = 'context'
    PARAM_MODEL = 'model'
    PARAM_API_KEY = 'apikey'

    DEFAULT_MODEL = "gemini-2.0-flash"

    sessions = {}

    def __init__(self):
        super().__init__(ADVISOR_GEMINI, __ADVISOR_PROVIDER__)

    def ask(self, prompt, **kwargs):
        api_key = self.get_parameter(GeminiAdvisor.PARAM_API_KEY)
        debug("Gemini API Key: {}".format(api_key))

        client = genai.Client(api_key=api_key)

        model = self.get_parameter(GeminiAdvisor.PARAM_MODEL)
        if model is None:
            model = GeminiAdvisor.DEFAULT_MODEL

        debug("[{}] be asked: {}".format(model, prompt))

        try:
            session = kwargs.get(Advisor.PARAM_SESSION)
            info(f"session: {session}")
            if session is not None:
                if session not in self.sessions:
                    chat = client.chats.create(model=model)
                    self.sessions[session] = chat
                else:
                    chat = self.sessions[session]


                response = chat.send_message(prompt)
            else:
                response = client.models.generate_content(
                    model=model, contents=[prompt]
                )

            if response is not None:
                return response.text
            else:
                return None
        except Exception as e:
            error(f"[{model}] failed to generate : {e}")
            response  = None

        return response


    def get_role_tag(self, role):
        pass