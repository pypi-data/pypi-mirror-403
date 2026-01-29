# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.volto.secondarymenu.testing import (
    VOLTO_SECONDARYMENU_INTEGRATION_TESTING,
)
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that collective.volto.secondarymenu is properly installed."""

    layer = VOLTO_SECONDARYMENU_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if collective.volto.secondarymenu is installed."""
        self.assertTrue(
            _is_installed(self.installer, "collective.volto.secondarymenu")
        )

    def test_browserlayer(self):
        """Test that ICollectiveVoltoSecondaryMenuLayer is registered."""
        from collective.volto.secondarymenu.interfaces import (
            ICollectiveVoltoSecondaryMenuLayer,
        )
        from plone.browserlayer import utils

        self.assertIn(
            ICollectiveVoltoSecondaryMenuLayer, utils.registered_layers()
        )


class TestUninstall(unittest.TestCase):

    layer = VOLTO_SECONDARYMENU_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        _uninstall(self.installer, "collective.volto.secondarymenu")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if collective.volto.secondarymenu is cleanly uninstalled."""
        self.assertFalse(
            _is_installed(self.installer, "collective.volto.secondarymenu")
        )

    def test_browserlayer_removed(self):
        """Test that ICollectiveVoltoSecondaryMenuLayer is removed."""
        from collective.volto.secondarymenu.interfaces import (
            ICollectiveVoltoSecondaryMenuLayer,
        )
        from plone.browserlayer import utils

        self.assertNotIn(
            ICollectiveVoltoSecondaryMenuLayer, utils.registered_layers()
        )


def _is_installed(installer, product_id):
    if hasattr(installer, "is_product_installed"):
        return installer.is_product_installed(product_id)
    return installer.isProductInstalled(product_id)


def _uninstall(installer, product_id):
    if hasattr(installer, "uninstall_product"):
        return installer.uninstall_product(product_id)
    return installer.uninstallProducts([product_id])
