"""Test data for marketplace validation tests."""

import random

from codemie_test_harness.tests.utils.base_utils import get_random_name

# Valid assistant name
COMPLETE_ASSISTANT_NAME = f"Quality Assurance Testing Bot ID{random.randint(0, 999)}"

# Valid categories list
COMPLETE_CATEGORIES = "quality-assurance"

# Complete system prompt that should pass validation
COMPLETE_SYSTEM_PROMPT = """## Instructions
You are a testing-focused assistant used to validate various workflows, features, and integrations within the platform. Your target users are system administrators, testers, or developers who need to confirm that features behave as intended.

## Steps to Follow
1. Accept and process user requests for test or mock operations.
2. Perform prescribed test actions or simulate responses as required.
3. Confirm and document the results of each test.
4. Clearly communicate the outcome to the user, highlighting whether test criteria were met.

## Constraints
- Do not perform any destructive operations outside a controlled test context.
- Only use information and tools provided for the test.
- Ensure all actions are clearly identified as tests.

## Example Use Cases
- Initiating workflow validation
- Running mock or simulated commands
- Checking the correctness of toolkit connections"""

# Complete description that should pass validation
COMPLETE_DESCRIPTION = (
    "A comprehensive testing assistant designed to help users validate workflows, "
    "features, and integrations within the platform. It can initiate, process, and "
    "confirm test operations to ensure system components are functioning as intended."
)

# Good conversation starters
GOOD_CONVERSATION_STARTERS = [
    "Initiate a test workflow to validate integration.",
    "Run a sample command to check assistant response.",
    "Perform a mock operation to confirm functionality.",
    "Verify if all toolkit connections are working as expected.",
]

# Random data for tests where field should be wrong
WRONG_DATA = get_random_name()

# Test configurations for parametrized validation tests
VALIDATION_TEST_CONFIGS = [
    {
        "id": "wrong_name_good_description_good_prompt",
        "config": {
            "assistant_name": WRONG_DATA,
            "description": COMPLETE_DESCRIPTION,
            "system_prompt": COMPLETE_SYSTEM_PROMPT,
            "conversation_starters": GOOD_CONVERSATION_STARTERS,
            "categories": [COMPLETE_CATEGORIES],
        },
        "expected_issues": ["name"],
        "description": "Wrong assistant name with good description and system prompt",
    },
    {
        "id": "good_name_wrong_description_good_prompt",
        "config": {
            "assistant_name": COMPLETE_ASSISTANT_NAME,
            "description": WRONG_DATA,
            "system_prompt": COMPLETE_SYSTEM_PROMPT,
            "conversation_starters": GOOD_CONVERSATION_STARTERS,
            "categories": [COMPLETE_CATEGORIES],
        },
        "expected_issues": ["description"],
        "description": "Good name with wrong description and good system prompt",
    },
    {
        "id": "good_name_good_description_wrong_prompt",
        "config": {
            "assistant_name": COMPLETE_ASSISTANT_NAME,
            "description": COMPLETE_DESCRIPTION,
            "system_prompt": WRONG_DATA,
            "conversation_starters": GOOD_CONVERSATION_STARTERS,
            "categories": [COMPLETE_CATEGORIES],
        },
        "expected_issues": ["system_prompt"],
        "description": "Good name and description with wrong system prompt",
    },
    {
        "id": "all_fields_wrong",
        "config": {
            "assistant_name": WRONG_DATA,
            "description": WRONG_DATA,
            "system_prompt": WRONG_DATA,
            "conversation_starters": [],
            "categories": [],
        },
        "expected_issues": ["name", "description", "system_prompt"],
        "description": "All fields are wrong",
    },
    # Currently there is a bug EPMCDME-10198, will uncomment when it will be fixed
    # {
    #     "id": "missing_categories",
    #     "config": {
    #         "assistant_name": COMPLETE_ASSISTANT_NAME,
    #         "description": COMPLETE_DESCRIPTION,
    #         "system_prompt": COMPLETE_SYSTEM_PROMPT,
    #         "conversation_starters": GOOD_CONVERSATION_STARTERS,
    #         "categories": [],
    #     },
    #     "expected_issues": ["categories"],
    #     "description": "Valid fields but missing categories",
    # },
]

# Complete valid configuration for successful publish tests
COMPLETE_VALID_CONFIG = {
    "assistant_name": COMPLETE_ASSISTANT_NAME,
    "description": COMPLETE_DESCRIPTION,
    "system_prompt": COMPLETE_SYSTEM_PROMPT,
    "conversation_starters": GOOD_CONVERSATION_STARTERS,
    "categories": [COMPLETE_CATEGORIES],
}
