from pydantic import BaseModel
class ShazamSong(BaseModel):
    title: str
    artist: str
    album: str
    genre: str
    key: str
    img_link: str
    release_date: str

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
    

class Pool_Song(BaseModel):
    title: str
    artist: str
    album: str
    img_link: str 
    genre: str
    spotify_link: str
    popularity_score: int
    duration_ms: int 
    release_date: str
    lyrics: str
    comes_from: str
    
    model_config = {"frozen": True}
    
    def __hash__(self):
        return hash((self.title, self.artist))
