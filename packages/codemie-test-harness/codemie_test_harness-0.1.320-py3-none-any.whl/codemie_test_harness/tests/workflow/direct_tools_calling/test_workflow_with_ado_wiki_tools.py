import copy
import json
import random

import pytest

from codemie_test_harness.tests.enums.tools import AzureDevOpsWikiTool
from codemie_test_harness.tests.test_data.direct_tools.ado_wiki_tools_test_data import (
    ado_wiki_get_test_data,
    ADO_WIKI_CREATE_NESTED_PARENT_DIRECT,
    ADO_WIKI_CREATE_NESTED_CHILD_DIRECT,
    ADO_WIKI_GET_NESTED_PAGE_DIRECT,
)
from codemie_test_harness.tests.utils.base_utils import get_random_name


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.ado
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-5192")
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    ado_wiki_get_test_data,
    ids=[f"{row[1]}" for row in ado_wiki_get_test_data],
)
def test_workflow_with_ado_wiki_get_tools_direct(
    ado_integration,
    workflow_utils,
    similarity_check,
    workflow_with_tool,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    tool_and_state_name = get_random_name()

    _workflow = workflow_with_tool(
        tool_and_state_name, tool_name, integration=ado_integration
    )
    response = workflow_utils.execute_workflow(
        _workflow.id, tool_and_state_name, user_input=json.dumps(prompt)
    )

    similarity_check.check_similarity(response, expected_response, 95)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.ado
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-5192")
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    ado_wiki_get_test_data,
    ids=[f"{row[1]}_hardcoded" for row in ado_wiki_get_test_data],
)
def test_workflow_with_ado_wiki_get_tools_with_hardcoded_args(
    ado_integration,
    workflow_utils,
    similarity_check,
    workflow_with_tool,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    tool_and_state_name = get_random_name()

    _workflow = workflow_with_tool(
        tool_and_state_name, tool_name, integration=ado_integration, tool_args=prompt
    )
    response = workflow_utils.execute_workflow(_workflow.id, tool_and_state_name)

    similarity_check.check_similarity(response, expected_response, 95)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.ado
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-5192")
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    ado_wiki_get_test_data,
    ids=[f"{row[1]}_overriding" for row in ado_wiki_get_test_data],
)
def test_workflow_with_ado_wiki_get_tools_with_overriding_args(
    ado_integration,
    workflow_utils,
    similarity_check,
    workflow_with_tool,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    tool_and_state_name = get_random_name()

    args_copy = copy.deepcopy(prompt)
    args_copy = {key: random.randint(1, 10) for key in args_copy}

    _workflow = workflow_with_tool(
        tool_and_state_name, tool_name, integration=ado_integration, tool_args=args_copy
    )
    response = workflow_utils.execute_workflow(
        _workflow.id, tool_and_state_name, user_input=json.dumps(prompt)
    )

    similarity_check.check_similarity(response, expected_response, 95)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.ado
@pytest.mark.api
def test_workflow_with_ado_wiki_nested_pages_direct(
    ado_integration,
    workflow_utils,
    similarity_check,
    workflow_with_tool,
    cleanup_ado_wiki_pages,
):
    """
    Test nested wiki page creation and retrieval using direct tool calling:
    - Create parent page using direct tool call
    - Create child page under parent
    - Retrieve nested page by path
    - Delete pages in correct order
    """
    parent_title = f"Autotest-Parent-{get_random_name()}"
    child_title = f"Autotest-Child-{get_random_name()}"

    # Setup cleanup with deletion function
    def delete_page(page_path):
        delete_args = {
            "wiki_identified": "CodemieAnton.wiki",
            "page_name": page_path,
        }
        delete_state = get_random_name()
        delete_workflow = workflow_with_tool(
            delete_state,
            AzureDevOpsWikiTool.DELETE_WIKI_PAGE_BY_PATH,
            integration=ado_integration,
        )
        workflow_utils.execute_workflow(
            delete_workflow.id, delete_state, user_input=json.dumps(delete_args)
        )

    register_page = cleanup_ado_wiki_pages(delete_page)

    # 1. Create parent page using hardcoded tool args to avoid serialization issues
    parent_args = copy.deepcopy(ADO_WIKI_CREATE_NESTED_PARENT_DIRECT)
    parent_args["new_page_name"] = parent_args["new_page_name"].format(parent_title)

    create_parent_state = get_random_name()
    create_parent_workflow = workflow_with_tool(
        create_parent_state,
        AzureDevOpsWikiTool.CREATE_WIKI_PAGE,
        integration=ado_integration,
        tool_args=parent_args,
    )

    # Execute without user_input since args are hardcoded in the tool
    workflow_utils.client.workflows.run(create_parent_workflow.id, user_input="")

    # Register parent page for cleanup immediately after creation
    register_page(parent_title)

    # 2. Create child page under parent using hardcoded tool args
    child_args = copy.deepcopy(ADO_WIKI_CREATE_NESTED_CHILD_DIRECT)
    child_args["parent_page_path"] = child_args["parent_page_path"].format(parent_title)
    child_args["new_page_name"] = child_args["new_page_name"].format(child_title)

    create_child_state = get_random_name()
    create_child_workflow = workflow_with_tool(
        create_child_state,
        AzureDevOpsWikiTool.CREATE_WIKI_PAGE,
        integration=ado_integration,
        tool_args=child_args,
    )

    # Execute without user_input since args are hardcoded in the tool
    workflow_utils.client.workflows.run(create_child_workflow.id, user_input="")

    # Register child page for cleanup immediately after creation
    register_page(f"{parent_title}/{child_title}")

    # 3. Retrieve nested child page by path
    get_args = copy.deepcopy(ADO_WIKI_GET_NESTED_PAGE_DIRECT)
    get_args["page_name"] = get_args["page_name"].format(parent_title, child_title)

    get_state = get_random_name()
    get_workflow = workflow_with_tool(
        get_state,
        AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_PATH,
        integration=ado_integration,
    )
    get_response = workflow_utils.execute_workflow(
        get_workflow.id, get_state, user_input=json.dumps(get_args)
    )
    similarity_check.check_similarity(get_response, "Child Page Content", 90)
