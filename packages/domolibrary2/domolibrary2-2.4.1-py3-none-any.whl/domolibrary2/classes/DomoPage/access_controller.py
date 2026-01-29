"""Page access control using relationship-based system."""

__all__ = ["DomoPageAccessController"]

from dataclasses import dataclass

from ...base.relationships import DomoRelationship
from ...client.context import RouteContext
from ...routes import page as page_routes
from ...routes.page.access import PageAccess
from ...utils import chunk_execution as dmce
from .. import DomoUser as dmu
from ..subentity.relationships_access import AccessRelationship, DomoAccess
from .exceptions import Page_NoAccess


@dataclass
class DomoPageAccessController(DomoAccess):
    """Page-specific access controller using unified relationship system.

    Manages access relationships for pages including owners, viewers, and editors.
    Uses PageAccess enum to represent different access levels.

    Example:
        >>> page = await DomoPage.get_by_id(page_id="123", auth=auth)
        >>> # Get all access relationships
        >>> await page.Access.get()
        >>> # Check owners
        >>> owners = page.Access.owners
        >>> # Grant viewer access
        >>> await page.Access.grant_access(user, PageAccess.CAN_VIEW)
    """

    share_enum: type = PageAccess

    async def test(
        self,
        suppress_no_access_error: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> bool:
        """Test if the authenticated user has access to the page.

        Args:
            suppress_no_access_error: If True, suppresses Page_NoAccess exception
            context: Optional RouteContext for API call configuration
            **context_kwargs: Additional context parameters

        Returns:
            True if user has access, False otherwise

        Raises:
            Page_NoAccess: If user doesn't have access and suppress_no_access_error is False
        """
        context = RouteContext.build_context(context=context, **context_kwargs)

        res = await page_routes.get_page_access_test(
            auth=self.parent.auth,
            page_id=self.parent.id,
            context=context,
        )

        page_access = res.response.get("pageAccess")

        if not page_access:
            if not suppress_no_access_error:
                raise Page_NoAccess(
                    page_id=self.parent.id,
                    page_title=self.parent.title,
                    domo_instance=self.parent.auth.domo_instance,
                    function_name="test",
                    parent_class=self.__class__.__name__,
                )
            return False

        return True

    async def get(
        self,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> list[DomoRelationship]:
        """Get all access relationships for this page.

        Fetches users and groups with access, converts to DomoRelationship objects.

        Args:
            return_raw: Return raw ResponseGetData without processing
            context: Optional RouteContext for API call configuration
            **context_kwargs: Additional context parameters

        Returns:
            list of DomoRelationship objects representing access grants
        """
        context = RouteContext.build_context(context=context, **context_kwargs)

        res = await page_routes.get_page_access_list(
            auth=self.parent.auth,
            is_expand_users=True,
            page_id=self.parent.id,
            context=context,
        )

        if return_raw:
            return res

        from ..DomoGroup import core as dmg

        relationships = []

        # Process users
        user_ls = res.response.get("users", [])
        if user_ls:
            domo_users_manager = dmu.DomoUsers(auth=self.parent.auth)
            domo_users = await domo_users_manager.search_by_id(
                user_ids=[user.get("id") for user in user_ls],
                only_allow_one=False,
                suppress_no_results_error=True,
            )

            for domo_user in domo_users:
                # Determine relationship type based on explicit share status
                user_data = next(
                    (obj for obj in user_ls if int(obj.get("id")) == int(domo_user.id)),
                    None,
                )
                is_explicit_share = (
                    user_data.get("isExplicitShare", False) if user_data else False
                )

                # Create relationship
                rel = AccessRelationship(
                    parent_entity=self.parent,
                    entity=domo_user,
                    relationship_type=PageAccess.CAN_VIEW,  # Default access level
                    metadata={
                        "is_explicit_share": is_explicit_share,
                        "group_membership": (
                            user_data.get("groupMembership", []) if user_data else []
                        ),
                    },
                )
                relationships.append(rel)

        # Process groups
        group_ls = res.response.get("groups", [])
        if group_ls:
            domo_groups = await dmce.gather_with_concurrency(
                n=60,
                *[
                    dmg.DomoGroup.get_by_id(
                        group_id=group.get("id"),
                        auth=self.parent.auth,
                        context=context,
                    )
                    for group in group_ls
                ],
            )

            for domo_group in domo_groups:
                rel = AccessRelationship(
                    parent_entity=self.parent,
                    entity=domo_group,
                    relationship_type=PageAccess.CAN_VIEW,
                    metadata={},
                )
                relationships.append(rel)

        # Get owner information
        owner_res = await page_routes.get_page_access_test(
            auth=self.parent.auth,
            page_id=self.parent.id,
            context=context,
        )

        owner_ls = owner_res.response.get("owners", [])
        for owner in owner_ls:
            owner_type = owner.get("type")
            owner_id = owner.get("id")

            # Update existing relationships to OWNER type or create new ones
            existing_rel = next(
                (
                    r
                    for r in relationships
                    if hasattr(r.entity, "id") and str(r.entity.id) == str(owner_id)
                ),
                None,
            )

            if existing_rel:
                existing_rel.relationship_type = PageAccess.OWNER
                existing_rel.metadata["is_owner"] = True
            else:
                # Owner not in access list, create minimal relationship
                rel = AccessRelationship(
                    parent_entity=self.parent,
                    entity=None,  # Not hydrated yet
                    relationship_type=PageAccess.OWNER,
                    metadata={"type": owner_type, "id": owner_id, "is_owner": True},
                )
                relationships.append(rel)

        self.relationships = relationships
        return relationships

    async def grant_access(
        self,
        domo_users: list = None,
        domo_groups: list = None,
        relationship_type: PageAccess = PageAccess.CAN_VIEW,
        message: str | None = None,
        send_email: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ) -> bool:
        """Grant access to users and/or groups.

        Currently only supports OWNER relationship type via add_page_owner endpoint.
        For VIEWER/EDITOR access, use datacenter sharing routes directly.

        Args:
            domo_users: list of DomoUser objects to grant access
            domo_groups: list of DomoGroup objects to grant access
            relationship_type: Type of access to grant (only OWNER currently supported)
            message: Optional message for notification email
            send_email: Whether to send notification email
            context: Optional RouteContext for API call configuration
            **context_kwargs: Additional context parameters

        Returns:
            True if successful
        """
        context = RouteContext.build_context(context=context, **context_kwargs)

        user_id_ls = [int(user.id) for user in (domo_users or [])]
        group_id_ls = [int(group.id) for group in (domo_groups or [])]

        # Use add_page_owner endpoint (works for both owner and viewer access)
        res = await page_routes.add_page_owner(
            auth=self.parent.auth,
            page_id_ls=[self.parent.id],
            group_id_ls=group_id_ls,
            user_id_ls=user_id_ls,
            note=message,
            send_email=send_email,
            context=context,
        )

        return res.is_success

    async def revoke_access(
        self,
        domo_users: list = None,
        domo_groups: list = None,
        relationship_type: PageAccess | None = None,
    ) -> bool:
        """Revoke access from users and/or groups.

        Note: Revoke functionality requires datacenter sharing routes.
        This is a placeholder for future implementation.

        Args:
            domo_users: list of DomoUser objects to revoke access
            domo_groups: list of DomoGroup objects to revoke access
            relationship_type: Type of access to revoke (not used currently)

        Returns:
            True if successful

        Raises:
            NotImplementedError: Revoke functionality not yet implemented
        """
        raise NotImplementedError(
            "revoke_access requires datacenter sharing routes that are not yet implemented. "
            "Use datacenter routes directly for unsharing operations."
        )

    @property
    def owners(self) -> list[DomoRelationship]:
        """Get owner relationships."""
        return [
            r for r in self.relationships if r.relationship_type == PageAccess.OWNER
        ]

    @property
    def viewers(self) -> list[DomoRelationship]:
        """Get viewer relationships."""
        return [
            r for r in self.relationships if r.relationship_type == PageAccess.CAN_VIEW
        ]

    @property
    def editors(self) -> list[DomoRelationship]:
        """Get editor relationships."""
        return [
            r for r in self.relationships if r.relationship_type == PageAccess.CAN_EDIT
        ]

    @property
    def shared_users(self) -> list[DomoRelationship]:
        """Get explicitly shared user relationships."""
        return [
            r for r in self.relationships if r.metadata.get("is_explicit_share", False)
        ]
