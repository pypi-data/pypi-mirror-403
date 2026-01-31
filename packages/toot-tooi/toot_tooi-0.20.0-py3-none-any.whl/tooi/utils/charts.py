from datetime import date

from textual.content import Content


def date_bar_chart(
    dates: list[date],
    values: list[int],
    bar_height: int = 5,
    col_spacing: int = 1,
) -> Content:
    full_block = "█"
    sub_blocks = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇"]
    col_spacer = " " * col_spacing

    if not dates or not values:
        return Content()

    if len(dates) != len(values):
        return Content()

    max_value = max(values)
    if max_value == 0:
        return Content()

    stacks: list[list[str]] = []
    for value in values:
        height = round(8 * bar_height * value / max_value)
        full_blocks = height // 8
        remainder = height % 8

        stack = [full_block] * full_blocks
        if remainder:
            stack += sub_blocks[remainder]
        stacks.append(stack)

    bars = ""
    for row in range(bar_height):
        index = bar_height - row - 1
        line = ""
        for stack in stacks:
            block = stack[index] if index < len(stack) else " "
            line += " " + block * 4 + " " + col_spacer
        bars += line.rstrip() + "\n"

    dates_line = col_spacer.join(date.strftime("%b %d") for date in dates)
    values_line = col_spacer.join(f"{value:^6d}" for value in values)

    return Content.from_markup(f"[$primary]{bars}[/$primary]{dates_line}\n{values_line}")
