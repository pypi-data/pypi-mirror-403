from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .entities import DomoEntity_w_Lineage


@dataclass
class DomoFederatedEntity(DomoEntity_w_Lineage):
    """Entity that can be federated across multiple Domo instances.

    This class extends lineage-enabled entities to support federation,
    allowing entities to maintain relationships across different Domo
    instances in federated environments.

    Provides federation support via the Federation context property.
    """

    __skip_lineage_registration__ = True  # Abstract intermediate class, not registered

    parent_entity: Any = field(default=None, repr=False)
