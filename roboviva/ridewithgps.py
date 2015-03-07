# Roboviva - Better cue sheets for everyone
# Copyright (C) 2015 Mike Kocurek
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cue
import csv
import urllib2
import socket
import hashlib
import re

class RideWithGpsError(Exception):
  '''Thrown by getCueSheet() in the event of an error'''
  pass

class RWGPS_Entry(object):
  '''Simple storage class containing the RWGPS-provided data for a single cue entry'''
  def __init__(self,
               instruction_str,
               description_str,
               absolute_distance,
               prev_absolute_distance,
               next_absolute_distance,
               note_str):
   self.instruction_str = instruction_str
   self.description_str = description_str
   self.absolute_distance = absolute_distance
   self.prev_absolute_distance = prev_absolute_distance
   self.next_absolute_distance = next_absolute_distance
   self.note_str = note_str

def getEtagForCSV(route_id):
  '''
      Queries RideWithGPS for the CSV file of the given route_id. Returns the
      HTTP etag header value for this route id, discarding the actual result.
      For testing purposes only.
  '''
  url = "http://ridewithgps.com/routes/%s.csv" % route_id
  Max_Attempts = 3
  for n_tries in xrange(Max_Attempts):
    try:
      headers = urllib2.urlopen(url, timeout = 5).info()
      etag = headers.getheader("ETag")
      break
    except urllib2.HTTPError as e:
      # Probably a 404, so don't bother retrying
      raise RideWithGpsError("Unknown Route ID: %s" % route_id)
    except socket.timeout as e:
      # Timeout, let this pass:
      pass
  print "etag: %s" % etag
  return etag

def getETagAndCuesheet_viaCSV(route_id, etag=None):
  '''
      Queries RideWithGPS for the cue data for 'route_id'. If 'etag' is
      non-None, then 'etag' is passed to the server in the 'If-None-Match' HTTP
      header.

      Returns: A 2-tuple of the server's ETag, and either a cue.Route object,
      if new data was on the server, or "None", if 'etag' is still current.

      NOTE: This method fetches the route info via RWGPS's CSV export feature,
            which does NOT include the route's name.

      route_id - The numeric route ID to fetch. (e.g. '12345' in ridewithgps.com/routes/12345)
      etag     - The HTTP ETag header returned by the server the last time we
                 asked for this route, or "None" if this is a new route, or we
                 want a fresh copy.

      Throws a RideWithGpsError in the event of a problem (invalid route id, etc.)
  '''
  url = "http://ridewithgps.com/routes/%s.csv" % route_id
  req = urllib2.Request(url)
  if etag:
    req.add_header("If-None-Match", etag)

  raw_csv      = None
  Max_Attempts = 3
  for n_tries in xrange(Max_Attempts):
    try:
      resp = urllib2.urlopen(req, timeout = 5)
      new_etag = resp.info().getheader("ETag")
      raw_csv = resp.read()
      break
    except urllib2.HTTPError as e:
      # This might be a 304: Not Modified, which means the etag we passed was still current:
      if e.code == 304:
        # Return the original ETag, and 'None" for the cue entries, as specified:
        return (etag, None)

      # Otherwise, this is probably a 404:
      raise RideWithGpsError("Unknown Route ID: %s" % route_id)
    except socket.timeout as e:
      # Timeout, let this pass:
      pass
  if not raw_csv:
    raise Exception("No data from RideWithGPS after %d tries" % Max_Attempts)

  # Read in CSV rows:
  reader = csv.DictReader(raw_csv.split("\n"),
                          ['type', 'note', 'absolute_distance', 'elevation', 'description'])
  rows   = [row for row in reader]
  rows   = rows[1:] # Prune header

  # Transform to RWGPS_Entry objects:
  entries = _rawCSVtoRWGPS_Entries(rows)

  # And then to cue.Entry objects:
  route = cue.Route([_RWGPS_EntryToCueEntry(entry) for entry in entries], route_id)
  return (new_etag, route)

def _cleanDescription(description):
  '''
    Clean up the description.

    RWGPS Duplicates the instruction in the description, e.g. "Right on Foo
    St.", instead of "Foo St.". This blows up the "On" column in the final
    sheet, so try to fix it as best we can.

    This method also removes any custom instructions, if they exist.

    description - the original ridewithgps description string, e.g. "Turn right onto Foo St."
  '''
  description = re.sub("^\s*\[[^\]]+\]\s*",                                "",     description)
  description = re.sub("^At the traffic circle,",                       "@ Circle,", description, flags=re.I)
  description = re.sub("^(Slight|Turn|Bear|Keep) (left|right) (toward|onto|on) ", "",description, flags=re.I)
  description = re.sub("^(Slight|Turn|Bear|Keep) (left|right) to stay on", "TRO",  description, flags=re.I)
  description = re.sub("to stay on",                                       "TRO",  description, flags=re.I)
  description = re.sub("to remain on",                                     "TRO",  description, flags=re.I)
  description = re.sub("^(Slight|Turn|Bear|Keep) (left|right) ",           "",     description, flags=re.I)
  description = re.sub("^(Left|Right) onto ",                              "",     description, flags=re.I)
  description = re.sub("^Continue onto ",                                  "",     description, flags=re.I)
  description = re.sub("^Continue straight (onto|on) ",                         "",     description, flags=re.I)
  return description

