import cue
import csv
import urllib2
import hashlib
import re

class RideWithGpsError(Exception):
  '''Thrown by getCueSheet() in the event of an error'''
  pass

def getMd5AndCueSheet(route_id):
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
  except urllib2.HTTPError as e:
    raise RideWithGpsError("Unknown Route ID: %s" % route_id)

  # Compute raw csv MD5:
  md5 = hashlib.md5(raw_csv).hexdigest()
  
  # Read in CSV rows:
  reader = csv.DictReader(raw_csv.split("\n"),
                          ['type', 'note', 'absolute_distance', 'elevation', 'description'])
  rows   = [row for row in reader]
  rows   = rows[1:] # Prune header

  # Augment the rows:
  # We need to figure out for_distances, as well as if a particular entry is
  # 'quick'; we do this by augmenting the row with the absolute distance of the
  # prior instruction (or None if this is the first instruction) and the next
  # instruction (or None if this is the last). We'll use these when converting
  # to the cue.Entry.
  for i, row in enumerate(rows):
    row["prev_absolute_distance"] = None
    row["next_absolute_distance"] = None

    if i is 0:
      continue # Start of route, skip this

    # Fill in prev/next distances
    rows[i - 1]['next_absolute_distance'] = row['absolute_distance']
    row['prev_absolute_distance']         = rows[i - 1]['absolute_distance']

  return (md5, [csvRowToCueEntry(row) for row in rows])

def cleanDescription(description):
  ''' 
    Clean up the description.

    RWGPS Duplicates the instruction in the description, e.g. "Right on Foo
    St.", instead of "Foo St.". This blows up the "On" column in the final
    sheet, so try to fix it as best we can.

    description - the original ridewithgps description string, e.g. "Turn right onto Foo St."
  '''
  description = re.sub("^At the traffic circle,",                     "@ Circle,", description)
  description = re.sub("^(Slight|Turn) (left|right) (toward|onto) ",   "",         description)
  description = re.sub("^(Slight|Turn|Keep) (left|right) to stay on",  "TRO",      description)
  description = re.sub("to stay on",                                   "TRO",      description)
  description = re.sub("to remain on",                                 "TRO",      description)
  description = re.sub("^(Slight|Turn|Bear) (left|right) ",            "",         description)
  description = re.sub("^(Left|Right) onto ",                          "",         description)
  description = re.sub("^Continue onto ",                              "",         description)
  description = re.sub("^Continue straight onto ",                     "",         description)
  return description

def csvRowToCueEntry(csv_row):
  '''Converts a ridewithgps CSV row into a cue.CueEntry. Assumes the following CSV layout:
     type,note,distance,elevation,description

     'csv_row' should be of dictionary type, with the following key -> value mappings:
     type                   -> instruction
     note                   -> description
     absolute_distance      -> absolute_distance
     next_absolute_distance -> (the abs distance of the next instruction, or None)
     prev_absolute_distance -> (the abs distance of the prev instruction, or None)
     description            -> notes
  '''
  instruction_str = csv_row['type']
  description     = csv_row['note']
  distance        = float(csv_row['absolute_distance'])
  notes           = csv_row['description']
  for_distance    = None

  if csv_row['next_absolute_distance']:
    for_distance = float(csv_row['next_absolute_distance']) - distance

  # Figure out the (base) instruction:
  instruction = None
  if instruction_str == "Left":
    instruction = cue.Instruction.LEFT
  elif instruction_str == "Right":
    instruction = cue.Instruction.RIGHT
  elif instruction_str == "Straight":
    instruction = cue.Instruction.STRAIGHT
  elif instruction_str in ("Food", "Water"):
    instruction = cue.Instruction.PIT
  elif instruction_str == "Danger":
    instruction = cue.Instruction.DANGER
  elif instruction_str in ("Start", "End", "Generic", "Summit"):
    instruction = cue.Instruction.NONE
  else:
    # Just punt to whatever they gave us:
    instruction = instruction_str

  # See if we can apply any modifiers yet:
  modifier = cue.Modifier.NONE
  if instruction in (cue.Instruction.LEFT, cue.Instruction.RIGHT):
    # RWGPS will use the terms "Keep [left|right]" or "Bear [left|right]" to
    # indicate slight turns:
    if re.match("^(Keep|Bear|Slight) ", description):
      modifier = cue.Modifier.SLIGHT
    elif csv_row['prev_absolute_distance']:
      # If this instruction is < 0.1 miles from the prior one, call it 'quick':
      dist_from_prev = distance - float(csv_row['prev_absolute_distance'])
      if dist_from_prev < 0.1:
        modifier = cue.Modifier.QUICK

  return cue.Entry(instruction,
                   cleanDescription(description),
                   distance,
                   notes,
                   modifier,
                   for_distance)
