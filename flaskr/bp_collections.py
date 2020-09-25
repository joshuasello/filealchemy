from flask import (
    Blueprint, request, redirect, render_template
)
from textblob import TextBlob
import os, cryptography

from definitions import *
from packages.testing import exec_time

from packages.handlers import CollectionsHandler

bp = Blueprint('collections', __name__, url_prefix='/c/')

collection_h = CollectionsHandler()
collection_h.load_data()


@bp.route('/', methods=('GET', 'POST'))
def index():
    return render_template('collections/index.html')


@bp.route('/post_add_collection/', methods=('GET', 'POST'))
def req_add_collection():
    if request.method == "POST":
        collection = request.form["collection_name"]
        collection_h.add_collection(collection=collection)
        return redirect("c/")


@bp.route('/req_add_to_collection/', methods=('GET', 'POST'))
def req_add_to_collection():
    collection = request.form["collection"]
    item_path = request.form["item_path"]

    if os.path.exists(item_path):
        collection_h.add_to_collection(collection=collection, item_path=item_path)

    return ""
