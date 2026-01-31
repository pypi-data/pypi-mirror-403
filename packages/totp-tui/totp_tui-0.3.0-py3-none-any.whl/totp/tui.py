import curses
import time
from curses import window
from dataclasses import dataclass
from typing import Self

from totp import utils

from totp.text import FormattedText, get_slider, calc_slider, init_colors
from totp.crypt import EntrySite, InvalidSecretKey
from totp.config import (
    BLANK_DEF,
    NICK_DEF,
    SITE_DEF,
    ENTRY_SCHEMA,
    STATUSLINE_SCHEMA,
    DEFAULT_FG,
)

logger = utils.get_logger(__name__)


class SchemaTypeError(Exception):
    def __init__(self, component: str) -> None:
        self.component = component
        self.message = f"Schema component {self.component} has incorrect typing or is missing an element."
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"Schema component {self.component} has incorrect typing or is missing an element."


@dataclass
class Schema:
    format = ENTRY_SCHEMA
    statusline = STATUSLINE_SCHEMA

    @classmethod
    def get_line_len(
        cls, components: (list[FormattedText], list[FormattedText])
    ) -> int:
        return sum(
            sum(len(comp.get_text()) for comp in components[x])
            for x in range(len(components))
        )

    def format_entry_line(
        self, line: list[dict], values: dict, max_width: int
    ) -> (list[FormattedText], list[FormattedText]):
        """ """

        left_align: list[FormattedText] = []
        right_align: list[FormattedText] = []

        for component in line:
            component_keys = component.keys()
            try:
                val = component["type"]
            except KeyError:
                logger.warn("Schema component ignored, invalid type found")
                continue
            if val in values.keys() and type(val) is str:
                text = values[val]

                match val:
                    case "slider":
                        if (
                            "width" in component_keys
                            and type(component["width"]) is int
                        ):
                            width = component["width"]
                        else:
                            raise SchemaTypeError(component="slider")

                        text = get_slider(width=width)
                    case "time":
                        localtime = time.localtime()
                        if (
                            "format" in component_keys
                            and type(component["format"]) is str
                        ):
                            text = time.strftime(component["format"], localtime)
                        else:
                            raise SchemaTypeError(component="time")
                    case "token_time":
                        rem = 30 - time.time() % 30
                        if (
                            "precision" in component_keys
                            and type(component["precision"]) is int
                        ):
                            prec = component["precision"]
                            text = repr(round(rem, prec))
                        else:
                            raise SchemaTypeError(component="token_time")
                    case "filler":
                        if (
                            "filler" in component_keys
                            and type(component["filler"]) is str
                        ):
                            text = component["filler"][0] * max_width
                        else:
                            raise SchemaTypeError(component="filler")
                    case "token":
                        text = values["token"]

                    case _:
                        if "width" in component_keys:
                            try:
                                width = int(component["width"])
                                if width == -1:
                                    dif = max_width - len(text)
                                    text = text[: min(max_width, len(text))]
                                    if dif > 0:
                                        text = text + (values["blank"] * dif)
                                else:
                                    dif = width - len(text)
                                    text = text[: min(max_width, width, len(text))]
                                    if dif > 0:
                                        text = text + (BLANK_DEF * dif)
                            except TypeError:
                                raise SchemaTypeError(component=val)
                        else:
                            raise SchemaTypeError(component=val)

                if "space_before" in component_keys:
                    try:
                        space_before = int(component["space_before"])
                        text = (BLANK_DEF * space_before) + text
                    except TypeError:
                        logger.warn("Schema component ignored, no valid type found.")
                if "space_after" in component_keys:
                    try:
                        space_after = int(component["space_after"])
                        text = text + (BLANK_DEF * space_after)
                    except TypeError:
                        logger.warn("Schema component ignored, no valid type found.")

                color = DEFAULT_FG
                if "color" in component_keys:
                    try:
                        color = str(component["color"])
                    except TypeError:
                        logger.warn("Color component ignored, not a valid option.")
                if "alignment" in component_keys:
                    try:
                        align = str(component["alignment"])
                        formatted = FormattedText(text=text, color=color)
                        if align == "right":
                            right_align.append(formatted)
                        elif align == "left":
                            left_align.append(formatted)
                    except TypeError:
                        left_align.append(FormattedText(text=text, color=color))
                else:
                    # treat as left-aligned by default
                    formatted = FormattedText(text=text, color=color)
                    left_align.append(formatted)
            else:
                logger.warn(
                    f'Schema component ignored, unknown element type "{str(val)}"'
                )

        return (left_align, right_align)

    def draw_line(
        self,
        src: window,
        start_y: int,
        components: (list[FormattedText], list[FormattedText]),
        reverse: bool = False,
    ) -> None:
        _, maxx = src.getmaxyx()
        pos_x = 0

        if Schema.get_line_len(components) <= maxx:
            for comp in components[0]:
                comp_off = comp.len()
                src.addstr(
                    start_y,
                    pos_x,
                    comp.get_text(),
                    curses.color_pair(comp.get_color(reverse=reverse)),
                )
                pos_x += comp_off
            filler = maxx - pos_x - sum(comp.len() for comp in components[1])
            src.addstr(
                start_y, pos_x, BLANK_DEF * filler, curses.A_REVERSE if reverse else 0
            )
            pos_x += filler
            for comp in components[1]:
                comp_off = comp.len()
                src.addstr(
                    start_y,
                    pos_x,
                    comp.get_text(),
                    curses.color_pair(comp.get_color(reverse=reverse)),
                )
                pos_x += comp_off
        else:
            for comp in components[0]:
                comp_off = comp.len()
                src.addstr(
                    start_y,
                    pos_x,
                    comp.get_text(),
                    curses.color_pair(comp.get_color(reverse=reverse)),
                )
                pos_x += comp_off
            for comp in components[1]:
                comp_off = comp.len()
                src.addstr(
                    start_y,
                    pos_x,
                    comp.get_text(),
                    curses.color_pair(comp.get_color(reverse=reverse)),
                )
                pos_x += comp_off

    def draw_entry(
        self, src: window, start_y: int, entry: EntrySite, selected: bool = False
    ) -> None:
        """ """

        _y, _x = src.getmaxyx()

        try:
            totp_token = entry.get_totp_token()
        except InvalidSecretKey as exc:
            totp_token = (
                NICK_DEF[0] if type(NICK_DEF) is str and len(NICK_DEF) > 0 else "\u0023"
            ) * 6
            logger.error(exc)

        values = {
            "nick": entry.nick,
            "site": entry.site,
            "time": None,
            "token_time": None,
            "token": totp_token,
            "slider": None,
            "blank": BLANK_DEF,
            "filler": NICK_DEF,
        }

        for off, (_, line) in enumerate(self.format.items()):
            ll = self.format_entry_line(line=line, values=values, max_width=_x - 1)
            self.draw_line(
                src=src, start_y=start_y + off, components=ll, reverse=selected
            )

    def format_statusline(
        self, line: list[dict], values: dict, max_width: int
    ) -> (list[FormattedText], list[FormattedText]):
        """ """

        left_align: list[FormattedText] = []
        right_align: list[FormattedText] = []

        for component in line:
            component_keys = component.keys()
            try:
                val = component["type"]
            except KeyError:
                logger.warn("Schema component ignored, invalid type found")
                continue
            if val in values.keys() and type(val) is str:
                text = values[val]

                match val:
                    case "slider":
                        if (
                            "width" in component_keys
                            and type(component["width"]) is int
                        ):
                            width = component["width"]
                        else:
                            raise SchemaTypeError(component="slider")
                        text = get_slider(width=width)
                    case "time":
                        localtime = time.localtime()
                        if (
                            "format" in component_keys
                            and type(component["format"]) is str
                        ):
                            text = time.strftime(component["format"], localtime)
                        else:
                            raise SchemaTypeError(component="time")
                    case "token_time":
                        rem = 30 - time.time() % 30
                        if (
                            "precision" in component_keys
                            and type(component["precision"]) is int
                        ):
                            prec = component["precision"]
                            text = repr(round(rem, prec))
                        else:
                            raise SchemaTypeError(component="token_time")
                    case "filler":
                        if (
                            "filler" in component_keys
                            and type(component["filler"]) is str
                        ):
                            text = component["filler"][0] * max_width
                        else:
                            raise SchemaTypeError(component="filler")

                if "space_before" in component_keys:
                    try:
                        space_before = int(component["space_before"])
                        text = (BLANK_DEF * space_before) + text
                    except TypeError:
                        logger.warn("Schema component ignored, no valid type found.")
                if "space_after" in component_keys:
                    try:
                        space_after = int(component["space_after"])
                        text = text + (BLANK_DEF * space_after)
                    except TypeError:
                        logger.warn("Schema component ignored, no valid type found.")

                color = DEFAULT_FG
                if "color" in component_keys:
                    try:
                        color = str(component["color"])
                    except TypeError:
                        pass
                if "alignment" in component_keys:
                    try:
                        align = str(component["alignment"])
                        formatted = FormattedText(text=text, color=color)
                        if align == "right":
                            right_align.append(formatted)
                        elif align == "left":
                            left_align.append(formatted)
                    except TypeError:
                        left_align.append(FormattedText(text=text, color=color))
                else:
                    formatted = FormattedText(text=text, color=color)
                    left_align.append(formatted)
            else:
                logger.warn(
                    f'Schema component ignored, unknown element type "{str(val)}"'
                )

        return (left_align, right_align)

    def draw_statusline(self, src: window) -> None:
        """
        Draw the statusline at the bottom of the screen, refreshing all of its components
        """

        _y, _x = src.getmaxyx()
        len_status = len(self.statusline)
        start_y = max(0, _y - len_status)

        values = {"time": None, "token_time": None, "slider": None, "filler": NICK_DEF}

        for off, (_, line) in enumerate(self.statusline.items()):
            ll = self.format_statusline(line=line, values=values, max_width=_x - 1)
            self.draw_line(src=src, start_y=start_y + off, components=ll)

    def entry_offset(self) -> int:
        return len(self.format)


