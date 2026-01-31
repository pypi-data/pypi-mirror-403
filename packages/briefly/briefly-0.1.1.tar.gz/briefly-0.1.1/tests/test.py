import pytest

from briefly.model.style import MochaStyle
from briefly.rendering.pdf_generator import PDF

DARK_BACKGROUND = (38, 33, 43)


@pytest.mark.skip(reason="Manually run")
def test():
    style = MochaStyle()
    pdf = PDF(style)
    pdf.add_page()

    pdf.main_title("JIRA Summary Test")

    pdf.section_title("Overview")
    pdf.summary_card(
        ["Total Tickets: 58", "Completed: 42", "In Progress: 10", "Blocked: 6"],
        width=50,
    )

    pdf.summary_card(
        ["Total Tickets: 58", "Completed: 42", "In Progress: 10", "Blocked: 6"],
        width=50,
    )

    (_, y) = pdf.summary_card(
        ["Total Tickets: 58", "Completed: 42", "In Progress: 10", "Blocked: 6"],
        width=50,
    )

    pdf.set_y(y + 10)

    pdf.styled_table(
        headers=["Key", "Summary", "Status", "Assignee"],
        rows=[
            ["PROJ-101", "Fix login flow", "Done", "Alice"],
            ["PROJ-102", "Add metrics dashboard", "In Progress", "Bob"],
            ["PROJ-103", "Payment gateway issue", "Blocked", "Eve"],
        ],
        col_widths=[20, 80, 30, 30],
    )

    data = {
        "cat1": 10,
        "cat3": 8,
        "cat2": 5,
        "cat4": 3,
        "cat5": 2,
        "cat6": 20,
        "cat7": 15,
        "cat8": 10,
    }

    pdf.bar_chart(data, caption="Categories", height=30)

    pdf.pie_chart(
        data,
        height=30,
        caption="Categories",
    )

    pdf.pie_chart(
        data,
        height=30,
        caption="Categories",
    )

    pdf.bar_chart(data, caption="Categories", height=30)
    pdf.bar_chart(data, caption="Categories", height=30)
    pdf.output("./output/test.pdf")
