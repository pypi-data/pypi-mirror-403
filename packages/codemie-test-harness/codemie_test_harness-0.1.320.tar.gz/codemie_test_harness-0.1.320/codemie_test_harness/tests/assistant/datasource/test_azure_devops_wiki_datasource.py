import os

import pytest
from hamcrest import assert_that, equal_to
from requests import HTTPError

from codemie_test_harness.tests.enums.tools import Default
from codemie_test_harness.tests.test_data.ado_wiki_tools_test_data import (
    ADO_WIKI_DATASOURCE,
)
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_response,
    assert_tool_triggered,
)


@pytest.mark.datasource
@pytest.mark.ado
@pytest.mark.api
def test_create_azure_devops_wiki_datasource_with_assistant(
    ado_wiki_datasource,
    ado_integration,
    datasource_utils,
    assistant,
    assistant_utils,
    kb_context,
    similarity_check,
):
    """
    Test datasource creation with Azure DevOps Wiki integration and assistant interaction.

    Validates:
    - Datasource is created successfully with valid integration
    - Datasource can be used as knowledge base context for assistant
    - Assistant can search wiki pages using the datasource
    - Search results contain information about SuperMegaPage under CodemieAnton.wiki
    """
    test_assistant = assistant(
        context=kb_context(ado_wiki_datasource),
        system_prompt="Search the knowledge base for relevant information on each user prompt",
    )

    answer, triggered_tools = assistant_utils.ask_assistant(
        test_assistant,
        ADO_WIKI_DATASOURCE["prompt_to_assistant"],
        minimal_response=False,
    )

    assert_tool_triggered(Default.SEARCH_KB, triggered_tools)
    similarity_check.check_similarity(
        answer, ADO_WIKI_DATASOURCE["expected_llm_answer"]
    )


@pytest.mark.datasource
@pytest.mark.ado
@pytest.mark.api
def test_reindex_azure_devops_wiki_datasource(
    ado_wiki_datasource,
    datasource_utils,
    assistant,
    assistant_utils,
    kb_context,
    similarity_check,
):
    """
    Test full reindex functionality for Azure DevOps Wiki datasource.

    Validates:
    - Full reindex can be triggered via update operation
    - Datasource status returns to COMPLETED after reindex
    - Assistant can still query the datasource after reindex
    - Response contains information about SuperMegaPage under CodemieAnton.wiki
    """
    test_assistant = assistant(
        context=kb_context(ado_wiki_datasource),
        system_prompt="Search the knowledge base for relevant information on each user prompt",
    )

    # Trigger full reindex
    datasource_utils.update_azure_devops_wiki_datasource(
        ado_wiki_datasource.id, full_reindex=True, skip_reindex=False
    )

    # Verify assistant can still query the datasource after reindex
    answer, triggered_tools = assistant_utils.ask_assistant(
        test_assistant,
        ADO_WIKI_DATASOURCE["prompt_to_assistant"],
        minimal_response=False,
    )

    assert_tool_triggered(Default.SEARCH_KB, triggered_tools)
    similarity_check.check_similarity(
        answer, ADO_WIKI_DATASOURCE["expected_llm_answer"]
    )


@pytest.mark.datasource
@pytest.mark.ado
@pytest.mark.api
def test_edit_description_for_azure_devops_wiki_datasource(
    client,
    ado_wiki_datasource,
    datasource_utils,
):
    """
    Test updating datasource description without reindexing.

    Validates:
    - Description can be updated successfully
    - Update does not trigger reindexing
    - Other metadata remains unchanged
    """
    updated_description = get_random_name()

    datasource_utils.update_azure_devops_wiki_datasource(
        ado_wiki_datasource.id, description=updated_description, skip_reindex=True
    )

    updated_datasource = client.datasources.get(ado_wiki_datasource.id)
    assert_that(updated_datasource.description, equal_to(updated_description))


@pytest.mark.datasource
@pytest.mark.ado
@pytest.mark.api
def test_create_azure_devops_wiki_datasource_with_existing_name(
    ado_wiki_datasource, datasource_utils
):
    """
    Test error handling for duplicate datasource names.

    Validates:
    - Creating datasource with existing name returns 409 Conflict
    - Error message indicates duplicate name
    """
    datasource = datasource_utils.get_datasource(ado_wiki_datasource.id)

    try:
        datasource_utils.create_azure_devops_wiki_datasource(
            name=datasource.name,
            setting_id=datasource.setting_id,
        )
        raise AssertionError("There are no error message for duplicate datasource name")
    except HTTPError as e:
        assert_response(
            e.response,
            409,
            f"An index with the name '{datasource.name}' already exists in the project '{os.getenv('PROJECT_NAME')}'.",
        )
