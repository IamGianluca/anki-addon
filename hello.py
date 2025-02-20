# import the main window object (mw) from aqt
from aqt import mw

# import the "show info" tool from utils.py
from aqt.utils import showInfo

# import all of the Qt GUI library
try:
    from PyQt6.QtGui import QAction
except ImportError:
    from PyQt5.QtGui import QAction
from aqt.qt import qconnect

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.


def test_function() -> None:
    # get the number of cards in the current collection, which is stored in
    # the main window
    card_count = mw.col.card_count()
    # show a message box
    showInfo("Card count: %d" % card_count)


# create a new menu item, "Count cards" and assign a functionality to it
action = QAction("Count cards", mw)
qconnect(action.triggered, test_function)
mw.form.menuTools.addAction(action)
