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
import cue_utils
import hashlib
import json
import re
import socket
import urllib
import urllib.request

from typing import List, Optional

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

def getETagAndCuesheet_viaJSON(route_id: int, etag: Optional[str] = None, api_key: Optional[str] = None):
  '''
      Queries RideWithGPS for the cue data for 'route_id'. If 'etag' is
      non-None, then 'etag' is passed to the server in the 'If-None-Match' HTTP
      header.

      Returns: A 2-tuple of the server's ETag, and either a cue.Route object,
      if new data was on the server, or "None", if 'etag' is still current.

      NOTE: This method fetches the route info via RWGPS's JSON export feature,
            which DOES include the route name and other metadata.

      route_id - The numeric route ID to fetch. (e.g. '12345' in ridewithgps.com/routes/12345)
      etag     - The HTTP ETag header returned by the server the last time we
                 asked for this route, or "None" if this is a new route, or we
                 want a fresh copy.
      api_key  - A RWGPS api_key to use when requesting the json. For now, this
                 seems to be unnecessary, so passing 'None' is OK.

      Throws a RideWithGpsError in the event of a problem (invalid route id, etc.)
  '''
  url = "http://ridewithgps.com/routes/{}.json?api_key={}&version=2".format(route_id, api_key)
  req = urllib.request.Request(url)
  if etag:
    req.add_header("If-None-Match", etag)

  raw_json = None
  Max_Attempts = 3
  for n_tries in range(Max_Attempts):
    try:
      resp = urllib.request.urlopen(req, timeout = 5)
      new_etag = resp.info()["ETag"]
      raw_json = resp.read()
      break
    except urllib.request.HTTPError as e:
      # This might be a 304: Not Modified, which means the etag we passed was still current:
      if e.code == 304:
        # Return the original ETag, and 'None" for the cue entries, as specified:
        return (etag, None)

      # Otherwise, this is probably a 404:
      raise RideWithGpsError("Unknown Route ID: %s" % route_id)
    except socket.timeout as e:
      # Timeout, let this pass:
      pass
  if not raw_json:
    raise RideWithGpsError("No data from RideWithGPS after %d tries" % Max_Attempts)

  try:
    data = json.loads(raw_json)
  except ValueError:
    raise RideWithGpsError("Error decoding JSON output:\n %s" % raw_json)

  # We can convert these into RWGPS_Entry objects pretty trivially, so we do it all here:
  route_name = data['route']['name']
  rwgps_entries = []
  Miles_Per_Meter = 0.000621371192
  Feet_Per_Meter  = 3.28084

  # The JSON data doesn't contain a "Start of Route" marker, so we add one manually:
  rwgps_entries.append(RWGPS_Entry(instruction_str = "Start",
                                   description_str = "Start of route",
                                   absolute_distance = 0.0,
                                   prev_absolute_distance = None,
                                   next_absolute_distance = None,
                                   note_str = None))

  for i, course_point in enumerate(data['route']['course_points']):
    description = "" # Called the 'note' by RWGPS
    note        = "" # Called the 'description' by RWGPS
    if 'n' in course_point:
      description = course_point['n']
    if 'description' in course_point:
      note = course_point['description']
    instruction = course_point['t']
    # Distance is in meters, but we want our silly miles:
    distance    = course_point['d'] * Miles_Per_Meter
    rwgps_entries.append(RWGPS_Entry(instruction_str = instruction,
                                     description_str = description,
                                     absolute_distance = distance,
                                     prev_absolute_distance = None, # WIll fill in below
                                     next_absolute_distance = None, # Will fill in below
                                     note_str = note))
    # This is always safe, since the "Start of route" entry guarantees [i - 1]
    # is a valid index, here:
    rwgps_entries[-1].prev_absolute_distance = rwgps_entries[-2].absolute_distance
    rwgps_entries[-2].next_absolute_distance = rwgps_entries[-1].absolute_distance

  # As of API version 2, there is no "End of Route" entry, so we add one
  # ourselves, for the "for" distance on the last cue entry is correct.
  end_distance_mi = data['route']['metrics']['distance'] * Miles_Per_Meter
  rwgps_entries.append(RWGPS_Entry(instruction_str = "End",
                                   description_str = "End of route",
                                   absolute_distance = end_distance_mi,
                                   prev_absolute_distance = None,
                                   next_absolute_distance = None,
                                   note_str = None))
  rwgps_entries[-1].prev_absolute_distance = rwgps_entries[-2].absolute_distance
  rwgps_entries[-2].next_absolute_distance = rwgps_entries[-1].absolute_distance

  route = cue.Route([_RWGPS_EntryToCueEntry(entry) for entry in rwgps_entries],
                    route_id   = route_id,
                    route_name = route_name,
                    elevation_gain_ft = data['route']['metrics']['ele_gain'] * Feet_Per_Meter,
                    length_mi = end_distance_mi)

  cue_utils.AdjustStartAndEnd(route)
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

def _instructionStrToCueInstruction(instruction_str: str) -> (str, Optional[str]):
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
  elif instruction_str == "Start":
    return cue.Instruction.ROUTE_START
  elif instruction_str == "End":
    return cue.Instruction.ROUTE_END
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
    return cue.Instruction.CUSTOM

def _getModifierFromRWGPSEntry(entry: RWGPS_Entry, quick_threshold_mi : float = 0.1) -> cue.Modifier:
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

def _parseCustomInstruction(raw_description: str) -> Optional[str]:
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

  # We figure out the color from the *original* RWGPS-provided instruction, this is so
  # turns, pits, etc. with [custom instructions] are colored properly.
  instruction: cue.Instruction = _instructionStrToCueInstruction(rwgps_entry.instruction_str)
  modifier: cue.Modifier = _getModifierFromRWGPSEntry(rwgps_entry)
  color: cue.Color = cue.ColorFromInstruction(instruction)
  
  # Once that's done, overwrite the instruction with the user-provided custom one:
  custom_instruction: Optional[str] = _parseCustomInstruction(rwgps_entry.description_str)
  if custom_instruction:
    instruction = cue.Instruction.CUSTOM
    modifier    = cue.Modifier.NONE

  clean_desc  = _cleanDescription(rwgps_entry.description_str)

  for_distance = None
  if rwgps_entry.next_absolute_distance:
    for_distance = rwgps_entry.next_absolute_distance - rwgps_entry.absolute_distance

  if rwgps_entry.note_str is None:
    rwgps_entry.note_str = ""

  return cue.Entry(instruction,
                   clean_desc,
                   rwgps_entry.absolute_distance,
                   rwgps_entry.note_str,
                   modifier,
                   for_distance,
                   color,
                   custom_instruction=custom_instruction)
