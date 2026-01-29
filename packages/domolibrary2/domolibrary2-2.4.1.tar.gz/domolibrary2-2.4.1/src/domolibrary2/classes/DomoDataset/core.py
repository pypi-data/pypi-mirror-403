"""a class based approach for interacting with Domo Datasets"""

__all__ = [
    "DomoDataset_Default",
    "DomoDatasetView",
    "DomoDataset",
]


from collections.abc import Callable
from dataclasses import dataclass

import httpx

from ...auth import DomoAuth
from ..subentity.lineage import register_lineage_type
from .dataset_default import DomoDataset_Default
from .view import DomoDatasetView


@register_lineage_type("DomoDataset", lineage_type="DATA_SOURCE")
@register_lineage_type("DomoDatasetView", lineage_type="DATA_SOURCE")
@dataclass
class DomoDataset(DomoDataset_Default):
    @classmethod
    def from_dict(
        cls,
        auth: DomoAuth,
        obj: dict,
        check_is_published: bool = None,
        is_use_default_dataset_class: bool = False,
        new_cls=None,
        is_published: bool = False,
        parent_auth_retrieval_fn: Callable | None = None,
        parent_auth: DomoAuth | None = None,
        **kwargs,
    ) -> "DomoDataset":
        """Factory method that automatically detects the dataset type and returns
        the appropriate class:
        - DomoDatasetView for views (dataset-view)
        - DomoDataset for regular datasets

        For federated datasets, use composition via dataset.Federation helper.
        """

        is_view = cls._is_view(obj)

        new_cls = DomoDataset

        # Check if it's a view (views can also be federated)
        if is_view and not is_use_default_dataset_class:
            new_cls = DomoDatasetView

        # Create instance using parent implementation
        instance = super().from_dict(
            auth=auth,
            obj=obj,
            is_use_default_dataset_class=is_use_default_dataset_class,
            new_cls=new_cls,
            **kwargs,
        )

        # Enable federation support if dataset is federated
        if instance.is_federated:
            instance.enable_federation_support()

        return instance

    @classmethod
    async def get_by_id(
        cls,
        auth: DomoAuth,
        dataset_id: str,
        debug_api: bool = False,
        return_raw: bool = False,
        session: httpx.AsyncClient | None = None,
        debug_num_stacks_to_drop: int = 2,
        is_use_default_dataset_class: bool = False,
        parent_class: str | None = None,
        is_get_account: bool = True,
        is_suppress_no_account_config: bool = True,
        check_if_published: bool = True,
        parent_auth_retrieval_fn: Callable | None = None,
        parent_auth: DomoAuth | None = None,
        max_subscriptions_to_check: int | None = None,
        *,
        context=None,
        **context_kwargs,
    ):
        """Retrieve dataset metadata by ID.

        This method uses the factory pattern in from_dict() to automatically
        return the appropriate dataset class (DomoDatasetView, FederatedDomoDataset, etc.)
        based on the dataset metadata.
        """
        # Delegate to parent class which has the published check logic
        return await super().get_by_id(
            auth=auth,
            dataset_id=dataset_id,
            debug_api=debug_api,
            return_raw=return_raw,
            session=session,
            debug_num_stacks_to_drop=debug_num_stacks_to_drop,
            is_use_default_dataset_class=is_use_default_dataset_class,
            parent_class=parent_class or cls.__name__,
            is_get_account=is_get_account,
            is_suppress_no_account_config=is_suppress_no_account_config,
            check_if_published=check_if_published,
            parent_auth_retrieval_fn=parent_auth_retrieval_fn,
            parent_auth=parent_auth,
            max_subscriptions_to_check=max_subscriptions_to_check,
            context=context,
            **context_kwargs,
        )
