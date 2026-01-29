"""Page classes and functionality.

This module provides comprehensive page management functionality for Domo pages,
organized using the subentity composition pattern:

- exceptions: Page-related exception classes
- core: Main DomoPage entity classes (DomoPage_Default, DomoPage factory)
- pages: DomoPages collection and hierarchy operations
- access_controller: Access control subentity (DomoPageAccessController)
- layout: Layout and content management subentity (DomoPageLayout)

Classes:
    DomoPage: Factory class for page operations
    DomoPage_Default: Default page implementation
    DomoPages: Collection class for managing multiple pages
    DomoPageAccessController: Access control subentity
    DomoPageLayout: Layout and content management subentity

Example:
    Basic page usage with subentities:

        >>> from domolibrary2.classes.DomoPage import DomoPage
        >>> page = await DomoPage.get_by_id(page_id="123", auth=auth)
        >>> # Access control via Access subentity
        >>> await page.Access.get()
        >>> owners = page.Access.owners
        >>> # Get cards via Layout subentity
        >>> await page.Layout.get_cards()
        >>> print(f"Found {len(page.Layout.cards)} cards")

    Managing access:

        >>> # Grant viewer access
        >>> await page.Access.grant_access(domo_users=[user1, user2])
        >>> # Check who has access
        >>> await page.Access.get()
        >>> owners = page.Access.owners

    Layout and content:

        >>> # Get cards
        >>> cards = await page.Layout.get_cards()
        >>> # Update layout
        >>> await page.Layout.update(body={...})
"""

__all__ = [
    "DomoPage_GetRecursive",
    "DomoPage",
    "DomoPage_Default",
    "DomoPages",
    "Page_NoAccess",
    "DomoPageAccessController",
    "DomoPageLayout",
]

# Import subentity classes
from .access_controller import DomoPageAccessController

# Import core classes
from .core import DomoPage, DomoPage_Default

# Import exceptions
from .exceptions import DomoPage_GetRecursive, Page_NoAccess
from .layout import DomoPageLayout
from .pages import DomoPages
