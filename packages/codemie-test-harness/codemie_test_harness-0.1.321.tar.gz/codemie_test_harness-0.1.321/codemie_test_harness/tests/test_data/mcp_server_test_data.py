from typing import NamedTuple, Optional

from codemie_sdk.models.assistant import MCPServerDetails, MCPServerConfig

from codemie_test_harness.tests.enums.tools import (
    PluginTool,
    McpServerSqlite,
    McpServerFilesystem,
    McpServerGithub,
    McpServerPostgresql,
    McpServerPlaywright,
    McpServerPuppeteer,
)
from codemie_test_harness.tests.test_data.vcs_tools_test_data import (
    GITHUB_TOOL_TASK,
    RESPONSE_FOR_GITHUB,
)
from codemie_test_harness.tests.utils.constants import TESTS_PATH


class MCPServerTestCase(NamedTuple):
    """Test case for MCP server assistant tests."""

    mcp_server: MCPServerDetails
    user_message: str
    expected_response: str
    expected_tools: list[str]
    integration_fixture: Optional[str] = None


cli_mcp_server_test_data = [
    (
        "ls",
        """
            Here is the list of directories and files in the current directory:
    
            bin
            games
            include
            lib
            lib64
            libexec
            local
            sbin
            share
            src
        """,
    ),
    (
        "ls /tmp",
        """
            It seems that the command `ls /tmp` cannot be executed because it is outside the allowed directory (`/usr`).
            Only commands within the `/usr` directory are permitted.
        """,
    ),
    (
        "touch long-file-name-for-test.txt",
        """
            It appears that the command exceeds the maximum allowed length of 20 characters.
            Let's try a shorter command.
        """,
    ),
    (
        "cat file.txt",
        """
            The `cat` command is not supported in this environment. If you need to list or display
            the contents of a file, please provide an alternative command that is supported.
            You can use `ls` to list files or `echo` to display text.
        """,
    ),
    (
        "ls -a",
        """
            The `-a` flag is not allowed in this environment. Here are the allowed commands and flags:
    
            - Commands: `ls`, `echo`
            - Flags: `-l`, `--help`
    
            Would you like to run a different command?
        """,
    ),
]

CLI_MCP_SERVER = MCPServerDetails(
    name="CLI MCP server",
    description="CLI MCP server",
    enabled=True,
    config=MCPServerConfig(
        command="uvx",
        args=["cli-mcp-server"],
        env={
            "ALLOWED_DIR": "/usr",
            "ALLOWED_COMMANDS": "ls,echo,touch",
            "ALLOWED_FLAGS": "-l,--help",
            "MAX_COMMAND_LENGTH": "20",
        },
    ),
)

TIME_MCP_SERVER_WITH_CONFIG = MCPServerDetails(
    name="Time MCP server",
    description="Time MCP server",
    enabled=True,
    config=MCPServerConfig(command="uvx", args=["mcp-server-time"]),
)

TIME_MCP_SERVER_WITHOUT_CONFIG = MCPServerDetails(
    name="Time MCP server",
    description="Time MCP server",
    command="uvx",
    arguments="mcp-server-time",
    enabled=True,
)

time_mcp_server_test_data = [
    TIME_MCP_SERVER_WITH_CONFIG,
    TIME_MCP_SERVER_WITHOUT_CONFIG,
]

FETCH_MCP_SERVER = MCPServerDetails(
    name="Fetch MCP server",
    description="Fetch MCP server",
    enabled=True,
    config=MCPServerConfig(command="uvx", args=["mcp-server-fetch"]),
)

fetch_server_prompt = "Fetch https://rubular.com/"

