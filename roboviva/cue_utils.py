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

def AdjustStartAndEnd(route : cue.Route):
  '''
  Scans the Route 'route' for entries tagged with [start] and [end] in their
  description. If found, these replace the default "Start of route" and "End of
  Route" cue entries.

  'route' is modified in-place.
  '''
  for index, entry in enumerate(route.entries):
    if entry.instruction == cue.Instruction.ROUTE_START:
      entry.absolute_distance = 0.0
      entry.for_distance = route.entries[1].absolute_distance
      entry.instruction = cue.Instruction.NONE
      route.entries[0] = entry
      prev_entry = route.entries[index - 1]
      next_entry = route.entries[index + 1]
      prev_entry.for_distance = next_entry.absolute_distance - prev_entry.absolute_distance
      del route.entries[index]
    elif entry.instruction == cue.Instruction.ROUTE_END:
      last_entry = route.entries[-1]
      penultimate_entry = route.entries[-2]
      penultimate_entry.for_distance = \
          last_entry.absolute_distance - penultimate_entry.absolute_distance
      entry.absolute_distance = last_entry.absolute_distance
      entry.for_distance = None
      entry.instruction = cue.Instruction.NONE
      route.entries[-1] = entry
      prev_entry = route.entries[index - 1]
      next_entry = route.entries[index + 1]
      prev_entry.for_distance = next_entry.absolute_distance - prev_entry.absolute_distance
      del route.entries[index]
