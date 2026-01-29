__all__ = [
    "AccessConfigError",
    "AccessRelationship",
    "DomoAccess",
]

from dataclasses import dataclass, field

from ...base.entities import Access, DomoEntity, DomoSubEntity
from ...base.exceptions import ClassError
from ...base.relationships import DomoRelationship, DomoRelationshipController

# from .. import DomoUser as dmdu


class AccessConfigError(ClassError):
    def __init__(self, cls_instance=None, account_id=None, message=None):
        super().__init__(
            cls_instance=cls_instance,
            entity_id=account_id,
            message=message,
        )


@dataclass
class AccessRelationship(DomoRelationship):
    """Describes an entity with access to an object.
    Will describe sharing accounts, datasets and dataflows
    """

    def to_dict(self) -> dict:
        """Convert relationship to dictionary."""
        return {
            "parent_id": self.parent_entity.id if self.parent_entity else None,
            "entity_id": self.entity.id if self.entity else None,
            "relationship_type": (
                self.relationship_type.value if self.relationship_type else None
            ),
            "metadata": self.metadata,
        }

    async def update(self):
        """Update relationship metadata or properties."""
        # Placeholder: implement update logic if needed
        pass


@dataclass
class DomoAccess(DomoRelationshipController, DomoSubEntity):
    """
    Describes concept of content access
    ex. DomoAccount.Access can be SHARED, VIEWED, EDIT access with DomoUsers and DomoGroups
    """

    share_enum: Access = field(
        repr=False, default=None
    )  # describes the types of access (view, read, owner) a related entity can have

    def __post_init__(self):
        # super().__post_init__()

        if self.share_enum and not issubclass(self.share_enum, Access):
            print(self.share_enum)
            raise AccessConfigError(
                cls_instance=self,
                account_id=self.parent_id,
                message="Share enum must be a subclass of ShareAccount.",
            )

    async def get(self) -> list[DomoRelationship]:
        """Get all access relationships for this object."""
        raise NotImplementedError("DomoAccess.get not implemented")

    async def grant_access(
        self,
        entity: DomoEntity,
        relationship_type: Access,
        **kwargs,
    ) -> bool:
        """Grant access to an entity."""
        raise NotImplementedError("DomoAccess.grant_access not implemented")

    async def revoke_access(
        self,
        entity: DomoEntity,
        relationship_type: Access,
        **kwargs,
    ) -> bool:
        """Revoke access from an entity."""
        raise NotImplementedError("DomoAccess.revoke_access not implemented")
