import random
import reportlab
from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, PageTemplate, Frame, Table, TableStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus.flowables import BalancedColumns, KeepTogether
from reportlab.lib import colors
from typing import List, Optional


import cue
import reportlab.pdfgen as pdfgen
import copy
import sys


import csv
import enum

'''The action a particular cue entry represents'''
class Instruction(enum.Enum):
        LEFT        = "L"
        RIGHT       = "R"
        STRAIGHT    = "S"

'''An instruction modifier. Only really makes sense for LEFT and RIGHT, at the moment'''
class Modifier (enum.Enum):
    NONE   = ""
    SLIGHT = "B"
    QUICK  = "Q"

'''The background color this cue entry should have'''
class Color(enum.Enum):
    NONE = "None"
    GRAY = "Gray"
    YELLOW = "Yellow"

def ColorFromInstruction(instruction):
  '''
  Given a cue.Instruction, return the cue.Color associated with it.
  '''
  if instruction in (Instruction.PIT, Instruction.DANGER):
    return Color.YELLOW
  elif instruction in (Instruction.RIGHT):
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

class Route(object):
  '''Simple storage class representing a route. This is just a list of Entrys,
  plus some metadata (title, route #, etc.)'''
  def __init__(self,
               entries,
               length_mi,
               route_id,
               route_name = None,
               elevation_gain_ft = None):
    '''
      Inits the storage members of the class:
      - entries:      A list of Entry objects
      - length_mi:    The total length of the route, in miles.
      - route_id:     The RWGPS route # for this route
      - route_name:   The name of this route (Optional)
      - elevation_gain_ft : The amount of climb in this route, in ft (Optional)
    '''
    self.name    = route_name
    self.id      = route_id
    self.entries = entries
    self.elevation_gain_ft = elevation_gain_ft
    self.length_mi = length_mi

  def __repr__(self):
    ret = ""
    ret += "Route:\n"
    ret += "  Name:  \"%s\"" % self.name
    ret += "  Id:    %s" % self.id
    ret += "  Climb: %s ft" % self.elevation_gain_ft
    ret += "  Length: %s mi\n" % self.length_mi
    for entry in self.entries:
      ret += "    %s\n" % entry
    return ret


entries = []
total_distance = 0.0
prev_for_dist = 0.0
for i in range(150):
    for_dist = random.random() * 13.0
    modifier = '' if random.random() < 0.5 else 'B'
    if prev_for_dist != 0 and prev_for_dist < 0.4:
      modifier = 'Q'
    instruction = "L" if random.random() < 0.5 else 'R'
    entries.append(Entry(modifier + instruction, "On foo turnpike " * random.randint(1, 3), total_distance, for_distance=for_dist, modifier=modifier))
    total_distance += for_dist
    prev_for_dist = for_dist


kPageSize = letter
kPageWidth, kPageHeight = kPageSize

kOuterMargin = 0.35 * inch
kMiddleMargin = 0.25 * inch

kHeaderHeight = 0.125 * inch
kFooterHeight = 1.0 * inch

kColWidth = (kPageWidth - (2.0 * kOuterMargin) - kMiddleMargin) / 2.0
kColHeight = kPageHeight - (2 * kOuterMargin) - kHeaderHeight - kFooterHeight

kGoCellWidth = 0.33 * inch
kAtCellWidth = 0.5 * inch
kForCellWidth = 0.4 * inch
kOnCellWidth = max(1.0 * inch, kColWidth - kGoCellWidth - kAtCellWidth - kForCellWidth)

class NumberedCanvas(reportlab.pdfgen.canvas.Canvas):
    def __init__(self, *args, **kwargs):
        reportlab.pdfgen.canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            reportlab.pdfgen.canvas.Canvas.showPage(self)
        reportlab.pdfgen.canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica-Oblique", 10)
        self.drawCentredString(kPageWidth / 2.0, kOuterMargin,
            "Page %d of %d" % (self._pageNumber, page_count))


metadata = ('Test Ride', total_distance, 1234, '123456')

