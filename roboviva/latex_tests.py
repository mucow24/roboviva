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
import latex
import cue
import tex
  
def _QuickRender(instruction = cue.Instruction.NONE,
                 modifier    = cue.Modifier.NONE,
                 description = "",
                 note        = "",
                 abs_dist    = 0.0,
                 for_dist    = 0.0,
                 color       = cue.Color.NONE):
  '''
  Renders a single instruction to PDF.
  '''
  ent = [cue.Entry(instruction, description, abs_dist, note, modifier, for_dist, color)]
  latex_code = latex.makeLatex(ent)
  pdf        = tex.latex2pdf(latex_code)

class LatexTestCase(unittest.TestCase):
  '''Tests for Roboviva's Cue Entry -} Latex Conversion'''


  def test_instructionToLatex(self):
    # This is a pretty simple function, so just spot-check a few things:
    self.assertEqual(latex._makeClimb("1"), latex._instructionToLatex(cue.Instruction.CAT_1, ""))
    self.assertEqual(latex._makeClimb("2"), latex._instructionToLatex(cue.Instruction.CAT_2, ""))
    self.assertEqual(latex._makeClimb("3"), latex._instructionToLatex(cue.Instruction.CAT_3, ""))
    self.assertEqual(latex._makeClimb("4"), latex._instructionToLatex(cue.Instruction.CAT_4, ""))
    self.assertEqual(latex._makeClimb("5"), latex._instructionToLatex(cue.Instruction.CAT_5, ""))

    self.assertEqual(r"\textbf{QR}",
                     latex._instructionToLatex(cue.Instruction.RIGHT, cue.Modifier.QUICK))
    
    self.assertEqual(r"\textbf{R}",
                     latex._instructionToLatex(cue.Instruction.RIGHT, cue.Modifier.NONE))

    self.assertEqual(r"\textbf{foobar}",
                     latex._instructionToLatex("bar", "foo"))

  def test_instructionToLatex_renders(self):
      # Verify all instructions render correctly:
      ents = []
      for i in cue.Instruction.__dict__:
        if '__' in i:
          continue 
        instruction = cue.Instruction.__dict__[i]
        ents.append(cue.Entry(instruction, r"Description", 0.0))
      latex_code = latex.makeLatex(ents)
      pdf_data = tex.latex2pdf(latex_code)

  def test_customInstructionIsEscaped(self):
    # Verify the user can't slip any sneaky Latex through custom instructions:
    _QuickRender(instruction="\ %")

  def test_escape(self):
    '''
    Verify all characters that could cause trouble in the Latex rendering are
    escaped properly:
    '''
    escape_test_desc = r'# & $ | < > { } \testcommand \\ %'
    _QuickRender(description = escape_test_desc)


  def test_entryColor(self):
    # Just verify entries get the right colors:
    nocolor_ent     = cue.Entry(cue.Instruction.NONE, "", 0.0, color = cue.Color.NONE)
    graycolor_ent   = cue.Entry(cue.Instruction.NONE, "", 0.0, color = cue.Color.GRAY)
    yellowcolor_ent = cue.Entry(cue.Instruction.NONE, "", 0.0, color = cue.Color.YELLOW)

    self.assertEqual(ur'{yellow}',
                     latex._entryColor(yellowcolor_ent))
    self.assertEqual(ur'[gray]{0.7}',
                     latex._entryColor(graycolor_ent))
    self.assertEqual(None,
                     latex._entryColor(nocolor_ent))

  def test_entryColor_renders(self):
    for Color in (cue.Color.NONE, cue.Color.YELLOW, cue.Color.GRAY):
      _QuickRender(color = Color)

  def test_entryToLatex(self):
    # No color, no 'for', no note, no modifier: 
    desc = "description_string & **formatted**"
    ent = cue.Entry(cue.Instruction.RIGHT,
                    desc,
                    0.0,
                    note = "",
                    modifier = cue.Modifier.NONE,
                    for_distance = None)
    expected = r' \textbf{R} &   0.0 & description_string \& \textbf{formatted} &  \\ \hline'
    self.assertEqual(expected, latex._entryToLatex(ent))
    
    # color, 'for', note, and modifier: 
    desc = "description_string & **formatted**"
    ent = cue.Entry(cue.Instruction.LEFT,
                    desc,
                    0.0,
                    note = "*formatted note*",
                    modifier = cue.Modifier.QUICK,
                    for_distance = 12.34,
                    color = cue.Color.GRAY)
    expected = r'\rowcolor[gray]{0.7} \textbf{QL} &   0.0 & description_string \& \textbf{formatted} \newline \textbf{Note:} \emph{formatted note} &  12.3 \\ \hline'
    self.assertEqual(expected, latex._entryToLatex(ent))
    
    # Custom description
    desc = "description_string"
    ent = cue.Entry("Custom Instruction",
                    desc,
                    0.0,
                    for_distance = 12.34)
    expected = r' \textbf{Custom Instruction} &   0.0 & description_string &  12.3 \\ \hline'
    self.assertEqual(expected, latex._entryToLatex(ent))

  def test_latexRenderTest(self):
    '''
    Create a few very pathological cue entries, verify the latex rendering
    doesn't choke:
    '''
    ents = [ cue.Entry(cue.Instruction.LEFT,
                      r"Are we escaping everything # & $ | < > % \\ {} ???",
                      0.0),
             cue.Entry(cue.Instruction.LEFT,
                      r"What **about *formatting***? **Does **it** work, too?**",
                      0.1)]
    latex_code = latex.makeLatex(ents)
    pdf_data = tex.latex2pdf(latex_code)

