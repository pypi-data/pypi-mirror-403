"""String utilities."""

# Future Library
from __future__ import annotations

# Standard Library
import re
import string

from typing import Callable, Optional, TypeVar, cast, overload

# 1st Party Library
from rwskit.exceptions import raise_exception
from rwskit.resources_ import read_text

W = TypeVar("W", bound=Callable[..., Optional[str]])
"""A Callable that returns a string."""

# Note: An additional character map variable used to transliterate
# accents is defined and loaded at the bottom of this script

_dash_characters = [
    "\u2010",
    "\u2011",
    "\u2012",
    "\u2013",
    "\u2014",
    "\u2015",
    "\u2e3a",
    "\u2e3b",
    "\ufe58",
    "\ufe63",
    "\uff0d",
]
_dash_pattern = re.compile("[" + "".join(map(re.escape, _dash_characters)) + "]")

_whitespace_map = {
    "\u00a0": " ",  # non-breaking space
    "\u2000": " ",  # en quad
    "\u2001": " ",  # em quad
    "\u2002": " ",  # en space
    "\u2003": " ",  # em space
    "\u2004": " ",  # three-per-em space
    "\u2005": " ",  # four-per-em space
    "\u2006": " ",  # six-per-em space
    "\u2007": " ",  # figure space
    "\u2008": " ",  # punctuation space
    "\u2009": " ",  # thin space
    "\u200a": " ",  # hair space
    "\u3000": " ",  # ideographic space
}


def camel_to_snake_case(s: str) -> str:
    """Convert the string from CamelCase to snake_case.

    This method uses a simple regular expression to convert a string
    in CamelCase to one in snake_case. Strings with 2 or fewer
    are simply lowercased and returned.

    Parameters
    ----------
    s : str
        The string to convert.

    Returns
    -------
    str
        The string in snake case.
    """
    # There are a number of approaches for converting CamelCase to snake_case
    # enumerated at
    # https://www.geeksforgeeks.org/python-program-to-convert-camel-case-string-to-snake-case/
    # However, the only one that passes all my unit tests is method #4 (regex).
    # The "naive" approach below also passes all the unit tests, is also
    # faster than any of the other listed methods (while #4 is the slowest).
    # See this post for some additional regex approaches:
    # https://stackoverflow.com/a/1176023
    if not s:
        return s

    if len(s) <= 2:
        return s.lower()

    # What will be the previous and next character
    p, c = s[0], s[1]

    # The array to store the result in.
    snake = [p]

    # The iterated variable represents the next character
    for n in s[2:]:
        # If the current character is uppercase and the next character
        # is not, then we'll start a new "word"
        if p.isalpha() and c.isupper() and not n.isupper():
            snake.append("_")

        snake.append(c)

        # Update the previous and next characters
        p, c = c, n

    snake.append(c)

    return "".join(snake).lower()


@overload
def normalize_whitespace(string_or_function: None) -> None: ...
@overload
def normalize_whitespace(string_or_function: str) -> str: ...
@overload
def normalize_whitespace(string_or_function: W) -> W: ...


def normalize_whitespace(string_or_function):
    """A function or decorator normalizes whitespace in a string.

    The primary functionality of this method will convert the following
    whitespace characters to a single ascii space (code 32). It will then
    replace all repeating whitespace characters with a single whitespace and
    trim any remaining whitespace from the front and back of the string.

    Normalized whitespace characters:

    ===== ==================
    Code    Type
    ===== ==================
    u0020 space
    u00a0 non-breaking space
    u2000 en quad
    u2001 em quad
    u2002 en space
    u2003 em space
    u2004 three-per-em space
    u2005 four-per-em space
    u2006 six-per-em space
    u2007 figure space
    u2008 punctuation space
    u2009 thin space
    u200a hair space
    u3000 ideographic space
    ===== ==================

    This function can either work as a decorator (i.e., if its argument is
    a callable) or as a regular function if the argument is a string.

    Parameters
    ----------
    string_or_function : Optional[str] | Callable[..., str]
        The string or callable function to normalize.

    Returns
    -------
    Optional[str] | Callable[..., str]
        ``None`` is returned if the argument is ``None``. If the argument
        is a string, then the normalized string is returned. Otherwise, it
        is treated as a decorator and the wrapped function that will do the
        normalizing is returned.
    """
    if string_or_function is None:
        return None

    # The primary functionality of the function
    def _normalize_whitespace(txt: Optional[str]) -> Optional[str]:
        if txt is None:
            return None

        # Convert all whitespace characters, e.g., tabs, newlines, unicode
        # spaces (including non-breaking spaces) to a standard ' ' space.
        transliterated = "".join([_whitespace_map.get(c, c) for c in txt])

        # Remove consecutive spaces with a single space and trim spaces from
        # the ends of strings.
        normalized = re.sub(r"\s+", " ", transliterated).strip()

        return normalized

    # If the argument is a callable, create a decorator
    if callable(string_or_function):
        fn = cast(Callable[..., str], string_or_function)

        def _wrapper(*args, **kwargs):
            return _normalize_whitespace(fn(*args, **kwargs))

        return _wrapper

    # Otherwise, normalize the whitespace directly and return the string.
    return _normalize_whitespace(string_or_function)


def transliterate_accents(s: str) -> str:
    """Try to replace accented characters with an ASCII equivalent.

    Note this may not preserve the length of the input string.

    Parameters
    ----------
    s: str
        The input string.

    Returns
    -------
    str
        A string with accent characters transliterated to an ASCII equivalent.
    """
    return "".join(_transliterate_map.get(c, c) for c in s)


def normalize_dashes(s: Optional[str]) -> Optional[str]:
    """Replace Unicode dash characters with an ASCII ``Hyphen-Minus``.

    The following dash characters are replaced:

    ===== ======= =======================
    Code    Char    Type
    ===== ======= =======================
    u2010 ‐       Hyphen
    u2011 ‑       Non-Breaking Hyphen
    u2012 ‒       Figure Dash
    u2013 –       En Dash
    u2014 —       Em Dash
    u2015 ―       Horizontal Bar
    u2e3a ⸺       Two-Em Dash
    u2e3b ⸻       Three-em Dash
    ufe58 ﹘       Small Em Dash
    ufe63 ﹣       Small Hyphen-Minus
    uff0d －       Full width Hyphen-Minus
    ===== ======= =======================

    Parameters
    ----------
    s : string, optional
        The string to normalize.

    Returns
    -------
    str
        The normalized string.
    """
    if s is None:
        return None

    return _dash_pattern.sub("-", s)


def strip_punctuation(s: str) -> str:
    """Strip punctuation from a string.

    Parameters
    ----------
    s : str
        The input string from which punctuation will be stripped.

    Returns
    -------
    str
        The modified string with all punctuation characters removed.

    """
    translator = str.maketrans("", "", string.punctuation)
    return s.translate(translator)


# region Utility Methods
def _load_accent_rules() -> dict[str, str]:
    current_package = __package__ or raise_exception("No package name detected")
    text_data = read_text(current_package, "transliterate_accent.rules")

    rules = dict()
    for line in text_data.splitlines():
        line = line.strip()
        if not line:
            continue

        tokens = line.split()

        rules[tokens[0]] = "" if len(tokens) == 1 else tokens[1]

    return rules


_transliterate_map: dict[str, str] = _load_accent_rules()
# endregion Utility Methods
