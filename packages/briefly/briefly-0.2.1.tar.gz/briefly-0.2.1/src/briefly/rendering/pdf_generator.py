from datetime import datetime, date
from importlib.resources import files
from typing import Any, List, Optional, Tuple

from fpdf import FPDF, YPos, XPos
from fpdf.enums import MethodReturnValue

from briefly.model.style import Style, PurpleHaze
from briefly.rendering.font_spec import FONT_FAMILY, FONTS, ICON_FONT_FAMILY
from briefly.rendering.graphs import build_pie_chart_bytes
from briefly.rendering.icons import FLAG_ICON, DUE_DATE_ICON, PRIORITY_ICON

HEADER_SIZE: int = 20
SECTION_TITLE_SIZE: int = 13
TEXT_SIZE: int = 10
ICON_FONT_SIZE: int = 7
LABEL_SIZE: int = 7
MARGIN_SIZE: int = 25

_SMALL_SPACING: float = 2
_MEDIUM_SPACING: float = 5
_LARGE_SPACING: float = 10


class PDF(FPDF):
    style: Style

    def __init__(self, style: Style = PurpleHaze(), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.style = style
        self.set_margin(MARGIN_SIZE)
        self.set_page_background(style.background_color)
        self.generation_time = datetime.now()
        self.setup_fonts()

    def setup_fonts(self) -> None:
        font_pkg = files("briefly.fonts")
        for font in FONTS:
            self.add_font(font.family, font.style, str(font_pkg / font.filename))
        self.set_font(FONT_FAMILY, "", TEXT_SIZE)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font(FONT_FAMILY, "I", 7)
        time_str: str = self.generation_time.strftime("%d.%m.%Y %H:%M:%S")
        self.cell(0, 10, time_str, align="L")
        self.cell(0, 10, f"Page {self.page_no()}", align="R")

    def main_title(self, text: str) -> None:
        self.set_font(FONT_FAMILY, "B", size=HEADER_SIZE)
        self.set_fill_color(*self.style.header_background)
        self.set_text_color(*self.style.header_color)
        self.cell(0, HEADER_SIZE, text, align="C", fill=True, new_y=YPos.NEXT)
        self.set_text_color(*self.style.font_color)
        self.set_y(self.get_y() + _LARGE_SPACING)

    def divider(self) -> None:
        self.set_draw_color(*self.style.border_color)
        x1, x2 = MARGIN_SIZE, self.w - MARGIN_SIZE
        y = self.get_y() + _MEDIUM_SPACING
        self.line(x1, y, x2, y)
        self.ln(_MEDIUM_SPACING)

    def section_title(self, text: str, link: Optional[str] = None) -> None:
        self.set_y(self.get_y() + _MEDIUM_SPACING)
        self._break_page_if_needed(content_height=40)
        self.set_font(FONT_FAMILY, "B", SECTION_TITLE_SIZE)
        self.set_text_color(*self.style.section_title_color)
        self.cell(0, 10, text, link=link or 0, new_y=YPos.NEXT)
        self.set_font(FONT_FAMILY, size=TEXT_SIZE)
        self.set_text_color(*self.style.font_color)
        self.set_y(self.get_y() + _MEDIUM_SPACING)

    def summary_card(self, items: List[str], width: int = 80) -> tuple[float, float]:
        padding = _MEDIUM_SPACING
        row_height = 6
        card_height = (len(items) * row_height) + 2 * padding
        self._break_page_if_needed(card_height)
        start_x, start_y = self.x, self.y

        if start_y + card_height >= self.h - self.b_margin:
            self.add_page()

        self.set_fill_color(*self.style.card_background)
        self.rect(
            start_x,
            start_y,
            width,
            card_height,
            style="F",
            round_corners=True,
            corner_radius=1.5,
        )
        self.set_font(FONT_FAMILY, "", TEXT_SIZE)
        self.set_text_color(*self.style.font_color)

        x = start_x + padding
        y = start_y + padding
        for text in items:
            self.set_xy(x, y)
            self.cell(width - 2 * padding, row_height, text, align="L")
            y = y + row_height

        if start_x + width >= self.w - self.r_margin:
            self.set_xy(self.l_margin, start_y + card_height + padding)
        else:
            self.set_xy(start_x + width + padding, start_y)
        return start_x + width, start_y + card_height

    def styled_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        col_widths: list[int],
    ) -> None:
        self.set_font(FONT_FAMILY, "B", TEXT_SIZE)
        self.set_fill_color(*self.style.table_header_color)
        self.set_text_color(*self.style.font_color)

        for i, h in enumerate(headers):
            self.cell(col_widths[i], 10, h, border="B", fill=True)
        self.ln(10)

        # rows
        self.set_font(FONT_FAMILY, "", LABEL_SIZE)

        for idx, row in enumerate(rows):
            self.set_fill_color(*self.style.table_row_colors[idx % 2])

            for i, cell in enumerate(row):
                self.cell(col_widths[i], LABEL_SIZE, cell, border="B", fill=True)
            self.set_fill_color(*self.style.card_background)
            self.ln()

        self.set_fill_color(*self.style.card_background)
        self.set_y(self.get_y() + _LARGE_SPACING)

    def tag(self, text: str) -> Tuple[float, float]:
        bg = self.style.background_color
        self.set_font(FONT_FAMILY, "", LABEL_SIZE)
        self.set_text_color(*self.style.font_color)

        text_w = self.get_string_width(text) + _SMALL_SPACING * 2
        text_h = 5
        x, y = self.x, self.y

        self.set_fill_color(*bg)
        self.rect(
            x, y, text_w, text_h, style="F", round_corners=True, corner_radius=1.5
        )

        self.cell(text_w, text_h, text, align="C")
        self.set_x(x + text_w)
        return text_w, text_h

    def _break_page_if_needed(self, content_height: float) -> None:
        if self.y + content_height >= self.h - self.b_margin:
            self.add_page()

    def task_card(
        self,
        task_id: str,
        title: str,
        status: str,
        due_date: Optional[date] = None,
        priority: Optional[int] = None,
        estimate: Optional[int] = None,
        flagged: bool = False,
        link: str | int = 0,
    ) -> None:
        width = 77.5
        height = 30
        self._break_page_if_needed(height)

        start_x, start_y = self.x, self.y
        row_height = 5

        stripe_color: tuple[int, int, int] = (
            self.style.priority_color if flagged else self.style.border_color
        )
        self.accent_card(stripe_color, width, height)

        if flagged:
            self.set_text_color(*self.style.disabled_color)

        text_start_x = start_x + 12.5
        self.set_font(FONT_FAMILY, "B", LABEL_SIZE)
        self.set_xy(text_start_x, start_y + 9)
        self.cell(
            15,
            row_height,
            task_id,
            align="R",
            link=link,
            new_x=XPos.LEFT,
            new_y=YPos.NEXT,
        )

        _, y = self._two_line_label(status, text_start_x, self.y + 1)
        y = y + 1
        self.set_xy(text_start_x - 3, y + 0.2)
        if due_date:
            self.set_font(ICON_FONT_FAMILY, "", 7)
            self.cell(3, row_height, DUE_DATE_ICON, align="L")
            x, _ = self._small_label(
                due_date.strftime("%d.%m.%Y") if due_date else "N/A",
                text_start_x,
                y,
            )
        else:
            x = text_start_x + 15

        x, _ = self._priority_icons(priority, flagged, x + 6, y)

        story_points_text = f"SP: {estimate or 'N/A'}"
        x, _ = self._small_label(story_points_text, x + 6, y)
        if flagged:
            self._flagged_icon(x + 8, y)

        self._task_title(title, text_start_x + 15, start_y + 4, link=link)

        self.set_text_color(*self.style.font_color)
        if start_x == self.l_margin:
            self.set_xy(start_x + width + _MEDIUM_SPACING, start_y)
        else:
            self.set_y(start_y + height + _MEDIUM_SPACING)

    def _task_title(self, title: str, x: float, y: float, link: str | int = 0) -> None:
        self.set_xy(x, y)
        self.set_font(FONT_FAMILY, size=TEXT_SIZE)
        title_lines = self.multi_cell(
            45,
            15,
            title,
            max_line_height=4,
            dry_run=True,
            output=MethodReturnValue.LINES,
        )
        if len(title_lines) == 1:
            self.cell(45, 5, title, align="L", link=link)
        elif len(title_lines) < 4:
            self.multi_cell(45, 15, title, align="L", max_line_height=4, link=link)
        else:
            title_lines[3] = self._trim_with_ellipsis(title_lines[3], 45)
            title = " ".join(title_lines[0:4])
            self.multi_cell(45, 15, title, align="L", max_line_height=4, link=link)

    def _trim_with_ellipsis(self, text: str, column_width: int) -> str:
        ellipsis_chars = "..."
        trimmed_text = text + ellipsis_chars
        string_width = self.get_string_width(trimmed_text)
        words = text.split()

        while string_width > (column_width - 1):
            words = words[:-1]
            trimmed_text = " ".join(words) + ellipsis_chars
            string_width = self.get_string_width(trimmed_text)

        return trimmed_text

    def _priority_icons(
        self,
        priority: Optional[int],
        flagged: bool = False,
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> tuple[float, float]:
        x, y = x or self.x, y or self.y
        if priority:
            self.set_font(ICON_FONT_FAMILY, size=ICON_FONT_SIZE)
            self.set_xy(x, y + 0.5)
            if priority == 1:
                self.set_text_color(*self.style.priority_color)

            text = PRIORITY_ICON * (5 - priority)
            self.cell(15, 5, text)
            self.set_font(FONT_FAMILY, size=LABEL_SIZE)
            if flagged:
                self.set_text_color(*self.style.disabled_color)
            else:
                self.set_text_color(*self.style.font_color)
        self.set_xy(x + 15, y)
        return x + 15, y + 3

    def _small_label(self, text: str, x: float, y: float) -> tuple[float, float]:
        self.set_font(FONT_FAMILY, "", LABEL_SIZE)
        self.set_xy(x, y)
        self.cell(15, 5, text, align="R")
        return x + 15, self.y + 3

    def _two_line_label(self, text: str, x: float, y: float) -> tuple[float, float]:
        self.set_font(FONT_FAMILY, "", LABEL_SIZE)
        self.set_xy(x, y)
        self.multi_cell(15, 6, text, align="R", max_line_height=3)

        return x + 15, self.y

    def _flagged_icon(self, x: float, y: float) -> None:
        self.set_font(ICON_FONT_FAMILY, "", ICON_FONT_SIZE)
        self.set_text_color(*self.style.priority_color)
        self.set_xy(x, y + 0.3)
        self.cell(3, 5, FLAG_ICON, align="R")
        self.set_xy(self.x, y - 0.3)
        self.set_text_color(*self.style.disabled_color)

    def _plot_bar_chart(
        self, values: list[float], height: float, max_width: Optional[float] = None
    ) -> tuple[float, float]:
        if not values:
            return self.x, self.y

        spacing: float = 2
        bar_width: float = 3
        x = self.x
        start_y = self.y

        if max_width is not None:
            total_bars_width = len(values) * bar_width + (len(values) - 1) * spacing
            if total_bars_width > max_width:
                scale_factor: float = max_width / total_bars_width
                bar_width *= scale_factor
                spacing *= scale_factor

        width = x + len(values) * (bar_width + spacing) + spacing
        max_value = max(values) if values else 0

        self.set_draw_color(*self.style.border_color)
        self.line(x, start_y, width, start_y)
        self.line(x, start_y + 5, width, start_y + 5)
        self.line(x, start_y + 10, width, start_y + 10)
        self.line(x, start_y + 15, width, start_y + 15)
        self.line(x, start_y + 20, width, start_y + 20)
        self.line(x, start_y + 25, width, start_y + 25)

        x += spacing

        for index, value in enumerate(values):
            if value > 0:
                self.set_fill_color(
                    *self.style.chart_colors[index % len(self.style.chart_colors)]
                )
                bar_height = height * value / max_value
                y = start_y + height - bar_height
                if bar_height > 0.7:
                    self.rect(
                        x,
                        y,
                        bar_width,
                        bar_height,
                        style="F",
                        round_corners=True,
                        corner_radius=0.5,
                    )
                else:
                    self.rect(x, y, bar_width, bar_height, style="F")
            x += bar_width + spacing

        return x - spacing, start_y + height

    def bar_chart(
        self,
        data: dict[str, float],
        caption: str,
        height: float = 30,
        wide: bool = False,
    ) -> tuple[float, float]:
        if not data.keys():
            return self.x, self.y

        self._break_page_if_needed(height)
        start_x, start_y = self.x, self.y

        sorted_labels = sorted(data)
        values = [data[label] for label in sorted_labels]
        chart_width = 40 if wide else 28

        x, y = self._plot_bar_chart(values, height, chart_width)
        if len(data.keys()) > 12:
            x, y = start_x, y + _SMALL_SPACING
        else:
            x, y = x + _SMALL_SPACING, start_y + _SMALL_SPACING

        legend_start_x = x + _MEDIUM_SPACING if wide else start_x + 30
        legend_start_y = start_y + _SMALL_SPACING if height >= 30 else start_y - 1

        legend_labels = [f"{key} ({data[key]:.2f})" for key in sorted_labels]
        x, y = self.legend(legend_labels, legend_start_x, legend_start_y, caption)
        end_x = x
        if start_x == self.l_margin:
            self.set_xy(end_x + _LARGE_SPACING, start_y)
        else:
            self.set_xy(self.l_margin, y + _LARGE_SPACING)
        return end_x, y

    def pie_chart(
        self,
        data: dict[str, float],
        caption: str,
        height: float = 70,
    ) -> tuple[float, float]:
        """Generate a pie chart in-memory and insert it into the PDF."""
        self._break_page_if_needed(height)

        self.set_x(self.x - _SMALL_SPACING)
        img_buf = build_pie_chart_bytes(
            list(data.values()), colors=self.style.chart_colors
        )

        if img_buf is None:
            return self.x, self.y

        start_x = self.x
        x, y = self.x, self.y
        self.image(img_buf, x=x, y=y, w=height)
        self.set_xy(x + height, y)

        if len(data.keys()) > 12:
            legend_x, legend_y = start_x, y + height + _SMALL_SPACING
        else:
            legend_x = x + height + _MEDIUM_SPACING
            legend_y = y + _SMALL_SPACING
        legend_labels = [f"{key} ({data[key]})" for key in data.keys()]
        end_x, end_y = self.legend(legend_labels, legend_x, legend_y, caption)
        if x <= self.l_margin:
            self.set_xy(end_x + _LARGE_SPACING, y)
        else:
            self.set_xy(self.l_margin, y + height + _LARGE_SPACING)
        return end_x, end_y

    def legend(
        self, labels: list[str], x: float, y: float, caption: str
    ) -> tuple[float, float]:
        self.set_xy(x, y)
        self.set_font(FONT_FAMILY, "", 9)
        self.cell(0, 5, caption, align="L", new_y=YPos.NEXT)
        legend_start_y = self.y + _SMALL_SPACING
        next_column_x = x + _SMALL_SPACING
        max_y = y

        legend_colors = self.style.chart_colors
        for idx, label in enumerate(labels):
            if idx % 4 == 0:
                self.set_xy(next_column_x, legend_start_y)
            color = legend_colors[idx % len(legend_colors)]
            x, y = self.legend_label(color, label)
            next_column_x = max(next_column_x, x + _LARGE_SPACING)

            max_y = max(max_y, y)

        return next_column_x, max_y

    def legend_label(
        self, color: tuple[int, int, int], label: str
    ) -> tuple[float, float]:
        """
        Generates a legend label with a colored dot. The label object has the height of 5mm.
        :param color: the color of the dot
        :param label: the text of the label
        :return: the position of the bottom right corner of the label
        """
        start_x, start_y = self.x, self.y
        self.set_fill_color(*color)
        self.ellipse(start_x + 1, start_y + 1.5, 2, 2, style="F")
        self.set_x(start_x + 3)
        self.set_font(FONT_FAMILY, size=LABEL_SIZE)
        self.set_text_color(*self.style.font_color)
        text_length = self.get_string_width(label)
        self.cell(15, 5, label, new_y=YPos.NEXT)
        self.set_font(FONT_FAMILY, size=TEXT_SIZE)
        self.set_x(start_x)
        return start_x + text_length, self.y

    def accent_card(
        self, accent_color: tuple[int, int, int], width: float, height: float
    ) -> None:
        self.set_draw_color(*self.style.border_color)
        self.rect(
            self.x,
            self.y,
            width,
            height,
            style="D",
            round_corners=True,
            corner_radius=2,
        )

        self.set_fill_color(*accent_color)
        self.rect(
            self.x,
            self.y,
            2,
            height,
            style="F",
            round_corners=True,
            corner_radius=2.2,
        )

    def bar_chart_with_limit(
        self, data: dict[str, float], limit: float, caption: str, height: float
    ) -> tuple[float, float]:
        self._break_page_if_needed(height)
        start_x, start_y = self.x, self.y
        x, y = self._plot_bar_chart_with_limit(list(data.values()), height, limit)
        if len(data.keys()) > 12:
            x, y = start_x, y + _SMALL_SPACING
        else:
            x, y = x + _SMALL_SPACING, start_y + _SMALL_SPACING

        legend_labels = [f"{key} ({data[key]:.2f})" for key in data.keys()]
        x, y = self.legend(legend_labels, x, y, caption)
        end_x = self.x
        if start_x == self.l_margin:
            self.set_xy(self.x + _LARGE_SPACING, start_y)
        else:
            self.set_xy(self.l_margin, y + _LARGE_SPACING)
        return end_x, y

    def _plot_bar_chart_with_limit(
        self, values: list[float], height: float, limit: float
    ) -> tuple[float, float]:
        spacing = 2
        bar_width = 3
        start_x = self.x
        start_y = self.y
        max_value = max(max(values), limit) if values else 0
        x = start_x + spacing

        for index, value in enumerate(values):
            if value > 0:
                self.set_fill_color(
                    *self.style.chart_colors[index % len(self.style.chart_colors)]
                )
                bar_height = height * value / max_value
                y = start_y + height - bar_height
                if bar_height > 1.5:
                    self.rect(
                        x,
                        y,
                        bar_width,
                        bar_height,
                        style="F",
                        round_corners=True,
                        corner_radius=1.5,
                    )
            x += bar_width + spacing

        limit_line_y = start_y + height - height * limit / max_value
        self.set_draw_color(*self.style.priority_color)
        self.set_line_width(0.4)
        self.line(start_x, limit_line_y, x - spacing, limit_line_y)
        self.set_line_width(0.2)
        return x - spacing, start_y + height
