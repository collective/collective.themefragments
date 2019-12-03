# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from Products.CMFPlone.utils import safe_unicode
from collective.themefragments.interfaces import FRAGMENTS_DIRECTORY
from collective.themefragments.traversal import ThemeFragment
from collective.themefragments.utils import cache
from collective.themefragments.utils import getFragmentsSettings
from os.path import splitext
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks.layoutbehavior import LayoutAwareTileDataStorage
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import getCurrentTheme
from plone.app.theming.utils import isThemeEnabled
from plone.app.tiles.browser.add import DefaultAddForm
from plone.app.tiles.browser.add import DefaultAddView
from plone.app.tiles.browser.edit import DefaultEditForm
from plone.app.tiles.browser.edit import DefaultEditView
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
from plone.memoize.view import memoize
from plone.resource.utils import queryResourceDirectory
from plone.supermodel import model
from plone.supermodel.interfaces import ISchemaPolicy
from plone.supermodel.parser import DefaultSchemaPolicy
from plone.supermodel.parser import parse
from plone.tiles import Tile
from plone.tiles.absoluteurl import TransientTileAbsoluteURL
from plone.tiles.data import TransientTileDataManager
from plone.tiles.data import decode
from plone.tiles.data import defaultTileDataStorage
from plone.tiles.data import encode
from plone.tiles.esi import ESI_TEMPLATE
from plone.tiles.interfaces import ESI_HEADER
from plone.tiles.interfaces import IESIRendered
from plone.tiles.interfaces import ITileDataManager
from plone.tiles.interfaces import ITileDataStorage
from plone.z3cform.fieldsets.group import Group
from z3c.form.form import Form
from zExceptions import Unauthorized
from zope import schema
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import noLongerProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

try:
    from plone.app.dexterity.permissions import GenericFormFieldPermissionChecker  # noqa: E501
except ImportError:
    # Plone 4.3.x compatibility
    from plone.app.widgets.dx import DXAddViewFieldPermissionChecker as GenericFormFieldPermissionChecker  # noqa: E501

import json
import logging
import six

_ = MessageFactory('collective.themefragments')

logger = logging.getLogger('collective.themefragments')

#
# [theme:themefragments:tiles]
# basename = Display title
#


class TileCatalogSource(CatalogSourceBase):
    """Catalog source, which falsely claims to include everything, because
    otherwise tile data with broken references cannot be deserialized
    (because broken reference would not be found from catalog source).
    """
    def __contains__(self, value):
        return True  # Always contains to allow lazy handling of removed objs


CatalogSource = TileCatalogSource()


class FragmentTileVocabulary(SimpleVocabulary):
    """Vocabulary, which falsely claims to include everything, because
    otherwise tile data with removed fragmets cannot be deserialized.
    """
    def __contains__(self, value):
        return True  # Always contains to allow lazy handling of removed fragments


@implementer(IVocabularyFactory)
class ThemeFragmentsTilesVocabularyFactory(object):
    """Return vocabulary of available theme fragments to be used as tiles"""

    @cache('vocabulary')
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
        titles = getFragmentsSettings(themeDirectory, 'themefragments:tiles')

        tiles = [splitext(filename)[0] for filename
                 in themeDirectory[FRAGMENTS_DIRECTORY].listDirectory()
                 if splitext(filename)[-1] == '.pt' and
                 themeDirectory[FRAGMENTS_DIRECTORY].isFile(filename)]

        terms = [SimpleTerm(None, '', _(u'-- select fragment --'))]
        for tile in tiles:
            title = titles.get(tile, None)
            title = title is None and tile or title.strip().split('#')[0]
            if title and not title.startswith("Hidden"):
                terms.append(SimpleTerm(tile, tile, title))
        return FragmentTileVocabulary(sorted(terms, key=lambda x: x.title))


# Helper adapters
@implementer(ISchemaPolicy)
class FragmentSchemaPolicy(DefaultSchemaPolicy):
    def bases(self, schemaName, tree):
        return IFragmentTile,


