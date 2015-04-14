import roboviva
import unittest
import flask.ext
import tempfile
import os


class RobovivaTestCase(unittest.TestCase):
  def setUp(self):
    roboviva.app.config['TESTING'] = True
    roboviva.app.config['SHELVE_FILENAME'] = 'test_shelf'
    self.app = roboviva.app.test_client()

  def tearDown(self):
    os.unlink(roboviva.app.config['SHELVE_FILENAME'] + '.db')

  def test_Empty(self):
    # Verify cache is empty at launch:
    ret = self.app.get("/roboviva/cache")
    self.assertTrue('Cache has 0 entries' in ret.data)

  def test_CacheAdd(self):
    # Generate a route, verify it ends up in the cache:
    Route_Id = "6260667"
    Expected_ETag = "\"fc3842ae134af2008092696c7b1af1fa\""
    self.app.get("/roboviva/routes/%s" % Route_Id)
    ret = self.app.get("/roboviva/cache")
    self.assertTrue(Route_Id in ret.data)
    self.assertTrue(Expected_ETag in ret.data)


if __name__ == "__main__":
  unittest.main()
