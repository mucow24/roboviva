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
import cue

class CueTestCase(unittest.TestCase):
  '''Tests for the cue library'''

  def test_ColorFromInstruction(self):
    # These have dedicated colors:
    self.assertEqual(cue.Color.GRAY, cue.ColorFromInstruction(cue.Instruction.RIGHT))
    self.assertEqual(cue.Color.YELLOW, cue.ColorFromInstruction(cue.Instruction.PIT))
    self.assertEqual(cue.Color.YELLOW, cue.ColorFromInstruction(cue.Instruction.DANGER))
    # Spot-check some of the other instructions:
    self.assertEqual(cue.Color.NONE, cue.ColorFromInstruction(cue.Instruction.LEFT))
    self.assertEqual(cue.Color.NONE, cue.ColorFromInstruction(cue.Instruction.CUSTOM))
    self.assertEqual(cue.Color.NONE, cue.ColorFromInstruction(cue.Instruction.ROUTE_START))
  
if __name__ == '__main__':
  unittest.main()
