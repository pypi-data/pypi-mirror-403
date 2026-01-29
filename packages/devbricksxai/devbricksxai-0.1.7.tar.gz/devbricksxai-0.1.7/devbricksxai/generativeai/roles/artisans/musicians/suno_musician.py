from devbricksxai.generativeai.roles.artisans.musician import Musician
from devbricksxai.generativeai.roles.artisans.musicians.song import Song
from devbricksxai.generativeai.roles.artisans.musicians.suno import Suno, ModelVersions, Clip
from devbricksx.development.log import debug, error, warn

MUSICIAN_SUNO = 'Suno'
__MUSICIAN_PROVIDER__ = 'suno.com'

class SunoMusician(Musician):
    PARAM_COOKIE = "cookie"
    PARAM_MODEL = "model"
    PARAM_TAGS = "tags"
    PARAM_TITLE = "title"
    PARAM_GENERATE_LYRICS = "generate_lyrics"
    PARAM_INSTRUMENTAL = "instrumental"

    DEFAULT_MODEL = ModelVersions.CHIRP_V3_5

    suno_api: Suno

    def __init__(self):
        super().__init__(MUSICIAN_SUNO, __MUSICIAN_PROVIDER__)

        self.create_suno_api()

    def create_suno_api(self):
        cookie = self.get_parameter(self.PARAM_COOKIE)
        model = self.get_parameter(self.PARAM_MODEL)

        debug(f"creating Suno Api: model = {model}, cookie = {cookie}")
        if model is None:
            model = self.DEFAULT_MODEL

        self.suno_api = Suno(
            cookie=cookie,
            model_version=model
        )

    def add_parameter(self, key, value):
        super().add_parameter(key, value)
        if key == self.PARAM_COOKIE:
            self.create_suno_api()

    def compose(self, prompt, **kwargs):
        tags = kwargs.get(self.PARAM_TAGS, None)
        title = kwargs.get(self.PARAM_TITLE, None)
        generate_lyrics = kwargs.get(self.PARAM_GENERATE_LYRICS, False)
        instrumental = kwargs.get(self.PARAM_INSTRUMENTAL, False)

        debug(
            f"compose: prompt = {prompt}, "
            f"instrumental = {instrumental}, "
            f"tags = {tags}, "
            f"title = {title}, "
            f"generate_lyrics = {generate_lyrics}")

        return self.generate_song(
            prompt, title, instrumental, tags, generate_lyrics)

    def get_lyrics(self, song_id):
        return self.suno_api.get_lyrics(song_id)

    def generate_song(self, prompt, title, instrumental, tags, generate_lyrics):
        song_items = []

        try:
            songs = self.suno_api.generate(
                prompt=prompt,
                title=title,
                make_instrumental=instrumental,
                tags=tags,
                is_custom=not generate_lyrics,
                wait_audio=True)

            for song in songs:
                if isinstance(song, Clip):
                    debug(f"url from song clip: song = {song}")

                    clip = song
                elif isinstance(song, str):
                    song_id = song
                    debug(f"url from song id: song id = {song_id}")
                    clip = self.suno_api.get_song(song_id)
                else:
                    continue

                song_item = Song()
                song_item.id = clip.id
                song_item.link = clip.audio_url
                song_item.title = clip.title
                song_item.lyrics = clip.metadata.prompt

                song_items.append(song_item)

        except Exception as e:
            error(f"failed to generate song: {e}")
            return None

        return song_items
