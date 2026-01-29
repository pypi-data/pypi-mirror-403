from abc import abstractmethod

from devbricksxai.generativeai.roles.artisan import Artisan, SKILL_RECORDING
from devbricksx.development.log import debug

class Historian(Artisan):
    PARAM_ACTION = 'action'
    PARAM_RECORDS = 'records'
    PARAM_ID = 'id'
    PARAM_QUERIES = 'queries'
    PARAM_COLLECTION = 'collection'

    ACTION_ADD = 'add'
    ACTION_GET = 'get'
    ACTION_GET_ONE = 'get_one'

    def __init__(self,
                 name,
                 provider):
        super().__init__(name, provider, SKILL_RECORDING)

    @abstractmethod
    def add_records(self,
                    collection,
                    records,
                    **kwargs):
        pass

    @abstractmethod
    def get_records(self,
                    collection,
                    queries=None,
                    order_by=None,
                    limit=None,
                    offset=None,
                    **kwargs):
        pass
    @abstractmethod
    def get_record(self,
                   collection,
                   record_id,
                   **kwargs):
        pass

    def craft(self, **kwargs) -> str:
        action = kwargs.pop(Historian.PARAM_ACTION, None)
        debug(f"action: {action}")
        if action is None:
            raise ValueError(
                f"craft() of {self.__class__.__name__} must include [{Historian.PARAM_ACTION}] in arguments.")

        if action == Historian.ACTION_ADD:
            collection = kwargs.pop(Historian.PARAM_COLLECTION, None)
            if collection is None:
                raise ValueError(
                    f"craft({action}) of {self.__class__.__name__} must include [{Historian.PARAM_COLLECTION}] in arguments.")

            records = kwargs.pop(Historian.PARAM_RECORDS)
            if records is None:
                raise ValueError(
                    f"craft({action}) of {self.__class__.__name__} must include [{Historian.PARAM_RECORDS}] in arguments.")

            debug(f"adding {records} to collection {collection}")
            return self.add_records(collection, records, **kwargs)

        if action == Historian.ACTION_GET:
            collection = kwargs.pop(Historian.PARAM_COLLECTION, None)
            if collection is None:
                raise ValueError(
                    f"craft({action}) of {self.__class__.__name__} must include [{Historian.PARAM_COLLECTION}] in arguments.")
            debug(f"retrieve data from collection {collection}")
            return self.get_records(collection, **kwargs)

        if action == Historian.ACTION_GET_ONE:
            collection = kwargs.pop(Historian.PARAM_COLLECTION, None)
            if collection is None:
                raise ValueError(
                    f"craft({action}) of {self.__class__.__name__} must include [{Historian.PARAM_COLLECTION}] in arguments.")

            record_id = kwargs.pop(Historian.PARAM_ID, None)
            if record_id is None:
                raise ValueError(
                    f"craft({action}) of {self.__class__.__name__} must include [{Historian.PARAM_ID}] in arguments.")
            debug(f"retrieve one from collection {collection}")
            return self.get_record(collection, record_id, **kwargs)


def init_historians():
    from devbricksxai.generativeai.roles.character import register_character
    # from devbricksxai.generativeai.roles.artisans.historians.firestore import FirestoreHistorian

    # register_character(FirestoreHistorian())