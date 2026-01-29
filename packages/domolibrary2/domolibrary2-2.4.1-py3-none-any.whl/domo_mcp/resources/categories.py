"""
Tool Category Resources for Domo MCP Server

Provides category-based tool discovery and organization using MCP resources.
Implements progressive disclosure pattern where LLMs can discover tools by
category rather than scanning entire tool list.
"""

import json

from domo_mcp.server import mcp


@mcp.resource("domo://tools/categories")
async def list_tool_categories() -> str:
    """List all available tool categories with descriptions and tool counts.

    Returns a JSON structure organizing all MCP tools by functional domain.
    This enables LLMs to discover relevant tools without loading full documentation.

    Categories:
        - user_management: User CRUD, roles, permissions (14 tools)
        - dataset_operations: Dataset queries, metadata, sharing (5 tools)
        - group_management: Group CRUD, membership (6 tools)
        - role_management: Role CRUD, grants, membership (6 tools)
        - page_management: Page access, layout, cards (4 tools)
        - dataflow_operations: Dataflow execution, monitoring (4 tools)
        - access_token_management: Token generation, revocation (5 tools)
        - code_analysis: CodeGraph analysis tools (6 tools)
    """
    return json.dumps(
        {
            "categories": {
                "user_management": {
                    "description": "Tools for managing Domo users and their properties",
                    "tools": [
                        "get_users",
                        "get_user_by_id",
                        "search_users_by_email",
                        "create_user",
                        "delete_user",
                        "update_user_properties",
                        "change_user_role",
                        "bulk_change_user_roles",
                        "set_user_landing_page",
                        "reset_user_password",
                        "request_password_reset_email",
                        "set_user_direct_signon",
                    ],
                    "common_workflows": [
                        "Create user → Assign role → Set landing page",
                        "Search by email → Update properties → Change role",
                        "Bulk role changes for multiple users",
                    ],
                },
                "dataset_operations": {
                    "description": "Tools for dataset retrieval, querying, and sharing",
                    "tools": [
                        "get_dataset",
                        "query_dataset",
                        "get_dataset_schema",
                        "share_dataset",
                        "search_datasets",
                    ],
                    "common_workflows": [
                        "Search datasets → Get schema → Query data",
                        "Find dataset → Share with user/group",
                        "Query dataset → Analyze results",
                    ],
                },
                "group_management": {
                    "description": "Tools for managing user groups and membership",
                    "tools": [
                        "get_groups",
                        "get_group_by_id",
                        "search_groups",
                        "get_group_membership",
                        "create_group",
                        "update_group_membership",
                    ],
                    "common_workflows": [
                        "Create group → Add users → Share content",
                        "Search groups → View membership → Modify",
                        "Get group → Add/remove members",
                    ],
                },
                "role_management": {
                    "description": "Tools for managing roles and permissions",
                    "tools": [
                        "get_roles",
                        "get_role_by_id",
                        "get_role_grants",
                        "get_role_membership",
                        "create_role",
                        "set_role_grants",
                    ],
                    "common_workflows": [
                        "Create role → Assign grants → Add users",
                        "Get role → View membership → Modify grants",
                        "List roles → Find role → View grants",
                    ],
                },
                "page_management": {
                    "description": "Tools for managing Domo pages and collections",
                    "tools": [
                        "get_pages",
                        "get_page_by_id",
                        "get_page_access",
                        "add_page_owners",
                    ],
                    "common_workflows": [
                        "Search pages → Get page details → View access",
                        "Get page → Add owners → Share with users",
                        "List pages → Find page → Manage access",
                    ],
                },
                "dataflow_operations": {
                    "description": "Tools for dataflow execution and monitoring",
                    "tools": [
                        "get_dataflows",
                        "get_dataflow_by_id",
                        "get_dataflow_execution_history",
                        "execute_dataflow",
                    ],
                    "common_workflows": [
                        "Get dataflow → Execute → Monitor history",
                        "List dataflows → Find dataflow → Check execution",
                        "Execute dataflow → Wait for completion",
                    ],
                },
                "access_token_management": {
                    "description": "Tools for managing API access tokens",
                    "tools": [
                        "get_access_tokens",
                        "get_expired_access_tokens",
                        "generate_access_token",
                        "revoke_access_token",
                        "revoke_expired_tokens",
                    ],
                    "common_workflows": [
                        "Generate token → Use for API access",
                        "List tokens → Find expired → Revoke",
                        "Bulk revoke expired tokens",
                    ],
                },
                "code_analysis": {
                    "description": "Tools for analyzing workspace code structure",
                    "tools": [
                        "list_workspace_files",
                        "get_file_dependencies",
                        "find_symbol_references",
                        "get_code_structure",
                        "analyze_import_graph",
                        "search_code_patterns",
                    ],
                    "common_workflows": [
                        "List files → Analyze dependencies → Find references",
                        "Search patterns → Get structure → Understand codebase",
                        "Find symbol → View references → Trace usage",
                    ],
                },
            },
            "total_tools": 48,
            "total_categories": 8,
            "usage_tip": "Request help for specific tools using domo://tools/{tool_name}/help resources",
        },
        indent=2,
    )


