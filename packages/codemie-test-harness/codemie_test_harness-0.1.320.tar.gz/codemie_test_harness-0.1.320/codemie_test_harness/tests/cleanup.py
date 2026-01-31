import copy
import logging
import time
from typing import Callable, Any

import pytest
from codemie_sdk.models.integration import IntegrationType

from codemie_test_harness.tests import PROJECT, TEST_USER
from codemie_test_harness.tests.utils.constants import test_project_name
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

logger = logging.getLogger(__name__)

DELETION_DELAY = 1 if EnvironmentResolver.is_production() else 0
DELETE_CONVERSATIONS = True
BATCH_SIZE = 200


def _get_common_filters():
    return {
        "project": [PROJECT, test_project_name],
        "created_by": TEST_USER,
    }


def _delete_entities(
    entity_name: str,
    fetch_fn: Callable[[], list[Any]],
    delete_fn: Callable[[Any], None],
    get_entity_name: Callable[[Any], str],
    get_entity_id: Callable[[Any], str],
    post_delete_fn: Callable[[Any], int] | None = None,
) -> tuple[int, int]:
    """
    Generic entity deletion function with batch processing.

    Args:
        entity_name: Display name for the entity type (e.g., "datasource", "workflow")
        fetch_fn: Function to fetch entities (should return a list)
        delete_fn: Function to delete a single entity
        get_entity_name: Function to extract entity name for logging
        get_entity_id: Function to extract entity ID for logging
        post_delete_fn: Optional callback after deleting each entity (returns additional count)

    Returns:
        Tuple of (primary_count, secondary_count) where secondary_count is from post_delete_fn
    """
    logger.info("🔍 Fetching %ss...", entity_name)

    total_count = 0
    secondary_count = 0
    batch_number = 1

    while True:
        entities = fetch_fn()
        batch_count = len(entities)

        if batch_count == 0:
            if total_count == 0:
                logger.info("✓ No %ss found", entity_name)
            else:
                logger.info("✓ No more %ss found", entity_name)
            break

        logger.info(
            "🗑️  Batch %d: Deleting %d %s(s)...", batch_number, batch_count, entity_name
        )

        for entity in entities:
            name = get_entity_name(entity)
            entity_id = get_entity_id(entity)
            logger.info("   - Deleting %s: %s (ID: %s)", entity_name, name, entity_id)

            delete_fn(entity)
            time.sleep(DELETION_DELAY)

            if post_delete_fn:
                secondary_count += post_delete_fn(entity)

        total_count += batch_count
        batch_number += 1

        if batch_count < BATCH_SIZE:
            break

    if total_count > 0:
        logger.info(
            "✓ Successfully deleted %d %s(s) in %d batch(es)",
            total_count,
            entity_name,
            batch_number - 1,
        )

    return total_count, secondary_count


def _delete_integrations(client, integration_type: IntegrationType) -> int:
    type_name = integration_type.value

    def fetch():
        integrations_filter = copy.deepcopy(_get_common_filters())
        if integration_type == IntegrationType.USER:
            integrations_filter.pop("created_by")
        return client.integrations.list(
            setting_type=integration_type,
            filters=integrations_filter,
            per_page=BATCH_SIZE,
        )

    def delete(integration):
        client.integrations.delete(
            setting_id=integration.id, setting_type=integration_type
        )

    count, _ = _delete_entities(
        entity_name=f"{type_name} integration",
        fetch_fn=fetch,
        delete_fn=delete,
        get_entity_name=lambda e: e.alias,
        get_entity_id=lambda e: e.id,
    )
    return count


def _delete_datasources(client) -> int:
    def fetch():
        return client.datasources.list(
            filters=_get_common_filters(),
            per_page=BATCH_SIZE,
        )

    count, _ = _delete_entities(
        entity_name="datasource",
        fetch_fn=fetch,
        delete_fn=lambda ds: client.datasources.delete(datasource_id=ds.id),
        get_entity_name=lambda e: e.name,
        get_entity_id=lambda e: e.id,
    )
    return count


def _delete_assistants(client) -> tuple[int, int]:
    def fetch():
        return client.assistants.list(
            filters=_get_common_filters(),
            per_page=BATCH_SIZE,
        )

    def post_delete(assistant):
        """Delete conversations for the assistant and return count."""
        if not DELETE_CONVERSATIONS:
            return 0

        conversations = client.conversations.list_by_assistant_id(assistant.id)
        if not conversations:
            return 0

        logger.info(
            "     └─ Deleting %d conversation(s) for assistant %s",
            len(conversations),
            assistant.id,
        )
        for conversation in conversations:
            logger.debug("        - Conversation ID: %s", conversation.id)
            client.conversations.delete(conversation.id)
            time.sleep(DELETION_DELAY)

        return len(conversations)

    assistant_count, conversation_count = _delete_entities(
        entity_name="assistant",
        fetch_fn=fetch,
        delete_fn=lambda a: client.assistants.delete(assistant_id=a.id),
        get_entity_name=lambda e: e.name,
        get_entity_id=lambda e: e.id,
        post_delete_fn=post_delete,
    )

    if assistant_count > 0:
        if DELETE_CONVERSATIONS:
            logger.info(
                "✓ Total: %d assistant(s) and %d conversation(s) deleted",
                assistant_count,
                conversation_count,
            )
        else:
            logger.info(
                "✓ Total: %d assistant(s) deleted (conversations cascade-deleted)",
                assistant_count,
            )

    return assistant_count, conversation_count


def _delete_workflows(client) -> int:
    def fetch():
        return client.workflows.list(
            filters=_get_common_filters(),
            per_page=BATCH_SIZE,
        )

    count, _ = _delete_entities(
        entity_name="workflow",
        fetch_fn=fetch,
        delete_fn=lambda w: client.workflows.delete(workflow_id=w.id),
        get_entity_name=lambda e: e.name,
        get_entity_id=lambda e: e.id,
    )
    return count


@pytest.mark.cleanup
@pytest.mark.timeout(1000)
def test_clean_all_entities(client):
    logger.info("=" * 80)
    logger.info("🧹 CLEANUP: Starting entity cleanup process")
    logger.info("=" * 80)
    logger.info("📋 Projects: %s, %s", PROJECT, test_project_name)
    logger.info("👤 User: %s", TEST_USER)

    assistant_count, conversation_count = _delete_assistants(client)

    total_deleted = {
        "project_integrations": _delete_integrations(client, IntegrationType.PROJECT),
        "user_integrations": _delete_integrations(client, IntegrationType.USER),
        "datasources": _delete_datasources(client),
        "assistants": assistant_count,
        "conversations": conversation_count,
        "workflows": _delete_workflows(client),
    }

    logger.info("=" * 80)
    logger.info("📊 CLEANUP SUMMARY")
    logger.info("=" * 80)
    logger.info("  Project Integrations: %d", total_deleted["project_integrations"])
    logger.info("  User Integrations:    %d", total_deleted["user_integrations"])
    logger.info("  Datasources:          %d", total_deleted["datasources"])
    logger.info("  Assistants:           %d", total_deleted["assistants"])
    if DELETE_CONVERSATIONS:
        logger.info("  Conversations:        %d", total_deleted["conversations"])
    else:
        logger.info(
            "  Conversations:        %d (cascade-deleted)",
            total_deleted["conversations"],
        )
    logger.info("  Workflows:            %d", total_deleted["workflows"])
    logger.info("-" * 80)
    total_count = sum(total_deleted.values())
    logger.info("  TOTAL ENTITIES:       %d", total_count)
    logger.info("=" * 80)
    logger.info("✅ Cleanup completed successfully!")
