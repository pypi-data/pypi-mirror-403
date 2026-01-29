from __future__ import annotations

from ...utils.logging import (
    DomoEntityExtractor,
    DomoEntityResultProcessor,
    LogDecoratorConfig,
    get_colored_logger,
    log_call,
)

logger = get_colored_logger()

"""
CodeEngine CRUD Route Functions

This module provides CRUD functions for managing Domo CodeEngine packages including
creation, deployment, update operations, and account sharing.

Functions:
    deploy_codeengine_package: Deploy a specific package version
    create_codeengine_package: Create a new codeengine package
    increment_version: Increment package version number
    upsert_codeengine_package_version: Create or update a package version
    upsert_package: Create or update a package
    share_accounts_with_package: Share Domo accounts with a package

Classes:
    CodeEnginePackageBuilder: Helper class for building packages (placeholder)
"""

from ...auth import DomoAuth
from ...client import (
    get_data as gd,
    response as rgd,
)
from ...client.context import RouteContext
from . import core as codeengine_routes
from .exceptions import (
    CodeEngine_CRUD_Error,
    CodeEngine_GET_Error,
    CodeEngine_InvalidPackageError,
)
from .packages import generate_share_account_package

__all__ = [
    "CodeEnginePackageBuilder",
    "deploy_codeengine_package",
    "create_codeengine_package",
    "increment_version",
    "upsert_codeengine_package_version",
    "upsert_package",
    "share_accounts_with_package",
]


class CodeEnginePackageBuilder:
    """Helper class for building CodeEngine packages."""

    def __init__(self):
        pass


@gd.route_function
@log_call(
    level_name="route",
    config=LogDecoratorConfig(
        entity_extractor=DomoEntityExtractor(),
        result_processor=DomoEntityResultProcessor(),
    ),
)
async def deploy_codeengine_package(
    auth: DomoAuth,
    package_id: str,
    version: str,
    *,
    context: RouteContext | None = None,
    return_raw: bool = False,
    **context_kwargs,
) -> rgd.ResponseGetData:
    """
    Deploy a specific codeengine package version.

    Args:
        auth: Authentication object
        package_id: Package identifier
        version: Package version to deploy
        context: Route context (optional)
        return_raw: Return raw response without processing

    Returns:
        ResponseGetData object containing deployment result

    Raises:
        CodeEngine_CRUD_Error: If deployment fails
    """
    context = RouteContext.build_context(context=context, **context_kwargs)

    await logger.info(f"Deploying CodeEngine package {package_id} version {version}")

    url = f"https://{auth.domo_instance}.domo.com/api/codeengine/v2/packages/{package_id}/versions/{version}/release"

    res = await gd.get_data(
        auth=auth,
        url=url,
        method="POST",
        context=context,
    )

    if return_raw:
        return res

    if not res.is_success:
        await logger.error(
            f"Failed to deploy package {package_id} v{version}: {res.status_code}"
        )
        raise CodeEngine_CRUD_Error(
            operation="deploy", entity_id=f"{package_id}/v{version}", res=res
        )

    await logger.info(f"Successfully deployed package {package_id} v{version}")
    return res


@gd.route_function
@log_call(
    level_name="route",
    config=LogDecoratorConfig(
        entity_extractor=DomoEntityExtractor(),
        result_processor=DomoEntityResultProcessor(),
    ),
)
async def create_codeengine_package(
    auth: DomoAuth,
    payload: dict,
    *,
    context: RouteContext | None = None,
    return_raw: bool = False,
    **context_kwargs,
) -> rgd.ResponseGetData:
    """
    Create a new codeengine package.

    Args:
        auth: Authentication object
        payload: Package data dictionary
        context: Route context (optional)
        return_raw: Return raw response without processing

    Returns:
        ResponseGetData object containing created package data

    Raises:
        CodeEngine_CRUD_Error: If package creation fails
    """
    context = RouteContext.build_context(context=context, **context_kwargs)

    package_name = payload.get("name", "Unknown")
    package_version = payload.get("version", "Unknown")
    await logger.info(
        f"Creating CodeEngine package '{package_name}' version {package_version}"
    )

    url = f"https://{auth.domo_instance}.domo.com/api/codeengine/v2/packages"

    res = await gd.get_data(
        auth=auth,
        url=url,
        method="POST",
        body=payload,
        context=context,
    )

    if return_raw:
        return res

    if not res.is_success:
        await logger.error(
            f"Failed to create package '{package_name}': {res.status_code}"
        )
        raise CodeEngine_CRUD_Error(operation="create", res=res)

    package_id = res.response.get("id")
    await logger.info(
        f"Successfully created package '{package_name}' with ID {package_id}"
    )
    return res


def increment_version(version: str) -> str:
    """
    Increment the version number.

    Increments the last part of a dot-separated version string.

    Args:
        version: Version string (e.g., "1.0.0")

    Returns:
        Incremented version string (e.g., "1.0.1")
    """
    parts = version.split(".")
    # Increment the last part
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


