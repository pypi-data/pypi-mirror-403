from codemie_test_harness.tests.enums.tools import Toolkit, AzureDevOpsWikiTool

ado_wiki_get_test_data = [
    (
        Toolkit.AZURE_DEVOPS_WIKI,
        AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_ID,
        {"wiki_identified": "CodemieAnton.wiki", "page_id": 13549},
        "Parent Page Content",
    ),
    (
        Toolkit.AZURE_DEVOPS_WIKI,
        AzureDevOpsWikiTool.GET_WIKI,
        {"wiki_identified": "CodemieAnton.wiki"},
        """
            {
              "mapped_path": "/",
              "name": "CodemieAnton.wiki",
              "project_id": "9d40cdc1-5404-4d40-8025-e5267d69dc89",
              "repository_id": "53500a82-a76e-44c4-a72c-be2b25fd90ff",
              "type": "projectWiki",
              "id": "53500a82-a76e-44c4-a72c-be2b25fd90ff",
              "remote_url": "https://dev.azure.com/AntonYeromin/9d40cdc1-5404-4d40-8025-e5267d69dc89/_wiki/wikis/53500a82-a76e-44c4-a72c-be2b25fd90ff",
              "url": "https://dev.azure.com/AntonYeromin/9d40cdc1-5404-4d40-8025-e5267d69dc89/_apis/wiki/wikis/53500a82-a76e-44c4-a72c-be2b25fd90ff",
              "versions": [
                {
                  "version": "wikiMaster"
                }
              ]
            }
        """,
    ),
    (
        Toolkit.AZURE_DEVOPS_WIKI,
        AzureDevOpsWikiTool.GET_WIKI_PAGE_BY_PATH,
        {
            "wiki_identified": "CodemieAnton.wiki",
            "page_name": "Autotest-Parent-qnw_tkcqxpfncddwtnk",
        },
        "Parent Page Content",
    ),
]

# === NESTED WIKI PAGES TEST DATA FOR DIRECT TOOLS ===

ADO_WIKI_CREATE_NESTED_PARENT_DIRECT = {
    "wiki_identified": "CodemieAnton.wiki",
    "parent_page_path": "/",
    "new_page_name": "{}",
    "page_content": "Parent Page Content",
    "version_identifier": "main",
    "version_type": "branch",
}

ADO_WIKI_CREATE_NESTED_CHILD_DIRECT = {
    "wiki_identified": "CodemieAnton.wiki",
    "parent_page_path": "/{}",
    "new_page_name": "{}",
    "page_content": "Child Page Content",
    "version_identifier": "main",
    "version_type": "branch",
}

ADO_WIKI_GET_NESTED_PAGE_DIRECT = {
    "wiki_identified": "CodemieAnton.wiki",
    "page_name": "/{}/{}",
}
