"""Pytest fixtures for workflow nodes tests."""

import pytest

from codemie_test_harness.tests.utils.yaml_utils import AssistantModel


@pytest.fixture(scope="module")
def item_processor(default_llm):
    """Fixture to create assistants that process individual items."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=(
                "You are a helpful assistant that processes items. "
                "Process the input data and return results in the requested format."
            ),
        )

    return _model


@pytest.fixture(scope="module")
def result_aggregator(default_llm):
    """Fixture to create assistants that aggregate results from iterations."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=(
                "You are a helpful assistant that aggregates and summarizes results. "
                "Analyze the conversation history and context to provide comprehensive summaries."
            ),
        )

    return _model


@pytest.fixture(scope="module")
def data_validator(default_llm):
    """Fixture to create assistants that validate data."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=(
                "You are a helpful assistant that validates data. "
                "Check if the provided information matches expectations and confirm or deny."
            ),
        )

    return _model


@pytest.fixture(scope="module")
def data_generator(default_llm):
    """Fixture to create assistants that generate structured data."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=(
                "You are a helpful assistant that generates structured data. "
                "Output exactly what is requested in valid JSON format without any additional text."
                "Do not use any additional formatting like markdown!"
            ),
        )

    return _model


@pytest.fixture(scope="module")
def result_handler(default_llm):
    """Fixture to create assistants that handle conditional results."""

    def _model(assistant_id: str) -> AssistantModel:
        return AssistantModel(
            id=assistant_id,
            model=default_llm.base_name,
            system_prompt=(
                "You are a helpful assistant that processes results. "
                "Confirm the branch you're in by stating it clearly."
            ),
        )

    return _model
