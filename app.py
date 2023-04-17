from flask import Flask, render_template, request, redirect, url_for
import logging
from database import conn_pool
from search import search_tracks, validate_input
from playlist import create_playlist

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_params = request.form.to_dict()
        return redirect(url_for('search', **search_params))

    search_params = {
        "genre": request.args.get('genre'),
        "style": request.args.get('style'),
        "countries": request.args.get('countries'),
        "search_format": request.args.get('format'),
        "year_from": request.args.get('year_from'),
        "year_to": request.args.get('year_to'),
        "one_release": request.args.get('one_release') == 'on',
        "no_master": request.args.get('no_master') == 'on',
        "gen_playlist": request.args.get('generate_playlist') == 'on',
        "playlist_name": request.args.get('playlist_name'),
        "playlist_description": request.args.get('playlist_description'),
        "page": int(request.args.get('page', 1)),
    }

    if any(x is None or x.strip() == '' for x in [search_params["genre"], search_params["style"], search_params["countries"], search_params["search_format"], search_params["year_from"], search_params["year_to"]]):
        return redirect(url_for('home'))

    if not validate_input(search_params["genre"], search_params["style"], search_params["countries"], search_params["search_format"]):
        return redirect(url_for('home'))

    connection = conn_pool.getconn()

    if connection:
        try:
            tracks = search_tracks(connection, **search_params)
            if search_params["gen_playlist"]:
                create_playlist(tracks, search_params["playlist_name"], search_params["playlist_description"])
                return render_template('home.html')
            else:
                return render_template("results.html", tracks=tracks, **search_params)
        except Exception as e:
            pass
        finally:
            conn_pool.putconn(connection)

if __name__ == '__main__':
    app.run(debug=True)
