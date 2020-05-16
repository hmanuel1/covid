"""
    Embed bokeh server session into a flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import requests
from flask import Flask, render_template, request, Response
from flask_cors import CORS, cross_origin

from bokeh import __version__ as ver
from bokeh.embed import server_document
from bokeh.resources import get_sri_hashes_for_version


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


# get port number for bokeh server
# in production this should be in a database or
# pass through environment variable
with open('.env', 'r') as env_file:
    bokeh_app_port = int(env_file.read())

# public facing url in heroku this will be something
# like `https//white-horse-58990.heroku.com`
FLASK_URL = "http://127.0.0.1:8000"

# internal bokeh url
BOKEH_URL = f"http://localhost:{bokeh_app_port}"


def bokeh_cdn_resources():
    included_resources = [f'bokeh-{ver}.min.js',
                          f'bokeh-api-{ver}.min.js',
                          f'bokeh-tables-{ver}.min.js',
                          f'bokeh-widgets-{ver}.min.js']

    resources = '  '
    for key, value in get_sri_hashes_for_version(ver).items():
        if key in included_resources:
            resources += '<script type="text/javascript" '
            resources += f'src="https://cdn.bokeh.org/bokeh/release/{key}" '
            resources += f'integrity="sha384-{value}" '
            resources += 'crossorigin="anonymous"></script>\n    '

    resources += '<script type="text/javascript">\n    '
    resources += '  Bokeh.set_log_level("info");\n    '
    resources += '</script>'
    return resources


@app.route('/', methods=['GET'])
def bkapp_route():
    resources = bokeh_cdn_resources()
    script = server_document(f"{FLASK_URL}/bkapp", resources=None)
    return render_template("embed.html", resources=resources, script=script,
                           template="Flask")


@app.route('/<path:path>', methods=['GET', 'POST', 'DELETE'])
@cross_origin(origins='*')
def proxy(path):

    query = request.query_string.decode("utf-8")
    if query != '':
        query = '?' + query

    # TODO one last puzzle to solve
    # there seems to be a handshake that Bokeh Server requires
    query = query.replace(FLASK_URL, BOKEH_URL)

    if request.method == 'GET':
        resp = requests.get(f'{BOKEH_URL}/{path}{query}')
        excluded_headers = ['content-encoding', 'content-length',
                            'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)

    elif request.method == 'POST':
        resp = requests.post(f'{BOKEH_URL}/{path}{query}', json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length',
                            'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)

    elif request.method == 'DELETE':
        resp = requests.delete(f'{BOKEH_URL}/{path}{query}').content
        response = Response(resp.content, resp.status_code, headers)

    return response


if __name__ == '__main__':
    # in heroku this part will be done with gunicorn
    # content of Procfile should look like "web: gunicorn -w 4 app:app"
    app.run(port=8000, debug=True)