@mcp.resource("domo://tools/category/user_management")
async def user_management_category() -> str:
    """Detailed information about user management tools.

    Provides comprehensive overview of all user-related operations including
    CRUD operations, role management, authentication, and bulk operations.
    """
    return json.dumps(
        {
            "category": "User Management",
            "description": "Comprehensive user administration and management tools",
            "tool_count": 14,
            "tools": [
                {
                    "name": "get_users",
                    "summary": "List all users in the Domo instance",
                    "input": "limit (optional)",
                    "output": "UserList with user details",
                },
                {
                    "name": "get_user_by_id",
                    "summary": "Get specific user by ID",
                    "input": "user_id",
                    "output": "DomoUser object",
                },
                {
                    "name": "search_users_by_email",
                    "summary": "Search users by email address",
                    "input": "email_search",
                    "output": "List of matching DomoUser objects",
                },
                {
                    "name": "create_user",
                    "summary": "Create a new Domo user",
                    "input": "name, email, role_id",
                    "output": "DomoUser object for created user",
                },
                {
                    "name": "delete_user",
                    "summary": "Delete a user from Domo",
                    "input": "user_id",
                    "output": "Success confirmation",
                },
                {
                    "name": "update_user_properties",
                    "summary": "Update user properties (name, email, title, etc.)",
                    "input": "user_id, properties to update",
                    "output": "Updated DomoUser object",
                },
                {
                    "name": "change_user_role",
                    "summary": "Change a user's role",
                    "input": "user_id, new_role_id",
                    "output": "Updated DomoUser object",
                },
                {
                    "name": "bulk_change_user_roles",
                    "summary": "Change roles for multiple users at once",
                    "input": "user_ids, target_role_id",
                    "output": "Success confirmation with count",
                },
                {
                    "name": "set_user_landing_page",
                    "summary": "Set the default landing page for a user",
                    "input": "user_id, page_id",
                    "output": "Success confirmation",
                },
                {
                    "name": "reset_user_password",
                    "summary": "Reset a user's password",
                    "input": "user_id, new_password",
                    "output": "Success confirmation",
                },
                {
                    "name": "request_password_reset_email",
                    "summary": "Send password reset email to user",
                    "input": "user_id",
                    "output": "Success confirmation",
                },
                {
                    "name": "set_user_direct_signon",
                    "summary": "Enable/disable direct sign-on for user",
                    "input": "user_id, enabled",
                    "output": "Success confirmation",
                },
            ],
            "common_workflows": [
                {
                    "workflow": "Onboard New User",
                    "steps": [
                        "1. create_user(name, email, role_id)",
                        "2. set_user_landing_page(user_id, page_id)",
                        "3. Request password reset email",
                    ],
                },
                {
                    "workflow": "Bulk Role Update",
                    "steps": [
                        "1. search_users_by_email(pattern) to find users",
                        "2. bulk_change_user_roles(user_ids, new_role_id)",
                    ],
                },
                {
                    "workflow": "User Audit",
                    "steps": [
                        "1. get_users() to list all users",
                        "2. Filter/analyze user properties",
                        "3. get_user_by_id() for detailed info",
                    ],
                },
            ],
            "related_categories": ["role_management", "group_management"],
        },
        indent=2,
    )


