"""Page layout and content management subentity."""

__all__ = [
    "DomoPageLayout",
    "PageLayout",
    "PageLayoutContent",
    "PageLayoutTemplate",
    "PageLayoutBackground",
    "PageLayoutStandard",
    "PageLayoutCompact",
]

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ...base.entities import DomoSubEntity
from ...client.context import RouteContext
from ...routes import page as page_routes
from ...utils import (
    chunk_execution as dmce,
    convert as dmcv,
)

# ============================================================================
# Layout dataclasses (previously in page_content.py)
# ============================================================================


@dataclass
class PageLayoutTemplate:
    content_key: int
    x: int
    y: int
    width: int
    height: int
    type: str
    virtual: bool
    virtual_appendix: bool

    @classmethod
    def from_dict(cls, dd):
        return cls(
            content_key=dd.contentKey,
            x=dd.x,
            y=dd.y,
            width=dd.width,
            height=dd.height,
            type=dd.type,
            virtual=dd.virtual,
            virtual_appendix=dd.virtualAppendix,
        )

    def get_body(self):
        return {
            "contentKey": self.content_key,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "type": self.type,
            "virtual": self.virtual,
            "virtualAppendix": self.virtual_appendix,
        }


@dataclass
class PageLayoutBackground:
    id: int
    crop_height: int
    crop_width: int
    x: int
    y: str
    data_file_id: int
    image_brightness: int
    image_height: int
    image_width: int
    selected_color: str
    text_color: str
    type: str
    is_darkMode: bool
    alpha: float
    src: str

    @classmethod
    def from_dict(cls, dd):
        if dd is not None:
            return cls(
                id=dd.id,
                crop_height=dd.cropHeight,
                crop_width=dd.cropWidth,
                x=dd.x,
                y=dd.y,
                data_file_id=dd.dataFileId,
                image_brightness=dd.imageBrightness,
                image_height=dd.imageHeight,
                image_width=dd.imageWidth,
                selected_color=dd.selectedColor,
                text_color=dd.textColor,
                type=dd.type,
                is_darkMode=dd.darkMode,
                alpha=dd.alpha,
                src=dd.src,
            )
        else:
            return None

    def get_body(self):
        return {
            "id": self.id,
            "cropHeight": self.crop_height,
            "cropWidth": self.crop_width,
            "x": self.x,
            "y": self.y,
            "dataFileId": self.data_file_id,
            "imageBrightness": self.image_brightness,
            "imageHeight": self.image_height,
            "imageWidth": self.image_width,
            "selectedColor": self.selected_color,
            "textColor": self.text_color,
            "type": self.type,
            "darkMode": self.is_darkMode,
            "alpha": self.alpha,
            "src": self.src,
        }


@dataclass
class PageLayoutContent:
    accept_date_filter: bool
    accept_filters: bool
    accept_segments: bool
    card_id: int
    card_urn: str
    compact_interaction_default: bool
    content_key: int
    fit_to_frame: bool
    has_summary: bool
    hide_border: bool
    hide_description: bool
    hide_footer: bool
    hide_margins: bool
    hide_summary: bool
    hide_timeframe: bool
    hide_title: bool
    hide_wrench: bool
    id: int
    summary_number_only: bool
    type: str
    text: str
    background_id: int
    background: PageLayoutBackground

    @classmethod
    def from_dict(cls, dd):
        return cls(
            accept_date_filter=dd.acceptDateFilter,
            accept_filters=dd.acceptFilters,
            accept_segments=dd.acceptSegments,
            card_id=dd.cardId,
            card_urn=dd.cardUrn,
            compact_interaction_default=dd.compactInteractionDefault,
            content_key=dd.contentKey,
            fit_to_frame=dd.fitToFrame,
            has_summary=dd.hasSummary,
            hide_border=dd.hideBorder,
            hide_description=dd.hideDescription,
            hide_footer=dd.hideFooter,
            hide_margins=dd.hideMargins,
            hide_summary=dd.hideSummary,
            hide_timeframe=dd.hideTimeframe,
            hide_title=dd.hideTitle,
            hide_wrench=dd.hideWrench,
            id=dd.id,
            summary_number_only=dd.summaryNumberOnly,
            type=dd.type,
            text=dd.text,
            background_id=dd.backgroundId,
            background=PageLayoutBackground.from_dict(dd=dd.background),
        )

    def get_body(self):
        body = {
            "acceptDateFilter": self.accept_date_filter,
            "acceptFilters": self.accept_filters,
            "acceptSegments": self.accept_segments,
            "cardId": self.card_id,
            "cardUrn": self.card_urn,
            "compactInteractionDefault": self.compact_interaction_default,
            "contentKey": self.content_key,
            "fitToFrame": self.fit_to_frame,
            "hasSummary": self.has_summary,
            "hideBorder": self.hide_border,
            "hideDescription": self.hide_description,
            "hideFooter": self.hide_footer,
            "hideMargins": self.hide_margins,
            "hideSummary": self.hide_summary,
            "hideTimeframe": self.hide_timeframe,
            "hideTitle": self.hide_title,
            "hideWrench": self.hide_wrench,
            "id": self.id,
            "summaryNumberOnly": self.summary_number_only,
            "type": self.type,
            "text": self.text,
            "backgroundId": self.background_id,
        }

        if self.background is not None:
            body["background"] = self.background.get_body()
        return body


