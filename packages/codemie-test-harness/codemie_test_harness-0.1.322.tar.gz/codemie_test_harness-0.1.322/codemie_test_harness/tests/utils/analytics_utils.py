"""Utility class for analytics operations."""

from codemie_sdk.models.analytics import (
    AnalyticsQueryParams,
    PaginatedAnalyticsQueryParams,
    SummariesResponse,
    TabularResponse,
    UsersListResponse,
)

from .base_utils import BaseUtils


class AnalyticsUtils(BaseUtils):
    """Utility class for analytics operations."""

    def get_summaries(self, **kwargs) -> SummariesResponse:
        """Get overall platform summary metrics.

        Args:
            **kwargs: Query parameters (time_period, start_date, end_date, users, projects)

        Returns:
            SummariesResponse with metrics array
        """
        params = AnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_summaries(params)

    def get_cli_summary(self, **kwargs) -> SummariesResponse:
        """Get CLI-specific summary metrics.

        Args:
            **kwargs: Query parameters (time_period, start_date, end_date, users, projects)

        Returns:
            SummariesResponse with CLI metrics
        """
        params = AnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_cli_summary(params)

    def get_assistants_chats(self, **kwargs) -> TabularResponse:
        """Get assistants chats analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with assistant performance metrics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_assistants_chats(params)

    def get_workflows(self, **kwargs) -> TabularResponse:
        """Get workflows analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with workflow execution metrics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_workflows(params)

    def get_tools_usage(self, **kwargs) -> TabularResponse:
        """Get tool usage analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with tool usage metrics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_tools_usage(params)

    def get_webhooks_invocation(self, **kwargs) -> TabularResponse:
        """Get webhooks invocation statistics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with webhook usage patterns
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_webhooks_invocation(params)

    def get_mcp_servers(self, **kwargs) -> TabularResponse:
        """Get top MCP servers analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with MCP server usage distribution
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_mcp_servers(params)

    def get_mcp_servers_by_users(self, **kwargs) -> TabularResponse:
        """Get MCP servers usage by users.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with individual user MCP adoption
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_mcp_servers_by_users(params)

    def get_projects_spending(self, **kwargs) -> TabularResponse:
        """Get money spent by projects.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with project-level spending
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_projects_spending(params)

    def get_llms_usage(self, **kwargs) -> TabularResponse:
        """Get top LLMs usage analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with LLM model usage distribution
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_llms_usage(params)

    def get_users_spending(self, **kwargs) -> TabularResponse:
        """Get money spent by users.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with individual user spending
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_users_spending(params)

    def get_budget_soft_limit(self, **kwargs) -> TabularResponse:
        """Get soft budget limit violations.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with users exceeding soft limits
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_budget_soft_limit(params)

    def get_budget_hard_limit(self, **kwargs) -> TabularResponse:
        """Get hard budget limit violations.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with users exceeding hard limits
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_budget_hard_limit(params)

    def get_users_activity(self, **kwargs) -> TabularResponse:
        """Get most active users analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with comprehensive user activity metrics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_users_activity(params)

    def get_projects_activity(self, **kwargs) -> TabularResponse:
        """Get most active projects analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with project activity metrics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_projects_activity(params)

    def get_agents_usage(self, **kwargs) -> TabularResponse:
        """Get top agents usage analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with agent usage analytics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_agents_usage(params)

    def get_cli_agents(self, **kwargs) -> TabularResponse:
        """Get top CLI agents analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with CLI agent usage distribution
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_cli_agents(params)

    def get_cli_llms(self, **kwargs) -> TabularResponse:
        """Get top CLI LLMs analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with CLI LLM usage distribution
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_cli_llms(params)

    def get_cli_users(self, **kwargs) -> TabularResponse:
        """Get most active CLI users analytics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with CLI user activity
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_cli_users(params)

    def get_cli_errors(self, **kwargs) -> TabularResponse:
        """Get top error codes for CLI.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with most common CLI error codes
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_cli_errors(params)

    def get_cli_repositories(self, **kwargs) -> TabularResponse:
        """Get repository statistics.

        Args:
            **kwargs: Query parameters including pagination

        Returns:
            TabularResponse with repository-level metrics
        """
        params = PaginatedAnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_cli_repositories(params)

    def get_users(self, **kwargs) -> UsersListResponse:
        """Get users list.

        Args:
            **kwargs: Query parameters (time_period, start_date, end_date, users, projects)

        Returns:
            UsersListResponse with list of unique users
        """
        params = AnalyticsQueryParams(**kwargs) if kwargs else None
        return self.client.analytics.get_users(params)
