# -*- coding: utf-8 -*-

"""
Anki Add-on: Remove UI elements when reviewing
"""

from anki.hooks import addHook
from aqt import mw
from os import path
from aqt.deckbrowser import DeckBrowser
from anki.hooks import wrap
from aqt.reviewer import Reviewer

this_script_dir = path.dirname(__file__)
user_css_path = path.join(this_script_dir, 'user_bottom_buttons.css')


with open(user_css_path, encoding='utf-8') as f:
    bottom_buttons_css = f.read()

js_append_css_toolbar = "$('head').append(`<style>body {{ display: {};}}</style>`);"
js_append_css = f"$('head').append(`<style>{bottom_buttons_css}</style>`);"

def reviewer_ui(*args, **kwargs):
    mw.toolbar.web.eval(js_append_css_toolbar.format('none'))
    mw.menuBar().hide()
    mw.toolbar.web.setFixedHeight(0)
    mw.reviewer.bottom.web.eval(js_append_css)
    



def main_ui(*args, **kwargs):
    mw.menuBar().show()
    mw.toolbar.web.eval(js_append_css_toolbar.format('inline'))
    mw.toolbar.web.setFixedHeight(30)




DeckBrowser._renderPage = wrap(DeckBrowser._renderPage, main_ui)
Reviewer._initWeb = wrap(Reviewer._initWeb, reviewer_ui)


