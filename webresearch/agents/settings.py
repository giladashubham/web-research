from __future__ import annotations

from agents import ModelSettings


def no_store_model_settings() -> ModelSettings:
    return ModelSettings(store=False)