@gd.route_function
@log_call(
    level_name="route",
    config=LogDecoratorConfig(
        entity_extractor=DomoEntityExtractor(),
        result_processor=DomoEntityResultProcessor(),
    ),
)
async def upsert_codeengine_package_version(
    auth: DomoAuth,
    payload: dict,
    version: str | None = None,
    auto_increment_version: bool = True,
    *,
    context: RouteContext | None = None,
    return_raw: bool = False,
    **context_kwargs,
) -> rgd.ResponseGetData:
    """
    Create or update a codeengine package version.

    If the package version exists and is released, optionally increment the version.
    If the package code is identical to existing, skip the update.

    Args:
        auth: Authentication object
        payload: Package data dictionary
        version: Package version (optional, defaults to version in payload)
        auto_increment_version: Automatically increment version if deployed
        debug_prn: Enable debug printing
        context: Route context (optional)
        return_raw: Return raw response without processing

    Returns:
        ResponseGetData object containing package data

    Raises:
        CodeEngine_InvalidPackageError: If package is already deployed and auto_increment is False
        CodeEngine_CRUD_Error: If package creation/update fails
    """
    context = RouteContext.build_context(context=context, **context_kwargs)

    package_id = payload.get("id")
    version = version or payload.get("version")

    try:
        existing_pkg = await codeengine_routes.get_codeengine_package_by_id_and_version(
            auth=auth,
            package_id=package_id,
            version=version,
            params={"parts": "code"},
            context=context,
        )
        if await codeengine_routes.test_package_is_released(
            existing_package=existing_pkg.response,
            package_id=package_id,
            version=version,
            auth=auth,
        ):
            if not auto_increment_version:
                raise CodeEngine_InvalidPackageError(
                    message=f"Package {package_id} v{version} already deployed",
                    auth=auth,
                )

            version = increment_version(version)

        if await codeengine_routes.test_package_is_identical(
            existing_package=existing_pkg.response,
            new_package=payload,
            package_id=package_id,
            version=version,
            auth=auth,
        ):
            await logger.debug(
                f"Package {package_id} v{version} is identical; skipping update."
            )
            return existing_pkg

    except CodeEngine_GET_Error:
        pass  # Not found, continue to create

    return await create_codeengine_package(
        auth=auth,
        payload=payload,
        context=context,
        return_raw=return_raw,
    )


@gd.route_function
@log_call(
    level_name="route",
    config=LogDecoratorConfig(
        entity_extractor=DomoEntityExtractor(),
        result_processor=DomoEntityResultProcessor(),
    ),
)
async def upsert_package(
    auth: DomoAuth,
    payload: dict,
    check_different: bool = True,
    create_new_version: bool = False,
    *,
    context: RouteContext | None = None,
    return_raw: bool = False,
    **context_kwargs,
) -> rgd.ResponseGetData:
    """
    Create or update a codeengine package.

    If the package doesn't exist, create it. If it exists, update the version.

    Args:
        auth: Authentication object
        payload: Package data dictionary
        check_different: If True, compare payload with existing package and skip
            update if identical (default: True)
        create_new_version: If True, force creation of a new version even if
            package exists (default: False)
        context: Route context (optional)
        return_raw: Return raw response without processing

    Returns:
        ResponseGetData object containing package data

    Raises:
        CodeEngine_CRUD_Error: If package creation/update fails
    """
    context = RouteContext.build_context(context=context, **context_kwargs)

    package_id = payload.get("id")
    version = payload.get("version")

    if not package_id:
        await logger.info("No Package ID found, creating new package...")

        return await create_codeengine_package(
            auth=auth,
            payload=payload,
            context=context,
            return_raw=return_raw,
        )

    # Try to get existing package
    await logger.debug(f"Checking if package {package_id} exists")
    try:
        existing_pkg = await codeengine_routes.get_codeengine_package_by_id(
            auth=auth,
            package_id=package_id,
            params={"parts": "code"},
            context=context,
        )
        await logger.debug(f"Found existing package {package_id}")
    except CodeEngine_GET_Error:
        # Package doesn't exist, create it
        await logger.info(f"Package {package_id} not found; creating new package")
        return await create_codeengine_package(
            auth=auth,
            payload=payload,
            context=context,
            return_raw=return_raw,
        )

    # If check_different is enabled, compare with existing package
    if check_different and version:
        await logger.debug(f"Comparing package {package_id} v{version} with existing")
        is_identical = await codeengine_routes.test_package_is_identical(
            existing_package=existing_pkg.response,
            new_package=payload,
            package_id=package_id,
            version=version,
            auth=auth,
            context=context,
        )

        if is_identical:
            await logger.info(
                f"Package {package_id} v{version} is identical to existing; skipping update."
            )
            return existing_pkg

        await logger.debug(
            f"Package {package_id} v{version} differs from existing; proceeding with update"
        )

    # If create_new_version is True, increment version before creating
    if create_new_version and version:
        version = increment_version(version)
        payload["version"] = version
        await logger.info(f"Creating new version {version} for package {package_id}")

    return await upsert_codeengine_package_version(
        payload=payload,
        auth=auth,
        auto_increment_version=not create_new_version,  # Don't auto-increment if we already did
        context=context,
        return_raw=return_raw,
    )


