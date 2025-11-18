
# Create your tests here.

from StartupWebApp.utilities.test_base import PostgreSQLTestCase


class SmokeTest(PostgreSQLTestCase):

    def test_bad_maths(self):
        self.assertEqual(1 + 2, 3)
        # self.assertEqual(1+1,3)
        # self.assertTrue(False)
