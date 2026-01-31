import pytest
from codemie_sdk.models.integration import CredentialTypes

from codemie_test_harness.tests.enums.tools import Toolkit, AzureDevOpsWikiTool
from codemie_test_harness.tests.test_data.ado_wiki_tools_test_data import (
    ado_wiki_get_test_data,
    ADO_WIKI_CREATE_PAGE,
    ADO_WIKI_RENAME_PAGE,
    ADO_WIKI_MODIFY_PAGE,
    ADO_WIKI_DELETE_PAGE,
    ADO_WIKI_CREATE_NESTED_PARENT,
    ADO_WIKI_CREATE_NESTED_CHILD,
    ADO_WIKI_CREATE_NESTED_GRANDCHILD,
    ADO_WIKI_GET_NESTED_CHILD,
    ADO_WIKI_MODIFY_NESTED_PAGE,
    ADO_WIKI_DELETE_NESTED_CHILD,
    ADO_WIKI_DELETE_NESTED_PARENT,
)
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager


@pytest.mark.assistant
@pytest.mark.ado
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    ado_wiki_get_test_data,
    ids=[f"{row[0]}_{row[1]}" for row in ado_wiki_get_test_data],
)
def test_assistant_with_ado_wiki_get_tools(
    assistant_utils,
    assistant,
    integration_utils,
    similarity_check,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    credential_values = CredentialsManager.azure_devops_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.AZURE_DEVOPS, credential_values
    )
    assistant = assistant(
        toolkit,
        tool_name,
        settings=settings,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.ado
@pytest.mark.api
def test_assistant_with_ado_wiki_modify_tools(
    assistant_utils,
    assistant,
    integration_utils,
    similarity_check,
):
    page_title = f"Autotest-Page-{get_random_name()}"
    credential_values = CredentialsManager.azure_devops_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.AZURE_DEVOPS, credential_values
    )
    assistant = assistant(
        Toolkit.AZURE_DEVOPS_WIKI,
        (
            AzureDevOpsWikiTool.MODIFY_WIKI_PAGE,
            AzureDevOpsWikiTool.RENAME_WIKI_PAGE,
            AzureDevOpsWikiTool.DELETE_WIKI_PAGE_BY_PATH,
            AzureDevOpsWikiTool.CREATE_WIKI_PAGE,
        ),
        settings=settings,
    )

    # 1. Create the page
    create_prompt = ADO_WIKI_CREATE_PAGE["prompt_to_assistant"].format(page_title)
    create_expected = ADO_WIKI_CREATE_PAGE["expected_llm_answer"].format(page_title)
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, create_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.CREATE_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, create_expected)

    # 2. Rename the page
    rename_prompt = ADO_WIKI_RENAME_PAGE["prompt_to_assistant"].format(
        page_title, page_title
    )
    rename_expected = ADO_WIKI_RENAME_PAGE["expected_llm_answer"].format(
        page_title, page_title
    )
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, rename_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.RENAME_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, rename_expected)

    # 3. Modify the page
    modify_prompt = ADO_WIKI_MODIFY_PAGE["prompt_to_assistant"].format(page_title)
    modify_expected = ADO_WIKI_MODIFY_PAGE["expected_llm_answer"].format(page_title)
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, modify_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.MODIFY_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, modify_expected)

    # 4. Delete the page
    delete_prompt = ADO_WIKI_DELETE_PAGE["prompt_to_assistant"].format(page_title)
    delete_expected = ADO_WIKI_DELETE_PAGE["expected_llm_answer"].format(page_title)
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, delete_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.DELETE_WIKI_PAGE_BY_PATH, triggered_tools)
    similarity_check.check_similarity(response, delete_expected)


