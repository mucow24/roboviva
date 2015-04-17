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
from roboviva import latex
from roboviva import tex

def main(argv):
  if len(argv) != 2:
    print "Usage: %s route_id" % argv[0]
    return 1

  route_id = int(argv[1])
  print "%% Downloading route from ridewithgps...",
  etag, cues = ridewithgps.getETagAndCuesheet_viaJSON(route_id)
  print "%% Done [etag: %s]" % etag
  src = latex.makeLatex(cues)
  print src

if __name__ == "__main__":
  sys.exit(main(sys.argv))
