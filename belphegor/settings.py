from pydantic import BaseSettings

#=============================================================================================================================#

class BelphegorSettings(BaseSettings):
    DISCORD_TOKEN: str
    GOOGLE_CLIENT_API_KEY: str
    DBOTS_TOKEN: str
    DBL_TOKEN: str

    G_EMAIL: str
    G_PASSWORD: str

    GFWIKI_BOT_USERNAME: str
    GFWIKI_BOT_PASSWORD: str

    LOG_CHANNEL_ID: int

    LOGGER: str = "belphegor"
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"

settings = BelphegorSettings(_env_file = ".env", _env_file_encoding = "utf-8")
