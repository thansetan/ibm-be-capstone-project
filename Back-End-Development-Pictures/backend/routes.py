from . import app
import os
import json
from flask import jsonify, request

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "pictures.json")
data: list = json.load(open(json_url))


class PictureNotFound(Exception):
    pass


@app.errorhandler(PictureNotFound)
def picturenotfound(e):
    return {"message": "picture not found"}, 404


######################################################################
# RETURN HEALTH OF THE APP
######################################################################


@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200


######################################################################
# COUNT THE NUMBER OF PICTURES
######################################################################


@app.route("/count")
def count():
    """return length of data"""
    if data:
        return jsonify(length=len(data)), 200

    return {"message": "Internal server error"}, 500


######################################################################
# GET ALL PICTURES
######################################################################
@app.route("/picture", methods=["GET"], strict_slashes=False)
def get_pictures():
    return data


######################################################################
# GET A PICTURE
######################################################################


@app.route("/picture/<int:id>", methods=["GET"])
def get_picture_by_id(id):
    for pic in data:
        if pic["id"] == id:
            return pic
    raise PictureNotFound


######################################################################
# CREATE A PICTURE
######################################################################
@app.route("/picture", methods=["POST"])
def create_picture():
    new_pic = request.json
    for pic in data:
        if pic["id"] == new_pic["id"]:
            return {"Message": f"picture with id {new_pic['id']} already present"}, 302
    data.append(new_pic)
    return new_pic, 201


######################################################################
# UPDATE A PICTURE
######################################################################


@app.route("/picture/<int:id>", methods=["PUT"])
def update_picture(id):
    updated_pic = request.json
    for i in range(len(data)):
        if data[i]["id"] == updated_pic["id"]:
            data[i] = updated_pic
            return data[i], 201
    raise PictureNotFound


######################################################################
# DELETE A PICTURE
######################################################################
@app.route("/picture/<int:id>", methods=["DELETE"])
def delete_picture(id):
    for pic in data:
        if pic["id"] == id:
            data.remove(pic)
            return "", 204
    raise PictureNotFound
