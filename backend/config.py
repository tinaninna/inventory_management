from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Inventory Management API"
    app_version: str = "0.2.0"
    database_url: str = Field(
        default="mysql+pymysql://root:@localhost:3306/inventory_management?charset=utf8mb4",
        alias="DATABASE_URL",
    )
    db_driver: str = Field(default="mysql", alias="DB_DRIVER")
    db_host: str | None = Field(default="localhost", alias="DB_HOST")
    db_port: int | None = Field(default=3306, alias="DB_PORT")
    db_name: str | None = Field(default="inventory_management", alias="DB_NAME")
    db_user: str | None = Field(default="root", alias="DB_USER")
    db_password: str | None = Field(default="", alias="DB_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        user = self.db_user or "root"
        password = self.db_password or ""
        host = self.db_host or "localhost"
        port = self.db_port or 3306
        name = self.db_name or "inventory_management"
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


settings = Settings()
