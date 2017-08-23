from flask import Flask
from flask_common import Common

app = Flask(__name__)
app.debug = True

common = Common(app)

@app.route("/")
@common.cache.cached(timeout=50)
def hello():
    return "Hello World!"


if __name__ == "__main__":
    common.serve()