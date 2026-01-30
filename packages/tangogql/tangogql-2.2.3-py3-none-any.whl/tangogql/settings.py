import logging
from logging.config import fileConfig

from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """
    Load app configuration from environment vars or JSON file
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_prefix="TANGOGQL_",  # Env vars need to be prefixed e.g. TANGOGQL_NO_AUTH
        json_file="config.json",  # If this file exists, load config from it
    )

    app_name: str = "TangoGQL"

    # The 'secret' is used for encrypting auth data in requests
    secret: str = "Replace me with a random string!"
    # If 'required_groups' is not empty, a user must be member of at least one
    # of these groups in order to do mutations.
    required_groups: list[str] = []
    # Set this to disable all auth checking (for testing and development)
    no_auth: bool = False

    # Wait time between reads for subscribed attributes with client polling
    attribute_poll_period: float = 3.0  # seconds

    logging_config: str | None = "logging.ini"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            # Env vars override JSON settings, which override defaults
            env_settings,
            JsonConfigSettingsSource(settings_cls),
        )


def get_settings():
    return Settings()


def setup_logging():
    # Note: It's important to setup logging at an early point, before
    # imports that use logging
    settings = get_settings()
    if settings.logging_config:
        try:
            fileConfig(settings.logging_config)
        except (FileNotFoundError, KeyError) as e:  # KeyError in python 3.10..?
            logging.error(f"Error configuring logging: {e}")
