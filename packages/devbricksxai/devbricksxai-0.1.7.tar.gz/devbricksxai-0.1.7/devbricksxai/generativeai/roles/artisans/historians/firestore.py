import json
from datetime import datetime

from google.cloud.firestore_v1 import FieldFilter

from devbricksxai.generativeai.roles.artisans.historian import Historian
from firebase_admin import firestore, credentials

from devbricksx.development.log import debug

HISTORIAN_FIRESTORE = 'Firestore'
__FIREBASE_PROVIDER__ = 'Firebase'

class FirestoreHistorian(Historian):

    db: firestore.Client

    def __init__(self):
        super().__init__(HISTORIAN_FIRESTORE, __FIREBASE_PROVIDER__)

        self.db = firestore.client()

    def add_records(self, collection, records, **kwargs):
        root_ref = self.db.collection(collection)

        timestamp = int(datetime.utcnow().timestamp() * 1000)
        for record in records:
            dict_of_record = FirestoreHistorian.to_dict(record)

            if 'id' in dict_of_record:
                doc_id = dict_of_record['id']
                debug(f'updating existed record [{doc_id}] in collection: {collection}')
                dict_of_record.pop('id', None)

                record.last_modified = timestamp
                dict_of_record['last_modified'] = timestamp
                root_ref.document(doc_id).update(dict_of_record)
            else:
                debug(f'adding new record to collection: {collection}')

                doc_ref = root_ref.document()

                record.id = doc_ref.id
                dict_of_record['id'] = doc_ref.id

                record.last_modified = timestamp
                dict_of_record['last_modified'] = timestamp

                record.created = timestamp
                dict_of_record['created'] = timestamp

                doc_ref.set(dict_of_record)

        return records

    def get_records(self, collection, queries=None, order_by=None, limit=None, offset=None, **kwargs):
        debug(f"queries: {queries}")
        debug(f"order_by: {order_by}")
        debug(f"limit: {limit}")
        root_ref = self.db.collection(collection)

        if queries is not None:
            for query in queries:
               root_ref = root_ref.where(filter=query)

        if order_by is not None:
            key = order_by["key"]
            direction = "ascending"
            if "direction" in order_by:
                direction = order_by["direction"]

            root_ref = root_ref.order_by(key, direction=direction.upper())

        if limit is not None:
            root_ref = root_ref.limit(limit)

        records = list()

        snapshot = root_ref.stream()
        if snapshot is not None:
            records = list(snapshot)

        return records

    def get_record(self, collection, record_id, **kwargs):
        queries = [
            FieldFilter("id", "==", record_id)
        ]

        found_records = self.get_records(collection, queries, **kwargs)
        if found_records is not None and len(found_records) > 0:
            return found_records[0]
        else:
            return None

    def get_record_by_key(self, collection, key, value, **kwargs):
        queries = [
            FieldFilter(key, "==", value)
        ]

        found_records = self.get_records(collection, queries, **kwargs)
        if found_records is not None and len(found_records) > 0:
            return found_records[0]
        else:
            return None

    @staticmethod
    def to_dict(obj):
        return json.loads(json.dumps(obj, default=lambda o: o.__dict__))