@mcp.resource("domo://tools/category/dataset_operations")
async def dataset_operations_category() -> str:
    """Detailed information about dataset operation tools."""
    return json.dumps(
        {
            "category": "Dataset Operations",
            "description": "Tools for querying, analyzing, and managing Domo datasets",
            "tool_count": 5,
            "tools": [
                {
                    "name": "get_dataset",
                    "summary": "Get dataset metadata by ID",
                    "input": "dataset_id",
                    "output": "DomoDataset object with metadata",
                },
                {
                    "name": "query_dataset",
                    "summary": "Execute SQL query against dataset",
                    "input": "dataset_id, sql_query",
                    "output": "Query results with columns and rows",
                },
                {
                    "name": "get_dataset_schema",
                    "summary": "Get dataset column schema",
                    "input": "dataset_id",
                    "output": "Schema with column names and types",
                },
                {
                    "name": "share_dataset",
                    "summary": "Share dataset with users or groups",
                    "input": "dataset_id, user_ids, group_ids",
                    "output": "Success confirmation",
                },
                {
                    "name": "search_datasets",
                    "summary": "Search datasets by name",
                    "input": "search_term",
                    "output": "List of matching datasets",
                },
            ],
            "common_workflows": [
                {
                    "workflow": "Data Analysis",
                    "steps": [
                        "1. search_datasets(name) to find dataset",
                        "2. get_dataset_schema(dataset_id) to understand structure",
                        "3. query_dataset(dataset_id, sql) to extract data",
                    ],
                },
                {
                    "workflow": "Dataset Sharing",
                    "steps": [
                        "1. get_dataset(dataset_id) to verify dataset",
                        "2. share_dataset(dataset_id, user_ids) to grant access",
                    ],
                },
            ],
            "related_categories": ["dataflow_operations"],
        },
        indent=2,
    )


@mcp.resource("domo://tools/category/dataflow_operations")
async def dataflow_operations_category() -> str:
    """Detailed information about dataflow operation tools."""
    return json.dumps(
        {
            "category": "Dataflow Operations",
            "description": "Tools for managing and executing Domo dataflows",
            "tool_count": 4,
            "tools": [
                {
                    "name": "get_dataflows",
                    "summary": "List all dataflows",
                    "input": "limit (optional)",
                    "output": "List of dataflows with metadata",
                },
                {
                    "name": "get_dataflow_by_id",
                    "summary": "Get specific dataflow by ID",
                    "input": "dataflow_id",
                    "output": "Dataflow object with details",
                },
                {
                    "name": "get_dataflow_execution_history",
                    "summary": "Get execution history for dataflow",
                    "input": "dataflow_id, limit (optional)",
                    "output": "List of execution records",
                },
                {
                    "name": "execute_dataflow",
                    "summary": "Trigger dataflow execution",
                    "input": "dataflow_id",
                    "output": "Execution confirmation",
                },
            ],
            "common_workflows": [
                {
                    "workflow": "Dataflow Execution and Monitoring",
                    "steps": [
                        "1. get_dataflow_by_id(dataflow_id) to verify dataflow",
                        "2. execute_dataflow(dataflow_id) to start execution",
                        "3. get_dataflow_execution_history(dataflow_id) to monitor status",
                    ],
                },
            ],
            "related_categories": ["dataset_operations"],
        },
        indent=2,
    )
