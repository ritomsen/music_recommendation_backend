from pydantic import BaseModel
class ShazamSong(BaseModel):
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str
    key: str | None = None
    img_link: str | None = None
    release_date: str | None = None

class SpotifySong(BaseModel):
    title: str
    artist: str
    album: str
    img_link: str 
    popularity_score: int
    duration_ms: int
    spotify_id: str
    spotify_link: str
    release_date: str
class SpotifyArtist(BaseModel):
    name: str
    genres: list[str]
    popularity_score: int
    artist_id: str = ""
    
    model_config = {"frozen": True}
    
    def __hash__(self):
        return hash((self.name, self.artist_id))

class Pool_Song(BaseModel):
    title: str
    artist: str
    album: str
    img_link: str 
    genre: str | None = None
    spotify_link: str
    popularity_score: int | None = None
    duration_ms: int | None = None
    release_date: str | None = None
    lyrics: str | None = None

    model_config = {"frozen": True}
    
    def __hash__(self):
        return hash((self.title, self.artist))
