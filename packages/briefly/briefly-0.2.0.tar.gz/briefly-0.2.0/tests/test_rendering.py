import pytest

from briefly.model.style import NotionStyle
from briefly.rendering.graphs import build_pie_chart_bytes
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
    assert pdf.font_size_pt == 13
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