@dataclass
class PageLayoutStandard:
    aspect_ratio: float
    width: int
    frame_margin: int
    frame_padding: int
    type: str
    template: list[PageLayoutTemplate]

    @classmethod
    def from_dict(cls, dd):
        obj = cls(
            aspect_ratio=dd.aspectRatio,
            width=dd.width,
            frame_margin=dd.frameMargin,
            frame_padding=dd.framePadding,
            type=dd.type,
            template=[],
        )

        if dd.template is not None:
            for template_item in dd.template:
                dc = PageLayoutTemplate.from_dict(dd=template_item)
                if dc not in obj.template:
                    obj.template.append(dc)
        return obj


@dataclass
class PageLayoutCompact:
    aspect_ratio: float
    width: int
    frame_margin: int
    frame_padding: int
    type: str
    template: list[PageLayoutTemplate]

    @classmethod
    def from_dict(cls, dd):
        obj = cls(
            aspect_ratio=dd.aspectRatio,
            width=dd.width,
            frame_margin=dd.frameMargin,
            frame_padding=dd.framePadding,
            type=dd.type,
            template=[],
        )
        if dd.template is not None:
            for template_item in dd.template:
                dc = PageLayoutTemplate.from_dict(dd=template_item)
                if dc not in obj.template:
                    obj.template.append(dc)
        return obj


@dataclass
class PageLayout:
    id: str
    page_id: int
    is_print_friendly: bool
    is_enabled: bool
    is_dynamic: bool
    has_page_breaks: bool
    content: list[PageLayoutContent]
    standard: PageLayoutStandard
    compact: PageLayoutCompact
    background: PageLayoutBackground

    @classmethod
    def from_dict(cls, dd):
        obj = cls(
            id=dd.layoutId,
            page_id=dd.pageUrn,
            is_print_friendly=dd.printFriendly,
            is_enabled=dd.enabled,
            is_dynamic=dd.isDynamic,
            content=[],
            has_page_breaks=dd.hasPageBreaks,
            standard=PageLayoutStandard.from_dict(dd=dd.standard),
            compact=PageLayoutCompact.from_dict(dd=dd.compact),
            background=PageLayoutBackground.from_dict(dd=dd.background),
        )
        if dd.content is not None:
            for content_item in dd.content:
                dc = PageLayoutContent.from_dict(dd=content_item)
                if dc not in obj.content:
                    obj.content.append(dc)
        return obj

    @classmethod
    def generate_new_background_body(cls):
        background_body = {
            "selectedColor": "#EEE000",
            "textColor": "#4A4A4A",
            "type": "COLOR",
            "darkMode": False,
            "alpha": 1,
        }

        return background_body

    def get_body(self):
        body = {
            "layoutId": self.id,
            "pageUrn": self.page_id,
            "printFriendly": self.is_print_friendly,
            "enabled": self.is_enabled,
            "isDynamic": self.is_dynamic,
            "hasPageBreaks": self.has_page_breaks,
            "standard": {
                "aspectRatio": self.standard.aspect_ratio,
                "width": self.standard.width,
                "frameMargin": self.standard.frame_margin,
                "framePadding": self.standard.frame_padding,
                "type": self.standard.type,
            },
            "compact": {
                "aspectRatio": self.compact.aspect_ratio,
                "width": self.compact.width,
                "frameMargin": self.compact.frame_margin,
                "framePadding": self.compact.frame_padding,
                "type": self.compact.type,
            },
        }
        if self.background is not None:
            body["background"] = self.background.get_body()

        if self.content == [] or self.content is None:
            body["content"] = []
        else:
            temp_list = []
            for content_item in self.content:
                temp_list.append(content_item.get_body())
            body["content"] = temp_list

        if self.standard.template is None or self.standard.template == []:
            body["standard"]["template"] = []
        else:
            temp_list = []
            for template_item in self.standard.template:
                temp_list.append(template_item.get_body())
            body["standard"]["template"] = temp_list

        if self.compact.template is None or self.compact.template == []:
            body["compact"]["template"] = []
        else:
            temp_list = []
            for template_item in self.compact.template:
                temp_list.append(template_item.get_body())
            body["compact"]["template"] = temp_list
        return body


# ============================================================================
# DomoPageLayout subentity (merges layout + content management)
# ============================================================================


