# -*- coding: utf-8 -*-
from collective.themefragments.interfaces import FRAGMENTS_DIRECTORY
from collective.themefragments.traversal import ThemeFragment
from os.path import splitext
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import getCurrentTheme
from plone.app.theming.utils import isThemeEnabled
from plone.resource.utils import queryResourceDirectory
from plone.supermodel import model
from plone.tiles import Tile
from zope import schema
from zope.globalrequest import getRequest
from zope.interface import provider
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('collective.themefragments')


@provider(IContextSourceBinder)
def themeFragments(context):
    request = getRequest()

    if not isThemeEnabled(request):
        return SimpleVocabulary([])

    currentTheme = getCurrentTheme()
    if currentTheme is None:
        return SimpleVocabulary([])

    themeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, currentTheme)
    if themeDirectory is None:
        return SimpleVocabulary([])

    if not themeDirectory.isDirectory(FRAGMENTS_DIRECTORY):
        return SimpleVocabulary([])

    fragments = [splitext(filename)[0] for filename
                 in themeDirectory[FRAGMENTS_DIRECTORY].listDirectory()
                 if splitext(filename)[-1] == '.pt'
                 and themeDirectory[FRAGMENTS_DIRECTORY].isFile(filename)]

    return SimpleVocabulary(map(SimpleTerm, fragments))


class IFragmentTile(model.Schema):
    fragment = schema.Choice(
        title=_(u'Fragment'),
        source=themeFragments
    )


class FragmentTile(Tile):
    """A tile that displays a theme fragment"""

    def update(self):
        self.index = ThemeFragment(
            self.context, self.request)[self.data['fragment'].encode('utf-8')]

    def __call__(self):
        self.update()
        return u'<html><body>{0:s}</body></html>'.format(self.index())
