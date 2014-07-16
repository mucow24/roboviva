import os

_cwd = os.path.dirname(os.path.abspath(__file__))

PDF_CACHE_DIR = os.path.join(_cwd, 'pdf_cache')
SHELVE_FILENAME = '/tmp/roboviva.db'