def _instructionStrToCueInstruction(instruction_str):
  '''Maps a RWGPS 'instruction' string to a cue.Instruction. If the instruction
  string doesn't match a known one, the original instruction string is
  returned'''
  if instruction_str == "Left":
    return cue.Instruction.LEFT
  elif instruction_str == "Right":
    return cue.Instruction.RIGHT
  elif instruction_str == "Straight":
    return cue.Instruction.STRAIGHT
  elif instruction_str in ("Food", "Water"):
    return cue.Instruction.PIT
  elif instruction_str == "Danger":
    return cue.Instruction.DANGER
  elif instruction_str in ("Start", "End", "Generic"):
    return cue.Instruction.NONE
  elif instruction_str == "Summit":
    return cue.Instruction.SUMMIT
  elif instruction_str == "4th Category":
    return cue.Instruction.CAT_4
  elif instruction_str == "3rd Category":
    return cue.Instruction.CAT_3
  elif instruction_str == "2nd Category":
    return cue.Instruction.CAT_2
  elif instruction_str == "1st Category":
    return cue.Instruction.CAT_1
  elif instruction_str == "Hors Category":
    return cue.Instruction.CAT_HC
  elif instruction_str == "First Aid":
    return cue.Instruction.FIRST_AID
  else:
    # Just punt to whatever they gave us:
    return instruction_str

def _getModifierFromRWGPSEntry(entry, quick_threshold_mi=0.1):
  '''
  Returns any cue.Modifier that might apply to a given RWGPS_Entry.
  Returns the relevant modifier, or cue.Modifier.NONE if none apply.
  'quick_threshold_mi' determines the distance, in miles, at which a turn is
  marked as 'quick'
  '''
  instruction = _instructionStrToCueInstruction(entry.instruction_str)
  if instruction in (cue.Instruction.LEFT, cue.Instruction.RIGHT):
    # RWGPS will use the terms "Keep [left|right]" or "Bear [left|right]" to
    # indicate slight turns:
    if re.match("^(Keep|Bear|Slight) ", entry.description_str):
      return cue.Modifier.SLIGHT
    elif entry.prev_absolute_distance:
      # If this instruction is < 0.1 miles from the prior one, call it 'quick':
      dist_from_prev = entry.absolute_distance - entry.prev_absolute_distance
      if dist_from_prev < 0.1:
        return cue.Modifier.QUICK
  # None apply.
  return cue.Modifier.NONE

def _rawCSVtoRWGPS_Entries(raw_csv_rows):
  '''Converts an array of raw CSV rows, as provided by ridewithgps, and
  converts them into an array of RWGPS_Entry objects. This assumes the first
  entry in the array is the first cue entry, *not* the CSV header. Each row
  should have been parsed into a python dictionary prior to calling this.

  This assumes the following field mappings:
  RWGPS Field Name:         Roboviva Field Name:
  type                   -> instruction_str
  note                   -> description_str
  absolute_distance      -> absolute_distance
  description            -> note_str
  '''
  ret = []
  for i, row in enumerate(raw_csv_rows):
    ret.append(RWGPS_Entry(instruction_str = row['type'],
                           description_str = row['note'],
                           absolute_distance = float(row['absolute_distance']),
                           prev_absolute_distance = None, # Will fill in in a moment
                           next_absolute_distance = None, # Will fill in in a moment
                           note_str               = row['description']))
    # Fill prev/next abs distances:
    if i > 0:
      ret[i - 1].next_absolute_distance = ret[i].absolute_distance
      ret[i].prev_absolute_distance = ret[i - 1].absolute_distance
  return ret

def _parseCustomInstruction(raw_description):
  '''
  Tries to determine if the user is providing a custom instruction in the
  description. These look like this:

  [L/QR] Left on Foo St., quick right on Bar St.

  This line should have a custom instruction of "L/QR", not "L". Custom
  instructions must meet the following criteria to be accepted as such:
    - They must be contained in []
    - They must be the first non-whitespace text in the
      description:
        "  [L/QR] Foo"
      is OK, but
        "Left on Foo St. [QR] on Bar St."
      is not.
   - They must be "short". That is, they shouldn't overflow the width of the
     "Go" column... we don't really enforce this, currently - we just let it
     get ugly.
  Returns the custom instruction as a string, if it exists. Otherwise, returns 'None'.
  '''
  m = re.match(r'^\s*\[([^\]]+)\]', raw_description)
  if m:
    return m.group(1)
  else:
    return None


def _RWGPS_EntryToCueEntry(rwgps_entry):
  '''
  Converts a RWGPS_Entry into a cue.CueEntry.
  '''

  # We figure out the color from the RWGPS-provided instruction:
  instruction = _instructionStrToCueInstruction(rwgps_entry.instruction_str)
  modifier    = _getModifierFromRWGPSEntry(rwgps_entry)
  color       = cue.ColorFromInstruction(instruction)

  # Once that's done, overwrite the instruction with the user-provided custom one:
  custom_instruction = _parseCustomInstruction(rwgps_entry.description_str)
  if custom_instruction:
    instruction = custom_instruction
    modifier    = cue.Modifier.NONE

  clean_desc  = _cleanDescription(rwgps_entry.description_str)

  for_distance = None
  if rwgps_entry.next_absolute_distance:
    for_distance = rwgps_entry.next_absolute_distance - rwgps_entry.absolute_distance

  return cue.Entry(instruction,
                   clean_desc,
                   rwgps_entry.absolute_distance,
                   rwgps_entry.note_str,
                   modifier,
                   for_distance,
                   color)
