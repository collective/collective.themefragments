# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from collective.themefragments.interfaces import FRAGMENTS_DIRECTORY
from collective.themefragments.traversal import ThemeFragment
from collective.themefragments.utils import getPluginSettings
from os.path import splitext
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks.layoutbehavior import LayoutAwareTileDataStorage
from plone.app.dexterity.permissions import GenericFormFieldPermissionChecker
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
from plone.supermodel.interfaces import ISchemaPolicy
from plone.supermodel.parser import DefaultSchemaPolicy
from plone.supermodel.parser import parse
from plone.tiles.absoluteurl import TransientTileAbsoluteURL
from plone.tiles.data import decode
from plone.tiles.data import defaultTileDataStorage
from plone.tiles.data import encode
from plone.tiles.data import PersistentTileDataManager
from plone.tiles.data import TransientTileDataManager
from plone.tiles import Tile
from plone.tiles.interfaces import ITile
from plone.tiles.interfaces import ITileDataManager
from plone.tiles.interfaces import ITileDataStorage
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.i18nmessageid import MessageFactory
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import getFields
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import logging

_ = MessageFactory('collective.themefragments')

logger = logging.getLogger('collective.themefragments')

#
# [theme:themefragments:tiles]
# basename = Display title
#


@implementer(IVocabularyFactory)
class ThemeFragmentsTilesVocabularyFactory(object):
    """Return vocabulary of available theme fragments to be used as tiles"""
    def __call__(self, context=None):
        request = getRequest()

        if not isThemeEnabled(request):
            return SimpleVocabulary([])

        currentTheme = getCurrentTheme()
        if currentTheme is None:
            return SimpleVocabulary([])

        themeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, currentTheme)  # noqa
        if themeDirectory is None:
            return SimpleVocabulary([])

        if not themeDirectory.isDirectory(FRAGMENTS_DIRECTORY):
            return SimpleVocabulary([])

        # Get settings to map titles
        settings = getPluginSettings(
            themeDirectory, plugins=[('themefragments:tiles', None)]
        ).get('themefragments:tiles', {})

        tiles = [splitext(filename)[0] for filename
                 in themeDirectory[FRAGMENTS_DIRECTORY].listDirectory()
                 if splitext(filename)[-1] == '.pt' and
                 themeDirectory[FRAGMENTS_DIRECTORY].isFile(filename)]

        return SimpleVocabulary(
            [SimpleTerm(None, '', _(u'-- select fragment --'))] +
            [SimpleTerm(tile, tile, settings.get(tile, tile))
             for tile in tiles if settings.get(tile, None) is not '']
        )


# Helper adapters
@implementer(ISchemaPolicy)
class FragmentSchemaPolicy(DefaultSchemaPolicy):
    def bases(self, schemaName, tree):
        return IFragmentTile,


def getFragmentSchemata(name):
    """Get matching XML schema for theme fragment"""
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
    schemata = parse(handle, 'collective.themefragments').schemata.values()
    for schema_ in schemata:
        schema_.__name__ = schema_.__name__.encode('utf-8', 'ignore')
    return schemata


def getFragmentSchema(name):
    """Only ever return the first schema of the parsed schemata or None"""
    for schema_ in getFragmentSchemata(name):
        return schema_
    return None


class IFragmentTile(model.Schema):
    """Generic theme fragment tile"""

    fragment = schema.Choice(
        title=_(u'Theme fragment'),
        vocabulary='collective.themefragments.tiles',
    )


class FragmentTile(Tile):
    """A tile that displays a theme fragment"""

    def __init__(self, context, request):
        super(FragmentTile, self).__init__(context, request)
        self.index = None

    def update(self):
        try:
            self.index = ThemeFragment(self.context, self.request)[
                self.data['fragment'].encode('utf-8')]
            self.index.data = self.data
        except KeyError:
            logger.error(u"Theme fragment '{0:s}' was not found.".format(
                self.data['fragment']))

    def __call__(self):
        self.update()
        if self.index is not None:
            return u'<html><body>{0:s}</body></html>'.format(self.index())
        else:
            return u'<html></html>'


