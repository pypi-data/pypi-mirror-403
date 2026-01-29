"""
PPrint.py
Author: Tyler Black

    Print homework solutions in an organized manner, with automatic problem tracking,
    and options for multiple parts.

Usage:
    - Just call PPrint.log. Do not instantiate PPrint. Problem number will be statically
      tracked. Turn off bounding boxes by setting bbox_on=False in method call.
    - Manually change problem number using PPrint.update_problem_num(int).
    - Change max line length using PPrint.set_max_line_len(int).
    - NOTE: "\t" is not supported.

    Input:
        from tylerproblemprint import PPrint

        PPrint.log(
            a=1123.45,
            b="Supports any type",
            weird_key="Use any key name",

            space="",
            for_spaces="use the key word 'space' or 'sp'",

            null="Just the value",
            null1="Just the value again",

            rounding="must be done manually",
            x=np.round(0.12345, 2),
        )

    Output:
        ╔══════════════════════════════════════════════╗
        ║ Problem 1                                    ║
        ╠══════════════════════════════════════════════╣
        ║ a: 1123.45                                   ║
        ║ b: Supports any type                         ║
        ║ weird_key: Use any key name                  ║
        ║                                              ║
        ║ for_spaces: use the key word 'space' or 'sp' ║
        ║ Just the value                               ║
        ║ Just the value again                         ║
        ║ rounding: must be done manually              ║
        ║ x: 0.12                                      ║
        ╚══════════════════════════════════════════════╝

"""

from enum import Enum


class Side(Enum):
    UPPER = 0
    LOWER = 1
    MIDDLE = 2

_framings = {
    "h": '═',
    "v": '║',
    "ulc": '╔',
    "urc": '╗',
    "llc": '╚',
    'lrc': '╝',
    'mlc': '╠',
    'mrc': '╣'
}


def _print_bounding_row(l: int, s: Side, bbox_on: bool = True):
    side_frame: tuple[str, str]
    match s:
        case Side.UPPER:
            side_frame = (_framings["ulc"], _framings["urc"])
        case Side.LOWER:
            side_frame = (_framings["llc"], _framings["lrc"])
        case Side.MIDDLE:
            side_frame = (_framings["mlc"], _framings["mrc"])
        case _:
            raise ValueError("Invalid side")

    for i in range(l):
        if i == 0:
            print((side_frame[0] if bbox_on else _framings['h']), end="")
        elif i == l - 1:
            print(side_frame[1] if bbox_on else _framings['h'])
        else:
            print(_framings["h"], end="")


def _print_text_row(text: str, max_len: int, bbox_on: bool = True):
    print_len = max_len - len(text)
    for i in range(print_len):
        if i == 0 or i == print_len - 1:
            print((_framings["v"] if bbox_on else " "), end="")
        if i == 1:
            print(text, end="")
        else:
            print(" ", end="")
    print()


class PPrint:
    _problem_num = 1
    _max_line_len = 100   # can go up to 3 digits wider than this!

    @classmethod
    def change_problem_num(cls, problem_num: int):
        cls._problem_num = problem_num

    @classmethod
    def set_max_line_len(cls, max_line_len: int):
        cls._max_line_len = max_line_len

    @classmethod
    def log(cls, bbox_on: bool=True, **kwargs):
        # strings
        problem_num_str = "Problem " + str(cls._problem_num) + " "
        subsections: list[str] = []

        # adjust for special cases
        for k, v in kwargs.items():
            k = str(k)
            v = str(v)
            kv_str: str

            # space / new line
            if k == "space" or k == "sp":
                subsections.append(" ")
                continue

            # null key, just use value
            if k.startswith("null"):
                kv_str = v

            # normal kv_str
            else:
                kv_str = k + ": " + v

            # add subsection in pieces if too long to fit on one line
            if len(kv_str) > cls._max_line_len:
                start = 0
                end = cls._max_line_len

                # add subsections in pieces
                while True:
                    end = kv_str.rfind(" ", start, end)
                    if start == 0:
                        subsections.append(kv_str[start:end])
                    else:
                        subsections.append("   " + kv_str[start:end])
                    start = end + 1
                    end += cls._max_line_len

                    if end > len(kv_str):
                        subsections.append("   " + kv_str[start:])
                        break


            # normal length
            else:
                subsections.append(kv_str)

        # get lengths of things
        max_text_len = max(len(problem_num_str), len(max(subsections, key=len)))
        bbox_width = max_text_len + 4

        ## printing
        # first row
        if bbox_on:
            _print_bounding_row(bbox_width, Side.UPPER)
        # problem number row
        _print_text_row(problem_num_str, bbox_width, bbox_on)
        # middle row (below problem number)
        _print_bounding_row(bbox_width, Side.MIDDLE, bbox_on)
        # arg rows
        for ss in subsections:
            _print_text_row(ss, bbox_width, bbox_on)
        # last row
        if bbox_on:
            _print_bounding_row(bbox_width, Side.LOWER)
        print()
        cls._problem_num += 1


if __name__ == "__main__":
    import numpy as np

    PPrint.set_max_line_len(100)

    PPrint.log(
        a=1123.45,
        b="Supports any type",
        weird_key="Use any key name",
        space="",
        for_spaces="use the key word 'space' or 'sp'",
        null="Just the value",
        null1="Just the value again",
        rounding="must be done manually",
        x=np.round(0.12345, 2),
    )
