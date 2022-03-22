roboviva
========

Convert RideWithGPS Cue .csv's into a nice PDF

 - 'master' branch is Roboviva 'classic', which uses LaTeX as the rendering backend and is written in python 2.x. This requires the server running roboviva to have pdflatex and the Helvetica font installed, and renders PDFs by converting RWGPS cues into raw LaTeX code which is passed to pdflatex via a subprocess. Ugly, but it produces great output.

 - 'python3' branch is beta code; in addition to using more modern python 3, it also uses Reportlab as a rendering backend. This is a big deal since Reportlab is native python through and through, making installation and deployment much, much simpler. Basic cuesheet rendering is in place, but some of the more advanced features like inline formatting aren't there yet.


Current development goal (March 2022) is to flesh out the reportlab-based version and get it into a state where it's trivally deployable as a Flask application by anyone.