@cache(lambda *args: args[0])
def getFragmentSchemata(name):
    """Get matching XML schema for theme fragment"""
    request = getRequest()
    filename = '{0}.xml'.format(name)

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

    if six.PY2: 
        handle = themeDirectory[FRAGMENTS_DIRECTORY].openFile(filename)
        try:
            schemata = parse(handle, 'collective.themefragments').schemata.values()
        finally:
            handle.close()
    else:
        with themeDirectory[FRAGMENTS_DIRECTORY].openFile(filename) as handle:
            schemata = parse(handle, 'collective.themefragments').schemata.values()

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


class IFragmentTileCacheRuleLookup(Interface):
    """Marker interface for fragment specific caching lookup"""


@implementer(IESIRendered)
class FragmentTile(Tile):
    """A tile that displays a theme fragment"""

    def __init__(self, context, request):
        super(FragmentTile, self).__init__(context, request)
        self.index = None

    def __getattr__(self, name):
        return getattr(self.index, name)

    def update(self):
        try:
            self.index = ThemeFragment(self.context, self.request)[
                self.data['fragment']]
            self.index.id = self.id
            self.index.url = self.url
            self.index.data = self.data
        except KeyError:
            raise
            logger.error(u"Theme fragment '{0}' was not found.".format(
                self.data['fragment']))
        except AttributeError:
            # 'NoneType' object has no attribute 'encode'
            logger.error(u"Theme fragment name was not specified.")

    def __call__(self):
        mode = self.request.form.get('_mode') or 'body'

        if self.request.getHeader(ESI_HEADER, 'false').lower() == 'true':
            return ESI_TEMPLATE.format(
                url=(self.request.get('PATH_INFO') and
                     self.request.get('PATH_INFO').replace(' ', '%20') or
                     self.request.getURL()),
                queryString=self.request.get('QUERY_STRING', ''),
                esiMode=mode == 'head' and 'esi-head' or 'esi-body'
            )

        self.update()

        result = u''
        if self.index is not None:
            try:
                result = self.index()
            except Unauthorized:
                self.request.response.setStatus(
                    401, reason='Unauthorized', lock=True)

        # Note that published may be different from self, like ESIBody
        published = self.request.get('PUBLISHED')
        if published is not None:
            if not IFragmentTileCacheRuleLookup.providedBy(published):
                alsoProvides(published, IFragmentTileCacheRuleLookup)

        if mode == 'head':
            return u'<html><head>{0}</head></html>'.format(result)
        else:
            return u'<html><body>{0}</body></html>'.format(result)


def FragmentTileCacheRuleFactory(obj):
    from z3c.caching.registry import ICacheRule
    from z3c.caching.registry import CacheRule

    noLongerProvides(obj, IFragmentTileCacheRuleLookup)
    try:
        default = ICacheRule(obj, None)
    except TypeError:
        try:
            default = ICacheRule(obj.context, None)
        except (TypeError, AttributeError):
            default = None
    try:
        fragment = obj.context.data['fragment']
    except (AttributeError, KeyError):
        fragment = getFragmentName(getRequest())

    if not fragment:
        return default

    currentTheme = getCurrentTheme()
    if not currentTheme:
        return default

    themeDirectory = queryResourceDirectory(THEME_RESOURCE_NAME, currentTheme)
    if not themeDirectory:
        return default

    rulesets = getFragmentsSettings(themeDirectory, 'themefragments:caching')
    if not rulesets:
        return default

    ruleset = rulesets.get(fragment)
    if not ruleset:
        return default

    return CacheRule(ruleset)


def getFragmentName(request):
    # 1) fragment name is serialized as 'fragment' by default, but
    #    until plone.app.tiles' forms prefix it with tiletype
    fragment = request.form.get(
        'fragment', request.form.get(
            'collective.themefragments.fragment.fragment'))
    # 2) because fragment is Choice, it may be a list
    if fragment and isinstance(fragment, list):
        fragment = fragment[0]
    # 3) during widget traversal, there's no querystring with fragment
    #    and a convention of prefixing fields with fragment is used
    if not fragment:
        prefix = '++widget++collective.themefragments.'
        last = request.getURL().split('/')[-1]
        if last.startswith(prefix):
            fragment = last[len(prefix):].split('.')[0]
    return safe_unicode(fragment)


