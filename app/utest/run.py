"""Run Bokeh App
"""

import waitress
import flask_trends

print('flask_trends:app running at: http://localhost:8000')

waitress.serve(flask_trends.app, host='0.0.0.0', port=8000)