@dataclass
class DomoPageLayout(DomoSubEntity):
    """Page layout and content management subentity.

    Manages page layout configuration and content operations including cards and datasets.
    Combines layout management with content operations that require page definition.

    Attributes:
        layout: PageLayout configuration object
        cards: list of DomoCard objects on the page
        datasets: list of DomoDataset objects used by page cards

    Example:
        >>> page = await DomoPage.get_by_id(page_id="123", auth=auth)
        >>> # Get cards from page
        >>> await page.Layout.get_cards()
        >>> print(f"Found {len(page.Layout.cards)} cards")
        >>> # Update layout
        >>> await page.Layout.update(layout_changes={...})
    """

    layout: PageLayout | None = None
    cards: list[Any] = field(default_factory=list)
    datasets: list[Any] = field(default_factory=list)

    async def get_cards(
        self,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        parent_auth_retrieval_fn: Callable[[str], Any] | None = None,
        check_if_published: bool | None = None,
        **context_kwargs,
    ):
        """Get all cards from the page.

        Fetches page definition and returns all cards, optionally checking if they're published.

        Args:
            return_raw: Return raw ResponseGetData without processing
            context: Optional RouteContext for API call configuration
            parent_auth_retrieval_fn: Callable returning publisher auth when given publisher domain
            check_if_published: Check if cards are published (requires subscription check)
            **context_kwargs: Additional context parameters

        Returns:
            list of DomoCard objects or ResponseGetData if return_raw=True
        """
        from .. import DomoCard as dc

        context = RouteContext.build_context(context=context, **context_kwargs)

        res = await page_routes.get_page_definition(
            auth=self.parent.auth, page_id=self.parent.id, context=context
        )

        if return_raw:
            return res

        if len(res.response.get("cards")) == 0:
            return []

        check_publish = True if check_if_published is None else check_if_published

        self.cards = await dmce.gather_with_concurrency(
            n=60,
            *[
                dc.DomoCard.get_by_id(
                    card_id=card["id"],
                    auth=self.parent.auth,
                    parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                    check_if_published=check_publish,
                    context=context,
                )
                for card in res.response.get("cards")
            ],
        )

        # Auto-fetch datasets with lineage for each card when parent_auth_retrieval_fn is provided
        if parent_auth_retrieval_fn:
            await dmce.gather_with_concurrency(
                n=60,
                *[
                    card.Datasets.get(
                        parent_auth_retrieval_fn=parent_auth_retrieval_fn,
                        context=context,
                    )
                    for card in self.cards
                    if card.Datasets
                ],
            )

        return self.cards

    async def get_datasets(
        self,
        return_raw: bool = False,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Get all datasets used by cards on the page.

        Args:
            return_raw: Return raw ResponseGetData without processing
            context: Optional RouteContext for API call configuration
            **context_kwargs: Additional context parameters

        Returns:
            list of DomoDataset objects or ResponseGetData if return_raw=True
        """
        context = RouteContext.build_context(context=context, **context_kwargs)

        res = await page_routes.get_page_definition(
            auth=self.parent.auth, page_id=self.parent.id, context=context
        )

        if return_raw:
            return res

        cards = await self.get_cards(context=context)

        card_datasets = await dmce.gather_with_concurrency(
            *[card.get_datasets(context=context) for card in cards],
            n=10,
        )

        self.datasets = [
            ds for ds_ls in card_datasets for ds in ds_ls if ds is not None
        ]

        return self.datasets

    async def update(
        self,
        body: dict,
        *,
        context: RouteContext | None = None,
        **context_kwargs,
    ):
        """Update page layout.

        Acquires write lock, updates layout, then releases lock.

        Args:
            body: Layout configuration dictionary
            context: Optional RouteContext for API call configuration
            **context_kwargs: Additional context parameters

        Returns:
            True if successful, False otherwise
        """
        context = RouteContext.build_context(context=context, **context_kwargs)

        if not self.layout:
            # Need layout ID - fetch it first
            res = await page_routes.get_page_by_id(
                auth=self.parent.auth,
                page_id=self.parent.id,
                include_layout=True,
                context=context,
            )
            if hasattr(res.response, "pageLayoutV4") and res.response.pageLayoutV4:
                self.layout = PageLayout.from_dict(dd=res.response.pageLayoutV4)

        if not self.layout:
            return False

        layout_id = self.layout.id

        datetime_now = dt.datetime.now()
        start_time_epoch = dmcv.convert_datetime_to_epoch_millisecond(datetime_now)

        res_writelock = await page_routes.put_writelock(
            auth=self.parent.auth,
            layout_id=layout_id,
            user_id=self.parent.auth.user_id,
            epoch_time=start_time_epoch,
            context=context,
        )

        if res_writelock.status == 200:
            res = await page_routes.update_page_layout(
                auth=self.parent.auth, body=body, layout_id=layout_id, context=context
            )

            if not res.is_success:
                return False

            res_writelock = await page_routes.delete_writelock(
                auth=self.parent.auth, layout_id=layout_id, context=context
            )
            if res_writelock.status != 200:
                return False

        else:
            return False

        return True
