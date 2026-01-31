from .types import StrsType, LIST_TYPES
from .maths import chars_len, is_str_float
from .fills import add_fills
from .colors import COLOR_TYPE, colored, decolored
from .logs import logclr

from copy import deepcopy
from typing import Literal

HAT_COLOR = logclr.NOTE
HEADER_COLOR = logclr.MESG
CELL_COLOR = logclr.FILE
SEPR_COLOR = logclr.DBUG
BOUND_COLOR = logclr.DBUG
VERT_COLOR = logclr.DBUG
TOTAL_COLOR = logclr.OKAY

SEPR = "-"
CSEPR = colored(SEPR, SEPR_COLOR)
VERT = "|"
CVERT = colored(VERT, VERT_COLOR)
WERT = f" | "


def is_listable(val) -> bool:
    return isinstance(val, LIST_TYPES)


def norm_any_to_str_list(val) -> list[str]:
    if is_listable(val):
        return [str(v) for v in val]
    else:
        return [str(val)]


def norm_any_to_type_list(val) -> list[str]:
    if is_listable(val):
        return [type(v).__name__ for v in val]
    else:
        return [type(val).__name__]


def add_bounds(
    line: str,
    bound_char: str = VERT,
    is_colored: bool = False,
    bound_color: COLOR_TYPE = BOUND_COLOR,
) -> str:
    end_bound_char = bound_char[::-1]
    if not is_colored:
        return f"{bound_char} {line} {end_bound_char}"
    else:
        beg_bound_str = colored(bound_char, bound_color)
        end_bound_str = colored(end_bound_char, bound_color)
        return f"{beg_bound_str} {line} {end_bound_str}"


def align_to_fill_side(align: str) -> Literal["left", "right", "both"]:
    if align[0].lower() == "l":
        return "right"
    elif align[0].lower() == "r":
        return "left"
    else:
        return "both"


def determine_aligns_from_row(
    row: list, default_align: Literal["left", "right"] = "left"
) -> list[str]:
    aligns: list[str] = []
    for cell in row:
        if is_str_float(decolored(cell)):
            aligns.append("right")
        else:
            aligns.append(default_align)
    return aligns


def rows_to_table_str(
    rows: list[list],
    headers: list[str] = None,
    aligns: StrsType = None,
    default_align: Literal["left", "right"] = "left",
    sum_at_tail: bool = False,
    header_case: Literal["raw", "lower", "upper", "capitalize"] = "upper",
    header_wsch: Literal[" ", "_", "-", "", None] = "_",
    col_gap_len: int = 2,
    is_bounded: bool = False,
    bound_char: str = VERT,
    is_hatted: bool = True,
    hat_char: str = "=",
    is_colored: bool = True,
    hat_color: COLOR_TYPE = HAT_COLOR,
    header_color: COLOR_TYPE = HEADER_COLOR,
    cell_color: COLOR_TYPE = CELL_COLOR,
    sepr_color: COLOR_TYPE = SEPR_COLOR,
    bound_color: COLOR_TYPE = BOUND_COLOR,
) -> str:
    if not rows:
        return ""

    # set table headers and table rows
    if not headers:
        headers = norm_any_to_str_list(rows[0])
        table_rows = rows[1:]
    else:
        table_rows = rows[:]

    table_headers: list[str] = deepcopy(headers)

    if header_wsch is not None:
        table_headers = [h.replace(" ", header_wsch) for h in table_headers]

    # set header case
    hc = header_case.lower() if header_case else ""
    if hc.startswith("l"):
        table_headers = [h.lower() for h in table_headers]
    elif hc.startswith("u"):
        table_headers = [h.upper() for h in table_headers]
    elif hc.startswith("c"):
        table_headers = [h.capitalize() for h in table_headers]
    # else: raw

    cols = len(table_headers)

    # determine aligns
    if not aligns:
        aligns = determine_aligns_from_row(table_rows[-1], default_align=default_align)
    if len(aligns) < cols:
        aligns += [default_align] * (cols - len(aligns))

    # add total row
    is_sum_at_tail = sum_at_tail and cols > 1
    if is_sum_at_tail:
        sum_row: list[str] = []
        for i in range(cols):
            is_sum_valid = True
            col_sum = 0
            for row in table_rows:
                cell = row[i]
                if not cell or cell == "-":
                    continue
                elif isinstance(cell, (int, float)):
                    col_sum += cell
                elif cell.isdigit():
                    col_sum += int(cell)
                elif is_str_float(cell):
                    col_sum += float(cell)
                else:
                    is_sum_valid = False
                    break
            if is_sum_valid and col_sum != 0:
                sum_row.append(str(col_sum))
            else:
                sum_row.append("")
        if any(v for v in sum_row):
            is_sum_at_tail = True
            # prepend "Total" label to numeric columns
            for i in range(1, cols):
                if sum_row[i]:
                    sum_row[i - 1] = "Total"
                    break
            table_rows.append(sum_row)
        else:
            is_sum_at_tail = False

    # calc column widths
    table_headers_rows = [table_headers] + table_rows
    col_widths = [
        max(
            chars_len(decolored(row[i])) if i < len(row) else 0
            for row in table_headers_rows
        )
        for i in range(cols)
    ]

    # set colors
    sepr = SEPR
    if is_colored:
        table_headers = [colored(h, header_color) for h in table_headers]
        if is_sum_at_tail:
            colored_sum_row = [
                colored(cell, TOTAL_COLOR) if cell else cell for cell in table_rows[-1]
            ]
            colored_non_sum_rows = [
                [colored(cell, cell_color) for cell in row] for row in table_rows[:-1]
            ]
            table_rows = colored_non_sum_rows + [colored_sum_row]
        else:
            table_rows = [
                [colored(cell, cell_color) for cell in row] for row in table_rows
            ]
        sepr = colored(SEPR, sepr_color)

    # set sep lines and col chars
    sep_lines = [sepr * col_widths[i] for i in range(cols)]

    jcol = " " * col_gap_len
    col_join = jcol.join
    sep_join = (sepr * len(jcol)).join
    header_line_str = col_join(
        add_fills(
            text=table_headers[i],
            filler=" ",
            fill_side=align_to_fill_side(aligns[i]),
            is_text_colored=is_colored,
            total_width=col_widths[i],
        )
        for i in range(cols)
    )
    sep_line_str = sep_join(sep_lines)

    # add vertical bounds
    if is_bounded:
        header_line_str = add_bounds(
            header_line_str,
            bound_char=bound_char,
            is_colored=is_colored,
            bound_color=bound_color,
        )
        sep_line_str = add_bounds(
            sep_line_str,
            bound_char=bound_char,
            is_colored=is_colored,
            bound_color=bound_color,
        )

    # build row lines
    rows_lines = []
    for row in table_rows:
        row_line = col_join(
            add_fills(
                text=row[i],
                filler=" ",
                fill_side=align_to_fill_side(aligns[i]),
                is_text_colored=is_colored,
                total_width=col_widths[i],
            )
            for i in range(cols)
        )
        if is_bounded:
            row_line = add_bounds(
                row_line, bound_char=bound_char, is_colored=is_colored
            )
        rows_lines.append(row_line)

    # build final table string
    if is_sum_at_tail:
        row_lines_str = (
            "\n".join(rows_lines[:-1]) + f"\n{sep_line_str}\n{rows_lines[-1]}"
        )
    else:
        row_lines_str = "\n".join(rows_lines)

    table_str = f"{header_line_str}\n{sep_line_str}\n{row_lines_str}"

    # add hat
    if is_hatted:
        hat_len = chars_len(decolored(table_str.splitlines()[0]))
        hat_str = add_fills(filler=hat_char, total_width=hat_len)
        if is_colored:
            hat_str = colored(hat_str, hat_color)
        table_str = f"{hat_str}\n{table_str}\n{hat_str}"

    return table_str


