from enum import Enum


class Toolkit(str, Enum):
    """Enum for toolkits."""

    GIT = "Git"
    VCS = "VCS"
    CODEBASE_TOOLS = "Codebase Tools"
    CODE_ANALYSIS = "CodeAnalysisToolkit"
    CODE_EXPLORATION = "CodeExplorationToolkit"
    CLOUD = "Cloud"
    PLUGIN = "Plugin"
    RESEARCH = "Research"
    AZURE_DEVOPS_TEST_PLAN = "Azure DevOps Test Plan"
    AZURE_DEVOPS_WORK_ITEM = "Azure DevOps Work Item"
    AZURE_DEVOPS_WIKI = "Azure DevOps Wiki"
    NOTIFICATION = "Notification"
    PROJECT_MANAGEMENT = "Project Management"
    FILE_MANAGEMENT = "FileSystem"
    OPEN_API = "OpenAPI"
    DATA_MANAGEMENT = "Data Management"
    SERVICENOW = "IT Service Management"
    ACCESS_MANAGEMENT = "Access Management"
    REPORT_PORTAL = "Report Portal"


class GitTool(str, Enum):
    """Enum for Git tool names."""

    LIST_BRANCHES_IN_REPO = "list_branches_in_repo"
    CREATE_BRANCH = "create_branch"
    SET_ACTIVE_BRANCH = "set_active_branch"
    CREATE_FILE = "create_file"
    UPDATE_FILE = "update_file"
    UPDATE_FILE_DIFF = "update_file_diff"
    DELETE_FILE = "delete_file"
    CREATE_PULL_REQUEST = "create_pull_request"
    GET_PR_CHANGES = "get_pr_changes"
    CREATE_PR_CHANGES_COMMENT = "create_pr_changes_comment"


class CodeBaseTool(str, Enum):
    """Enum for CodeBase tool names."""

    SONAR = "Sonar"
    SONAR_CLOUD = "Sonar Cloud"
    GET_REPOSITORY_FILE_TREE_V2 = "get_repository_file_tree_v2"
    SEARCH_CODE_REPO_V2 = "search_code_repo_v2"
    READ_FILES_CONTENT = "read_files_content"
    READ_FILES_CONTENT_SUMMARY = "read_files_content_summary"
    SEARCH_CODE_REPO_BY_PATH = "search_code_repo_by_path"


class VcsTool(str, Enum):
    """Enum for VCS tool names."""

    GITLAB = "gitlab"
    GITHUB = "github"
    AZURE_DEVOPS_GIT = "azure_devops_git"


class CloudTool(str, Enum):
    """Enum for Cloud tool names."""

    AWS = "AWS"
    GCP = "GCP"
    AZURE = "Azure"
    KUBERNETES = "Kubernetes"


class PluginTool(str, Enum):
    """Enum for Plugin tool names."""

    # development plugin tools
    LIST_FILES_IN_DIRECTORY = "_list_files_in_directory"
    RUN_COMMAND_LINE_TOOL = "_run_command_line_tool"
    WRITE_FILE_TO_FILE_SYSTEM = "_write_file_to_file_system"
    READ_FILE_FROM_FILE_SYSTEM = "_read_file_from_file_system"
    GENERIC_GIT_TOOL = "_generic_git_tool"

    # cli mcp serv er tools
    RUN_COMMAND = "_run_command"
    SHOW_SECURITY_RULES = "_show_security_rules"

    # filesystem mcp
    LIST_DIRECTORY = "_list_directory"
    WRITE_FILE = "_write_file"
    READ_FILE = "_read_file"


class AzureDevOpsWikiTool(str, Enum):
    """Enum for Azure DevOps Wiki tool names."""

    GET_WIKI = "get_wiki"
    GET_WIKI_PAGE_BY_PATH = "get_wiki_page_by_path"
    GET_WIKI_PAGE_BY_ID = "get_wiki_page_by_id"
    DELETE_WIKI_PAGE_BY_PATH = "delete_page_by_path"
    DELETE_WIKI_PAGE_BY_ID = "delete_page_by_id"
    MODIFY_WIKI_PAGE = "modify_wiki_page"
    RENAME_WIKI_PAGE = "rename_wiki_page"
    CREATE_WIKI_PAGE = "create_wiki_page"


class AzureDevOpsTestPlanTool(str, Enum):
    """Enum for Azure DevOps Test Plan tool names."""

    CREATE_TEST_PLAN = "create_test_plan"
    DELETE_TEST_PLAN = "delete_test_plan"
    GET_TEST_PLAN = "get_test_plan"
    CREATE_TEST_SUITE = "create_test_suite"
    DELETE_TEST_SUITE = "delete_test_suite"
    GET_TEST_SUITE = "get_test_suite"
    ADD_TEST_CASE = "add_test_case"
    GET_TEST_CASE = "get_test_case"
    GET_TEST_CASES = "get_test_cases"


