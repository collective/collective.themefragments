# -*- coding: utf-8 -*-
from collective.themefragments.testing import COLLECTIVE_THEMEFRAGMENTS_FUNCTIONAL_TESTING  # noqa
from plone.app.theming.interfaces import IThemeSettings
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from urllib2 import HTTPError
from zope.component import getUtility
import Globals
import transaction
import unittest


class TestCase(unittest.TestCase):
    layer = COLLECTIVE_THEMEFRAGMENTS_FUNCTIONAL_TESTING

    def setUp(self):
        # Enable debug mode always to ensure cache is disabled by default
        Globals.DevelopmentMode = True

        self.settings = getUtility(IRegistry).forInterface(IThemeSettings)
        self.settings.enabled = False

        transaction.commit()

    def tearDown(self):
        Globals.DevelopmentMode = False

    def test_theme_fragment_traverser(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = True
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/rules.xml'

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '/@@theme-fragment/customnav')

        self.assertTrue('<h2>%s</h2>' % portal.Title() in browser.contents)

    def test_scripted_theme_fragment_traverser(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = True
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/rules.xml'

        transaction.commit()

        browser = Browser(app)
        browser.open(portal.absolute_url() + '/@@theme-fragment/scripted_customnav')  # noqa

        self.assertTrue('<h2>%s</h2>' % portal.Title() in browser.contents)

    def test_theme_fragment_traverser_invalid_url(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = True
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/rules.xml'  # noqa

        transaction.commit()

        browser = Browser(app)

        try:
            browser.open(portal.absolute_url() + '/@@theme-fragment/foo')
        except HTTPError, e:
            error = e
        self.assertEqual(error.code, 404)

    def test_theme_fragment_traverser_theme_disabled(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = False
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/rules.xml'  # noqa

        transaction.commit()

        browser = Browser(app)

        try:
            browser.open(portal.absolute_url() + '/@@theme-fragment/customnav')
        except HTTPError, e:
            error = e
        self.assertEqual(error.code, 404)

    def test_theme_fragment_traverser_restricted_python(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = True
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/rules.xml'  # noqa

        transaction.commit()

        browser = Browser(app)

        try:
            # tries to use an underscore attribute, which isn't traversable
            # in restricted python
            browser.open(portal.absolute_url() + '/@@theme-fragment/invalid')
        except HTTPError, e:
            error = e

        self.assertEqual(error.code, 500)

    def test_scripted_theme_fragment_traverser_restricted_python(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = True
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/rules.xml'  # noqa

        transaction.commit()

        browser = Browser(app)

        try:
            # tries to use an underscore attribute, which isn't traversable
            # in restricted python
            browser.open(portal.absolute_url() + '/@@theme-fragment/scripted_invalid')  # noqa
        except HTTPError, e:
            error = e

        self.assertEqual(error.code, 500)

    def test_theme_fragment_href_include(self):
        app = self.layer['app']
        portal = self.layer['portal']
        self.settings.enabled = True
        self.settings.currentTheme = u'collective.themefragments.tests'
        self.settings.rules = u'/++theme++collective.themefragments.tests/fragment.xml'  # noqa

        transaction.commit()

        browser = Browser(app)

        browser.open(portal.absolute_url())
        self.assertTrue('<div id="nav">' in browser.contents)
        self.assertTrue('<h2>%s</h2>' % portal.Title() in browser.contents)