@gd.route_function
@log_call(
    level_name="route",
    config=LogDecoratorConfig(
        entity_extractor=DomoEntityExtractor(),
        result_processor=DomoEntityResultProcessor(),
    ),
)
async def share_accounts_with_package(
    auth: DomoAuth,
    package_id: str,
    account_mappings: list[dict[str, str | int]],
    is_set: bool = True,
    version_id: str | None = None,
    *,
    context: RouteContext | None = None,
    return_raw: bool = False,
    dry_run: bool = False,
    **context_kwargs,
) -> rgd.ResponseGetData:
    """
    Share Domo accounts with a CodeEngine package.

    Updates the package manifest to include account mappings, allowing the package
    to access specific Domo accounts by alias.

    Args:
        auth: Authentication object
        package_id: Package identifier
        account_mappings: List of account mapping dicts with 'accountId' and 'alias' keys
            Example: [{"accountId": 92, "alias": "sdk_config"}]
        is_set: If True, replace all existing account mappings with new ones.
            If False, add new mappings to existing ones (default: True)
        context: Route context (optional)
        return_raw: Return raw response without processing

    Returns:
        ResponseGetData object containing updated package data

    Raises:
        CodeEngine_CRUD_Error: If account sharing fails

    Example:
        >>> # Replace all account mappings
        >>> accounts = [
        ...     {"accountId": 92, "alias": "sdk_config"},
        ...     {"accountId": 189, "alias": "sdk_d2c"}
        ... ]
        >>> res = await share_accounts_with_package(
        ...     auth=auth,
        ...     package_id="b368d630-7ca5-4b8a-b4ec-f130cf312dc1",
        ...     account_mappings=accounts,
        ...     is_set=True
        ... )
        >>>
        >>> # Add to existing account mappings
        >>> new_accounts = [{"accountId": 366, "alias": "sdk_audit"}]
        >>> res = await share_accounts_with_package(
        ...     auth=auth,
        ...     package_id="b368d630-7ca5-4b8a-b4ec-f130cf312dc1",
        ...     account_mappings=new_accounts,
        ...     is_set=False
        ... )
    """
    context = RouteContext.build_context(context=context, **context_kwargs)

    await logger.info(
        f"Sharing {len(account_mappings)} account mappings with package {package_id}"
    )

    # First, get the current package version
    if not version_id:
        await logger.debug(f"Retrieving current version for package {package_id}")
        res_version = await codeengine_routes.get_current_package_version(
            auth=auth, package_id=package_id, context=context
        )
        version_id = res_version.response

    if not version_id:
        await logger.error(
            f"Could not determine current version for package {package_id}"
        )
        raise CodeEngine_CRUD_Error(
            operation="share_accounts",
            entity_id=package_id,
            message="Could not determine package version",
        )

    # Get the full version data including code
    res_p = await codeengine_routes.get_codeengine_package_by_id(
        auth=auth,
        package_id=package_id,
        # params={"parts": "code,environment,id,language,manifest,name,version"},
        context=context,
    )

    res_v = await codeengine_routes.get_codeengine_package_by_id_and_version(
        auth=auth,
        package_id=package_id,
        version=version_id,
        # params={"parts": "code,environment,id,language,manifest,name,version"},
        context=context,
    )

    if not is_set:
        # Replace all existing mappings with new ones
        await logger.debug("Merging new account mappings with existing mappings")
        existing_mappings = res_v.response["configuration"].get("accountsMapping", [])
        await logger.debug(
            f"Found {len(existing_mappings)} existing account mappings for version {version_id}"
        )

        # Build dict keyed by accountId for fast lookup
        existing_dict = {
            mapping.get("accountId"): mapping for mapping in existing_mappings
        }

        # Update with new mappings (overwrites if accountId exists, updates alias)
        for new_mapping in account_mappings:
            account_id = new_mapping.get("accountId")
            if account_id:
                existing_dict[account_id] = new_mapping

        # Convert back to list
        account_mappings = list(existing_dict.values())
        await logger.debug(f"Final account mappings count: {len(account_mappings)}")

    body = generate_share_account_package(
        package_id=res_p.response["id"],
        code=res_v.response["code"],
        version=res_v.response["version"],
        name=res_p.response["name"],
        environment=res_p.response["environment"],
        language=res_p.response["language"],
        functions=res_v.response["functions"],
        account_mappings=account_mappings,
    )

    url = f"https://{auth.domo_instance}.domo.com/api/codeengine/v2/packages"

    await logger.debug(
        f"Submitting account mappings for package {package_id} version {version_id}"
    )
    res = await gd.get_data(
        auth=auth,
        url=url,
        method="POST",
        body=body,
        context=context,
    )

    if return_raw:
        return res

    if not res.is_success:
        await logger.error(
            f"Failed to share accounts with package {package_id}: {res.status_code}"
        )
        raise CodeEngine_CRUD_Error(
            operation="share_accounts",
            entity_id=package_id,
            res=res,
        )

    await logger.info(
        f"Successfully shared {len(account_mappings)} account mappings with package {package_id}"
    )
    return res
