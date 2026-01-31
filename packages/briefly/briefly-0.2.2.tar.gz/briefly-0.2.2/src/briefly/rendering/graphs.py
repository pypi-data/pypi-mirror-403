from io import BytesIO
from typing import Optional

from matplotlib import pyplot as plt

NOTION_CHART_COLORS = [
    (155, 207, 87),  # green
    (246, 199, 68),  # yellow
    (108, 155, 245),  # blue
    (221, 148, 255),  # purple
    (255, 170, 153),  # coral
    (181, 181, 181),  # gray
]


def build_pie_chart_bytes(
    values: list[float],
    size: float = 35,
    colors: Optional[list[tuple[int, int, int]]] = None,
) -> Optional[BytesIO]:
    """
    Return a PNG image as bytes for a pie chart.
    :param values: The values to plot
    :param size: The size of the chart in mm
    :param colors: Optional list of colors to use for each value
    :return: the bytes of the chart or None if there are no values
    """

    size_inch = size / 25.4

    if sum(values) == 0:
        return None

    fig, ax = plt.subplots(figsize=(size_inch, size_inch))
    colors = colors or NOTION_CHART_COLORS
    graph_colors = [(r / 255, g / 255, b / 255) for r, g, b in colors[: len(values)]]
    ax.pie(values, colors=graph_colors, startangle=90, counterclock=False)

    buf = BytesIO()
    plt.tight_layout(pad=0)
    plt.savefig(buf, format="png", dpi=200, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf
