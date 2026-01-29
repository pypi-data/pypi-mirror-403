from devbricksxai.generativeai.roles.artisans.escort import Escort, InEscort, OutEscort
from devbricksxai.generativeai.roles.artisans.historian import Historian
from devbricksxai.generativeai.roles.artisans.musician import Musician
from devbricksxai.generativeai.roles.artisans.painter import Painter
from devbricksxai.generativeai.roles.character import Role
from devbricksx.development.log import debug

class TaskForce:
    name: None
    members: []
    parameters: {}

    def __init__(self,
                 name):
        self.name = name
        self.members = []
        self.parameters = {}

    def __str__(self):
        print_str = '[members]: %s\n[parameters]: %s'

        return print_str % (", ".join(str(m) for m in self.members),
                            ", ".join(str(k) + ":" + str(self.parameters[k]) for k in self.parameters.keys()),)


    def add_member(self, character):
        self.members.append(character)

    def select_members(self, role, instance=None):
        debug(f"select: role = {role}, instance = {instance}")

        filtered_by_roles = [char for char in self.members if char.role == role]
        if len(filtered_by_roles) <= 0:
            return []

        if instance is None:
            return filtered_by_roles

        filtered_by_instance = [char for char in filtered_by_roles if isinstance(char, instance)]
        if len(filtered_by_instance) <= 0:
            return []

        return filtered_by_instance

    def select_member(self, role, instance=None, alias=None):
        debug(f"select one: role = {role}, instance = {instance}")

        characters = self.select_members(role, instance)
        if len(characters) <= 0:
            return None

        if alias is None:
            return characters[0]

        filtered_by_name = [char for char in characters if char.alias == alias.lower()]
        if len(filtered_by_name) <= 0:
            return None

        return filtered_by_name[0]


    def get_member(self, alias, instance=None):
        filtered_by_name = [char for char in self.members if char.alias == alias.lower()]
        if len(filtered_by_name) <= 0:
            return None

        if instance is None:
            return filtered_by_name[0]

        filtered_by_instance = [char for char in filtered_by_name if isinstance(char, instance)]
        if len(filtered_by_instance) <= 0:
            return []

        return filtered_by_instance[0]

    def get_advisor(self, alias=None):
        return self.select_member(Role.ADVISOR, alias)

    def get_painter(self, alias=None) -> Painter:
        return self.select_member(Role.ARTISAN, Painter, alias)

    def get_musician(self, alias=None) -> Musician:
        return self.select_member(Role.ARTISAN, Musician, alias)

    def get_historian(self, alias=None) -> Historian:
        return self.select_member(Role.ARTISAN, Historian, alias)

    def get_escort(self, alias=None) -> Escort:
        return self.select_member(Role.ARTISAN, Escort, alias)

    def get_in_escort(self, alias=None) -> InEscort:
        return self.select_member(Role.ARTISAN, InEscort, alias)

    def get_out_escort(self, alias=None) -> OutEscort:
        return self.select_member(Role.ARTISAN, OutEscort, alias)
