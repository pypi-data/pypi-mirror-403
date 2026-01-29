import re
from enum import Enum

from devbricksx.development.log import info, warn, debug
from devbricksxai.generativeai.settings.aisettings import get_ai_settings

__CHARACTERS = {}
# Define the enum class for character types
class Role(Enum):
    UNSUPPORTED = 0
    ARTISAN = 1
    ADVISOR = 2

# Define the character class
class Character:
    role: Role = Role.UNSUPPORTED
    name: str
    alias: str
    provider: str
    parameters: {}
    def __init__(self, name, provider, role):
        if not isinstance(role, Role):
            raise ValueError("role must be an instance of Role")
        self.name = name
        self.alias = Character.name_to_alias(name)
        self.provider = provider
        self.role = role
        self.parameters = {}

    def add_parameter(self, key, value):
        self.parameters[key] = value

    def get_parameter(self, key):
        value = None

        if key in self.parameters:
            value = self.parameters[key]

        if value is None:
            provider = get_ai_settings().providers.get(self.provider)
            if provider is not None:
                value = provider.get(key)

        if value is None:
            character = get_ai_settings().characters.get(self.alias)
            if character is not None:
                value = character.get(key)

        return value

    @staticmethod
    def name_to_alias(name):
        return re.sub(r'[^a-zA-Z0-9_-]', '', name).lower()

    def __str__(self):
        return f"[{self.name}, {self.role.name.upper()}]:\n|- Alias: {self.alias}\n|- Provider: {self.provider}\n`- Parameters: {self.parameters}"

    def __repr__(self):
        return f"{self.__class__.__name__}?name={self.name}&alias={self.alias}&provider={self.provider}&type={self.role.name.lower()}"


def register_character(character):
    global __CHARACTERS

    if character.name not in __CHARACTERS:
        __CHARACTERS[character.alias] = character
    else:
        warn(f"{character.name} is registered by {__CHARACTERS[character.name]}. It will be replaced by new one {character}")
        __CHARACTERS[character.alias] = character


def unregister_character(character):
    global __CHARACTERS

    if character.alias in __CHARACTERS:
        del __CHARACTERS[character.alias]

def init_characters():
    from devbricksxai.generativeai.roles.artisans.painter import init_painters
    from devbricksxai.generativeai.roles.artisans.historian import init_historians
    from devbricksxai.generativeai.roles.advisor import init_advisors
    from devbricksxai.generativeai.roles.artisans.escort import init_escorts
    from devbricksxai.generativeai.roles.artisans.analyst import init_analysts
    from devbricksxai.generativeai.roles.artisans.musician import init_musicians

    init_painters()
    init_historians()
    init_advisors()
    init_escorts()
    init_analysts()
    init_musicians()


def get_character_by_name(name, instance=None):
    global __CHARACTERS

    alias = Character.name_to_alias(name)
    character = __CHARACTERS.get(alias)
    if character is None:
        return None

    if instance is None:
        return character

    if isinstance(character, instance):
        return character
    else:
        return None

def list_characters(role=None, in_instances=None, providers=None, custom_filter=None, custom_filter_params=None):
    global __CHARACTERS

    all_characters = list(__CHARACTERS.values())

    if role is None:
        filtered_by_role =  all_characters
    else:
        filtered_by_role =  [char for char in all_characters if char.role == role]

    if in_instances is not None:
        filtered_by_characters = [char for char in filtered_by_role if isinstance(char, tuple(in_instances))]
    else:
        filtered_by_characters = filtered_by_role

    if providers is not None:
        if isinstance(providers, list):
            provider_list = providers
        else:
            provider_list = [providers]

        filtered_by_providers = [char for char in filtered_by_characters if char.provider in provider_list]
    else:
        filtered_by_providers = filtered_by_characters

    if custom_filter is None:
        return filtered_by_providers

    return [character for character in filtered_by_providers if custom_filter(character, **custom_filter_params)]
