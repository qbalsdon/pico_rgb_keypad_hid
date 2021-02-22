# SPDX-FileCopyrightText: 2020 Tim C for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Display Text module helper functions
"""


def wrap_text_to_lines(string, max_chars):
    """wrap_text_to_lines function
    A helper that will return a list of lines with word-break wrapping

    :param str string: The text to be wrapped
    :param int max_chars: The maximum number of characters on a line before wrapping

    :return list the_lines: A list of lines where each line is separated based on the amount
        of max_chars provided

    """

    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    string = string.replace("\n", "").replace("\r", "")  # Strip confusing newlines
    words = string.split(" ")
    the_lines = []
    the_line = ""
    for w in words:
        if len(w) > max_chars:
            if the_line:  # add what we had stored
                the_lines.append(the_line)
            parts = []
            for part in chunks(w, max_chars - 1):
                parts.append("{}-".format(part))
            the_lines.extend(parts[:-1])
            the_line = parts[-1][:-1]
            continue

        if len(the_line + " " + w) <= max_chars:
            the_line += " " + w
        elif not the_line and len(w) == max_chars:
            the_lines.append(w)
        else:
            the_lines.append(the_line)
            the_line = "" + w
    if the_line:  # Last line remaining
        the_lines.append(the_line)
    # Remove any blank lines
    while not the_lines[0]:
        del the_lines[0]
    # Remove first space from first line:
    if the_lines[0][0] == " ":
        the_lines[0] = the_lines[0][1:]
    return the_lines
