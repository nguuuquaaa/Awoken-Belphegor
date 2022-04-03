from pydantic import BaseSettings

#=============================================================================================================================#

class BelphegorSettings(BaseSettings):
    DISCORD_TOKEN: str
    GOOGLE_CLIENT_API_KEY: str
    DBOTS_TOKEN: str
    DBL_TOKEN: str

settings = BelphegorSettings(_env_file=".env", _env_file_encoding="utf-8")