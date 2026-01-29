"""
User Management Tools for Domo MCP Server

Provides tools for managing users in Domo including listing, searching,
creating, updating, and deleting users.
"""

import json

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from pydantic import BaseModel, Field

from domo_mcp.auth_context import DomoContext
from domo_mcp.server import mcp
from domolibrary2.routes import (
    role as role_routes,
    user as user_routes,
)


class DomoUser(BaseModel):
    """Structured output for Domo user data."""

    id: str = Field(description="User ID")
    display_name: str = Field(description="User display name")
    email: str = Field(description="User email address")
    role_name: str | None = Field(default=None, description="User role name")
    role_id: int | None = Field(default=None, description="User role ID")
    department: str | None = Field(default=None, description="User department")
    title: str | None = Field(default=None, description="User job title")


class UserList(BaseModel):
    """Structured output for list of users."""

    users: list[DomoUser] = Field(description="List of Domo users")
    total_count: int = Field(description="Total number of users returned")


def _parse_user(user_data: dict) -> DomoUser:
    """Parse user data from API response to DomoUser model."""
    role = user_data.get("role") or user_data.get("roleId") or {}
    return DomoUser(
        id=str(user_data.get("id", "")),
        display_name=user_data.get("displayName", ""),
        email=user_data.get("emailAddress", user_data.get("email", "")),
        role_name=role.get("name") if isinstance(role, dict) else None,
        role_id=role.get("id") if isinstance(role, dict) else role,
        department=user_data.get("department"),
        title=user_data.get("title"),
    )


@mcp.tool()
async def get_users(
    ctx: Context[ServerSession, DomoContext],
    limit: int = Field(default=500, description="Maximum number of users to return"),
) -> UserList:
    """List all users in the Domo instance.

    Returns a list of all users with their basic information including
    ID, display name, email, role, department, and title.
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Fetching users from {auth.domo_instance}")

    try:
        res = await user_routes.get_all_users(auth=auth)
        users_data = res.response or []

        # Apply limit
        users_data = users_data[:limit]

        users = [_parse_user(u) for u in users_data]

        await ctx.info(f"Found {len(users)} users")
        return UserList(users=users, total_count=len(users))

    except user_routes.User_GET_Error as e:
        await ctx.error(f"Failed to get users: {e}")
        raise


@mcp.tool()
async def get_user_by_id(
    user_id: str,
    ctx: Context[ServerSession, DomoContext],
) -> DomoUser:
    """Get a specific Domo user by their ID.

    Args:
        user_id: The unique identifier of the user to retrieve
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Fetching user {user_id}")

    try:
        res = await user_routes.get_by_id(auth=auth, user_id=user_id)
        user_data = res.response

        return _parse_user(user_data)

    except user_routes.User_GET_Error as e:
        await ctx.error(f"Failed to get user {user_id}: {e}")
        raise


@mcp.tool()
async def search_users_by_email(
    email: str,
    ctx: Context[ServerSession, DomoContext],
) -> UserList:
    """Search for Domo users by email address.

    Args:
        email: Email address or partial email to search for
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Searching users with email: {email}")

    try:
        res = await user_routes.search_users_by_email(auth=auth, user_email_ls=[email])
        users_data = res.response or []

        users = [_parse_user(u) for u in users_data]

        await ctx.info(f"Found {len(users)} users matching '{email}'")
        return UserList(users=users, total_count=len(users))

    except user_routes.SearchUserNotFoundError:
        await ctx.info(f"No users found matching '{email}'")
        return UserList(users=[], total_count=0)


@mcp.tool()
async def create_user(
    email: str,
    display_name: str,
    role_id: int,
    ctx: Context[ServerSession, DomoContext],
) -> DomoUser:
    """Create a new user in Domo.

    Args:
        email: Email address for the new user
        display_name: Display name for the new user
        role_id: Role ID to assign to the user
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Creating user: {email}")

    try:
        res = await user_routes.create_user(
            auth=auth,
            email_address=email,
            display_name=display_name,
            role_id=role_id,
        )
        user_data = res.response

        await ctx.info(f"Created user: {user_data.get('id')}")
        return _parse_user(user_data)

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to create user: {e}")
        raise


