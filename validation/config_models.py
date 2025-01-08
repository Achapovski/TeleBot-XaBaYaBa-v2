from pydantic import BaseModel, SecretStr, PostgresDsn


class BotConfig(BaseModel):
    token: SecretStr


class DBConfig(BaseModel):
    connection: str
    user: str
    password: SecretStr
    host: str
    port: int
    database: str
    is_echo: bool
    dsn: PostgresDsn

