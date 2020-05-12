"""Run Flask App
"""

from waitress import serve
from app import app

print('app running at: http://localhost:8000')
serve(app, host='localhost', port=8000)