@mcp.tool()
async def delete_user(
    user_id: str,
    ctx: Context[ServerSession, DomoContext],
) -> str:
    """Delete a user from Domo (soft delete - user can be restored).

    This performs a soft delete where the user is marked as deleted but can be
    restored. Use this for standard user removal operations.

    Args:
        user_id: The ID of the user to delete
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Deleting user: {user_id}")

    try:
        await user_routes.delete_user(auth=auth, user_id=user_id)
        await ctx.info(f"Deleted user: {user_id}")
        return f"Successfully deleted user {user_id}"

    except user_routes.DeleteUserError as e:
        await ctx.error(f"Failed to delete user: {e}")
        raise


@mcp.tool()
async def update_user_properties(
    user_id: str,
    ctx: Context[ServerSession, DomoContext],
    display_name: str | None = Field(
        default=None, description="New display name for the user"
    ),
    email: str | None = Field(
        default=None, description="New email address for the user"
    ),
    title: str | None = Field(default=None, description="New job title for the user"),
    department: str | None = Field(
        default=None, description="New department for the user"
    ),
    phone_number: str | None = Field(
        default=None, description="New phone number for the user"
    ),
) -> str:
    """Update user properties in Domo.

    Updates one or more properties for a user. Only provided fields will be updated.

    Args:
        user_id: The ID of the user to update
        display_name: New display name for the user
        email: New email address for the user
        title: New job title for the user
        department: New department for the user
        phone_number: New phone number for the user
    """
    auth = ctx.request_context.lifespan_context.auth

    # Build list of properties to update
    properties = []

    if display_name is not None:
        properties.append(
            user_routes.UserProperty(
                user_routes.UserProperty_Type.display_name, display_name
            )
        )
    if email is not None:
        properties.append(
            user_routes.UserProperty(user_routes.UserProperty_Type.email_address, email)
        )
    if title is not None:
        properties.append(
            user_routes.UserProperty(user_routes.UserProperty_Type.title, title)
        )
    if department is not None:
        properties.append(
            user_routes.UserProperty(
                user_routes.UserProperty_Type.department, department
            )
        )
    if phone_number is not None:
        properties.append(
            user_routes.UserProperty(
                user_routes.UserProperty_Type.phone_number, phone_number
            )
        )

    if not properties:
        return "No properties provided to update"

    await ctx.info(f"Updating {len(properties)} properties for user {user_id}")

    try:
        await user_routes.update_user(
            auth=auth,
            user_id=user_id,
            user_property_ls=properties,
        )

        property_names = [p.property_type.name for p in properties]
        await ctx.info(f"Updated user {user_id}: {', '.join(property_names)}")
        return f"Successfully updated user {user_id}: {', '.join(property_names)}"

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to update user properties: {e}")
        raise


@mcp.tool()
async def change_user_role(
    user_id: str,
    new_role_id: int,
    ctx: Context[ServerSession, DomoContext],
) -> str:
    """Change a user's role.

    Assigns a new role to the specified user.

    Args:
        user_id: The ID of the user to update
        new_role_id: The ID of the new role to assign
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Changing role for user {user_id} to role {new_role_id}")

    try:
        # Update the role using the user properties API
        properties = [
            user_routes.UserProperty(user_routes.UserProperty_Type.role_id, new_role_id)
        ]

        await user_routes.update_user(
            auth=auth,
            user_id=user_id,
            user_property_ls=properties,
        )

        await ctx.info(f"Changed user {user_id} to role {new_role_id}")
        return f"Successfully changed user {user_id} to role {new_role_id}"

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to change user role: {e}")
        raise