class AuthWindow:
    def __init__(self, stdsrc: window) -> None:
        self.orig: window = stdsrc
        self.smax: tuple[int, int] = self.orig.getmaxyx()
        self.sites: list[EntrySite] = []
        self.schema = Schema()
        self.pad = None
        self.selected_entry = 0
        self.scroll_y = 0
        init_colors()

    def update_pad(self) -> None:
        """
        Updates pad's dimensions in case the window has changed size
        """

        max_y, max_x = self.orig.getmaxyx()
        h = len(self.sites) * self.schema.entry_offset()

        # only update pad on changed dimensions
        if self.pad is None or self.smax != (max_y, max_x):
            self.smax = (max_y, max_x)

            try:
                self.pad = curses.newpad(h, max_x)
            except curses.error:
                raise RuntimeError("Failed to create newpad")

    def draw(self) -> None:
        """
        Refresh the screen and updates all components
        """

        try:
            self.update_pad()
            self.pad.erase()
        except RuntimeError:
            logger.error("Empty sites list.")
            raise RuntimeError("Empty sites list")

        for i, site in enumerate(self.sites):
            try:
                y = self.schema.entry_offset() * i
                selected = self.selected_entry == i
                self.schema.draw_entry(
                    src=self.pad, start_y=y, entry=site, selected=selected
                )
            except curses.error:
                pass
        try:
            self.schema.draw_statusline(src=self.orig)
        except curses.error:
            pass

        max_y, max_x = self.orig.getmaxyx()

        entry_h = self.schema.entry_offset()
        cursor_top = self.selected_entry * self.schema.entry_offset()
        cursor_bottom = cursor_top + entry_h

        pad_height = len(self.sites) * entry_h
        view_height = max_y - (1 + len(self.schema.statusline))

        view_top = self.scroll_y
        view_bottom = view_top + view_height

        if cursor_top < view_top:
            view_top = cursor_top
        elif cursor_bottom > view_bottom:
            view_top = cursor_bottom - view_height

        view_top = max(0, min(view_top, max(0, pad_height - view_height)))
        self.scroll_y = view_top

        self.pad.refresh(self.scroll_y, 0, 0, 0, view_height, max_x - 1)
        self.orig.refresh()

    def add_site(self, site: EntrySite) -> None:
        self.sites.append(site)

    def get_code(self) -> str:
        """
        Return TOTP code for hovered entry
        """

        assert self.selected_entry >= 0 and self.selected_entry < len(self.sites)
        return self.sites[self.selected_entry].get_totp_token()

    def update_cursor(self, ch: int):
        """
        Moves the cursor downwards if ch is 'j', and upwards if ch is 'k'
        """

        if ch == ord("j"):
            self.selected_entry = min(self.selected_entry + 1, len(self.sites) - 1)
        elif ch == ord("k"):
            self.selected_entry = max(self.selected_entry - 1, 0)
