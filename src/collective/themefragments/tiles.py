# -*- coding: utf-8 -*-
from collective.themefragments.interfaces import FRAGMENTS_DIRECTORY
from collective.themefragments.traversal import ThemeFragment
from collective.themefragments.utils import getPluginSettings
from os.path import splitext
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import getCurrentTheme
from plone.app.theming.utils import isThemeEnabled
from plone.app.tiles.browser.add import DefaultAddForm
from plone.app.tiles.browser.add import DefaultAddView
from plone.app.tiles.browser.edit import DefaultEditForm
from plone.app.tiles.browser.edit import DefaultEditView
from plone.memoize.view import memoize
from plone.resource.utils import queryResourceDirectory
from plone.supermodel import model
from plone.supermodel.parser import parse
from plone.tiles import Tile
from plone.tiles.absoluteurl import TransientTileAbsoluteURL
from plone.tiles.data import encode
from plone.tiles.data import decode
from plone.tiles.data import TransientTileDataManager
from plone.tiles.interfaces import ITileDataManager
from zope import schema
from zope.globalrequest import getRequest
from zope.i18nmessageid import MessageFactory
from zope.interface import provider
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import logging

_ = MessageFactory('collective.themefragments')

logger = logging.getLogger('collective.themefragments')

#
# [theme:themefragments:tiles]
# basename = Display title
#


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

    settings = getPluginSettings(
        themeDirectory, plugins=[('themefragments:tiles', None)]
    ).get('themefragments:tiles', {})

    tiles = [splitext(filename)[0] for filename
             in themeDirectory[FRAGMENTS_DIRECTORY].listDirectory()
             if splitext(filename)[-1] == '.pt'
             and themeDirectory[FRAGMENTS_DIRECTORY].isFile(filename)]

    return SimpleVocabulary(
        [SimpleTerm(None, '', _(u'-- select fragment --'))] +
        [SimpleTerm(tile, tile, settings.get(tile, tile)) for tile in tiles]
    )


def getFragmentSchemata(name):
    request = getRequest()
    filename = (u'{0:s}.xml'.format(name)).encode('utf-8', 'ignore')

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

    if not themeDirectory[FRAGMENTS_DIRECTORY].isFile(filename):
        return ()

    handle = themeDirectory[FRAGMENTS_DIRECTORY].openFile(filename)
    schemata = parse(handle).schemata.values()
    for schema_ in schemata:
        schema_.__name__ = schema_.__name__.encode('utf-8', 'ignore')
    return schemata


class IFragmentTile(model.Schema):
    fragment = schema.Choice(
        title=_(u'Theme fragment'),
        source=themeFragments,
    )


class FragmentTile(Tile):
    """A tile that displays a theme fragment"""

    def update(self):
        try:
            self.index = ThemeFragment(self.context, self.request)[
                self.data['fragment'].encode('utf-8')]
        except KeyError:
            logger.error(u"Theme fragment '{0:s}' was not found.".format(
                self.data['fragment']
            ))
            self.index = lambda: u''

    def __call__(self):
        self.update()
        return u'<html><body>{0:s}</body></html>'.format(self.index())


class FragmentTileAddForm(DefaultAddForm):
    """Fragment tile add form"""

    @property
    @memoize
    def additionalSchemata(self):
        fragment = self.request.form.get('fragment')
        if fragment:
            return getFragmentSchemata(fragment)
        else:
            return ()


class FragmentTileEditForm(DefaultEditForm):
    """Fragment tile edit form"""

    @property
    @memoize
    def additionalSchemata(self):
        fragment = self.request.form.get('fragment')
        if fragment:
            return getFragmentSchemata(fragment)
        else:
            return ()


class FragmentTileAddView(DefaultAddView):
    form = FragmentTileAddForm


class FragmentTileEditView(DefaultEditView):
    form = FragmentTileEditForm


class FragmentTileDataManager(TransientTileDataManager):
    def get(self):
        data = super(FragmentTileDataManager, self).get()
        if data and self.key not in self.annotations and 'fragment' in data:
            fragment = data['fragment']
            for schema_ in getFragmentSchemata(fragment):
                try:
                    data.update(decode(self.tile.request.form,
                                       schema_, missing=True))
                except (ValueError, UnicodeDecodeError,):
                    pass
        return data


class FragmentTileAbsoluteURL(TransientTileAbsoluteURL):
    def __str__(self):
        url = super(FragmentTileAbsoluteURL, self).__str__()
        data = ITileDataManager(self.context).get()
        if data and 'fragment' in data:
            fragment = data['fragment']
            for schema_ in getFragmentSchemata(fragment):
                if '?' in url:
                    url += '&' + encode(data, schema_)
                else:
                    url += '?' + encode(data, schema_)
        return url
