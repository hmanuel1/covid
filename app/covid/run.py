"""Run Flask App
"""

import os
from waitress import serve
from app import app

print('app running at: http://localhost:8000')
print('port number': int(os.environ.get("PORT", 8000)))
serve(app, host='localhost', port=int(os.environ.get("PORT", 8000)))
