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

import unittest
from roboviva import ridewithgps
from roboviva import cue
import roboviva.tex

class RWGPSTestCase(unittest.TestCase):
  '''Tests for Roboviva's RWGPS-facing functions'''

  def test_RWGPS_EntryToCueEntry(self):
    pass

  def test_instructionToInstruction(self):
    '''Just sanity check:'''
    ins = {'Left'     : cue.Instruction.LEFT,
           'Right'    : cue.Instruction.RIGHT,
           'Straight' : cue.Instruction.STRAIGHT,
           'Food'     : cue.Instruction.PIT,
           'Water'    : cue.Instruction.PIT,
           'Danger'   : cue.Instruction.DANGER,
           'Start'    : cue.Instruction.ROUTE_START,
           'End'      : cue.Instruction.ROUTE_END,
           'Generic'  : cue.Instruction.CUSTOM,
           '4th Category'  : cue.Instruction.CAT_4,
           '3rd Category'  : cue.Instruction.CAT_3,
           '2nd Category'  : cue.Instruction.CAT_2,
           '1st Category'  : cue.Instruction.CAT_1,
           'Hors Category' : cue.Instruction.CAT_HC,
           'Test Instruction' : cue.Instruction.CUSTOM}
    for s in ins:
      self.assertEqual(ins[s], ridewithgps._instructionStrToCueInstruction(s))

  def test_RWGPSUnknownEntryType(self):
    '''Make sure we don't barf out if RWGPS adds new instructions'''
    rwgps_entry = ridewithgps.RWGPS_Entry(instruction_str        = "XXX",
                                          description_str        = "Slight left",
                                          absolute_distance      = 10.0,
                                          prev_absolute_distance = 9.0,
                                          next_absolute_distance = 11.0,
                                          note_str               = "")
    cue_ent = ridewithgps._RWGPS_EntryToCueEntry(rwgps_entry)
    print(cue_ent) 
    self.assertEqual(cue.Instruction.CUSTOM, cue_ent.instruction)
    self.assertNotEqual(None, cue_ent.custom_instruction)


  def test_getModifierFromRWGPSEntry(self):
    slight_ent = ridewithgps.RWGPS_Entry(instruction_str        = "Left",
                                         description_str        = "Slight left",
                                         absolute_distance      = 10.0,
                                         prev_absolute_distance = 9.0,
                                         next_absolute_distance = 11.0,
                                         note_str               = "")
    self.assertEqual(cue.Modifier.SLIGHT, ridewithgps._getModifierFromRWGPSEntry(slight_ent))

    none_ent = ridewithgps.RWGPS_Entry(instruction_str        = "Left",
                                       description_str        = "Turn left",
                                       absolute_distance      = 10.0,
                                       prev_absolute_distance = 9.0,
                                       next_absolute_distance = 11.0,
                                       note_str               = "")
    self.assertEqual(cue.Modifier.NONE, ridewithgps._getModifierFromRWGPSEntry(none_ent))

    none_ent_2 = ridewithgps.RWGPS_Entry(instruction_str        = "Food",
                                       description_str        = "Bear Mt Inn",
                                       absolute_distance      = 10.0,
                                       prev_absolute_distance = 9.0,
                                       next_absolute_distance = 11.0,
                                       note_str               = "")
    self.assertEqual(cue.Modifier.NONE, ridewithgps._getModifierFromRWGPSEntry(none_ent_2))

    quick_ent = ridewithgps.RWGPS_Entry(instruction_str        = "Left",
                                       description_str        = "Turn left",
                                       absolute_distance      = 10.0,
                                       prev_absolute_distance = 9.9,
                                       next_absolute_distance = 11.0,
                                       note_str               = "")
    self.assertEqual(cue.Modifier.QUICK, ridewithgps._getModifierFromRWGPSEntry(quick_ent))

    quick_ent_2 = ridewithgps.RWGPS_Entry(instruction_str        = "Left",
                                       description_str        = "Turn left",
                                       absolute_distance      = 10.0,
                                       prev_absolute_distance = 9.5,
                                       next_absolute_distance = 11.0,
                                       note_str               = "")
    self.assertEqual(cue.Modifier.QUICK, ridewithgps._getModifierFromRWGPSEntry(quick_ent, quick_threshold_mi=0.5))

  def test_cleanDescription(self):
    descs = { "At the traffic circle, foo" : "@ Circle, foo",
              "Slight left toward foo"     : "foo",
              "Slight right onto foo"      : "foo",
              "Bear left on foo"           : "foo",
              "Keep right toward foo"      : "foo",
              "Bear right to stay on foo"  : "TRO foo",
              "Bear right to remain on foo": "TRO foo",
              "Continue onto foo"          : "foo",
              "Continue straight onto foo" : "foo",
              "Continue straight on foo"   : "foo",
        }
    for desc in descs:
      self.assertEqual(descs[desc], ridewithgps._cleanDescription(desc))

  def test_parseCustomInstruction(self):
    descs_insts = [ ("[L/QR] Foo Bar", "L/QR"),     # Common case
                    ("   [L/QR] Foo Bar", "L/QR"),  # Starting whitespace (OK)
                    ("[] Foo Bar",     None),       # Instruction must be at least one character
                    ("Foo [L] Bar",    None),       # Must be at the start of the description
                    ("[L/QR] Foo [Rough]", "L/QR"), # Make sure it's not greedily matching
                  ]
    for desc_exp in descs_insts:
      desc, exp = desc_exp
      instruction = ridewithgps._parseCustomInstruction(desc)
      self.assertEqual(exp, instruction)

  def test_RWGPSEntryToCueEntry(self):
    basic_ent = ridewithgps.RWGPS_Entry(instruction_str        = "Left",
                                        description_str        = "Turn left on Foobar St.",
                                        absolute_distance      = 10.0,
                                        prev_absolute_distance = 9.5,
                                        next_absolute_distance = 11.0,
                                        note_str               = "Note!")
    cue_ent = ridewithgps._RWGPS_EntryToCueEntry(basic_ent)
    self.assertEqual(cue.Instruction.LEFT, cue_ent.instruction)
    self.assertEqual(cue.Modifier.NONE,    cue_ent.modifier)
    self.assertEqual("Foobar St.", cue_ent.description)
    self.assertEqual(basic_ent.note_str, cue_ent.note)
    self.assertEqual(basic_ent.absolute_distance, cue_ent.absolute_distance)
    self.assertEqual(basic_ent.next_absolute_distance - basic_ent.absolute_distance,
                     cue_ent.for_distance)

    quick_ent = basic_ent
    quick_ent.absolute_distance = 10.0
    quick_ent.prev_absolute_distance = 9.9
    cue_ent = ridewithgps._RWGPS_EntryToCueEntry(quick_ent)
    self.assertEqual(cue_ent.modifier,    cue.Modifier.QUICK)
    self.assertEqual(cue_ent.instruction, cue.Instruction.LEFT)

    custom_ent = basic_ent
    custom_ent.description_str = "[Custom Instruction] Left onto Foo Bar Baz"
    cue_ent = ridewithgps._RWGPS_EntryToCueEntry(custom_ent)
    self.assertEqual(cue_ent.modifier,    cue.Modifier.NONE)
    self.assertEqual(cue_ent.instruction, cue.Instruction.CUSTOM)
    self.assertEqual(cue_ent.custom_instruction, "Custom Instruction")
    self.assertEqual("Foo Bar Baz", cue_ent.description)

  def test_RWGPSQueryAndParse_JSON(self):
    Route_Id      = "6260667"
    Route_Name    = "Roboviva Unit Test Route"
    Expected_ETag = "W/\"5e668792f4c8bd376091dd89f3648698\""
    Route_Length  = 0.5
    Route_Climb   = 16.

    # Note we do NOT pass in 'Expected_ETag', here, so we always get the full
    # set of cue data:
    etag, route = ridewithgps.getETagAndCuesheet_viaJSON(Route_Id)

    if etag != Expected_ETag:
      print("Queried RWGPS (route id %s):" % Route_Id)
      print("\tGot etag: %s" % etag)
      print("\tExp etag: %s" % Expected_ETag)
      print("Skipping end-to-end test.")
      self.skipTest("MD5 mismatch: expected %s, got %s (route id: %s)" % (Expected_ETag, etag, Route_Id))

    self.assertEqual(Route_Id, route.id)
    self.assertEqual(Route_Name, route.name)
    self.assertAlmostEqual(Route_Length, route.length_mi, places = 1)
    self.assertAlmostEqual(Route_Climb, route.elevation_gain_ft, places = 0)
    cues = route.entries
                      # Desc              Instruction                  Modifier            Color          Custom Ins.   Dist  For   Note
    expected_cues = [("Start of route",   cue.Instruction.ROUTE_START, cue.Modifier.NONE,  cue.Color.NONE,   None,     0.0,  0.19, ""),
                     ("A",                cue.Instruction.CUSTOM,      cue.Modifier.NONE,  cue.Color.GRAY,   "Custom", 0.19, 0.09, ""),
                     ("B",                cue.Instruction.RIGHT,       cue.Modifier.QUICK, cue.Color.GRAY,   None,     0.28, 0.08, ""),
                     ("CVS on Right",     cue.Instruction.PIT,         cue.Modifier.NONE,  cue.Color.YELLOW, None,     0.36, 0.08, "Test note"),
                     ("C",                cue.Instruction.LEFT,        cue.Modifier.NONE,  cue.Color.NONE,   None,     0.47, 0.08, ""),
                     ("Custom end entry", cue.Instruction.ROUTE_END,   cue.Modifier.NONE,  cue.Color.NONE,   None,     0.55, None, "")]

    self.assertEqual(len(expected_cues), len(cues))
    for i, exp in enumerate(expected_cues):
      desc, ins, mod, color, custom_ins, dist, for_dist, note = exp
      self.assertEqual(desc,           cues[i].description)
      self.assertEqual(ins,            cues[i].instruction)
      self.assertEqual(custom_ins,     cues[i].custom_instruction)
      self.assertEqual(color,          cues[i].color)
      self.assertEqual(mod,            cues[i].modifier)
      self.assertAlmostEqual(dist,     cues[i].absolute_distance, places = 1)
      self.assertAlmostEqual(for_dist, cues[i].for_distance, places = 1)
      self.assertEqual(note,           cues[i].note)

    # Finally, query RWGPS again, this time passing in Expected_ETag, to verify
    # the call returns 'None' as expected:
    etag, cues = ridewithgps.getETagAndCuesheet_viaJSON(Route_Id, Expected_ETag)
    self.assertEqual(None, cues)
    self.assertEqual(Expected_ETag, etag)
  

  

if __name__ == '__main__':
  unittest.main()
