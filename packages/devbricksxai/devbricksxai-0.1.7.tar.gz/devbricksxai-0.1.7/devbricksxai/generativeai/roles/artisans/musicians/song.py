class Song:
    id = None
    title = None
    link = None
    lyrics = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def from_dict(data):
        return Song(**data)

    def __str__(self):
        print_str = '[%s][title: %s, link: %s]: lyrics = [%s]'

        return print_str % (self.id,
                            self.title,
                            self.link,
                            self.lyrics,
                            )