@pytest.mark.assistant
@pytest.mark.ado
@pytest.mark.api
def test_assistant_with_ado_wiki_nested_pages(
    assistant_utils,
    assistant,
    integration_utils,
    similarity_check,
    cleanup_ado_wiki_pages,
):
    """
    Test complete lifecycle of nested wiki pages:
    - Create parent page
    - Create child page under parent
    - Create grandchild page (3-level nesting)
    - Retrieve nested pages by path
    - Modify nested page content
    - Delete nested pages in correct order (child first, then parent)
    """
    parent_title = f"Autotest-Parent-{get_random_name()}"
    child_title = f"Autotest-Child-{get_random_name()}"
    grandchild_title = f"Autotest-Grandchild-{get_random_name()}"

    credential_values = CredentialsManager.azure_devops_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.AZURE_DEVOPS, credential_values
    )
    test_assistant = assistant(
        Toolkit.AZURE_DEVOPS_WIKI,
        (
            AzureDevOpsWikiTool.CREATE_WIKI_PAGE,
            AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_PATH,
            AzureDevOpsWikiTool.MODIFY_WIKI_PAGE,
            AzureDevOpsWikiTool.DELETE_WIKI_PAGE_BY_PATH,
        ),
        settings=settings,
    )

    # Setup cleanup with deletion function
    def delete_page(page_path):
        if "/" in page_path:
            parent = page_path.rsplit("/", 1)[0]
            child = page_path.rsplit("/", 1)[1]
            prompt = ADO_WIKI_DELETE_NESTED_CHILD["prompt_to_assistant"].format(
                parent, child
            )
        else:
            prompt = ADO_WIKI_DELETE_NESTED_PARENT["prompt_to_assistant"].format(
                page_path
            )
        assistant_utils.ask_assistant(test_assistant, prompt, minimal_response=False)

    register_page = cleanup_ado_wiki_pages(delete_page)

    # 1. Create parent page
    create_parent_prompt = ADO_WIKI_CREATE_NESTED_PARENT["prompt_to_assistant"].format(
        parent_title
    )
    create_parent_expected = ADO_WIKI_CREATE_NESTED_PARENT[
        "expected_llm_answer"
    ].format(parent_title)
    response, triggered_tools = assistant_utils.ask_assistant(
        test_assistant, create_parent_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.CREATE_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, create_parent_expected)

    # Register parent page for cleanup immediately after creation
    register_page(parent_title)

    # 2. Create child page under parent
    create_child_prompt = ADO_WIKI_CREATE_NESTED_CHILD["prompt_to_assistant"].format(
        parent_title, child_title
    )
    create_child_expected = ADO_WIKI_CREATE_NESTED_CHILD["expected_llm_answer"].format(
        child_title, parent_title
    )
    response, triggered_tools = assistant_utils.ask_assistant(
        test_assistant, create_child_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.CREATE_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, create_child_expected)

    # Register child page for cleanup immediately after creation
    register_page(f"{parent_title}/{child_title}")

    # 3. Create grandchild page (3-level nesting)
    create_grandchild_prompt = ADO_WIKI_CREATE_NESTED_GRANDCHILD[
        "prompt_to_assistant"
    ].format(parent_title, child_title, grandchild_title)
    create_grandchild_expected = ADO_WIKI_CREATE_NESTED_GRANDCHILD[
        "expected_llm_answer"
    ].format(grandchild_title, parent_title, child_title)
    response, triggered_tools = assistant_utils.ask_assistant(
        test_assistant, create_grandchild_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.CREATE_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, create_grandchild_expected)

    # Register grandchild page for cleanup immediately after creation
    register_page(f"{parent_title}/{child_title}/{grandchild_title}")

    # 4. Retrieve nested child page by path
    get_child_prompt = ADO_WIKI_GET_NESTED_CHILD["prompt_to_assistant"].format(
        parent_title, child_title
    )
    get_child_expected = ADO_WIKI_GET_NESTED_CHILD["expected_llm_answer"].format(
        parent_title, child_title
    )
    response, triggered_tools = assistant_utils.ask_assistant(
        test_assistant, get_child_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_PATH, triggered_tools)
    similarity_check.check_similarity(response, get_child_expected)

    # 5. Modify nested page content
    modify_child_prompt = ADO_WIKI_MODIFY_NESTED_PAGE["prompt_to_assistant"].format(
        parent_title, child_title
    )
    modify_child_expected = ADO_WIKI_MODIFY_NESTED_PAGE["expected_llm_answer"].format(
        parent_title, child_title
    )
    response, triggered_tools = assistant_utils.ask_assistant(
        test_assistant, modify_child_prompt, minimal_response=False
    )
    assert_tool_triggered(AzureDevOpsWikiTool.MODIFY_WIKI_PAGE, triggered_tools)
    similarity_check.check_similarity(response, modify_child_expected)
