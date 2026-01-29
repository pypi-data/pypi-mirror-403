__all__ = ["DomoPublishAppStudio"]

from dataclasses import dataclass

from ..auth import DomoAuth
from .DomoAppStudio import DomoAppStudio
from .subentity.lineage import register_lineage_type


@register_lineage_type("DomoPublishAppStudio", lineage_type="DATA_APP")
@dataclass
class DomoPublishAppStudio(DomoAppStudio):
    """Published AppStudio app that supports publish/subscribe across instances.

    Use .Federation for all subscription operations:
        - app.Federation.ensure_subscription(retrieve_parent_auth_fn=fn)
        - app.Federation.get_parent_publication(parent_auth=auth)
        - app.Federation.get_publisher_entity(parent_auth=auth)
    """

    @classmethod
    async def get_entity_by_id(cls, auth: DomoAuth, entity_id: str, **kwargs):
        """Factory used by DomoPublication to resolve publisher-side entities."""
        return await cls.get_by_id(auth=auth, appstudio_id=entity_id, **kwargs)
