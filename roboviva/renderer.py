
import roboviva.cue
import roboviva.latex
import roboviva.tex
import os.path

class LatexRenderer(object):
  def __init__(self):
      pass

  @staticmethod
  def MakePDF(route: roboviva.cue.Route, pdf_filepath: str):
      ''' 
      'route' is the route to render, 'pdf_file_path' is the full
      path+filename of the PDF to produce.
      '''
      latex = roboviva.latex.makeLatex(route)
      pdf_data = roboviva.tex.latex2pdf(latex)
      with open(pdf_filepath, 'wb') as pdffile:
          pdffile.write(pdf_data)



class ReportLabRenderer(object):
    def __init__(self):
        pass

    @staticmethod
    def MakePDF(route: roboviva.cue.Route, pdf_file_path: str):
      pass

class DummyRenderer(object):
    @staticmethod
    def MakePDF(route: roboviva.cue.Route, pdf_file_path: str):
        pass