fetch_expected_response = """
    Rubular is a Ruby regular expression editor. It provides a quick reference guide for regex syntax:

    ### Regex Quick Reference
    
    #### Character Classes
    - `[abc]`: A single character of: a, b, or c
    - `[^abc]`: Any single character except: a, b, or c
    - `[a-z]`: Any single character in the range a-z
    - `[a-zA-Z]`: Any single character in the range a-z or A-Z
    
    #### Anchors
    - `^`: Start of line
    - `$`: End of line
    - `\A`: Start of string
    - `\z`: End of string
    
    #### Special Characters
    - `.`: Any single character
    - `\s`: Any whitespace character
    - `\S`: Any non-whitespace character
    - `\d`: Any digit
    - `\D`: Any non-digit
    - `\w`: Any word character (letter, number, underscore)
    - `\W`: Any non-word character
    - `\b`: Any word boundary
    
    #### Grouping and Quantifiers
    - `(...)`: Capture everything enclosed
    - `(a|b)`: a or b
    - `a?`: Zero or one of a
    - `a*`: Zero or more of a
    - `a+`: One or more of a
    - `a{3}`: Exactly 3 of a
    - `a{3,}`: 3 or more of a
    - `a{3,6}`: Between 3 and 6 of a
    
    #### Options
    - `i`: Case insensitive
    - `m`: Make dot match newlines
    - `x`: Ignore whitespace in regex
    - `o`: Perform `#{...}` substitutions only once
    
    This editor can be helpful for testing and experimenting with Ruby regular expressions.
"""

time_server_prompt = (
    'Convert time 23:11 from "Asia/Tokyo" timezone to "America/New_York" timezone'
)

time_expected_response = """
    The time 23:11 (11:11 PM) in the "Asia/Tokyo" timezone converts to 10:11 (10:11 AM) on the same day
     in the "America/New_York" timezone.
"""

cli_mcp_server_with_plugin_test_data = [
    (
        "ls",
        f"""
            Here is a list of files and directories in `{TESTS_PATH}`:

            - Files:
              - `.DS_Store`
              - `__init__.py`
              - `conftest.py`

            - Directories:
              - `__pycache__`
              - `assistant`
              - `e2e`
              - `enums`
              - `integrations`
              - `llm`
              - `providers`
              - `search`
              - `service`
              - `test_data`
              - `ui`
              - `utils`
              - `workflow`
        """,
    ),
    (
        "Run ls /tmp. In case of any error do not try to execute the command in other directory or with additional parameters.",
        f"""
            It seems that the command `ls /tmp` cannot be executed because it is outside the allowed directory (`{TESTS_PATH}`).
            Only commands within the `{TESTS_PATH}` directory are permitted.
        """,
    ),
]

filesystem_mcp_server_with_plugin_test_data = [
    (
        f"ls {TESTS_PATH}",
        f"""
            Here is a list of files and directories in `{TESTS_PATH}`:

            - Files:
              - `.DS_Store`
              - `__init__.py`
              - `conftest.py`

            - Directories:
              - `__pycache__`
              - `assistant`
              - `e2e`
              - `enums`
              - `integrations`
              - `llm`
              - `providers`
              - `search`
              - `service`
              - `test_data`
              - `ui`
              - `utils`
              - `workflow`
        """,
        PluginTool.LIST_DIRECTORY,
    ),
    (
        "ls /tmp",
        f"""
            It seems that the command `ls /tmp` cannot be executed because it is outside the allowed directory (`{TESTS_PATH}`).
            Only commands within the `{TESTS_PATH}` directory are permitted.
        """,
        PluginTool.LIST_DIRECTORY,
    ),
    (
        f"Create a new {TESTS_PATH}/sdk_tests.properties file with content sdk_tests=preview",
        f"I have successfully created the {TESTS_PATH}/sdk_tests.properties file with the content sdk_tests=preview.",
        PluginTool.WRITE_FILE,
    ),
    (
        f"Show the content of the {TESTS_PATH}/enums/integrations.py file",
        """
            from enum import Enum


            class DataBaseDialect(str, Enum):
            \"""Enum for DB Dialect names.\"""

            MS_SQL = "mssql"
            MY_SQL = "mysql"
            POSTGRES = "postgres"
        """,
        PluginTool.READ_FILE,
    ),
]

