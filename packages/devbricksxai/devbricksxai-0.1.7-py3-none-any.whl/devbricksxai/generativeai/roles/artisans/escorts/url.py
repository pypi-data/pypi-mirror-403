import os
from os import path

import requests

from devbricksx.development.log import debug, error
from devbricksxai.generativeai.roles.artisans.escort import Escort, InEscort


ESCORT_URL = 'Url'
__URL_PROVIDER__ = 'DailyStudio'

class UrlEscort(InEscort):

    def __init__(self):
        super().__init__(ESCORT_URL, __URL_PROVIDER__)

    def escort(self, direction, src, dest, **kwargs):
        if direction == Escort.DIRECTION_IN:
            return self.download_file(src, dest)
        else:
            return None

    def download_file(self, file_url, local_file):
        debug("downloading url [{}] to file: {}".format(file_url, local_file))

        dir_of_file = path.dirname(local_file)
        if not path.exists(dir_of_file):
            debug('directory of file [{}] is not existed. creating it...'
                  .format(dir_of_file))
            os.mkdir(dir_of_file)

        try:
            with open(local_file, 'wb') as handle:
                response = requests.get(file_url, stream=True)

                if not response.ok:
                    error('error resp from [{}]: {}'.format(file_url, response))

                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)

        except Exception as err:
            error('failed to download url [{}]: {}'.format(file_url, err))
            return None

        return local_file
