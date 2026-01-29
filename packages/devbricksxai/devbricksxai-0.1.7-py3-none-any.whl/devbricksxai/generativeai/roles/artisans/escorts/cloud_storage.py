from os import path
from urllib.parse import quote
from devbricksxai.generativeai.roles.artisans.escort import OutEscort, Escort
from firebase_admin import credentials, storage

from devbricksx.development.log import debug, error

ESCORT_CLOUD_STORAGE = 'CloudStorage'
__CLOUD_STORAGE_PROVIDER__ = 'Firebase'

class CloudStorageEscort(OutEscort):
    PARAM_FILE_NAME = "filename"
    PARAM_FILE_META = "metadata"

    PARAM_DOWNLOAD_TOKEN = "firebaseStorageDownloadTokens"

    def __init__(self):
        super().__init__(ESCORT_CLOUD_STORAGE, __CLOUD_STORAGE_PROVIDER__)

    def escort(self, direction, src, dest, **kwargs):
        if direction == Escort.DIRECTION_OUT:
            filename = kwargs.pop(CloudStorageEscort.PARAM_FILE_NAME, None)
            metadata = kwargs.pop(CloudStorageEscort.PARAM_FILE_META, None)
            return self.upload_file(src, dest, filename, metadata)
        else:
            return None

    def upload_file(self, local_file, target_dir, target_filename=None, metadata=None):
        debug(f'uploading file [{local_file}] to cloud: {target_dir} [filename: {target_filename}, meta: {metadata}]')

        if target_filename is None:
            target_filename = path.basename(local_file)

        target = path.join(target_dir, target_filename)
        debug(f'target: {target}')

        bucket = storage.bucket()
        blob = bucket.blob(str(target))

        if metadata is not None:
            blob.metadata = metadata

        try:
            blob.upload_from_filename(local_file)
            download_link = f'https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encodeURIComponent(target)}'
            if metadata is not None:
                if metadata[CloudStorageEscort.PARAM_DOWNLOAD_TOKEN] is not None:
                    download_link += f'?alt=media&token={metadata[CloudStorageEscort.PARAM_DOWNLOAD_TOKEN]}'

        except Exception as e:
            error(f'failed to upload file {local_file}:', e)
            download_link = None

        return download_link


def encodeURIComponent(s):
    return quote(s, safe='')