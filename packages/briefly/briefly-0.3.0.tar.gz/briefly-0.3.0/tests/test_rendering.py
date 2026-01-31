from datetime import date
from unittest.mock import MagicMock, call

import pytest
from fpdf import XPos, YPos

from briefly.model.style import NotionStyle
from briefly.rendering.graphs import build_pie_chart_bytes
from briefly.rendering.icons import DUE_DATE_ICON
from briefly.rendering.pdf_generator import PDF


@pytest.fixture
def pdf() -> PDF:
    pdf = PDF(NotionStyle())
    pdf.add_page()
    return pdf


@pytest.fixture
def data() -> dict[str, float]:
    return {
        "one": 12,
        "two": 0,
        "three": 30,
        "four": 55,
    }


def test_graph_with_no_data_returns_none():
    assert build_pie_chart_bytes([0, 0, 0]) is None


def test_graph():
    assert build_pie_chart_bytes([1, 2, 3]) is not None


def test_graph_with_negative_values():
    with pytest.raises(ValueError):
        build_pie_chart_bytes([-1, -2, -3])


def test_header(pdf: PDF):
    pdf.main_title("TEST - Header")
    assert pdf.font_family == "inter"
    assert pdf.get_y() == 55
    assert pdf.get_x() == 25


def test_section_title(pdf: PDF):
    pdf.section_title("Test section")
    assert pdf.font_family == "inter"
    assert pdf.font_size_pt == 10
    assert pdf.get_y() == 45
    assert pdf.get_x() == 25


def test_summary_card(pdf: PDF):
    (x, y) = pdf.summary_card(["Test summary card"])
    assert pdf.font_family == "inter"
    assert pdf.font_size_pt == 10
    assert x == 105
    assert y == 25 + 6 + 10


def test_styled_table(pdf: PDF):
    pdf.styled_table(
        ["header1", "header2", "header3", "header4"],
        [
            ["asd", "asd", "asd", "asd"],
            ["asd", "asd", "asd", "asd"],
            ["asd", "asd", "asd", "asd"],
        ],
        [30, 15, 20, 5],
    )
    assert pdf.font_family == "inter"
    assert pdf.font_size_pt == 7
    assert pdf.get_x() == 25
    assert pdf.get_y() == 66


def test_tag(pdf: PDF):
    width, height = pdf.tag("Test tag")
    assert pdf.font_family == "inter"
    assert pdf.font_size_pt == 7
    assert width == pytest.approx(13.15, 0.01)
    assert height == 5


def test_pie_chart(pdf: PDF, data: dict[str, float]):
    x, y = pdf.pie_chart(data, "Test Pie Chart")
    assert pdf.font_family == "inter"
    assert pdf.font_size_pt == 10
    assert x == pytest.approx(121, 0.1)
    assert y == 54


def test_task_card_with_all_properties(pdf: PDF):
    task_id = "TEST-1234"
    status = "In Progress"
    due_date = date(2025, 1, 3)
    flagged = True
    priority = 1
    estimate = 5
    title = "Test task"
    link = "link"

    pdf.cell = MagicMock()
    pdf.accent_card = MagicMock()
    pdf._two_line_label = MagicMock()
    pdf._two_line_label.return_value = 30, 30
    pdf._priority_icons = MagicMock()
    pdf._priority_icons.return_value = 30, 30
    pdf._small_label = MagicMock()
    pdf._small_label.return_value = 30, 30
    pdf._flagged_icon = MagicMock()
    pdf._task_title = MagicMock()
    pdf.task_card(task_id, title, status, due_date, priority, estimate, flagged, link)

    pdf.accent_card.assert_called_once_with((252, 216, 212), 77.5, 30)
    pdf._two_line_label.assert_called_once_with(status, 37.5, 35)
    pdf._priority_icons.assert_called_once_with(priority, flagged, 36, 31)
    pdf._flagged_icon.assert_called_once_with(36, 31)
    pdf._task_title.assert_called_once_with(title, 52.5, 29, link=link)

    label_calls = [call("SP: 5", 30, 31), call("03.01.2025", 37.5, 31)]
    pdf._small_label.assert_has_calls(label_calls, any_order=True)
    cell_calls = [
        call(15, 5, task_id, align="R", link=link, new_x=XPos.LEFT, new_y=YPos.NEXT),
        call(3, 5, DUE_DATE_ICON, align="L"),
    ]
    pdf.cell.assert_has_calls(cell_calls, any_order=True)
