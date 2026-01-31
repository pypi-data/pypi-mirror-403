# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ModelFineTuneParams"]


class ModelFineTuneParams(TypedDict, total=False):
    base_model: Required[str]

    training_data_url: Required[str]

    hyperparameters: object
