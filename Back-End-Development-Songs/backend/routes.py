import json
import os
import sys

import pymongo
from bson import json_util
from flask import jsonify, request
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

from . import app

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

mongodb_service = os.environ.get("MONGODB_SERVICE")
mongodb_username = os.environ.get("MONGODB_USERNAME")
mongodb_password = os.environ.get("MONGODB_PASSWORD")
mongodb_port = os.environ.get("MONGODB_PORT")

print(f"The value of MONGODB_SERVICE is: {mongodb_service}")

if mongodb_service == None:
    app.logger.error("Missing MongoDB server in the MONGODB_SERVICE variable")
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))


def check_song_exist(id):
    return db.songs.find_one({"id": id}) != None


# ERROR HANDLING
class SongNotFound(Exception):
    def __init__(self, id):
        self.id = id


@app.errorhandler(SongNotFound)
def songnotfound(e):
    return jsonify(message=f"song with id {e.id} not found"), 404


@app.errorhandler(ValueError)
def idmustint(e):
    return jsonify(message="song id can only be integer")


@app.errorhandler(ServerSelectionTimeoutError)
def mongodbdead(e):
    return jsonify(message="internal server error"), 500


## ROUTES
@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/count")
def count():
    return jsonify(count=db.songs.count_documents({}))


@app.route("/song", strict_slashes=False)
def songs():
    songs = db.songs.find({})
    return jsonify(songs=parse_json(songs))


@app.route("/song/<id>")
def get_song_by_id(id):
    song = db.songs.find_one({"id": int(id)})
    if song:
        return parse_json(song)
    raise SongNotFound(id)


@app.route("/song", methods=["POST"])
def create_song():
    song = request.json
    if not isinstance(song["id"], int):
        raise ValueError
    if check_song_exist(song["id"]):
        return jsonify(Message=f"song with id {song['id']} already present"), 302
    db.songs.insert_one(song)
    return (
        parse_json(
            db.songs.find_one({"id": song["id"]}, {"_id": 0, "inserted id": "$_id"})
        ),
        201,
    )


@app.route("/song/<id>", methods=["PUT"])
def update_song(id):
    new_song = request.json
    res = db.songs.update_one({"id": int(id)}, {"$set": new_song})
    if res.matched_count == 1:
        if res.modified_count == 1:
            return parse_json(db.songs.find_one(res.upserted_id)), 201
        return jsonify(message="song found, but nothing updated")
    raise SongNotFound(id)


@app.route("/song/<id>", methods=["DELETE"])
def delete_song(id):
    res = db.songs.delete_one({"id": int(id)})
    if res.deleted_count == 1:
        return "", 204
    raise SongNotFound(id)
