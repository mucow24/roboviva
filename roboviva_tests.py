import roboviva
import unittest
import tempfile
import os


class RobovivaTestCase(unittest.TestCase):
  def setUp(self):
    roboviva.app.config['TESTING'] = True
    roboviva.app.config['SHELVE_FILENAME'] = 'test_shelf.db'
    self.app = roboviva.app.test_client()

  def tearDown(self):
    os.unlink(roboviva.app.config['SHELVE_FILENAME'])
    pass

  def test_Empty(self):
    # Verify cache is empty at launch:
    ret = self.app.get("/roboviva/cache")
    self.assertTrue('Cache has 0 entries' in str(ret.data))

  def test_CacheAdd(self):
    # Generate a route, verify it ends up in the cache:
    # Uses same test route as ridewithgps_tests.py; if this ETag is invalid
    # check the one used there to see if this is out of date.
    Route_Id = "6260667"
    Expected_ETag = "W/\"5e668792f4c8bd376091dd89f3648698\""
    self.app.get("/roboviva/routes/%s" % Route_Id)
    ret = self.app.get("/roboviva/cache")
    self.assertTrue(Route_Id in str(ret.data))
    self.assertTrue(Expected_ETag in str(ret.data))


if __name__ == "__main__":
  unittest.main()
