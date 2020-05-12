"""Run Bokeh App
"""
import os
import waitress
import app

waitress.serve(app.app, host='*', port=int(os.environ.get("PORT", 5000)))
