# -*- coding: utf-8 -*-
"""
Anki Add-on: Progress Bar

Shows progress in the Reviewer in terms of passed cards per session.

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

# Do not modify the following lines
from __future__ import unicode_literals
from anki.lang import _, ngettext

from anki.hooks import addHook, wrap
from anki import version as anki_version

from aqt.qt import *
from aqt import mw

__version__ = '1.3.0'

############## USER CONFIGURATION START ##############

# CARD TALLY CALCULATION

# Which queues to include in the progress calculation (all True by default)
includeNew = True
includeRev = True
includeLrn = True

# Only include new cards once reviews are exhausted.
includeNewAfterRevs = True

# Limit count to your review settings as opposed to deck overall
limitToReviewSettings = True

# PROGRESS BAR APPEARANCE

showPercent = False # Show the progress text percentage or not.
showNumber = False # Show the progress text as a fraction


qtxt = "aliceblue" # Percentage color, if text visible.
qbg = "#18adab" # Background color of progress bar.
qfg = "#38e3b2" # Foreground color of progress bar.
qbr = 0 # Border radius (> 0 for rounded corners).

# optionally restricts progress bar width
maxWidth = ""  # (e.g. "5px". default: "")

orientationHV = Qt.Horizontal # Show bar horizontally (side to side). Use with top/bottom dockArea.
# orientationHV = Qt.Vertical # Show bar vertically (up and down). Use with right/left dockArea.

invertTF = False # If set to True, inverts and goes from right to left or top to bottom.

dockArea = Qt.TopDockWidgetArea # Shows bar at the top. Use with horizontal orientation.
#dockArea = Qt.BottomDockWidgetArea # Shows bar at the bottom. Use with horizontal orientation.
#dockArea = Qt.RightDockWidgetArea # Shows bar at right. Use with vertical orientation.
#dockArea = Qt.LeftDockWidgetArea # Shows bar at left. Use with vertical orientation.

pbStyle = "" # Stylesheet used only if blank. Else uses QPalette + theme style.
'''pbStyle options (insert a quoted word above):
    -- "plastique", "windowsxp", "windows", "windowsvista", "motif", "cde", "cleanlooks"
    -- "macintosh", "gtk", or "fusion" might also work
    -- "windowsvista" unfortunately ignores custom colors, due to animation?
    -- Some styles don't reset bar appearance fully on undo. An annoyance.
    -- Themes gallery: http://doc.qt.io/qt-4.8/gallery.html'''

##############  USER CONFIGURATION END  ##############

## Set up variables

nm = 0
failed = 0
progressBar = None
mx = 0
limitedBarLength = 0

pbdStyle = QStyleFactory.create("%s" % (pbStyle)) # Don't touch.

#Defining palette in case needed for custom colors with themes.
palette = QPalette()
palette.setColor(QPalette.Base, QColor(qbg))
palette.setColor(QPalette.Highlight, QColor(qfg))
palette.setColor(QPalette.Button, QColor(qbg))
palette.setColor(QPalette.WindowText, QColor(qtxt))
palette.setColor(QPalette.Window, QColor(qbg))

if maxWidth:
    if orientationHV == Qt.Horizontal:
        restrictSize = "max-height: %s;" % maxWidth
    else:
        restrictSize = "max-width: %s;" % maxWidth
else:
    restrictSize = ""

try:
    # Remove that annoying separator strip if we have Night Mode, avoiding conflicts with this add-on.
    import Night_Mode
    Night_Mode.nm_css_menu \
    += Night_Mode.nm_css_menu \
    + '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    '''
except ImportError:
    failed = 1


def nmc():
    """Checks whether Night_Mode is disabled:
        if so, we remove the separator here."""
    global nm
    if not failed:
        nm = Night_Mode.nm_state_on
    if not nm:
        mw.setStyleSheet(
    '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    ''')

def getMX():
    return 200

def getCurrent():
    """Get deck's card counts for progress bar updates."""
    mx = getMX()
    cards, thetime = mw.col.db.first("""
select count(), sum(time)/1000 from revlog
where id > ?""", (mw.col.sched.dayCutoff-86400)*1000)
    while(cards > mx):
        cards -= mx
    return cards

def _dock(pb):
    """Dock for the progress bar. Giving it a blank title bar,
        making sure to set focus back to the reviewer."""
    dock = QDockWidget()
    tWidget = QWidget()
    dock.setObjectName("pbDock")
    dock.setWidget(pb)
    dock.setTitleBarWidget( tWidget )
    
    ## Note: if there is another widget already in this dock position, we have to add ourself to the list

    # first check existing widgets
    existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]

    # then add ourselves
    mw.addDockWidget(dockArea, dock)

    # stack with any existing widgets
    if len(existing_widgets) > 0:
        mw.setDockNestingEnabled(True)

        if dockArea == Qt.TopDockWidgetArea or dockArea == Qt.BottomDockWidgetArea:
            stack_method = Qt.Vertical
        if dockArea == Qt.LeftDockWidgetArea or dockArea == Qt.RightDockWidgetArea:
            stack_method = Qt.Horizontal
        mw.splitDockWidget(existing_widgets[0], dock, stack_method)

    if qbr > 0 or pbdStyle != None:
        # Matches background for round corners.
        # Also handles background for themes' percentage text.
        mw.setPalette(palette)
    mw.web.setFocus()
    return dock


def pb():
    """Initialize and set parameters for progress bar, adding it to the dock."""
    mx = getMX()
    progressBar = QProgressBar()
    progressBar.setRange(0, mx)
    progressBar.setTextVisible(showPercent or showNumber)
    progressBar.setInvertedAppearance(invertTF)
    progressBar.setOrientation(orientationHV)
    if pbdStyle == None:
        progressBar.setStyleSheet(
        '''
                    QProgressBar
                {
                    text-align:center;
                    color:%s;
                    background-color: %s;
                    border-radius: %dpx;
                    %s
                }
                    QProgressBar::chunk
                {
                    background-color: %s;
                    margin: 0px;
                    border-radius: %dpx;
                }
                ''' % (qtxt, qbg, qbr, restrictSize, qfg, qbr))
    else:
        progressBar.setStyle(pbdStyle)
        progressBar.setPalette(palette)
    _dock(progressBar)
    return progressBar, mx



def _updatePB():
    """Update progress bar; hiding/showing prevents flashing bug."""
    if progressBar:
        nmc()

        curr = getCurrent()
        progressBar.hide()
            
        if showNumber:
            if showPercent:
                percent = 100 if barSize==0 else int(100*curr/barSize)
                progressBar.setFormat("%d / %d (%d%%)" % (curr, barSize, percent))
            else:
                progressBar.setFormat("%d / %d" % (curr, barSize))
        
        progressBar.setValue(curr)
        progressBar.show()



def _renderBar(state, oldState):
    global mx, progressBar
    if state == "overview":
        # Set up progress bar at deck's overview page: initialize or modify.
        progressBar, mx = pb()
        if showNumber:
            _updatePB()
        progressBar.show()
        nmc()
    elif state == "deckBrowser":
        # Hide the progress bar at deck list. Not deleted, so we just modify later.
        if progressBar:
            progressBar.hide()




addHook("afterStateChange", _renderBar)
addHook("showQuestion", _updatePB)

