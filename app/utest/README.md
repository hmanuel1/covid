
# Flask + Bokeh Server App Integration

## Use Case

It's often desired to embed Bokeh Server Apps in established environments and frameworks, such as Flask or Tornado.

In addition, it's desired to have only one public facing interface to the internet. This implies that Bokeh may need to run behind reverse-proxy configurations such as NGINX and Apache.

However, during software development, teams will need access to simulated environments to test code. Likewise, student will test new applications in free hosting services like Heroku.com.

This application presents a proof of concept of how to integrate Bokeh Server Apps with Flask Apps for scenarios in which there are not security concerns and the most bare bone configuration is needed.

## Technical Description

This application wraps the Flask App into Tornado framework. Implements a HTTP reverse-proxy using Flask and a Web Socket reverse-proxy using Tornado.

## Run Application with a Single Command

1. Clone or download repository.
2. Navigate to the utest directory covid/app/utest.
3. Open config.yaml file and change "heroku" to "local" in first line and save it.
4. In your terminal run the following command from the same directory.

``` Python
python run.py
```

5. Open http://127.0.0.1:8000/ in your internet browser to see Bokeh App embedded into Flask framework.

## Run Each Application Independently

1. Clone or download repository.
2. Navigate to the covid-master/app/utest directory
3. Open config.yaml file and change "heroku" to "local" in first line and save it.
4. In your terminal run the following command from the covid-master/app/utest directory.

``` Python
python bkapp.py
```

5. Open the url displayed in your terminal with your internet browser to see the Bokeh server app.

6. Open a second terminal session without closing the one running bkapp.py and run the following command from the same directory.

``` Python
python app.py
```

7. Open http://127.0.0.1:8000/ in your internet browser to see Bokeh server app embedded into Flask framework.

## Design Diagrams

Similar architecture is used in the flask_gunicorn_embed.py but it won't work in heroku within one Heroku app without a reverse-proxy configuration.

These diagrams need Markup-Mermaid support to shown:

### Bokeh Example HTTP Request Flow

``` Mermaid
sequenceDiagram
    participant A as Browser
    participant B as Heroku
    participant C as Flask Server (8000)
    participant D as Bokeh Server (5000)
    A->>B: HTTPS Request 1
    B->>C: Forward HTTPS Request 1
    C->>A: HTTPS Response from Flask with Bokeh script
    A->>D: HTTPS Request 2 to load Bokeh page
    D->>A: HTTPS Response from Bokeh Server
```

### Alternative 1

it may be possible to setup two Heroku apps to simulate the architecture of the Bokeh example.

``` mermaid
sequenceDiagram
    participant A as Browser
    participant B as Heroku (Flask APP)
    participant C as Flask Server (8000)
    A->>B: HTTPS Request 1
    B->>C: Forward HTTPS Request 1
    C->>A: HTTPS Response from Flask with embedded Bokeh script
```

``` mermaid
sequenceDiagram
    participant A as Browser
    participant B as Flask
    participant C as Bokeh Server (5000)
    A->>B: HTTPS Request 2 to load bokeh page
    B->>C: Forward HTTPS Request 2
    C->>A: Bokeh Server HTTPS Response
```

### Alternative 2

Another alternative is to use Flask as a reverse-proxy for the Bokeh Server.

``` mermaid
sequenceDiagram
    participant A as Browser
    participant B as Flask Server (8000)
    participant C as Bokeh Server (5000)
    A->>B: HTTPS Request to load home page
    B->>C: Forward HTTPS Request to Bokeh
    C->>B: HTTPS Response from Bokeh with autoload script
    B->>A: HTTPS Response forward to browser
    A->>B: HTTPS Request to load Bokeh page
    B->>C: HTTPS Request forward to load bokeh page
    C->>B: HTTPS Response from Bokeh Server page
    B->>A: HTTPS Response with Bokeh page
    A->>A: If no new requests needed.
```

### Bokeh Sever <-> Browser Client Message flow

``` mermaid
sequenceDiagram
    participant A as Client Browser
    participant B as Bokeh Server <bkapp>
    A->>B: HTTPS Request bkapp/autoload.js <params>
    B->>A: HTTPS Response bkapp/autoload.js script
    A->>B: HTTPS Request bkapp/ws
    B->>A: HTTPS Response Can "Upgrade" only to "WebSocket"
    A->>B: WebSocket connect
    B->>A: WebSocket <json><encoding: str, bytes> messages from Bokeh to Browser
    A->>B: WebSocket <json><encoding: str, bytes> messages from Browser to Bokeh
```
