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

import sys
from roboviva import ridewithgps
from roboviva import reportlab_renderer
from roboviva import cue

def main(argv):

  cues = [
    cue.Entry(cue.Instruction.ROUTE_START, "Start", 0.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.LEFT, "Left turn", 1.0, "note", cue.Modifier.NONE, 0.3, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.LEFT, "Bear left", 1.3, "note", cue.Modifier.SLIGHT, 0.3, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.LEFT, "Quick left", 1.6, "note", cue.Modifier.QUICK, 0.4, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.RIGHT, "Right turn", 2.0, "note", cue.Modifier.NONE, 1.0, cue.Color.GRAY, None),
    cue.Entry(cue.Instruction.STRAIGHT, "Straight", 3.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.PIT, "Pit stop", 4.0, "note", cue.Modifier.NONE, 1.0, cue.Color.YELLOW, None),
    cue.Entry(cue.Instruction.DANGER, "Danger", 5.0, "note", cue.Modifier.NONE, 1.0, cue.Color.YELLOW, None),
    cue.Entry(cue.Instruction.CROSSES, "Crosses", 6.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CAT_HC, "Climb (HC)", 7.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CAT_1, "Climb C1", 8.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CAT_2, "Climb C2", 9.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CAT_3, "Climb C3", 10.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CAT_4, "Climb C4", 11.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CAT_5, "Climb C5", 12.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.SUMMIT, "Summit", 13.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.FIRST_AID, "First Aid", 14.0, "note", cue.Modifier.NONE, 1.0, cue.Color.YELLOW, None),
    cue.Entry(cue.Instruction.NONE, "None", 15.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.NONE, "Inline *formatting* **test**", 16.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.NONE, "<html> escape <test> & ! @ $ # % ^ * ( ) punctuation test", 17.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, None),
    cue.Entry(cue.Instruction.CUSTOM, "Custom", 18.0, "note", cue.Modifier.NONE, 1.0, cue.Color.NONE, "CUS"),
    cue.Entry(cue.Instruction.ROUTE_END, "End", 19.0, "note", cue.Modifier.NONE, None, cue.Color.NONE, None),
  ]
  route = cue.Route(cues, 19.0, 1234, "Renderer test", 0.0)

  reportlab_renderer.ReportLabRenderer.MakePDF(route, 'roboviva_test_pdf.pdf')
  print("Done.")

if __name__ == "__main__":
  sys.exit(main(sys.argv))