@mcp.tool()
async def set_user_landing_page(
    user_id: str,
    page_id: str,
    ctx: Context[ServerSession, DomoContext],
) -> str:
    """Set a user's default landing page.

    Sets the page that will be shown when the user logs into Domo.

    Args:
        user_id: The ID of the user to update
        page_id: The ID of the page to set as landing page
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Setting landing page for user {user_id} to page {page_id}")

    try:
        await user_routes.set_user_landing_page(
            auth=auth,
            user_id=user_id,
            page_id=page_id,
        )

        await ctx.info(f"Set landing page for user {user_id}")
        return f"Successfully set landing page for user {user_id} to page {page_id}"

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to set landing page: {e}")
        raise


@mcp.tool()
async def reset_user_password(
    user_id: str,
    new_password: str,
    ctx: Context[ServerSession, DomoContext],
) -> str:
    """Reset a user's password.

    Sets a new password for the specified user. The password should meet
    Domo's password requirements.

    Args:
        user_id: The ID of the user whose password to reset
        new_password: The new password to set
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Resetting password for user {user_id}")

    try:
        await user_routes.reset_password(
            auth=auth,
            user_id=user_id,
            new_password=new_password,
        )

        await ctx.info(f"Reset password for user {user_id}")
        return f"Successfully reset password for user {user_id}"

    except user_routes.ResetPasswordPasswordUsedError:
        await ctx.warning(f"Password was previously used for user {user_id}")
        return f"Failed: Password has been used previously for user {user_id}"

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to reset password: {e}")
        raise


