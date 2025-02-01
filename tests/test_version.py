"""
Created on 2025-02-01

@author: wf
"""

from ngwidgets.basetest import Basetest
from velorail.version import Version


class TestVersion(Basetest):
    """
    test Version
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_Version(self):
        """
        test Version object - effectively only testing the test infrastructure
        """
        version=Version()
        self.assertIsNotNone(version)