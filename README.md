`rq-dashboard` is a general purpose, lightweight, [Flask][flask]-based web
front-end to monitor your [RQ][rq] queues, jobs, and workers in realtime.


## It looks like this

![](https://github.com/downloads/nvie/rq-dashboard/scrot_high.png)
![](https://github.com/downloads/nvie/rq-dashboard/scrot_failed.png)


## Installing

```console
$ pip install rq-dashboard
```

## Running the dashboard

You can either run the dashboard standalone, like this...

```console
$ rq-dashboard
* Running on http://127.0.0.1:9181/
* Restarting with reloader
...
```


## Integrating the dashboard in your Flask app

...or you can integrate the dashboard in your own [Flask][flask] app, like
this:

```python
from flask import Flask
from rq_dashboard import RQDashboard


app = Flask(__name__)
RQDashboard(app)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()
```

This will register the dashboard on the `/rq` URL root in your Flask app.  To
use a different URL root, use the following:

```python
RQDashboard(app, url_prefix='/some/other/url')
```

## Setting the Redis URL

RQ dashboard defaults to the following settings:

```python
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = None
REDIS_DB = 0
```

To change this, you can set these values or the value of `REDIS_URL` in your Flask app's `app.config`.

Alternatively, you can set an environmental variable `RQ_DASHBOARD_REDIS_URL` to the full Redis URL, including authentication and port.  Please note that this will override anything that you set it your `app.config`, so if you decide to stop using this method, make sure you remove that environmental variable.

## Maturity notes

The RQ dashboard is currently being developed and is in beta stage.



[flask]: http://flask.pocoo.org/
[rq]: http://python-rq.org/
