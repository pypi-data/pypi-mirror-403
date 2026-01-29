from abc import abstractmethod, ABC

from devbricksxai.generativeai.roles.artisan import Artisan, SKILL_ESCORTING
from devbricksx.development.log import debug

class Escort(Artisan, ABC):
    PARAM_SOURCE = 'src'
    PARAM_DESTINATION = 'dest'
    PARAM_DIRECTION = 'direction'

    DIRECTION_IN = 'in'
    DIRECTION_OUT = 'out'
    DIRECTION_BOTH = 'both'

    direction: DIRECTION_BOTH

    def __init__(self,
                 name,
                 provider,
                 direction):
        super().__init__(name, provider, SKILL_ESCORTING)
        self.direction = direction


    @abstractmethod
    def escort(self,
               direction,
               src,
               dest,
               **kwargs):
        pass

    def craft(self, **kwargs) -> str:
        kwargs.update(self.parameters)
        direction = kwargs.pop(Escort.PARAM_DIRECTION, None)
        src = kwargs.pop(Escort.PARAM_SOURCE, None)
        dest = kwargs.pop(Escort.PARAM_DESTINATION, None)

        if direction is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Escort.PARAM_DIRECTION}] in arguments.")

        if src is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Escort.PARAM_SOURCE}] in arguments.")

        if dest is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Escort.PARAM_DESTINATION}] in arguments.")

        debug(f"[{direction.upper()}]: [{src}] -> [{dest}]")

        if self.direction != Escort.DIRECTION_BOTH and self.direction != direction:
            raise ValueError(
                f"craft() of {self.__class__.__name__} can direction [{Escort.PARAM_SOURCE}]. "
                f"Only support direction [{self.direction}]"
            )

        return self.escort(direction, src, dest, **kwargs)

class InEscort(Escort, ABC):
    def __init__(self,
                 name,
                 provider):
        super().__init__(name, provider, Escort.DIRECTION_IN)

class OutEscort(Escort, ABC):
    def __init__(self,
                 name,
                 provider):
        super().__init__(name, provider, Escort.DIRECTION_OUT)


def init_escorts():
    from devbricksxai.generativeai.roles.character import register_character
    from devbricksxai.generativeai.roles.artisans.escorts.url import UrlEscort

    register_character(UrlEscort())