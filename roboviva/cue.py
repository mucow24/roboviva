import csv
import enum

'''The action a particular cue entry represents'''
Instruction = enum.Enum(LEFT        = "L",
                        RIGHT       = "R",
                        STRAIGHT    = "S",
                        PIT         = "PIT",
                        DANGER      = "!",
                        CROSSES     = "X",
                        CAT_HC      = "CHC",
                        CAT_1       = "C1",
                        CAT_2       = "C2",
                        CAT_3       = "C3",
                        CAT_4       = "C4",
                        CAT_5       = "C5",
                        SUMMIT      = "^",
                        FIRST_AID   = "+",
                        NONE        = "")

'''An instruction modifier. Only really makes sense for LEFT and RIGHT, at the moment'''
Modifier = enum.Enum(NONE   = "",
                     SLIGHT = "B",
                     QUICK  = "Q")

'''The background color this cue entry should have'''
Color = enum.Enum(NONE = "None",
                  GRAY = "Gray",
                  YELLOW = "Yellow")

def ColorFromInstruction(instruction):
  '''
  Given a cue.Instruction, return the cue.Color associated with it.
  '''
  if instruction in (Instruction.PIT, Instruction.DANGER):
    return Color.YELLOW
  elif instruction in (Instruction.LEFT):
    return Color.GRAY
  else:
    return Color.NONE

class Entry(object):
  '''Simple storage class representing a single cue sheet entry. Nothing fancy.'''
  def __init__(self, 
              instruction,
              description,
              absolute_distance,
              note         = "",
              modifier     = Modifier.NONE,
              for_distance = None,
              color        = Color.NONE):
    ''' Inits a CueEntry.
        instruction       - The entry's Instruction (see above)
        description       - The entry's 'action' (e.g., 'Turn right on Pine St')
        absolute_distance - How far this entry is from the ride's start (miles)
        note              - Optional. Any additional notes on this entry.
        modifier          - Optional. A Modifier to apply to the Instruction.
        for_distance      - Optional. How long from this entry to the next entry.
        color             - Optional. The color of this cue entry.
    '''
    self.instruction       = instruction
    self.description       = description
    self.absolute_distance = float(absolute_distance)
    self.note              = note
    self.modifier          = modifier
    self.for_distance      = for_distance
    self.color             = color

  def __repr__(self):
    for_str = ""
    if self.for_distance:
      for_str = "%5.2f" % self.for_distance
    else:
      for_str = "     "

    return "Entry[%s%s | %5.2f | %s | %s | %s | %s]" % (self.modifier, 
                                                   self.instruction,
                                                   self.absolute_distance,
                                                   for_str,
                                                   self.description,
                                                   self.note, 
                                                   self.color)