def dict_to_rows(d: dict) -> list[list]:
    rows: list[list] = []
    for key, val in d.items():
        key_strs = norm_any_to_str_list(key)
        val_strs = norm_any_to_str_list(val)
        row = key_strs + val_strs
        rows.append(row)
    return rows


def dict_to_table_str(
    d: dict,
    key_headers: StrsType = None,
    val_headers: StrsType = None,
    aligns: StrsType = None,
    default_align: Literal["left", "right"] = "left",
    sum_at_tail: bool = False,
    header_case: Literal["raw", "lower", "upper", "capitalize"] = "upper",
    header_wsch: Literal[" ", "_", "-", "", None] = "_",
    col_gap_len: int = 2,
    is_bounded: bool = False,
    bound_char: str = VERT,
    is_hatted: bool = True,
    hat_char: str = "=",
    is_colored: bool = True,
    hat_color: COLOR_TYPE = HAT_COLOR,
    header_color: COLOR_TYPE = HEADER_COLOR,
    cell_color: COLOR_TYPE = CELL_COLOR,
    sepr_color: COLOR_TYPE = SEPR_COLOR,
    bound_color: COLOR_TYPE = BOUND_COLOR,
) -> str:
    if not d:
        return ""
    if not key_headers or not val_headers:
        k1, v1 = next(iter(d.items()))
        if not key_headers:
            key_headers = norm_any_to_str_list(k1)
        if not val_headers:
            val_headers = norm_any_to_str_list(v1)
    table_headers: list[str] = key_headers + val_headers
    table_rows = dict_to_rows(d)

    return rows_to_table_str(
        rows=table_rows,
        headers=table_headers,
        aligns=aligns,
        default_align=default_align,
        sum_at_tail=sum_at_tail,
        header_case=header_case,
        header_wsch=header_wsch,
        col_gap_len=col_gap_len,
        is_bounded=is_bounded,
        bound_char=bound_char,
        is_hatted=is_hatted,
        hat_char=hat_char,
        is_colored=is_colored,
        hat_color=hat_color,
        header_color=header_color,
        cell_color=cell_color,
        sepr_color=sepr_color,
        bound_color=bound_color,
    )
