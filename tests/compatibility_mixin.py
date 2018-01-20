"""
Compatibility mixin to support proper testing in  Python 2.6.
"""
import sys


class CompatibilityMixin(object):
    if sys.version_info < (2, 7):
        def assertIsInstance(self, obj, cls, msg=None):
            if msg is None:
                msg = '%s is not of type %s' % (obj, getattr(cls, '__name__', '<unknown type>'))
            self.assertTrue(isinstance(obj, cls), msg)

        def assertIn(self, member, container, msg=None):
            if msg is None:
                msg = '%r not found in %r' % (member, container)
            self.assertTrue(member in container, msg)
