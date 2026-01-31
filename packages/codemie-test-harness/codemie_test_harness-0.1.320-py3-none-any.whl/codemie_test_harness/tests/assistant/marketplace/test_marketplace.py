import json

import pytest
from hamcrest import (
    assert_that,
    equal_to,
    is_in,
    has_key,
    contains_string,
    has_item,
    greater_than,
    any_of,
)

from codemie_test_harness.tests.test_data.marketplace_test_data import (
    VALIDATION_TEST_CONFIGS,
    COMPLETE_VALID_CONFIG,
)


@pytest.mark.marketplace
@pytest.mark.assistant
@pytest.mark.api
def test_marketplace_publish_with_valid_data(assistant, assistant_utils):
    """Test validating and publishing an assistant with all valid data without ignore_recommendations."""
    # Create assistant with complete valid configuration
    created_assistant = assistant(**COMPLETE_VALID_CONFIG)

    # Validate assistant for marketplace
    validation_response = assistant_utils.validate_assistant_for_marketplace(
        created_assistant.id
    )

    # Assert validation response structure
    assert_that(validation_response, has_key("message"))
    assert_that(
        validation_response.get("message"),
        contains_string(
            f"Assistant {created_assistant.id} is ready to be published to marketplace"
        ),
    )

    # After successful validation, publish to marketplace WITHOUT ignore_recommendations
    publish_response = assistant_utils.publish_assistant_to_marketplace(
        created_assistant.id,
    )

    # Assert publish response
    assert_that(publish_response, has_key("message"))
    assert_that(
        publish_response.get("message"),
        contains_string(
            f"Assistant {created_assistant.id} published to marketplace successfully"
        ),
    )

    # Verify assistant appears in marketplace
    marketplace_assistants = assistant_utils.get_assistants(
        scope="marketplace", per_page=100
    )
    marketplace_assistant_ids = [asst.id for asst in marketplace_assistants]

    assert_that(
        created_assistant.id,
        is_in(marketplace_assistant_ids),
        "Published assistant should appear in marketplace",
    )


@pytest.mark.marketplace
@pytest.mark.assistant
@pytest.mark.api
def test_marketplace_publish_with_invalid_data(assistant, assistant_utils):
    """Test that publishing a basic assistant without validation fails."""
    # Create basic assistant without proper marketplace requirements
    created_assistant = assistant()

    # Attempt to publish without validation should fail
    with pytest.raises(Exception) as exec_info:
        assistant_utils.publish_assistant_to_marketplace(created_assistant.id)

    # Verify response contains quality validation rejection
    response_data = json.loads(exec_info.value.response.content)
    assert_that(exec_info.value.response.status_code, equal_to(422))
    assert_that(
        response_data["error"]["message"],
        equal_to(
            "Assistant quality validation failed. Please improve the assistant before publishing."
        ),
    )


@pytest.mark.marketplace
@pytest.mark.assistant
@pytest.mark.api
def test_marketplace_publish_ignore_recommendations(
    assistant, assistant_utils, default_llm
):
    """Test publishing assistant to marketplace by ignoring validation recommendations."""
    # Create basic assistant without proper marketplace requirements
    created_assistant = assistant()

    # Publish directly with ignore_recommendations=True and categories
    publish_response = assistant_utils.publish_assistant_to_marketplace(
        created_assistant.id,
        categories=["quality-assurance"],
        ignore_recommendations=True,
    )

    # Assert publish response
    assert_that(publish_response, has_key("message"))
    assert_that(
        publish_response.get("message"),
        contains_string(
            f"Assistant {created_assistant.id} published to marketplace successfully"
        ),
    )

    # Verify assistant appears in marketplace
    marketplace_assistants = assistant_utils.get_assistants(
        scope="marketplace",
        per_page=100,
    )
    marketplace_assistant_ids = [asst.id for asst in marketplace_assistants]

    assert_that(
        created_assistant.id,
        is_in(marketplace_assistant_ids),
        "Published assistant should appear in marketplace",
    )


