import http.server
import socketserver
import smashgg
import os
from urllib.parse import unquote
from jinja2 import FileSystemLoader, Environment

entrants = dict()

# tournament / event ids to use
smashgg_tournament_slug = "octo-gon-3"
smashgg_event_id = 519066
# smashgg_event_id = 517237

print("currently using these ids for data queries:")
print(f"tournament: { smashgg_tournament_slug }")
print(f"event: { smashgg_event_id }")


def get_placement_delta(entrant, placement):

    if entrant not in entrants:
        entrants[entrant] = placement

    last_placement = entrants[entrant]
    entrants[entrant] = placement

    return last_placement - placement


# read HTML template


class Templates:

    env = Environment(loader=FileSystemLoader("./"))
    ladder = env.get_template("templates/ladder.html")
    countdown = env.get_template("templates/countdown.html")
    bracket = env.get_template("templates/bracket.html")
    scoreboard = env.get_template("templates/scoreboard.html")


# HTML server

smash_api = smashgg.SmashAPI()


class HTTPHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):

        self.path = unquote(self.path)
        print(f"requesting path: {self.path}")
        ext = os.path.splitext(self.path)[1]

        # ------------------------------------------------------------------------------
        #  Ladder Standings Overlay
        # -----------------------------------------------------------------------------

        if self.path == "/":
            # serve main HTML
            self.send_response(200)
            # self.send_header("Content-type", "text/html")
            self.end_headers()
            res = smash_api.query(
                "standings", eventId=smashgg_event_id, page=1, perPage=10
            )
            body = ""

            placements = res["data"]["event"]["standings"]["nodes"]

            # test for handling changing placements
            # random.shuffle(placements)

            print(res)

            placement = 1
            for place in placements:
                entrant = place["entrant"]["name"]
                # placement = int(place["placement"])
                delta = get_placement_delta(entrant, placement)

                # add extra class for top4 placements
                placement_classes = "placement"
                if placement <= 4:
                    placement_classes += " top4"

                css_class = ""
                if delta > 0:
                    css_class = "up"
                elif delta < 0:
                    css_class = "down"
                body += f"""
                    <div class="place">
                        <div class="placement-wrapper"><span class="{placement_classes}">{placement}</span></div>
                        <!--span class="delta {css_class}">{delta}</span-->
                        <span class="name">{entrant}</span>
                    </div>
                """
                placement += 1

            self.wfile.write(bytes(Templates.ladder.render(body=body), "utf8"))

        # ------------------------------------------------------------------------------
        #  Countdown Overlay
        # -----------------------------------------------------------------------------

        elif self.path == "/countdown":

            self.send_response(200)
            self.end_headers()

            res = smash_api.query_raw(
                """
                query TournamentQuery($slug: String) {
                    tournament(slug: $slug) {
                        startAt
                    }
                }
            """,
                slug=smashgg_tournament_slug,
            )

            timestamp = res["data"]["tournament"]["startAt"]

            print(f"tournament starts at {timestamp}")

            self.wfile.write(
                bytes(Templates.countdown.render(timestamp=timestamp), "utf8")
            )

        # ------------------------------------------------------------------------------
        #  Bracket Overlay
        # -----------------------------------------------------------------------------

        elif self.path == "/bracket":

            self.send_response(200)
            self.end_headers()

            res = smash_api.query("bracket", id=smashgg_event_id)

            print(res)

            body = ""
            # for s in reversed(res["data"]["event"]["sets"]["nodes"]):
            for s in res["data"]["event"]["sets"]["nodes"]:
                round_text = s["fullRoundText"]
                round_games = s["totalGames"]

                # skip grand final reset set
                if round_text == "Grand Final Reset":
                    continue

                body += f"""
                    <div class="match">
                        <div class="round-name">{ round_text } · Best of { round_games }</div>
                """
                body += """<div class="match-players">"""
                winner_id = s["winnerId"]
                for i, entrant in enumerate(s["slots"]):

                    if entrant["entrant"]:
                        name = entrant["entrant"]["name"]
                        id = entrant["entrant"]["id"]
                    else:  # placeholder entrant
                        name = "?"
                        id = None

                    # append span representing a player
                    if winner_id and id == winner_id:
                        body += (
                            f"""<span class="player winner">{ name }</span>"""
                        )
                    else:
                        body += f"""<span class="player">{ name }</span>"""

                    # append "vs" text
                    if i < len(s["slots"]) - 1:
                        body += """<span class="vs">vs.</span>"""

                body += "</div>"
                body += "</div>"

                print(s)

            self.wfile.write(
                bytes(Templates.bracket.render(body=body), "utf8")
            )

        elif self.path == "/scoreboard":

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(Templates.scoreboard.render(), "utf8"))

        elif ext == ".png":  # attempt to serve the requested path as a file

            f = open(self.path[1:], "rb")

            self.send_response(200)
            self.send_header("Content-type", "image/png")
            self.end_headers()

            self.wfile.write(f.read())
            f.close()
        else:
            try:
                f = open(self.path[1:], "r")

                self.send_response(200)
                self.send_header("Content-type", "text/css")
                self.end_headers()

                self.wfile.write(bytes(f.read(), "utf8"))
            except FileNotFoundError:
                self.send_error(404, f"File Not Found: {self.path}")


# window = pyglet.window.Window(width=800, height=600)

# @window.event
# def on_draw():
#     window.clear(

# pyglet.app.run()


def start_server(server):
    print(f"starting server on port { server.server_address[1] }...")
    server.allow_reuse_address = True
    server.serve_forever()


def create_server(port=8000) -> socketserver.TCPServer:
    """
    Start the server that serves overlays.
    """
    # prevents a "port already binded" error when restarting program
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", port), HTTPHandler)
    return server


# open("output.html", "w").write(html)
