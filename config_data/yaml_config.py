from functools import lru_cache

from yaml import load, CSafeLoader
from validation.config_models import BaseModel


@lru_cache
def _parse_config_file() -> dict:
    with open("config.yml") as file:
        return load(file, CSafeLoader)


@lru_cache
def get_config(model: type[BaseModel], root_key: str) -> BaseModel.model_validate:
    config_dict = _parse_config_file()
    if root_key not in config_dict:
        error = f"Key {root_key} not found in bot config."
        raise ValueError(error)
    return model.model_validate(config_dict[root_key])
