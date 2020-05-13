"""Run Bokeh App
"""
import os
import waitress
import app

waitress.serve(app.app, host='127.0.0.1', port=int(os.environ.get("PORT", 5000)))