# PNL Optimizer MCP Server with streamable-http transport
PNL_OPTIMIZER_MCP_SERVER = MCPServerDetails(
    name="PNL Optimizer MCP Server",
    description="PNL Optimizer MCP Server with streamable-http transport",
    enabled=True,
    config=MCPServerConfig(
        url="http://pnl-optimizer-mcp.preview-codemie:8080/mcp",
        headers={
            "X-API-KEY": "$API_KEY",
            "Content-Type": "application/json",
        },
        auth_token="SecretAccessToken",
        type="streamable-http",
    ),
)

PNL_OPTIMIZER_MCP_SERVER_PROMPT = "Show employee info by ID 4060741400382660039"

PNL_OPTIMIZER_MCP_SERVER_EXPECTED_RESPONSE = """
    Here are the details for the employee with ID 4060741400382660039:
        Name: Andrei Maskouchanka
        Business Email: Andrei_Maskouchanka@epam.com
        Location: Rechitsky, 80, Gomel, Gomel Oblast, Belarus (Europe - East)
        Job Function: Software Engineering in Test Level 3
        Track Level: A-3
        Key Skill: Automated Testing in .NET (Intermediate proficiency)
"""

# SQLite MCP Server
SQLITE_MCP_SERVER = MCPServerDetails(
    name="SQLITE MCP Server",
    description="SQLITE MCP Server with all tool available",
    enabled=True,
    config=MCPServerConfig(
        command="uvx",
        args=[
            "mcp-server-sqlite",
            "--db-path",
            "/home/codemie/SQLite/$DB_NAME.db",
        ],
        env={"DB_NAME": "testSQLite"},
    ),
    mcp_connect_url="",
    tools=[tool.value for tool in McpServerSqlite],
)

SQLITE_MCP_SERVER_PROMPT = (
    "Delete table USERS, then create table USERS and fill it with 5 records"
)

SQLITE_MCP_SERVER_EXPECTED_RESPONSE = """
     The USERS table was deleted (if it existed), newly created, and filled with 5 records.
     If you want to view the records or perform further actions, let me know!
"""

# Filesystem MCP Server
FILESYSTEM_MCP_SERVER = MCPServerDetails(
    name="Filesystem MCP Server",
    description="Filesystem MCP Server for file operations",
    enabled=True,
    config=MCPServerConfig(
        command="mcp-server-filesystem",
        args=[
            "$WORKING_FOLDER",
        ],
        env={"WORKING_FOLDER": "/home/codemie"},
    ),
    tools=[tool.value for tool in McpServerFilesystem],
)

FILESYSTEM_MCP_SERVER_PROMPT = "List directory /home/codemie"

FILESYSTEM_MCP_SERVER_EXPECTED_RESPONSE = """
    Here are the contents of the /home/codemie directory:
Files:
.bash_logout
.bashrc
.profile

Directories:
.cache
.local
.npm
SQLite
"""

# GitHub MCP Server
GITHUB_MCP_SERVER = MCPServerDetails(
    name="GitHub MCP Server",
    description="GitHub MCP Server for GitHub API operations",
    enabled=True,
    config=MCPServerConfig(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_PERSONAL_ACCESS_TOKEN"},
    ),
    tools=[tool.value for tool in McpServerGithub],
)

# PostgreSQL MCP Server
POSTGRESQL_MCP_SERVER = MCPServerDetails(
    name="PostgreSQL MCP Server",
    description="PostgreSQL MCP Server for database operations",
    enabled=True,
    config=MCPServerConfig(
        command="mcp-server-postgres",
        args=["postgresql://$USERNAME:$PASSWORD@$HOST:$PORT/$DBNAME"],
    ),
    tools=[tool.value for tool in McpServerPostgresql],
)

POSTGRESQL_MCP_SERVER_PROMPT = "Show the DB version"

POSTGRESQL_MCP_SERVER_EXPECTED_RESPONSE = """
    The database version is:
    PostgreSQL 17.5 on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit.
"""

