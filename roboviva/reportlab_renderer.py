import random
import reportlab
from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, PageTemplate, Frame, Table, TableStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus.flowables import BalancedColumns, KeepTogether
from reportlab.lib import colors

from typing import List

from . import cue

import datetime

import reportlab.pdfgen as pdfgen
import copy
import sys
import re


import csv
import enum

class ReportLabRenderer(object):
    @staticmethod
    def MakePDF(route: cue.Route, pdf_filename: str):
        doc = MyDocTemplate(pdf_filename, pagesize=MyDocTemplate.kPageSize, route=route)
        stylesheet = reportlab.lib.styles.getSampleStyleSheet()
        header_style = copy.deepcopy(stylesheet['Normal'])
        header_style.textColor = colors.white
        header_style.background = colors.black
        header_style.fontName = "Helvetica"
        header_style.fontSize = 12
        header_row = [
          Paragraph("<b>Go</b>", header_style),
          Paragraph("<b>At</b>", header_style),
          Paragraph("<b>On</b>", header_style),
          Paragraph("<b>For</b>", header_style),
        ]
        rows = [header_row]
        for i, entry in enumerate(route.entries):
          entry: cue.Entry = entry
          print(entry)
          row: List[Paragraph] = []
          row_style = copy.deepcopy(stylesheet['Normal'])
          row_style.textColor = colors.black
          row_style.background = colors.white
          row_style.fontName = "Helvetica"
          row_style.fontSize = 11
    
          instruction_style = copy.deepcopy(row_style)
          instruction_style.alignment = 1
          instruction_str = EntryToInstructionStr(entry)
          
          for_distance_str = ""
          if entry.for_distance:
            for_distance_str = "{:0.1f}".format(entry.for_distance)
          row.append(Paragraph("<b>{}</b>".format(_Escape(instruction_str)), instruction_style))
          row.append(Paragraph("{:0.1f}".format(entry.absolute_distance), row_style))
          row.append(Paragraph(_Escape(entry.description), row_style))
          row.append(Paragraph(for_distance_str, row_style))
          rows.append(row)
    
        # Generate row color overrides:
        row_colors = []
        for i, entry in enumerate(route.entries):
          row_colors += [(i + 1, _EntryColorToColor(entry.color))]

        cell_padding = 0.04 * inch
        table_style = [
              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
              ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
              ('LEFTPADDING', (0,0), (-1, -1), cell_padding),
              ('RIGHTPADDING', (0,0), (-1, -1), cell_padding),
              ('BOTTOMPADDING', (0,0), (-1, -1), cell_padding),
              ('TOPPADDING', (0,0), (-1, -1), cell_padding),
              ('GRID', (0,0), (-1,-1), 0.25, colors.black),
              ('ROWBACKGROUNDS', (0, 0), (-1, 0), [colors.black])
        ]
    
        for row, color in row_colors:
          table_style.append(('BACKGROUND', (0, row), (-1, row), color))
        t = Table(rows, 
            [MyDocTemplate.kGoCellWidth, MyDocTemplate.kAtCellWidth, MyDocTemplate.kOnCellWidth, MyDocTemplate.kForCellWidth], repeatRows=1)
        t.setStyle(TableStyle(table_style))
        doc.build([t], canvasmaker=NumberedCanvas)
        return 0

def _EntryColorToColor(entry_color: cue.Color) -> colors.Color:
  if entry_color == cue.Color.YELLOW:
    return colors.yellow
  elif entry_color == cue.Color.GRAY:
    return colors.Color(0.8, 0.8, 0.8)
  return colors.white

def EntryToInstructionStr(entry: cue.Entry) -> str:
  ret: str = ""
  if entry.instruction == cue.Instruction.CUSTOM:
    ret = entry.custom_instruction
  else:
    if entry.modifier:
      ret += entry.modifier.value
    ret += entry.instruction.value
  return ret

def _Escape(s: str) -> str:
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    # Markdown style **bold** and *italic*. The regexes below aren't perfect but they're good enough.
    # Basically just looking for "(whitespace)**(not whitespace)(stuff that's not a '*')**" and the * equivalent.
    # We do this twice, to handle one **level of *nesting* if need be**.
    # **bold**
    s = re.sub(r'(^|\s)\*\*([^\s\*])([^\*]*)\*\*', r'\1<b>\2\3</b>', s)
    # *italic*
    s = re.sub(r'(^|\s)\*([^\s\*])([^\*]*)\*', r'\1<i>\2\3</i>', s)
    # **bold**
    s = re.sub(r'(^|\s)\*\*([^\s\*])([^\*]*)\*\*', r'\1<b>\2\3</b>', s)
    # *italic*
    s = re.sub(r'(^|\s)\*([^\s\*])([^\*]*)\*', r'\1<i>\2\3</i>', s)
    return s




