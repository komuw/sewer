# the test dir is a sub dir of sewer/sewer so as
# not to pollute the global namespace.
# see: https://python-packaging.readthedocs.io/en/latest/testing.html

# from unittest import TestCase

# import funniest

# class TestJoke(TestCase):
#     def test_is_string(self):
#         s = funniest.joke()
#         self.assertTrue(isinstance(s, basestring))

# The best way to get these tests going (particularly if you're not sure what to use) is Nose.
# With those files added, it's just a matter of running this from the root of the repository:

# $ pip install nose
# $ nosetests
# To integrate this with our setup.py, and ensure that Nose is installed when we run the tests, we'll add a few lines to setup():

# setup(
#     ...
#     test_suite='nose.collector',
#     tests_require=['nose'],
# )
# Then, to run tests, we can simply do:

# $ python setup.py test
# Setuptools will take care of installing nose and running the test suite.

# from unittest import TestCase
# from funniest.command_line import main

# class TestConsole(TestCase):
#     def test_basic(self):
#         main()
