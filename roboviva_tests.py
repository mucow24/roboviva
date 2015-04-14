import roboviva
import unittest
import flask.ext
import tempfile
import os


class RobovivaTestCase(unittest.TestCase):
  def setUp(self):
    roboviva.app.config['TESTING'] = True
    shelve_fd, roboviva.app.config['SHELVE_FILENAME'] = tempfile.mkstemp(suffix=".db")
    os.close(shelve_fd)
    print roboviva.app.config
    self.app = roboviva.app.test_client()

  def tearDown(self):
    os.unlink(roboviva.app.config['SHELVE_FILENAME'])

  def test_empty(self):
    ret = self.app.get("/roboviva/cache")
    print ret.data
    self.assertTrue('Cache has 0 entries' in ret.data)


if __name__ == "__main__":
  unittest.main()
