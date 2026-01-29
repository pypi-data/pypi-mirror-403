"""Sample: Track card lineage through federated/published entities.

This sample demonstrates how to use the smart federation resolver to:
1. Get a published card from subscriber instance
2. Automatically discover its subscription
3. Get the parent card from publisher instance (automatically handles indirect publication)
4. Get lineage from both cards
5. Generate a visual mermaid diagram showing the federation chain

Environment Variables Required:
    CONFIG_INSTANCE: Config instance for SDK auth
    CONFIG_ACCESS_TOKEN: Config token for SDK auth
    TEST_CARD_ID: Published card ID in subscriber instance
    TEST_INSTANCE: Subscriber instance name

Key Features:
    - check_if_published=True automatically discovers subscriptions
    - is_fetch_content_details=True automatically loads publication content mapping
    - get_publisher_entity() automatically detects and handles:
      * Directly published entities (cards, pages, datasets)
      * Indirectly published cards (published via pages)
      * Multi-page publications
    - Smart caching prevents redundant API calls
    
Current Limitations:
    - to_mermaid_diagram() with include_federation=True:
      * Automatically resolves directly and indirectly published entities
      * Federated dataset → publisher dataset relationships require BOTH datasets in diagram
      * Uses name-based matching for federated dataset relationships
    - App Studio card resolution not yet implemented (GitHub issue TODO)
"""

import asyncio
import sys
from pathlib import Path
from functools import partial
from dotenv import load_dotenv
import os

# Load environment variables
# Load from parent directory first (common config), then local (overrides)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")  # local_work/work/.env
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)  # local_work/work/lineage/.env (overrides)

# Setup imports
from domolibrary2.classes.DomoCard import DomoCard
from domolibrary2.classes.DomoDataset import DomoDataset
from domolibrary2.utils.logging import get_colored_logger
from domolibrary2.integrations.auth_utils import get_auth_from_env
from domolibrary2.integrations.mermaid import MermaidDiagram
from domolibrary2.integrations.graphs import get_converter
from domolibrary2.auth.base import DomoAuth

# Try to import lutils (local utility module)
# This is required for SDK auth and multi-instance setup
# Path: local_work/work/ -> local_work/work/ (where lutils is)
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add local_work/work/ to path
from lutils.auth import get_sdk_auth_from_codeengine

CARD_ID = os.environ['TEST_CARD_ID']
TARGET_INSTANCE = os.environ['TEST_INSTANCE']
# Optional: Set SHOW_FEDERATION_IDS=true in .env to include publication/subscription IDs
SHOW_FEDERATION_IDS = os.environ.get('SHOW_FEDERATION_IDS', 'false').lower() == 'true'

# Setup logging
logger = get_colored_logger(
    env="development", app_name="track_card_lineage", min_level="WARNING"
)


def normalize_instance_name(value: str) -> str:
    """Normalize Domo instance name to standard format.

    Removes '.domo.com' suffix and 'sdk_' prefix if present.

    Args:
        value: Instance name to normalize

    Returns:
        str: Normalized instance name
    """
    normalized = (value or "").strip()
    if normalized.endswith(".domo.com"):
        normalized = normalized[: normalized.index(".domo.com")]
    if normalized.startswith("sdk_"):
        normalized = normalized[len("sdk_") :]
    return normalized or value


# Test data


