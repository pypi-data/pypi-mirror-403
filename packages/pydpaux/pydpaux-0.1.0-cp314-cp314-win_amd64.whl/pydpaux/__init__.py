from __future__ import annotations

from ._core import __doc__, __version__, get_displays, Display

#Fined display with given keyword, support partial match
def find_display_by_name(kwd):
    for display in get_displays():
          if display.name.find(kwd) >= 0:
            return display

    return None


__all__ = ["__doc__", "__version__", "Display", "get_displays", "find_display_by_name"]