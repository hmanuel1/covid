"""Run Flask App
"""

import os
from waitress import serve
from app import app

#HOST = '127.0.0.1'
PORT = int(os.environ.get('PORT', default=8000))
TRUSTED_PROXY = 'localhost'
PROXY_HEADERS = "x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port"
NUM_THREADS = 4
INACTIVITY_TIMEOUT = 660

print("app served locally at http://127.0.0.1:8000")
print(f"app served heroku at http://{HOST}:{PORT}")
serve(app,
      threads=NUM_THREADS,
      host=HOST,
      port=PORT,
      channel_timeout=INACTIVITY_TIMEOUT,
      trusted_proxy=TRUSTED_PROXY,
      trusted_proxy_headers=PROXY_HEADERS,
      log_untrusted_proxy_headers=True)