class PrefixedGroup(Group):
    prefix = ''

    def updateWidgets(self, prefix=None):
        prefix = prefix or self.parentForm.widgetPrefix
        if six.PY2 and isinstance(prefix, six.text_type):
            prefix = prefix.encode('utf-8')
        super(PrefixedGroup, self).updateWidgets(prefix=prefix)


class FragmentTileAddForm(DefaultAddForm):
    """Fragment tile add form"""

    group_class = PrefixedGroup

    @property
    @memoize
    def schema(self):
        fragment = getFragmentName(self.request)
        return fragment and getFragmentSchema(fragment) or IFragmentTile

    @property
    @memoize
    def widgetPrefix(self):
        prefix = self.tileType.__name__
        if six.PY2 and isinstance(prefix, six.text_type):
            prefix = prefix.encode('utf8')

        fragment = getFragmentName(self.request)
        if fragment:
            if six.PY2 and isinstance(fragment, six.text_type):
                fragment = fragment.encode('utf8')
            prefix = 'collective.themefragments.' + fragment

        return prefix

    def updateWidgets(self, prefix=None):
        prefix = self.widgetPrefix
        if six.PY2 and isinstance(prefix, six.text_type):
            prefix = prefix.encode('utf-8')

        Form.updateWidgets(self, prefix=prefix)
        self.widgets['fragment'].name = self.tileType.__name__ + '.fragment'
        self.widgets['fragment'].update()

        # Ensure fragment value
        if not self.widgets['fragment'].value:
            fragment = getFragmentName(self.request)
            if fragment:
                self.widgets['fragment'].value = [fragment]


class FragmentTileEditForm(DefaultEditForm):
    """Fragment tile edit form"""

    group_class = PrefixedGroup

    @property
    @memoize
    def schema(self):
        fragment = getFragmentName(self.request)
        return fragment and getFragmentSchema(fragment) or IFragmentTile

    @property
    @memoize
    def widgetPrefix(self):
        prefix = self.tileType.__name__
        if six.PY2 and isinstance(prefix, six.text_type):
            prefix = prefix.encode('utf8')

        fragment = getFragmentName(self.request)
        if fragment:
            if six.PY2 and isinstance(fragment, six.text_type):
                fragment = fragment.encode('utf8')
            prefix = 'collective.themefragments.' + fragment

        return prefix

    def updateWidgets(self, prefix=None):
        prefix = self.widgetPrefix
        if six.PY2 and isinstance(prefix, six.text_type):
            prefix = prefix.encode('utf-8')

        Form.updateWidgets(self, prefix=prefix)
        self.widgets['fragment'].name = self.tileType.__name__ + '.fragment'
        self.widgets['fragment'].update()

        # Ensure fragment value
        if not self.widgets['fragment'].value:
            fragment = getFragmentName(self.request)
            if fragment:
                self.widgets['fragment'].value = [fragment]


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

        # We need to read the persisted fragment name for the right schema
        fragment = None
        for el in self.storage.tree.xpath(
                '//*[contains(@data-tile, "{0}")]'.format(name)):
            try:
                data = json.loads(el.get('data-tiledata') or '{}')
                fragment = data.get('fragment')
            except ValueError:
                pass
            break
        if not fragment:
            fragment = getFragmentName(self.request)

        return name, fragment and getFragmentSchema(fragment) or schema_


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
    @memoize
    def __str__(self):
        url = super(FragmentTileAbsoluteURL, self).__str__().split('?')[0]
        data = ITileDataManager(self.context).get()
        if data and 'fragment' in data:
            fragment = data['fragment']
            if fragment:
                if '?' in url:
                    url += '&fragment=' + fragment
                else:
                    url += '?fragment=' + fragment
                for schema_ in getFragmentSchemata(fragment):
                    url += '&' + encode(data, schema_)
        return url
