from pydantic import BaseModel

class SongResponse(BaseModel):
    title: str
    artist: str
    album: str
    spotify_link: str
    img_link: str 