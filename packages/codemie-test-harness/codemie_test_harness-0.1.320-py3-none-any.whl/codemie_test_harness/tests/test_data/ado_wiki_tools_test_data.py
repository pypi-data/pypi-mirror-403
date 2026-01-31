from codemie_test_harness.tests.enums.tools import AzureDevOpsWikiTool, Toolkit

ado_wiki_get_test_data = [
    (
        Toolkit.AZURE_DEVOPS_WIKI,
        AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_ID,
        "In the CodemieAnton.wiki show page id 13549 content",
        """
            The content of the page with ID 1 in the `CodemieAnton.wiki` is:
    
            ```
                Parent Page Content
            ```
        """,
    ),
    (
        Toolkit.AZURE_DEVOPS_WIKI,
        AzureDevOpsWikiTool.GET_WIKI,
        "Show the details for CodemieAnton.wiki",
        """
            - **Name**: CodemieAnton.wiki
            - **Project ID**: 9d40cdc1-5404-4d40-8025-e5267d69dc89
            - **Repository ID**: 53500a82-a76e-44c4-a72c-be2b25fd90ff
            - **Type**: projectWiki
            - **ID**: 53500a82-a76e-44c4-a72c-be2b25fd90ff
            - **Remote URL**: [CodemieAnton.wiki Remote URL](https://dev.azure.com/AntonYeromin/9d40cdc1-5404-4d40-8025-e5267d69dc89/_wiki/wikis/53500a82-a76e-44c4-a72c-be2b25fd90ff)
            - **API URL**: [CodemieAnton.wiki API URL](https://dev.azure.com/AntonYeromin/9d40cdc1-5404-4d40-8025-e5267d69dc89/_apis/wiki/wikis/53500a82-a76e-44c4-a72c-be2b25fd90ff)
        """,
    ),
    (
        Toolkit.AZURE_DEVOPS_WIKI,
        AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_PATH,
        "Show the content of the root page with '/Autotest-Parent-qnw_tkcqxpfncddwtnk path in 'CodemieAnton.wiki' project wiki.",
        """
            The content of the page with the path /Autotest-Parent-qnw_tkcqxpfncddwtnk in the CodemieAnton.wiki project wiki is:
            ```
                Parent Page Content
            ```
        """,
    ),
]

ADO_WIKI_CREATE_PAGE = {
    "prompt_to_assistant": """
        Create a new root page in 'CodemieAnton.wiki' project wiki with title '{}' and content 'Greeting from CodeMie!'.
        version_identifier = 'main'
    """,
    "expected_llm_answer": """
        The page titled "{}" has been successfully created in the "CodemieAnton.wiki" project wiki with the content:

        ```
        Greeting from CodeMie!
        ```
    """,
}

ADO_WIKI_RENAME_PAGE = {
    "prompt_to_assistant": """
        Rename the page in 'CodemieAnton.wiki' project wiki '/{}' with new title '{}-Renamed'.
        Use 'version_identifier': 'main', 'version_type': 'branch'
    """,
    "expected_llm_answer": """
        The page in the `CodemieAnton` wiki has been successfully renamed from `{}` to `{}-Renamed`.
    """,
}

ADO_WIKI_MODIFY_PAGE = {
    "prompt_to_assistant": """
        Update the content of '/{}-Renamed' page in 'CodemieAnton.wiki' project wiki by adding new string: 
        'Updated content' to the end of the page. Assume you are appending to an empty page.
        Use 'version_identifier': 'main', 'version_type': 'branch'
    """,
    "expected_llm_answer": """
        The content of the '{}-Renamed' page in the 'CodemieAnton.wiki' project wiki has been successfully 
        updated to include the string 'Updated content'.
    """,
}

ADO_WIKI_DELETE_PAGE = {
    "prompt_to_assistant": "Delete the '/{}-Renamed' page located on root level in 'CodemieAnton.wiki' project wiki.",
    "expected_llm_answer": """
        The '{}-Renamed' page in the 'CodemieAnton.wiki' project wiki has been successfully deleted.
    """,
}

# === NESTED WIKI PAGES TEST DATA ===

ADO_WIKI_CREATE_NESTED_PARENT = {
    "prompt_to_assistant": """
        Create a new root page in 'CodemieAnton.wiki' project wiki with title '{}' and content 'Parent Page Content'.
        version_identifier = 'main'
    """,
    "expected_llm_answer": """
        The page titled "{}" has been successfully created in the "CodemieAnton.wiki" project wiki with the content:

        ```
        Parent Page Content
        ```
    """,
}

ADO_WIKI_CREATE_NESTED_CHILD = {
    "prompt_to_assistant": """
        Create a child page in 'CodemieAnton.wiki' project wiki under parent page '/{}'
        with title '{}' and content 'Child Page Content'.
        version_identifier = 'main'
    """,
    "expected_llm_answer": """
        The child page titled "{}" has been successfully created under parent page "{}"
        in the "CodemieAnton.wiki" project wiki with the content:

        ```
        Child Page Content
        ```
    """,
}

ADO_WIKI_CREATE_NESTED_GRANDCHILD = {
    "prompt_to_assistant": """
        Create a nested page in 'CodemieAnton.wiki' project wiki under parent page '/{}/{}'
        with title '{}' and content 'Grandchild Page Content'.
        version_identifier = 'main'
    """,
    "expected_llm_answer": """
        The nested page titled "{}" has been successfully created under parent page "{}/{}"
        in the "CodemieAnton.wiki" project wiki.
    """,
}

ADO_WIKI_GET_NESTED_CHILD = {
    "prompt_to_assistant": """
        Show the content of the nested page with '/{}/{}' path in 'CodemieAnton.wiki' project wiki.
    """,
    "expected_llm_answer": """
        The content of the nested page with the path /{}/{} in the CodemieAnton.wiki project wiki is:
        ```
        Child Page Content
        ```
    """,
}

ADO_WIKI_MODIFY_NESTED_PAGE = {
    "prompt_to_assistant": """
        Update the content of '/{}/{}' nested page in 'CodemieAnton.wiki' project wiki
        by adding new string: 'Updated nested content' to the end of the page.
        Use 'version_identifier': 'main', 'version_type': 'branch'
    """,
    "expected_llm_answer": """
        The content of the '{}/{}' nested page in the 'CodemieAnton.wiki' project wiki
        has been successfully updated to include the string 'Updated nested content'.
    """,
}

ADO_WIKI_DELETE_NESTED_CHILD = {
    "prompt_to_assistant": "Delete the '/{}/{}' nested page in 'CodemieAnton.wiki' project wiki.",
    "expected_llm_answer": """
        The '{}/{}' nested page in the 'CodemieAnton.wiki' project wiki has been successfully deleted.
    """,
}

ADO_WIKI_DELETE_NESTED_PARENT = {
    "prompt_to_assistant": "Delete the '/{}' parent page in 'CodemieAnton.wiki' project wiki.",
    "expected_llm_answer": """
        The '{}' parent page in the 'CodemieAnton.wiki' project wiki has been successfully deleted.
    """,
}

ADO_WIKI_DATASOURCE = {
    "prompt_to_assistant": "Show page under CodemieAnton.wiki named SuperMegaPage.",
    "expected_llm_answer": """
        Here is the content of the page SuperMegaPage under CodemieAnton.wiki:
            SuperMegaPage
            Test Purpose
            View in Wiki
        Let me know if you need more information or details from other pages
    """,
}
