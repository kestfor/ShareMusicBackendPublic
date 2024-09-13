from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    spotify_client_id: SecretStr
    spotify_client_secret: SecretStr
    sql_host: SecretStr
    sql_port: SecretStr
    sql_username: SecretStr
    sql_password: SecretStr
    sql_database: SecretStr
    global_domain: SecretStr
    bot_token: SecretStr
    bot_login: SecretStr
    test_bot_id: SecretStr
    redis_host: SecretStr
    redis_port: SecretStr
    redis_password: SecretStr

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