class AzureDevOpsWorkItemTool(str, Enum):
    """Enum for Azure DevOps Work Item tool names."""

    GET_WORK_ITEM = "get_work_item"
    GET_COMMENTS = "get_comments"
    GET_RELATION_TYPES = "get_relation_types"
    SEARCH_WORK_ITEMS = "search_work_items"
    CREATE_WORK_ITEM = "create_work_item"
    UPDATE_WORK_ITEM = "update_work_item"
    LINK_WORK_ITEMS = "link_work_items"


class ResearchToolName(str, Enum):
    """Enum for Research tool names."""

    GOOGLE_SEARCH = "google_search_tool_json"
    GOOGLE_PLACES = "google_places"
    GOOGLE_PLACES_FIND_NEAR = "google_places_find_near"
    WIKIPEDIA = "wikipedia"
    TAVILY_SEARCH = "tavily_search_results_json"
    WEB_SCRAPPER = "web_scrapper"


class NotificationTool(str, Enum):
    """Enum for Notification tool names."""

    EMAIL = "Email"
    TELEGRAM = "Telegram"


class ProjectManagementTool(str, Enum):
    """Enum for Project Management tool names."""

    JIRA = "generic_jira_tool"
    CONFLUENCE = "generic_confluence_tool"


class FileManagementTool(str, Enum):
    """Enum for File Management tool names."""

    READ_FILE = "read_file_from_file_system"
    WRITE_FILE = "write_file_to_file_system"
    LIST_DIRECTORY = "list_directory_from_file_system"
    RUN_COMMAND_LINE = "run_command_line_tool"
    PYTHON_CODE_INTERPRETER = "python_repl_code_interpreter"
    CODE_EXECUTOR = "code_executor"
    GENERATE_IMAGE = "generate_image_tool"
    DIFF_UPDATE = "diff_update_file_tool"
    FILESYSTEM_EDITOR = "str_replace_editor"


class OpenApiTool(str, Enum):
    """Enum for Open API tool names."""

    INVOKE_EXTERNAL_API = "open_api"
    GET_OPEN_API_SPEC = "open_api_spec"


class DataManagementTool(str, Enum):
    """Enum for Data Management tool names."""

    ELASTIC = "elastic"
    SQL = "sql"


class ServiceNowTool(str, Enum):
    """Enum for ServiceNow tool names."""

    SERVICE_NOW = "servicenow_table_tool"


class AccessManagementTool(str, Enum):
    """Enum for Access Management tool names."""

    KEYCLOAK = "keycloak"


class ReportPortalTool(str, Enum):
    """Enum for Report Portal tool names."""

    GET_EXTENDED_LAUNCH_DATA_AS_RAW = "get_extended_launch_data_as_raw"
    GET_LAUNCH_DETAILS = "get_launch_details"
    GET_ALL_LAUNCHES = "get_all_launches"
    FIND_TEST_ITEM_BY_ID = "find_test_item_by_id"
    GET_TEST_ITEMS_FOR_LAUNCH = "get_test_items_for_launch"
    GET_LOGS_FOR_TEST_ITEM = "get_logs_for_test_item"
    GET_USER_INFORMATION = "get_user_information"
    GET_DASHBOARD_DATA = "get_dashboard_data"


class McpServerTime(str, Enum):
    """Enum for Time MCP Server tool names."""

    GET_CURRENT_TIME = "get_current_time"
    CONVERT_TIME = "convert_time"


class CliMcpServer(str, Enum):
    """Enum for Cli MCP Server tool names."""

    RUN_COMMAND = "run command"


class McpServerFetch(str, Enum):
    """Enum for MCP Server Fetch tool names."""

    FETCH = "fetch"


class McpServerPnlOptimizer(str, Enum):
    """Enum for PNL Optimizer MCP Server tool names."""

    GET_EMPLOYEES_INFO = "GetEmployeesInfo"


class McpServerSqlite(str, Enum):
    """Enum for SQLite MCP Server tool names."""

    LIST_TABLES = "list_tables"
    DESCRIBE_TABLE = "describe_table"
    READ_QUERY = "read_query"
    CREATE_TABLE = "create_table"
    WRITE_QUERY = "write_query"


class McpServerFilesystem(str, Enum):
    """Enum for Filesystem MCP Server tool names."""

    READ_FILE = "read_file"
    READ_TEXT_FILE = "read_text_file"
    READ_MEDIA_FILE = "read_media_file"
    READ_MULTIPLE_FILES = "read_multiple_files"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    CREATE_DIRECTORY = "create_directory"
    LIST_DIRECTORY = "list_directory"
    LIST_DIRECTORY_WITH_SIZES = "list_directory_with_sizes"
    DIRECTORY_TREE = "directory_tree"
    MOVE_FILE = "move_file"
    SEARCH_FILES = "search_files"
    GET_FILE_INFO = "get_file_info"
    LIST_ALLOWED_DIRECTORIES = "list_allowed_directories"