def page(canvas, doc):
    print("page!")
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 11)
    header_str_left = "{} ({:0.1f} mi / {:d} ft)".format(metadata[0], metadata[1], metadata[2])
    header_str_right = "Route #{}".format(metadata[3])
    header_height = kOuterMargin + kFooterHeight + kColHeight + kHeaderHeight * 1.0
    canvas.drawString(kOuterMargin, header_height, header_str_left)
    line_offset_vertical = 0.05 * inch
    line_offset_horizontal = 0.1 * inch
    canvas.line(
        kOuterMargin - line_offset_horizontal,
        header_height - line_offset_vertical,
        kPageWidth - kOuterMargin + line_offset_horizontal,
        header_height - line_offset_vertical)
    canvas.drawRightString(kPageWidth - kOuterMargin, header_height, header_str_right)
    canvas.restoreState()

class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        print(kPageWidth)
        print(kOuterMargin)
        print(kMiddleMargin)
        print(kPageWidth - kOuterMargin - kOuterMargin - kMiddleMargin)
        print(kColWidth)
        col1_xpos = kOuterMargin
        col_ypos = kOuterMargin + kFooterHeight
        col2_xpos = kOuterMargin + kColWidth + kMiddleMargin
        template = PageTemplate('normal', [
                Frame(col1_xpos, col_ypos, kColWidth, kColHeight, id='LeftColumn'),
                Frame(col2_xpos, col_ypos, kColWidth, kColHeight, id='RightColumn')],
                onPage=page)
        self.addPageTemplates(template)

class XTable(Table):
    def onSplit(self, T, byRow=1):
        pass
        #print(T)
        #T.setStyle(TableStyle([

        #  ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        #  ('BACKGROUND', (0, 0), (0, -1), colors.black)]))

def main(argv : List[str]) -> int:
    doc = MyDocTemplate("doc.pdf", pagesize=kPageSize) # allowSplitting = False)
    stylesheet = getSampleStyleSheet()
    #paragraphs = []
    h_style = copy.deepcopy(stylesheet['Normal'])
    h_style.textColor = colors.white
    h_style.background = colors.black
    h_style.fontName = "Helvetica"
    h_style.fontSize = 12
    header_row = [
      Paragraph("<b>Go</b>", h_style),
      Paragraph("<b>At</b>", h_style),
      Paragraph("<b>On</b>", h_style),
      Paragraph("<b>For</b>", h_style),
    ]
    rows = [header_row]
    i = 0
    for entry in entries:
      row = []
      r_style = copy.deepcopy(stylesheet['Normal'])
      r_style.textColor = colors.black
      r_style.background = colors.white
      r_style.fontName = "Helvetica"
      r_style.fontSize = 11

      g_style = copy.deepcopy(r_style)
      g_style.alignment = 1
      row.append(Paragraph("<b>{}</b>".format(str(entry.instruction)), g_style))
      row.append(Paragraph("{:0.1f}".format(entry.absolute_distance), r_style))
      row.append(Paragraph(entry.description, r_style))
      row.append(Paragraph("{:0.1f}".format(entry.for_distance), r_style))
      rows.append(row)
      i += 1

    row_colors = [(5, colors.yellow)]
    cell_padding = 0.04 * inch
    table_style = [
          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
          ('LEFTPADDING', (0,0), (-1, -1), cell_padding),
          ('RIGHTPADDING', (0,0), (-1, -1), cell_padding),
          ('BOTTOMPADDING', (0,0), (-1, -1), cell_padding),
          ('TOPPADDING', (0,0), (-1, -1), cell_padding),
          ('GRID', (0,0), (-1,-1), 0.25, colors.black),
          ('ROWBACKGROUNDS', (0,1), (-1, -1), [colors.white, colors.Color(0.8, 0.8, 0.8)]),
          ('ROWBACKGROUNDS', (0, 0), (-1, 0), [colors.black])
    ]

    for row, color in row_colors:
      table_style.append(('BACKGROUND', (0, row), (-1, row), color))
    t = XTable(rows, 
        [kGoCellWidth, kAtCellWidth, kOnCellWidth, kForCellWidth], repeatRows=1)
    t.setStyle(TableStyle(table_style))
    doc.build([t], canvasmaker=NumberedCanvas)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