# Playwright MCP Server
PLAYWRIGHT_MCP_SERVER = MCPServerDetails(
    name="Playwright MCP Server",
    description="Playwright MCP Server for browser automation",
    enabled=True,
    config=MCPServerConfig(
        command="npx",
        args=[
            "@playwright/mcp@latest",
            "--isolated",
            "--headless",
            "--no-sandbox",
            "--executable-path",
            "/usr/bin/chromium",
            "--viewport-size",
            "1920x1080",
        ],
    ),
    tools=[tool.value for tool in McpServerPlaywright],
)

# Puppeteer MCP Server
PUPPETEER_MCP_SERVER = MCPServerDetails(
    name="Puppeteer MCP Server",
    description="Puppeteer MCP Server for browser automation",
    enabled=True,
    config=MCPServerConfig(
        command="mcp-server-puppeteer",
        args=[],
        env={
            "DEBIAN_FRONTEND": "noninteractive",
            "DOCKER_CONTAINER": True,
            "PUPPETEER_EXECUTABLE_PATH": "/usr/bin/chromium",
            "PUPPETEER_SKIP_CHROMIUM_DOWNLOAD": True,
        },
    ),
    tools=[tool.value for tool in McpServerPuppeteer],
)

PUPPETEER_AND_PLAYWRIGHT_MCP_SERVER_PROMPT = (
    "Open amazon.com and take a screenshot. Capture the default homepage."
)

PUPPETEER_AND_PLAYWRIGHT_MCP_SERVER_EXPECTED_RESPONSE = """
    Here is a screenshot of the homepage after opening amazon.com:
"""

# Parametrized test data for assistant with MCP servers
mcp_server_assistant_test_data = [
    MCPServerTestCase(
        mcp_server=SQLITE_MCP_SERVER,
        user_message=SQLITE_MCP_SERVER_PROMPT,
        expected_response=SQLITE_MCP_SERVER_EXPECTED_RESPONSE,
        expected_tools=[McpServerSqlite.CREATE_TABLE, McpServerSqlite.WRITE_QUERY],
    ),
    MCPServerTestCase(
        mcp_server=FILESYSTEM_MCP_SERVER,
        user_message=FILESYSTEM_MCP_SERVER_PROMPT,
        expected_response=FILESYSTEM_MCP_SERVER_EXPECTED_RESPONSE,
        expected_tools=[McpServerFilesystem.LIST_DIRECTORY],
    ),
    MCPServerTestCase(
        mcp_server=GITHUB_MCP_SERVER,
        user_message=GITHUB_TOOL_TASK,
        expected_response=RESPONSE_FOR_GITHUB,
        expected_tools=[McpServerGithub.GET_ISSUE],
        integration_fixture="github_mcp_integration",
    ),
    MCPServerTestCase(
        mcp_server=POSTGRESQL_MCP_SERVER,
        user_message=POSTGRESQL_MCP_SERVER_PROMPT,
        expected_response=POSTGRESQL_MCP_SERVER_EXPECTED_RESPONSE,
        expected_tools=[McpServerPostgresql.QUERY],
        integration_fixture="mcp_postgres_integration",
    ),
    MCPServerTestCase(
        mcp_server=PLAYWRIGHT_MCP_SERVER,
        user_message=PUPPETEER_AND_PLAYWRIGHT_MCP_SERVER_PROMPT,
        expected_response=PUPPETEER_AND_PLAYWRIGHT_MCP_SERVER_EXPECTED_RESPONSE,
        expected_tools=[
            McpServerPlaywright.BROWSER_NAVIGATE,
            McpServerPlaywright.BROWSER_SCREENSHOT,
        ],
    ),
    MCPServerTestCase(
        mcp_server=PUPPETEER_MCP_SERVER,
        user_message=PUPPETEER_AND_PLAYWRIGHT_MCP_SERVER_PROMPT,
        expected_response=PUPPETEER_AND_PLAYWRIGHT_MCP_SERVER_EXPECTED_RESPONSE,
        expected_tools=[
            McpServerPuppeteer.PUPPETEER_NAVIGATE,
            McpServerPuppeteer.PUPPETEER_SCREENSHOT,
        ],
    ),
]
