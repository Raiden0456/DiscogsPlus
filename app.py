import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, render_template, request, redirect, url_for
import logging
import psycopg2  # Add this line
from dotenv import load_dotenv  # Add this line

# from database import conn_pool
# from search import search_tracks, validate_input
from playlist import create_playlist

import time
app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

load_dotenv()

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/test_db")
def test_db():
    connection = None
    app.logger.debug("Starting connection attempt")
    start_time = time.time()
    try:
        connection = psycopg2.connect(
            host=os.environ.get('HOST'),
            dbname=os.environ.get('DATABASE_NAME'),
            user=os.environ.get('USER_DB'),
            password=os.environ.get('PASSWORD'),
            port=os.environ.get('PORT')
        )
        if connection:
            end_time = time.time()
            app.logger.debug(f"Connection successful, time elapsed: {end_time - start_time} seconds")
            return "Connection to the database is successful!"
    except Exception as e:
        end_time = time.time()
        app.logger.error(f"An error occurred while connecting to the database: {e}, time elapsed: {end_time - start_time} seconds")
        return f"An error occurred while connecting to the database: {e}", 500
    finally:
        if connection:
            connection.close()

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
        "limit_results": request.args.get('generate_playlist') == 'on',
        "no_master": request.args.get('no_master') == 'on',
        "gen_playlist": request.args.get('generate_playlist') == 'on',
        "playlist_name": request.args.get('playlist_name'),
        "playlist_description": request.args.get('playlist_description'),
    }

    if any(x is None or x.strip() == '' for x in [search_params["genre"], search_params["style"], search_params["countries"], search_params["search_format"], search_params["year_from"], search_params["year_to"]]):
        return redirect(url_for('home'))

    # if not validate_input(search_params["genre"], search_params["style"], search_params["countries"], search_params["search_format"]):
    #     return redirect(url_for('home'))

    connection = conn_pool.getconn()

    if connection:
        try:
            gen_playlist = search_params.pop("gen_playlist")  # Remove 'gen_playlist' from search_params
            playlist_name = search_params.pop("playlist_name")  # Remove 'playlist_name' from search_params
            playlist_description = search_params.pop("playlist_description")  # Remove 'playlist_description' from search_params

            tracks = search_tracks(connection, **search_params)
            if gen_playlist:
                create_playlist(tracks, playlist_name, playlist_description)
                return render_template('home.html')
            else:
                return render_template("results.html", tracks=tracks, **search_params)
        except Exception as e:
            app.logger.error(f"An error occurred while searching tracks: {e}")
            return f"An error occurred while searching tracks: {e}", 500
        finally:
            conn_pool.putconn(connection)
    else:
        app.logger.error("No connection available")
        return "No connection available", 500

if __name__ == '__main__':
    app.run(debug=True)