def MakeRandomRoute(num_entries, name = "My Rad Route", route_id = 1234, elevation_ft = 2000):
  entries = []
  prev_for_dist = 0.0
  entries.append(cue.Entry(cue.Instruction.ROUTE_START, "Start St.", 0.0, for_distance=0.5))
  total_distance = 0.5
  is_climb = False
  for i in range(num_entries):
    for_dist = random.random() * 13.0
    modifier = '' if random.random() < 0.5 else 'B'
    instruction = None
    modifier = None
    color = cue.Color.NONE
    custom_instruction = None
    if random.random() < 0.1:
      # Custom instruction
      instruction = cue.Instruction.CUSTOM
      custom_instruction = "XXX"
    else:
      if prev_for_dist != 0 and prev_for_dist < 0.4:
        modifier = cue.Modifier.QUICK
      elif random.random() < 0.2:
        modifier = cue.Modifier.SLIGHT

      instruction = cue.Instruction.LEFT
      if is_climb:
        instruction = cue.Instruction.SUMMIT
        modifier = cue.Modifier.NONE
        is_climb = False
      elif random.random() < 0.5:
        instruction = cue.Instruction.RIGHT
      elif random.random() < 0.05:
        instruction = cue.Instruction.PIT
        modifier = cue.Modifier.NONE
      elif random.random() < 0.05:
        instruction = cue.Instruction.CAT_HC
        modifier = cue.Modifier.NONE
        is_climb = True
      elif random.random() < 0.05:
        instruction = cue.Instruction.DANGER
        modifier = cue.Modifier.NONE


      if instruction == cue.Instruction.RIGHT:
          color = cue.Color.GRAY
      if instruction == cue.Instruction.PIT or instruction == cue.Instruction.DANGER:
          color = cue.Color.YELLOW

    entries.append(cue.Entry(
        instruction, "On foo turnpike " * random.randint(1, 3), total_distance,
        for_distance=for_dist, modifier=modifier, custom_instruction=custom_instruction, color=color))
    total_distance += for_dist
    prev_for_dist = for_dist

  entries.append(cue.Entry(cue.Instruction.ROUTE_END, "End St.", total_distance))
  return cue.Route(entries, total_distance, route_id, name, elevation_ft)

class NumberedCanvas(reportlab.pdfgen.canvas.Canvas):
    """
    ReportLab Canvas subclass that adds 'page X of Y' in the footer.

    Modified version of the solution proposed by https://stackoverflow.com/questions/51498663/properly-add-page-numbers-and-total-number-of-pages-to-pdf-using-reportlab
    """
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
        self.drawCentredString(MyDocTemplate.kPageWidth / 2.0, MyDocTemplate.kOuterMargin,
            "Page %d of %d" % (self._pageNumber, page_count))


# metadata = ('Test Ride', total_distance, 1234, '123456')

class MyDocTemplate(BaseDocTemplate):
  # Page / margin constants. Rest of world: apologies for the stupid 
  # imperial units. 
  kPageSize = reportlab.lib.pagesizes.letter
  kPageWidth, kPageHeight = kPageSize
    
  kOuterMargin = 0.35 * inch
  kMiddleMargin = 0.25 * inch

  kHeaderHeight = 0.125 * inch
  kFooterPadding = 0.125 * inch
  
  # Unit Names (Used in header text)
  kDistanceUnit = "mi"
  kElevationUnit = "ft"
  
  # Page column size constants.
  kColWidth = (kPageWidth - (2.0 * kOuterMargin) - kMiddleMargin) / 2.0
  kColHeight = kPageHeight - (2 * kOuterMargin) - kHeaderHeight - kFooterPadding

  # Cell column size constants. Pulled from classic Roboviva, then tweaked to prevent line wrapping
  # on normal inputs. Rows will wrap if the content is too long, though.
  kGoCellWidth = 0.42 * inch
  kAtCellWidth = 0.5 * inch
  kForCellWidth = 0.4 * inch
  kOnCellWidth = max(1.0 * inch, 
          kColWidth - kGoCellWidth - kAtCellWidth - kForCellWidth)

  # Style constants
  kHeaderFont = "Helvetica-Oblique"
  kHeaderFontSize = 11

  kFooterFont = "Helvetica-Oblique"
  kFooterFontSize = 10

  kTableFont = "Helvetica"
  kTableFontSize = 12

  

  def __init__(self, filename, route, **kw):
    self.allowSplitting = 0
    BaseDocTemplate.__init__(self, filename, **kw)
    self.route = route
    col1_xpos = self.kOuterMargin
    col_ypos = self.kOuterMargin + self.kFooterPadding
    col2_xpos = self.kOuterMargin + self.kColWidth + self.kMiddleMargin
    template = PageTemplate('normal', [
        Frame(col1_xpos, col_ypos, self.kColWidth, self.kColHeight, id='LeftColumn'),
        Frame(col2_xpos, col_ypos, self.kColWidth, self.kColHeight, id='RightColumn')],
        onPage=self.OnNewPage)
    self.addPageTemplates(template)

  def OnNewPage(self, canvas, doc):
    """
    Draws header text + dividing line onto each new page
    """
    print("page!")
    canvas.saveState()
    canvas.setFont(self.kHeaderFont, self.kHeaderFontSize)
    header_str_left = "{} ({:0.1f} {} / {:d} {})".format(
            self.route.name,
            self.route.length_mi,
            self.kDistanceUnit,
            int(self.route.elevation_gain_ft),
            self.kElevationUnit)
    header_str_right = "Route #{}".format(self.route.id)
    header_height = self.kOuterMargin + self.kFooterPadding + self.kColHeight + self.kHeaderHeight
    canvas.drawString(self.kOuterMargin, header_height, header_str_left)
    line_offset_vertical = 0.05 * inch
    line_offset_horizontal = 0.1 * inch
    canvas.line(
        self.kOuterMargin - line_offset_horizontal,
        header_height - line_offset_vertical,
        self.kPageWidth - self.kOuterMargin + line_offset_horizontal,
        header_height - line_offset_vertical)
    canvas.drawRightString(self.kPageWidth - self.kOuterMargin, header_height, header_str_right)
    canvas.restoreState()


def main(argv : List[str]) -> int:
    route = MakeRandomRoute(1)
    ReportLabRenderer.MakePDF(route, "doc.pdf")






if __name__ == "__main__":
    sys.exit(main(sys.argv))
