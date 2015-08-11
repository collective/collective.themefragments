# -*- coding: utf-8 -*-
from ConfigParser import SafeConfigParser

from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.plugins.utils import getPlugins
from plone.resource.manifest import MANIFEST_FILENAME


# This is copied from p.a.theming.plugins.utils to get uncached data
# noinspection PyPep8Naming
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