class McpServerGit(str, Enum):
    """Enum for Git MCP Server tool names."""

    GIT_STATUS = "git_status"
    GIT_DIFF = "git_diff"
    GIT_DIFF_UNSTAGED = "git_diff_unstaged"
    GIT_DIFF_STAGED = "git_diff_staged"
    GIT_COMMIT = "git_commit"
    GIT_ADD = "git_add"
    GIT_RESET = "git_reset"
    GIT_LOG = "git_log"
    GIT_SHOW = "git_show"
    CREATE_BRANCH = "create_branch"
    CHECKOUT_BRANCH = "checkout_branch"
    LIST_BRANCHES = "list_branches"


class McpServerGithub(str, Enum):
    """Enum for GitHub MCP Server tool names."""

    CREATE_OR_UPDATE_FILE = "create_or_update_file"
    SEARCH_REPOSITORIES = "search_repositories"
    CREATE_REPOSITORY = "create_repository"
    GET_FILE_CONTENTS = "get_file_contents"
    PUSH_FILES = "push_files"
    CREATE_ISSUE = "create_issue"
    CREATE_PULL_REQUEST = "create_pull_request"
    FORK_REPOSITORY = "fork_repository"
    CREATE_BRANCH = "create_branch"
    LIST_COMMITS = "list_commits"
    LIST_ISSUES = "list_issues"
    UPDATE_ISSUE = "update_issue"
    ADD_ISSUE_COMMENT = "add_issue_comment"
    SEARCH_CODE = "search_code"
    SEARCH_ISSUES = "search_issues"
    SEARCH_USERS = "search_users"
    GET_ISSUE = "get_issue"
    GET_PULL_REQUEST = "get_pull_request"
    LIST_PULL_REQUESTS = "list_pull_requests"
    CREATE_PULL_REQUEST_REVIEW = "create_pull_request_review"
    MERGE_PULL_REQUEST = "merge_pull_request"
    GET_PULL_REQUEST_FILES = "get_pull_request_files"
    GET_PULL_REQUEST_STATUS = "get_pull_request_status"
    UPDATE_PULL_REQUEST_BRANCH = "update_pull_request_branch"
    GET_PULL_REQUEST_COMMENTS = "get_pull_request_comments"
    GET_PULL_REQUEST_REVIEWS = "get_pull_request_reviews"


class McpServerPostgresql(str, Enum):
    """Enum for PostgreSQL MCP Server tool names."""

    QUERY = "query"


class McpServerPlaywright(str, Enum):
    """Enum for Playwright MCP Server tool names."""

    BROWSER_NAVIGATE = "browser_navigate"
    BROWSER_SCREENSHOT = "browser_take_screenshot"


class McpServerPuppeteer(str, Enum):
    """Enum for Puppeteer MCP Server tool names."""

    PUPPETEER_NAVIGATE = "puppeteer_navigate"
    PUPPETEER_SCREENSHOT = "puppeteer_screenshot"
    PUPPETEER_CLICK = "puppeteer_click"
    PUPPETEER_FILL = "puppeteer_fill"
    PUPPETEER_SELECT = "puppeteer_select"
    PUPPETEER_HOVER = "puppeteer_hover"
    PUPPETEER_EVALUATE = "puppeteer_evaluate"


class Default(str, Enum):
    """Enum for tools that attached automatically e.g. on added datasource or file uploaded."""

    GET_REPOSITORY_FILE_TREE = "get_repository_file_tree"
    SEARCH_KB = "search_kb"
    FILE_ANALYSIS = "file_analysis"
    DOCX_TOOL = "docx_tool"
    EXCEL_TOOL = "excel_tool"
    PYTHON_REPL_AST = "python_repl_ast"
    PPTX_TOOL = "pptx_tool"
    PDF_TOOL = "pdf_tool"


class CodeAnalysisTools(str, Enum):
    """Enum for CodeAnalysisToolkit tool names."""

    GET_FILES_TREE = "get_files_tree"
    GET_FILES_LIST = "get_files_list"
    GET_CODE = "get_code"
    GET_CODE_MEMBERS = "get_code_members"
    GET_OUTGOING_DEPENDENCIES = "get_outgoing_dependencies"
    GET_METADATA = "get_metadata"
    GET_DATASOURCE = "get_datasource"


class CodeExplorationTools(str, Enum):
    """Enum for CodeExplorationToolkit tool names."""

    GET_NODES_BY_IDS = "get_nodes_by_ids"
    GRAPH_SEARCH = "graph_search"
    GET_DATASOURCE = "get_datasource"
    FIND_NODES_BY_NAME = "find_nodes_by_name"
    WORKSPACE_TREE_EXPLORATION = "workspace_tree_exploration"
    GET_GRAPH_DATA_MODEL = "get_graph_data_model"
    SUMMARIES_SEARCH = "summaries_search"
