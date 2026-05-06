from __future__ import annotations

import os

from agents import ModelSettings


def no_store_model_settings() -> ModelSettings:
    return ModelSettings(store=False)


def model_from_env(env_var: str, default: str) -> str:
    return os.getenv(env_var) or default
