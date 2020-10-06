import os
import logging
from flask import Flask, request, send_from_directory
from octogon.renderer.renderer import Renderer
from octogon.config import get_print_fn

print = get_print_fn("flask")

# tournament / event ids to use

smashgg_tournament_slug = "octo-gon-5"
smashgg_event_id = 522705  # octo-gon 5
# smashgg_event_id = 521088  # octo-gon 4 singles
# smashgg_event_id = 519066  # octo-gon 3 singles
# smashgg_event_id = 517237  # octo-gon 2 singles

print("currently using these ids for data queries:")
print(f"tournament: { smashgg_tournament_slug }")
print(f"event: { smashgg_event_id }")

# disable info logging for flask
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
renderer = Renderer()


def start_server():
    app.run(debug=True, use_reloader=False, port=8000)


def stop_server():
    """
    Stop the Flask server.
    Provided by:
    https://stackoverflow.com/a/17053522/2886326
    """

    try:
        fn = request.environ.get("werkzeug.server.shutdown")
        fn()

    except Exception:
        pass


@app.route("/standings")
def _smashgg_standings():
    return renderer.render_standings(smashgg_event_id)


@app.route("/countdown")
def _smashgg_countdown():
    return renderer.render_countdown(smashgg_tournament_slug)


@app.route("/bracket")
def _smashgg_bracket():
    return renderer.render_bracket(smashgg_event_id)


@app.route("/test-player")
def _test_player():
    return renderer.render_test_player()


@app.route("/scoreboard")
def _scoreboard():
    return renderer.render_scoreboard()


@app.route("/background")
def _background():
    return renderer.render_background()


current = 0


@app.route("/rotation")
def _rotation():
    global current
    if current == 0:
        current += 1
        return _smashgg_bracket()
    elif current == 1:
        current = 0
        return _smashgg_standings()


@app.route("/<path:path>", methods=["GET"])
def _get_file(path):
    # _, ext = os.path.splitext(path)
    # if ext == ".json":
    # return send_from_directory("../", path, mimetype="text/json")
    # print(f"cwd: {os.getcwd()}, path: {path}")
    return send_from_directory(os.getcwd(), path, cache_timeout=0)
