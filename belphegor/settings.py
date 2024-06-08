from pydantic_settings import BaseSettings, SettingsConfigDict

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

    LOGGER: str = "belphegor"
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"

    LOG_CHANNEL_ID: int
    TEST_GUILDS: list[int]

    EQ_ALERT_API_USER_AGENT: str

    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"

    model_config = SettingsConfigDict(env_file = ".env", env_file_encoding = "utf-8")

settings = BelphegorSettings()
