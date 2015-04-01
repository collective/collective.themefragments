# -*- coding: utf-8 -*-
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer


class CollectiveThemeFragmentsLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import collective.themefragments
        import collective.themefragments.tests
        self.loadZCML(package=collective.themefragments)
        self.loadZCML(package=collective.themefragments.tests)

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'plone.app.theming:default')


COLLECTIVE_THEMEFRAGMENTS_FIXTURE =\
    CollectiveThemeFragmentsLayer()

COLLECTIVE_THEMEFRAGMENTS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_THEMEFRAGMENTS_FIXTURE,),
    name='Integration')
COLLECTIVE_THEMEFRAGMENTS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_THEMEFRAGMENTS_FIXTURE,),
    name='Functional')