@mcp.tool()
async def request_password_reset_email(
    email: str,
    ctx: Context[ServerSession, DomoContext],
) -> str:
    """Request a password reset email for a user.

    Sends a password reset email to the specified email address.

    Args:
        email: The email address of the user requesting password reset
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Requesting password reset for {email}")

    try:
        await user_routes.request_password_reset(
            domo_instance=auth.domo_instance,
            email=email,
        )

        await ctx.info(f"Password reset email sent to {email}")
        return f"Password reset email sent to {email}"

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to request password reset: {e}")
        raise


@mcp.tool()
async def set_user_direct_signon(
    user_ids: list[str],
    ctx: Context[ServerSession, DomoContext],
    allow_direct_signon: bool = Field(
        default=True, description="Whether to allow direct sign-on"
    ),
) -> str:
    """Enable or disable direct sign-on for users.

    Controls whether users can sign in directly to Domo or must use SSO.

    Args:
        user_ids: List of user IDs to update
        allow_direct_signon: Whether to allow direct sign-on (default: True)
    """
    auth = ctx.request_context.lifespan_context.auth
    action = "Enabling" if allow_direct_signon else "Disabling"
    await ctx.info(f"{action} direct sign-on for {len(user_ids)} users")

    try:
        await user_routes.user_is_allowed_direct_signon(
            auth=auth,
            user_ids=user_ids,
            is_allow_dso=allow_direct_signon,
        )

        status = "enabled" if allow_direct_signon else "disabled"
        await ctx.info(f"Direct sign-on {status} for {len(user_ids)} users")
        return f"Successfully {status} direct sign-on for {len(user_ids)} users"

    except user_routes.User_CRUD_Error as e:
        await ctx.error(f"Failed to update direct sign-on: {e}")
        raise


@mcp.tool()
async def bulk_change_user_roles(
    user_ids: list[str],
    new_role_id: str,
    ctx: Context[ServerSession, DomoContext],
) -> str:
    """Change roles for multiple users at once.

    Assigns a new role to all specified users. This is more efficient than
    changing roles individually for bulk operations.

    Args:
        user_ids: List of user IDs to update
        new_role_id: The ID of the new role to assign to all users
    """
    auth = ctx.request_context.lifespan_context.auth
    await ctx.info(f"Changing {len(user_ids)} users to role {new_role_id}")

    try:
        await role_routes.role_membership_add_users(
            auth=auth,
            role_id=new_role_id,
            user_ids=user_ids,
        )

        await ctx.info(f"Changed {len(user_ids)} users to role {new_role_id}")
        return f"Successfully changed {len(user_ids)} users to role {new_role_id}"

    except role_routes.Role_CRUD_Error as e:
        await ctx.error(f"Failed to change user roles: {e}")
        raise


# Help Resources for Progressive Disclosure


@mcp.resource("domo://tools/get_user_by_id/help")
async def get_user_by_id_help() -> str:
    """Detailed documentation for get_user_by_id tool."""
    return json.dumps(
        {
            "name": "get_user_by_id",
            "summary": "Retrieve a Domo user by their unique identifier",
            "description": """
                Fetches detailed information about a specific Domo user including
                their display name, email, role, department, and job title.
                Requires that the authenticated user has permission to view user details.
            """,
            "parameters": {
                "user_id": {
                    "type": "string",
                    "required": True,
                    "description": "The unique identifier for the user",
                    "format": "String representation of user ID (numeric)",
                    "validation": "Must be a valid user ID that exists in the instance",
                    "examples": ["27", "12345", "67890"],
                    "how_to_find": "Use get_users() to list all users or search_users_by_email() to find by email",
                }
            },
            "returns": {
                "type": "DomoUser",
                "description": "User object with profile information",
                "fields": {
                    "id": "User's unique identifier",
                    "display_name": "User's full name as shown in Domo",
                    "email": "User's email address (login credential)",
                    "role_name": "Name of user's role",
                    "role_id": "Numeric ID of user's role (see get_roles())",
                    "department": "User's department (optional)",
                    "title": "User's job title (optional)",
                },
                "example": {
                    "id": "27",
                    "display_name": "John Doe",
                    "email": "john.doe@company.com",
                    "role_name": "Admin",
                    "role_id": 1,
                    "department": "Engineering",
                    "title": "Senior Developer",
                },
            },
            "usage_examples": [
                {
                    "scenario": "Get user by known ID",
                    "code": "get_user_by_id(user_id='27')",
                    "result": "Returns DomoUser object with John Doe's information",
                },
                {
                    "scenario": "After searching by email",
                    "code": "users = search_users_by_email(email_search='john.doe')\\nuser = get_user_by_id(user_id=users.users[0].id)",
                    "result": "Find user by email, then get full details",
                },
            ],
            "errors": {
                "User_GET_Error": {
                    "when": "User ID not found or permission denied",
                    "message": "Failed to get user",
                    "resolution": "Verify user ID exists using get_users() and check permissions",
                }
            },
            "permissions_required": ["View users"],
            "related_tools": [
                "get_users - List all users",
                "search_users_by_email - Search users by email",
                "create_user - Create new user",
                "update_user_properties - Update user properties",
                "delete_user - Remove user",
            ],
            "performance_notes": [
                "Single user lookup is fast (~100-200ms)",
                "Results are not cached - repeated calls make fresh API requests",
            ],
        }
    )


@mcp.resource("domo://tools/search_users_by_email/help")
async def search_users_by_email_help() -> str:
    """Detailed documentation for search_users_by_email tool."""
    return json.dumps(
        {
            "name": "search_users_by_email",
            "summary": "Search for users by email address pattern",
            "description": """
                Searches for users whose email addresses match the provided search pattern.
                Supports partial matching and case-insensitive search. Returns all matching
                users with their profile information.
            """,
            "parameters": {
                "email_search": {
                    "type": "string",
                    "required": True,
                    "description": "Email pattern to search for",
                    "format": "Partial email address or full email",
                    "matching": "Case-insensitive partial match",
                    "examples": [
                        "john.doe@company.com - Exact email",
                        "john.doe - Matches any domain",
                        "@company.com - All users at company.com",
                        "john - Matches john*, *john*, john@*",
                    ],
                }
            },
            "returns": {
                "type": "UserList",
                "description": "List of matching users",
                "fields": {
                    "users": "Array of DomoUser objects matching search",
                    "total_count": "Number of users found",
                },
                "example": {
                    "users": [
                        {
                            "id": "27",
                            "display_name": "John Doe",
                            "email": "john.doe@company.com",
                        },
                        {
                            "id": "42",
                            "display_name": "John Smith",
                            "email": "john.smith@company.com",
                        },
                    ],
                    "total_count": 2,
                },
            },
            "usage_examples": [
                {
                    "scenario": "Find user by exact email",
                    "code": "search_users_by_email(email_search='john.doe@company.com')",
                    "result": "Returns single user or empty list",
                },
                {
                    "scenario": "Find all users at domain",
                    "code": "search_users_by_email(email_search='@company.com')",
                    "result": "Returns all users with @company.com emails",
                },
                {
                    "scenario": "Find users by name in email",
                    "code": "search_users_by_email(email_search='john')",
                    "result": "Returns all users with 'john' in their email",
                },
            ],
            "errors": {
                "User_SEARCH_Error": {
                    "when": "Search fails or permission denied",
                    "message": "Failed to search users",
                    "resolution": "Check search pattern and permissions",
                }
            },
            "permissions_required": ["View users"],
            "related_tools": [
                "get_users - List all users",
                "get_user_by_id - Get specific user",
                "create_user - Create new user",
            ],
            "performance_notes": [
                "Search is case-insensitive for better matches",
                "Partial matching allows flexible searching",
                "Returns empty list if no matches (not an error)",
            ],
        }
    )


@mcp.resource("domo://tools/create_user/help")
async def create_user_help() -> str:
    """Detailed documentation for create_user tool."""
    return json.dumps(
        {
            "name": "create_user",
            "summary": "Create a new user in the Domo instance",
            "description": """
                Creates a new Domo user with the specified name, email, and role.
                The user will receive a welcome email with instructions to set their password.
                Requires admin permissions to create users.
            """,
            "parameters": {
                "name": {
                    "type": "string",
                    "required": True,
                    "description": "User's full display name",
                    "format": "First Last or full name",
                    "examples": ["John Doe", "Jane Smith"],
                },
                "email": {
                    "type": "string",
                    "required": True,
                    "description": "User's email address (login credential)",
                    "format": "Valid email address",
                    "validation": "Must be unique in instance, valid email format",
                    "examples": ["john.doe@company.com", "jane.smith@company.com"],
                },
                "role_id": {
                    "type": "integer",
                    "required": True,
                    "description": "Role to assign to user",
                    "format": "Numeric role ID",
                    "how_to_find": "Use get_roles() to list available roles",
                    "examples": [1, 5, 10],
                    "common_values": {
                        "1": "Admin",
                        "3": "Privileged",
                        "4": "Participant",
                    },
                },
                "title": {
                    "type": "string",
                    "required": False,
                    "description": "User's job title",
                    "examples": ["Senior Developer", "Data Analyst"],
                },
                "department": {
                    "type": "string",
                    "required": False,
                    "description": "User's department",
                    "examples": ["Engineering", "Marketing", "Sales"],
                },
            },
            "returns": {
                "type": "DomoUser",
                "description": "Newly created user object",
                "fields": {
                    "id": "Auto-generated user ID",
                    "display_name": "User's display name",
                    "email": "User's email address",
                    "role_id": "Assigned role ID",
                    "role_name": "Assigned role name",
                    "department": "Department (if provided)",
                    "title": "Job title (if provided)",
                },
            },
            "usage_examples": [
                {
                    "scenario": "Create basic user",
                    "code": "create_user(name='John Doe', email='john.doe@company.com', role_id=4)",
                    "result": "Creates user with Participant role",
                },
                {
                    "scenario": "Create user with full details",
                    "code": "create_user(name='Jane Smith', email='jane.smith@company.com', role_id=1, title='Data Analyst', department='Analytics')",
                    "result": "Creates admin user with title and department",
                },
            ],
            "errors": {
                "User_CREATE_Error": {
                    "when": "Email already exists or invalid parameters",
                    "message": "Failed to create user",
                    "resolution": "Check email is unique and role_id is valid",
                }
            },
            "permissions_required": ["Create users", "Admin privileges"],
            "related_tools": [
                "get_roles - List available roles",
                "set_user_landing_page - Set default page after creation",
                "request_password_reset_email - Send welcome email",
                "change_user_role - Modify role after creation",
            ],
            "post_creation_steps": [
                "User receives automated welcome email",
                "User must set password on first login",
                "Consider setting landing page with set_user_landing_page()",
            ],
        }
    )


@mcp.resource("domo://tools/query_dataset/help")
async def query_dataset_help() -> str:
    """Detailed documentation for query_dataset tool."""
    return json.dumps(
        {
            "name": "query_dataset",
            "summary": "Execute SQL queries against Domo datasets",
            "description": """
                Run SQL queries on Domo datasets using the Adrenaline query engine.
                Supports standard SQL syntax with Domo-specific extensions for
                data analysis and reporting. Use 'table' as the table name in queries.
            """,
            "parameters": {
                "dataset_id": {
                    "type": "string",
                    "required": True,
                    "description": "Unique identifier for the dataset to query",
                    "format": "UUID string or dataset ID",
                    "how_to_find": "Use search_datasets() or get_dataset()",
                    "examples": [
                        "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "12345",
                    ],
                },
                "sql_query": {
                    "type": "string",
                    "required": True,
                    "description": "SQL query to execute",
                    "syntax": "Standard SQL with 'table' as table name",
                    "table_name": "Must use 'table' keyword, not actual dataset name",
                    "supported_features": [
                        "SELECT with column lists or *",
                        "WHERE clauses with AND/OR/NOT",
                        "JOIN operations (INNER, LEFT, RIGHT, FULL)",
                        "GROUP BY with aggregation functions",
                        "ORDER BY with ASC/DESC",
                        "LIMIT and OFFSET for pagination",
                    ],
                    "functions": {
                        "aggregation": [
                            "COUNT",
                            "SUM",
                            "AVG",
                            "MIN",
                            "MAX",
                            "DISTINCT",
                        ],
                        "string": [
                            "CONCAT",
                            "UPPER",
                            "LOWER",
                            "SUBSTRING",
                            "TRIM",
                        ],
                        "date": [
                            "DATE",
                            "YEAR",
                            "MONTH",
                            "DAY",
                            "DATE_ADD",
                            "DATE_DIFF",
                        ],
                        "math": ["ROUND", "FLOOR", "CEIL", "ABS", "MOD"],
                    },
                    "examples": [
                        "SELECT * FROM table LIMIT 100",
                        "SELECT category, SUM(revenue) as total FROM table GROUP BY category",
                        "SELECT * FROM table WHERE status = 'active' AND created_date > '2024-01-01'",
                        "SELECT a.name, COUNT(*) FROM table a GROUP BY a.name ORDER BY COUNT(*) DESC",
                    ],
                },
            },
            "returns": {
                "type": "dict",
                "description": "Query results with columns and data rows",
                "structure": {
                    "columns": "List of column names in result set",
                    "rows": "List of row data (each row is an array of values)",
                    "row_count": "Number of rows returned",
                },
                "example": {
                    "columns": ["category", "total"],
                    "rows": [
                        ["Electronics", 150000],
                        ["Clothing", 95000],
                        ["Food", 73000],
                    ],
                    "row_count": 3,
                },
            },
            "constraints": {
                "max_rows": "Default limit of 1000 rows per query",
                "timeout": "Queries timeout after 60 seconds",
                "table_name": "Must use 'table' keyword in FROM clause",
                "columns": "Column names are case-sensitive",
            },
            "performance_tips": [
                "Use LIMIT to restrict result set size",
                "Filter with WHERE before JOIN when possible",
                "Avoid SELECT * for datasets with many columns",
                "Use aggregations to reduce row count",
                "Add indexes via dataset settings for better performance",
            ],
            "common_errors": {
                "Column not found": "Check column names match dataset schema exactly (case-sensitive)",
                "Timeout": "Simplify query, add filters, or use LIMIT clause",
                "Permission denied": "Verify you have access to query the dataset",
                "Invalid table name": "Remember to use 'table' not the actual dataset name",
            },
            "permissions_required": [
                "View dataset",
                "Query dataset (Adrenaline access)",
            ],
            "related_tools": [
                "get_dataset_schema - View available columns before querying",
                "get_dataset - Get dataset metadata",
                "search_datasets - Find datasets to query",
            ],
        }
    )