@pytest.mark.marketplace
@pytest.mark.assistant
@pytest.mark.api
def test_marketplace_unpublish(assistant, assistant_utils, default_llm):
    """Test unpublishing an assistant from marketplace."""
    # Create and publish assistant first
    created_assistant = assistant()

    # Publish with ignore_recommendations to bypass validation
    assistant_utils.publish_assistant_to_marketplace(
        created_assistant.id,
        categories=["quality-assurance"],
        ignore_recommendations=True,
    )

    # Verify it's in marketplace
    marketplace_assistants = assistant_utils.get_assistants(
        scope="marketplace", per_page=100
    )
    marketplace_assistant_ids = [asst.id for asst in marketplace_assistants]
    assert_that(
        created_assistant.id,
        is_in(marketplace_assistant_ids),
        "Assistant should be in marketplace before unpublishing",
    )

    # Unpublish from marketplace
    unpublish_response = assistant_utils.unpublish_assistant_from_marketplace(
        created_assistant.id
    )

    # Assert unpublish response
    assert_that(unpublish_response, has_key("message"))
    assert_that(
        unpublish_response.get("message"),
        contains_string(
            f"Assistant {created_assistant.id} unpublished from marketplace successfully"
        ),
    )

    # Verify assistant no longer appears in marketplace
    marketplace_assistants_after = assistant_utils.get_assistants(
        scope="marketplace", per_page=100
    )
    marketplace_assistant_ids_after = [asst.id for asst in marketplace_assistants_after]

    assert_that(
        created_assistant.id not in marketplace_assistant_ids_after,
        "Unpublished assistant should not appear in marketplace",
    )


def _make_test_params():
    """Generate pytest.param objects from VALIDATION_TEST_CONFIGS, applying skip marks if needed."""
    params = []
    for tc in VALIDATION_TEST_CONFIGS:
        marks = []
        if "skip" in tc:
            marks.append(pytest.mark.skip(reason=tc["skip"]))
        params.append(pytest.param(tc, id=tc["id"], marks=marks))
    return params


@pytest.mark.marketplace
@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.parametrize(
    "test_case",
    [pytest.param(tc, id=tc["id"]) for tc in VALIDATION_TEST_CONFIGS],
)
def test_marketplace_validation_fields_recommendation(
    assistant, assistant_utils, test_case
):
    """Test validation recommendations for different field configurations."""
    config = test_case["config"]
    expected_issues = test_case["expected_issues"]

    # Create assistant with specific configuration
    created_assistant = assistant(**config)

    # Attempt to publish without ignore_recommendations should fail with validation errors
    with pytest.raises(Exception) as exec_info:
        assistant_utils.publish_assistant_to_marketplace(created_assistant.id)

    # Extract validation response from error
    response_data = json.loads(exec_info.value.response.content)
    assert_that(exec_info.value.response.status_code, equal_to(422))

    # Check if response has quality_validation in error.details
    assert_that(response_data, has_key("error"))
    error = response_data["error"]
    assert_that(error, has_key("details"))
    details = error["details"]
    assert_that(details, has_key("quality_validation"))

    quality_validation = details["quality_validation"]

    # Validation returned recommendations (rejected)
    assert_that(
        quality_validation["decision"],
        equal_to("reject"),
        f"Expected validation to reject assistant with issues in {expected_issues}",
    )

    # Check that recommendations structure exists
    assert_that(quality_validation, has_key("recommendations"))
    recommendations = quality_validation["recommendations"]
    assert_that(recommendations, has_key("fields"))

    # Get all field recommendations
    field_recommendations = recommendations["fields"]

    # Verify there are recommendations provided
    assert_that(
        len(field_recommendations),
        greater_than(0),
        "Validation should provide field recommendations",
    )

    # Extract field names from recommendations
    recommended_field_names = [field["name"] for field in field_recommendations]

    # Assert that all expected fields are in the recommendations
    for expected_field in expected_issues:
        assert_that(
            recommended_field_names,
            has_item(expected_field),
            f"Expected field '{expected_field}' to be flagged in validation recommendations",
        )

        # Find the specific field recommendation
        field_rec = next(
            (f for f in field_recommendations if f["name"] == expected_field), None
        )

        if field_rec:
            # Assert field recommendation has required keys
            assert_that(field_rec, has_key("action"))
            assert_that(field_rec, has_key("severity"))
            assert_that(field_rec, has_key("reason"))
            assert_that(field_rec, has_key("recommended"))

            # Assert action is valid
            assert_that(
                field_rec["action"],
                any_of(equal_to("change"), equal_to("add"), equal_to("remove")),
                f"Action should be 'change', 'add', or 'remove' for field {expected_field}",
            )

            # Assert severity is valid
            assert_that(
                field_rec["severity"],
                any_of(equal_to("critical"), equal_to("optional"), equal_to("warning")),
                f"Severity should be 'critical', 'optional', or 'warning' for field {expected_field}",
            )

            # Assert reason is not empty
            assert_that(
                len(field_rec["reason"]),
                greater_than(10),
                f"Reason should be descriptive for field {expected_field}",
            )

            # Assert recommended value is not empty for change actions
            if field_rec["action"] == "change":
                assert_that(
                    len(str(field_rec["recommended"])),
                    greater_than(0),
                    f"Recommended value should be provided for field {expected_field}",
                )
