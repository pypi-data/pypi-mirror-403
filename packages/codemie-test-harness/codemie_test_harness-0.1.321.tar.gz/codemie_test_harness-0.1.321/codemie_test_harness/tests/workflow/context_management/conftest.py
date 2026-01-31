"""Pytest fixtures for context management tests."""

import pytest

from codemie_test_harness.tests.utils.yaml_utils import AssistantModel
from codemie_test_harness.tests.workflow.context_management import SYSTEM_PROMPTS


@pytest.fixture(scope="module")
def data_extractor(default_llm):
    """Context Management fixture to create data extraction assistants."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=SYSTEM_PROMPTS["data_extractor"],
        )

    return _model


@pytest.fixture(scope="module")
def data_processor(default_llm):
    """Context Management fixture to create data processing assistants."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=SYSTEM_PROMPTS["data_processor"],
        )

    return _model


@pytest.fixture(scope="module")
def information_provider(default_llm):
    """Context Management fixture to create information provider assistants."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=SYSTEM_PROMPTS["information_provider"],
        )

    return _model


@pytest.fixture(scope="module")
def information_validator(default_llm):
    """Context Management fixture to create information validator assistants."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=SYSTEM_PROMPTS["information_validator"],
        )

    return _model