class FragmentTileAddForm(DefaultAddForm):
    """Fragment tile add form"""

    @property
    @memoize
    def schema(self):
        fragment = self.request.form.get(
            'fragment', self.request.form.get(
                'collective.themefragments.fragment.fragment'))
        if fragment and isinstance(fragment, list):
            fragment = fragment[0]
        return fragment and getFragmentSchema(fragment) or IFragmentTile


class FragmentTileEditForm(DefaultEditForm):
    """Fragment tile edit form"""

    @property
    @memoize
    def schema(self):
        fragment = self.request.form.get(
            'fragment', self.request.form.get(
                'collective.themefragments.fragment.fragment'))
        if fragment and isinstance(fragment, list):
            fragment = fragment[0]
        return fragment and getFragmentSchema(fragment) or IFragmentTile


class FragmentTileAddView(DefaultAddView):
    form = FragmentTileAddForm


class FragmentTileEditView(DefaultEditView):
    form = FragmentTileEditForm


class FragmentTilePermissionChecker(GenericFormFieldPermissionChecker):
    def validate(self, field_name, vocabulary_name=None):
        # We may not have fragment name and therefore cannot resolve
        # the real schema. The best we can is check for the default permission.
        checker = getSecurityManager().checkPermission
        return checker(self.DEFAULT_PERMISSION, self.context)


@adapter(ITile)
@implementer(ITileDataManager)
def fragmentTileDataManagerFactory(tile):
    if tile.request.get('X-Tile-Persistent'):
        return PersistentFragmentTileDataManager(tile)
    else:
        return FragmentTileDataManager(tile)


@implementer(ITileDataStorage)
@adapter(ILayoutBehaviorAdaptable, Interface, FragmentTile)
def layoutAwareFragmentTileDataStorage(context, request, tile):
    if tile.id is not None:
        return LayoutAwareFragmentTileDataStorage(context, request, tile)
    else:
        return defaultTileDataStorage(context, request, tile)


@implementer(ITileDataStorage)
@adapter(ILayoutBehaviorAdaptable, Interface, FragmentTile)
class LayoutAwareFragmentTileDataStorage(LayoutAwareTileDataStorage):
    def resolve(self, key):
        name, schema_ = super(
            LayoutAwareFragmentTileDataStorage, self).resolve(key)
        fragment = self.request.form.get(
            'fragment', self.request.form.get(
                'collective.themefragments.fragment.fragment'))
        if fragment and isinstance(fragment, list):
            fragment = fragment[0]
        return '@@{0:s}/{1:s}'.format(name, key), \
            fragment and getFragmentSchema(fragment) or schema_


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
        url = super(FragmentTileAbsoluteURL, self).__str__().split('?')[0]
        data = ITileDataManager(self.context).get()
        if data and 'fragment' in data:
            fragment = data['fragment']
            for schema_ in getFragmentSchemata(fragment):
                if '?' in url:
                    url += '&' + encode(data, schema_)
                else:
                    url += '?' + encode(data, schema_)
        return url


class PersistentFragmentTileDataManager(PersistentTileDataManager):
    def get_default_request_data(self):
        data = super(PersistentFragmentTileDataManager, self).get_default_request_data()  # noqa
        if data and self.key not in self.annotations and 'fragment' in data:
            fragment = data['fragment']
            for schema_ in getFragmentSchemata(fragment):
                try:
                    data.update(decode(self.tile.request.form,
                                       schema_, missing=True))
                except (ValueError, UnicodeDecodeError):
                    pass
        return data

    def get(self):
        data = super(PersistentFragmentTileDataManager, self).get()
        if data and self.key not in self.annotations and 'fragment' in data:
            fragment = data['fragment']
            for schema_ in getFragmentSchemata(fragment):
                for name, field in getFields(schema_).items():
                    if name not in data:
                        data[name] = field.missing_value
        return data