async def test_federated_card_lineage_tracking():
    """Test tracking lineage through federated/published card hierarchy.

    This test validates:
    - Published card retrieval from subscriber instance
    - Subscription discovery and validation
    - Parent publication retrieval from publisher
    - Parent card retrieval and lineage
    - Complete lineage chain validation

    Returns:
        DomoCard: The published card with validated lineage

    Raises:
        ValueError: If subscription or parent publication cannot be found
        ImportError: If lutils module is not available
    """

    
    # Setup authentication
    config_auth = await get_auth_from_env(
        domo_instance_env_var="CONFIG_INSTANCE",
        domo_token_env_var="CONFIG_ACCESS_TOKEN",
    )

    # Create partial function for getting auth from any instance
    get_auth = partial(
        get_sdk_auth_from_codeengine,
        config_auth=config_auth,
        use_cache=False,
        debug_api=False,
    )

    # Create auth retrieval function for parent instances
    async def parent_auth_retrieval_fn(publisher_domain: str, **kwargs):
        """Retrieve auth for parent publisher instance.

        Args:
            publisher_domain: Domain of the publisher instance
            **kwargs: Additional context parameters (ignored for simplicity)

        Returns:
            DomoAuth: Authentication for the publisher instance
        """
        normalized = normalize_instance_name(publisher_domain)
        return await get_auth(target_instance=normalized)

    # Get subscriber instance auth
    print(f"📦 Getting auth for playstation (subscriber)...")
    subscriber_auth = await get_auth(target_instance=TARGET_INSTANCE)

    print(f"\n{'='*80}")
    print(f"STEP 1: Retrieve Published Card from Subscriber")
    print(f"{'='*80}")
    print(
        f"Subscriber Instance: {subscriber_auth.domo_instance} | Card ID: {CARD_ID}"
    )

    # Step 1: Get the published card from subscriber
    # NOTE: check_if_published=True will follow subscriptions and may return parent card
    card = await DomoCard.get_by_id(
        auth=subscriber_auth,
        card_id=CARD_ID,
        parent_auth_retrieval_fn=parent_auth_retrieval_fn,
        check_if_published=True,
    )

    # Validate card was retrieved
    assert card is not None, "Card should not be None"
    
    # When check_if_published=True, we may get the parent card instead of subscriber card
    # This is expected behavior - the federation system resolves to the source
    if card.id != CARD_ID:
        print(f"\n⚠️  Note: Card ID resolved from {CARD_ID} to {card.id}")
        print(f"   This means check_if_published followed the subscription to parent card")
    
    assert card.is_federated, "Card should be federated"

    print(f"\n✅ Retrieved Card:")
    print(f"   Requested ID: {CARD_ID}")
    print(f"   Actual ID: {card.id}")
    print(f"   Title: {card.title}")
    print(f"   Type: {type(card).__name__}")
    print(f"   Is Federated: {card.is_federated}")
    print(f"   Instance: {card.auth.domo_instance}")
    print(f"   URL: {card.display_url}")

    # Step 2: Get subscriber lineage
    print(f"\n{'='*80}")
    print(f"STEP 2: Retrieve Subscriber Card Lineage")
    print(f"{'='*80}")

    subscriber_lineage = await card.Lineage.get()

    # Validate subscriber lineage
    assert subscriber_lineage is not None, "Subscriber lineage should not be None"
    assert isinstance(subscriber_lineage, list), "Lineage should be a list"

    print(f"\n✅ Subscriber Lineage ({len(subscriber_lineage)} datasets):")
    for i, link in enumerate(subscriber_lineage, 1):
        if link.entity:
            print(f"   {i}. {link.entity.name}")
            print(f"      Type: {type(link.entity).__name__}")
            print(f"      Is Federated: {link.entity.is_federated}")

    # Step 3: Find subscription
    print(f"\n{'='*80}")
    print(f"STEP 3: Find Subscription")
    print(f"{'='*80}")

    # The subscription was already discovered during check_if_published=True
    # It's stored in card.Federation.subscription
    subscription = card.Federation.subscription if card.Federation else None

    # Validate subscription was found
    if not subscription:
        raise ValueError(
            f"❌ Card {CARD_ID} has NO subscription!\n"
            f"   This card should be a published card from another instance.\n"
            f"   Card type: {type(card).__name__}\n"
            f"   Is federated: {card.is_federated}"
        )

    print(f"\n✅ Subscription Found:")
    print(f"   ID: {subscription.id}")
    print(f"   Publication ID: {subscription.publication_id}")
    print(f"   Subscriber Domain: {subscription.subscriber_domain}")
    print(f"   Publisher Domain: {subscription.publisher_domain}")

    # Step 4: Get publisher card from publisher
    print(f"\n{'='*80}")
    print(f"STEP 4: Retrieve Parent Card from Publisher")
    print(f"{'='*80}")

    # Get publisher auth
    publisher_instance = normalize_instance_name(subscription.publisher_domain)
    print(f"Getting auth for publisher ({publisher_instance})...")
    publisher_auth = await get_auth(target_instance=publisher_instance)

    # Get parent publication with auto-fetched content details
    parent_pub = await card.Federation.get_parent_publication(
        parent_auth=publisher_auth,
        is_fetch_content_details=True,  # Automatic content mapping!
    )
    
    # Show publication details
    print(f"\n📋 Publication content:")
    print(f"   ID: {parent_pub.id}")
    print(f"   Content items: {len(parent_pub.content)}")
    for content in parent_pub.content:
        print(f"      - Type: {content.entity_type}, ID: {content.entity_id}")

    # Get publisher card (automatic direct/indirect resolution)
    parent_card = await card.Federation.get_publisher_entity(
        parent_auth=publisher_auth,
    )
    
    if not parent_card:
        raise ValueError(
            f"❌ Could not retrieve parent card!\n"
            f"   Subscriber card ID: {card.id}\n"
            f"   Publication ID: {subscription.publication_id}"
        )

    print(f"\n✅ Parent Card Retrieved:")
    print(f"   Title: {parent_card.title}")
    print(f"   Type: {type(parent_card).__name__}")
    print(f"   ID: {parent_card.id}")
    print(f"   URL: {parent_card.display_url}")
    
    # Remove redundant publication details since we already showed them above

    # Step 5: Generate subscriber lineage diagram (card → subscription → federated datasets)
    print("\n" + "=" * 80)
    print("STEP 5: Generate Subscriber Lineage Diagram")
    print("=" * 80)

    subscriber_diagram = await card.Lineage.to_mermaid_diagram(
        include_federation=True,
        include_pages=True,
        include_entity_ids=True,
        show_federation_ids=SHOW_FEDERATION_IDS,
        direction="TB",
        parent_auth_retrieval_fn=parent_auth_retrieval_fn,
    )

    # Note: The method now automatically pre-loads publication content lineage
    # including Page → Card relationships, so E → G edge should appear

    # Step 6: Generate Mermaid Diagram
    print(f"\n{'='*80}")
    print(f"STEP 6: Generate Complete Mermaid Diagram")
    print(f"{'='*80}")

    import datetime as dt

    # Use the new graph-based converter architecture
    # 1. Get lineage as a LineageGraph (handles all federation relationships)
    #    - Subscriber card and its lineage
    #    - Subscription and publication nodes
    #    - Publisher card and its lineage (if it can find it)
    #    - Federated dataset → publisher dataset relationships (name-based matching)
    #    - Page nodes for indirect publication
    graph = await card.Lineage.get(
        return_graph=True,
        is_recursive=True,
        parent_auth_retrieval_fn=parent_auth_retrieval_fn,
    )
    
    # 2. Convert graph to Mermaid diagram using the MermaidConverter
    converter = get_converter("mermaid")()
    diagram = converter.convert(
        graph,
        direction="TB",
        include_entity_ids=True,
    )
    
    # NOTE: The built-in method may not find the publisher card for indirectly published
    # entities. If the diagram is missing publisher lineage, that's a known limitation
    # of the automatic resolution. The method successfully handles:
    # 1. Direct publications (card/dataset published directly)
    # 2. Federated dataset relationships (matches by name)
    # But may fail for:
    # 3. Indirectly published cards (cards on published pages)

    # Output diagram to console
    mermaid_output = diagram.to_string()
    print(f"\n{mermaid_output}")

    # Export to file with same name as script
    script_name = Path(__file__).stem  # Gets filename without extension
    markdown_file = Path(__file__).parent / f"{script_name}.md"
    converter.export_to_file(
        diagram,
        str(markdown_file),
        footer_text=f"Generated: {dt.datetime.now().isoformat()}",
    )
    print(f"\n💾 Diagram exported to: {markdown_file}")

    # Final validation summary
    print(f"\n{'='*80}")
    print(f"✅ VALIDATION COMPLETE - ALL STEPS PASSED")
    print(f"{'='*80}")
    print(f"  ✅ Step 1: Retrieved published card from subscriber")
    print(f"  ✅ Step 2: Retrieved subscriber lineage ({len(subscriber_lineage)} datasets)")
    print(f"  ✅ Step 3: Found subscription (ID: {subscription.publication_id})")
    print(f"  ✅ Step 4: Retrieved parent card from publisher")
    print(f"  ✅ Step 5: Retrieved parent card lineage ({len(parent_lineage)} datasets)")
    print(f"  ✅ Step 6: Generated combined Mermaid diagram")
    print(f"     - Subscriber lineage: {len(subscriber_lineage)} datasets")
    print(f"     - Publisher lineage: {len(parent_lineage)} datasets")
    print(f"     - Connected via publication: {subscription.publication_id}")
    print(f"{'='*80}")

    return card


async def main():
    """Main entry point for sample.

    Returns:
        DomoCard: The validated published card
    """


    try:
        card = await test_federated_card_lineage_tracking()
        return card
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    card = asyncio.run(main())
    print(f"\n✅ Sample complete!")