class FormatterTestCase(unittest.TestCase):
  '''
  Tests Roboviva's **bold** and *italic* formatting functionality. Cases are
  added to this dynamically, below.
  '''
  pass

# All Latex formatter test cases should be defined here -- this code will dynamically add
# test_* functions to FormatterTestCase according to the paramaters defined below.

def make_format_test(format_str, expected_latex):
  def test(self):
    self.assertEqual(expected_latex, latex._format(format_str))
    _QuickRender(description = format_str)
  return test

# This is the master list of all formatter tests.
#
# "Name" should be suitable for turning into a python method name -- so
# no spaces, etc.
    # Name           # Input string         # Expected Latex output
formatter_tests = [
    ("basic_emph",              "*foo*",                 r"\emph{foo}"),
    ("basic_strong",            "**foo**",               r"\textbf{foo}"),
    ('strong_internal',         "foo**bar**baz",         r'foo\textbf{bar}baz'),
    ('emph_internal',           "foo*bar*baz",           r'foo\emph{bar}baz'),
    ('emph_noclose',            "*foobar",               r'*foobar'),
    ('strong_noclose',          "**foobar",              r'**foobar'),
    ('emph_unbalanced',         "**foobar*",             r'*\emph{foobar}'),
    ('emph_unbalanced2',        "*foobar**",             r'\emph{foobar}*'),
    ('emph_strong_together',    "***foobar***",          r'\emph{\textbf{foobar}}'),
    ('star_with_escape',        "**foo \* bar \* baz**", r'\textbf{foo * bar * baz}'),
    ('star_with_space',         "**foo * bar * baz**",   r'\textbf{foo * bar * baz}'),
    ('strong_in_emph',          '***strong** in emph*',  r'\emph{\textbf{strong} in emph}'),
    ('emph_in_strong',          '***emph* in strong**',  r'\textbf{\emph{emph} in strong}'),
    ('emph_in_strong_internal', "**foo *bar* baz**",     r'\textbf{foo \emph{bar} baz}'),
    ('strong_in_emph_internal', "*foo **bar** baz*",     r'\emph{foo \textbf{bar} baz}'),
    ('in_emph_strong',          '*in emph **strong***',  r'\emph{in emph \textbf{strong}}'),
    ('in_strong_emph',          '**in strong *emph***',  r'\textbf{in strong \emph{emph}}'),
    ('odd_nestings',            "*bar *baz**",           r'\emph{bar \emph{baz}}'),
    ('odd_nestings2',           "**bar* baz*",           r'\emph{\emph{bar} baz}'),
    ('pathological_nesting',    '**foo**bar**baz**',     r'\textbf{foo}bar\textbf{baz}'),
    ('delimiter_closing',       "*foo**bar***",          r'\emph{foo\textbf{bar}}'),
    ('mismatches1',             "*bar***",               r'\emph{bar}**'),
    ('mismatches2',             "***foo*",               r'**\emph{foo}'),
    ('mismatches3',             "***bar**",              r'*\textbf{bar}'),
    ('mismatches4',             "**bar***",              r'\textbf{bar}*'),
    ('mismatches5',             '***foo *bar*',          r'***foo \emph{bar}'),
        ]
for test in formatter_tests:
  name, input_str, output_str = test
  test_name = "test_format_" + name
  test_method = make_format_test(input_str, output_str)
  test_method.__name__ = test_name
  setattr(FormatterTestCase, test_method.__name__, test_method)

if __name__ == '__main__':
  unittest.main()
