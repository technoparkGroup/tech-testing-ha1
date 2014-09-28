#!/usr/bin/env python2.7

import os
import sys
import unittest
from source.tests.test_utils import UtilsTestCase

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from source.tests.test_notification_pusher import NotificationPusherTestCase
from source.tests.test_redirect_checker import RedirectCheckerTestCase


if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(NotificationPusherTestCase),
        unittest.makeSuite(RedirectCheckerTestCase),
        unittest.makeSuite(UtilsTestCase)
    ))
    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
