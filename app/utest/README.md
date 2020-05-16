
# Deploying a Flask + Bokeh Server App in Heroku


### Similar architecture is used in the flask_gunicorn_embed.py but it won't in heroku within one heroku app.


```mermaid
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

### it may be possible to setup two heroku apps to simulate the architecture of the example.

```mermaid
sequenceDiagram
    participant A as Browser
    participant B as Heroku (Flask)
    participant C as Flask Server (8000)
    A->>B: HTTPS Request 1
    B->>C: Forward HTTPS Request 1
    C->>A: HTTPS Response from Flask with embedded Bokeh script
```

```mermaid
sequenceDiagram
    participant A as Browser
    participant B as Heroku (Bokeh)
    participant C as Bokeh Server (5000)
    A->>B: HTTPS Request 2 to load bokeh page
    B->>C: Forward HTTPS Request 2
    C->>A: Bokeh Server HTTPS Response
```

### Another alternative is having Flask as a reverse-proxy for the Bokeh Server.

```mermaid
sequenceDiagram
    participant A as Browser
    participant B as Heroku
    participant C as Flask Server (8000)
    participant D as Bokeh Server (5000)
    A->>B: HTTPS Request 1
    B->>C: Forward HTTPS Request 1
    C->>A: HTTPS Response from Flask with Bokeh script
    A->>C: HTTPS Request 2 to load Bokeh page
    C->>D: HTTPS Request 2
    D->>C: HTTPS Response from Bokeh Server
    C->>A: HTTPS Response with Bokeh page
```
