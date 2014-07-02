import cue
import csv
import urllib2
import hashlib

class RideWithGpsError(Exception):
  '''Thrown by getCueSheet() in the event of an error'''
  pass

def getCueSheet(route_id):
  '''
      Queries RideWithGPS, and returns a list of CueEntrys, along with the MD5
      checksum of the raw CSV data that generated it.

      route_id - The numeric route ID to fetch. (e.g. '12345' in ridewithgps.com/routes/12345)

      Throws a RideWithGpsError in the event of a problem (invalid route id, etc.)
  '''
  url = "http://ridewithgps.com/routes/%s.csv" % route_id

  raw_csv = ""
  try:
    raw_csv = urllib2.urlopen(url, timeout=5).read()
  except HTTPError as e:
    if e.code is 404:
      raise RideWithGpsError("Invalid Route ID")
    else:
      raise RideWithGpsError(e.reason)

  md5 = hashlib.md5(raw_csv).hexdigest()


def csvRowToCueEntry(csv_row):
  '''Converts a ridewithgps CSV row into a cue.CueEntry. Assumes the following CSV layout:
     type,notes,distance,elevation,description

     With the following mapping:
     type        -> instruction
     notes       -> description
     distance    -> absolute_distance
     description -> notes
  '''
  instruction_str = csv_row['type']
  description     = csv_row['notes']
  distance        = csv_row['distance']
  notes           = csv_row['notes']

  # Figure out the (base) instruction:



