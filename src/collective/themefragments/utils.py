# -*- coding: utf-8 -*-
from App.config import getConfiguration
from ConfigParser import SafeConfigParser
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.plugins.utils import getPlugins
from plone.resource.manifest import MANIFEST_FILENAME
from zope.globalrequest import getRequest

try:
    from plone.app.theming.interfaces import IThemingPolicy
    CACHE = True
except ImportError:
    CACHE = False


def cache(key):
    def wrapper(func):
        def cached(*args, **kwargs):
            if not CACHE or getConfiguration().debug_mode:
                return func(*args, **kwargs)

            request = getRequest()
            policy = IThemingPolicy(request)
            cache_ = policy.getCache()
            if not hasattr(cache_, 'collective.themefragments'):
                setattr(cache_, 'collective.themefragments', {})
            cache_ = getattr(cache_, 'collective.themefragments')

            if callable(key):
                key_ = key(*args)
            else:
                key_ = key

            if key_ not in cache_:
                cache_[key_] = func(*args, **kwargs)
            return cache_[key_]

        return cached
    return wrapper


@cache(lambda directory, section: ':'.join([directory.__name__, section]))
def getFragmentsSettings(themeDirectory, section):
    return getPluginSettings(
        themeDirectory, plugins=[(section, None)]
    ).get(section) or {}


# This is copied from p.a.theming.plugins.utils to get properly cached data
def getPluginSettings(themeDirectory, plugins=None):
    """Given an IResourceDirectory for a theme, return the settings for the
    given list of plugins (or all plugins, if not given) provided as a list
    of (name, plugin) pairs.

    Returns a dict of dicts, with the outer dict having plugin names as keys
    and containing plugins settings (key/value pairs) as values.
    """

    if plugins is None:
        plugins = getPlugins()

    # noinspection PyPep8Naming
    manifestContents = {}

    if themeDirectory.isFile(MANIFEST_FILENAME):
        parser = SafeConfigParser()
        fp = themeDirectory.openFile(MANIFEST_FILENAME)

        try:
            parser.readfp(fp)
            for section in parser.sections():
                manifestContents[section] = {}

                for name, value in parser.items(section):
                    manifestContents[section][name] = value

        finally:
            try:
                fp.close()
            except AttributeError:
                pass

    pluginSettings = {}
    for name, plugin in plugins:
        pluginSettings[name] = manifestContents.get("%s:%s" % (THEME_RESOURCE_NAME, name), {})  # noqa

    return pluginSettings
