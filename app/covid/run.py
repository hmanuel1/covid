"""Run Flask App
"""

import os
from waitress import serve
from app import app

print(f'port number {int(os.environ.get("PORT", 8000))}')
serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
