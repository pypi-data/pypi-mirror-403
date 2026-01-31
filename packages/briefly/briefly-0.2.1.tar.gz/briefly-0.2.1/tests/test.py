from datetime import date

import pytest

from briefly.model.style import PurpleHaze
from briefly.rendering.pdf_generator import PDF

DARK_BACKGROUND = (38, 33, 43)


@pytest.mark.skip(reason="Manually run")
def test():
    style = PurpleHaze()
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

    pdf.task_card(
        "TEST-123",
        "Analysis of performance issues",
        "In Progress",
        date(2025, 10, 12),
        1,
        8,
        link="https://google.com",
    )
    pdf.task_card(
        "TEST-421",
        "Refactoring of processing",
        "To Do",
    )

    pdf.task_card(
        "TEST-123",
        "A very very very very very very long and very very very very complex task",
        "In Progress",
        date(2025, 10, 12),
        3,
        8,
        link="https://google.com",
    )

    pdf.task_card(
        "TEST-123",
        "A very very very very very very long and very very very very complex task with some addition stuff",
        "In Progress",
        date(2025, 10, 12),
        2,
        21,
        flagged=True,
        link="https://google.com",
    )

    data = {
        "cat1": 10,
        "cat3": 8,
        "cat2": 5,
        "cat4": 3,
        "cat5": 2,
        "cat6": 20,
        "cat7": 15,
        "cat8": 120,
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
    pdf.bar_chart(data, caption="Categories", height=25, wide=True)
    pdf.output("./output/test.pdf")
