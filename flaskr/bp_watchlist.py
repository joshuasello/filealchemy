from flask import (
    Blueprint, request, redirect, render_template
)
from textblob import TextBlob
import os, cryptography

from definitions import *
from packages.testing import exec_time

from packages.handlers import QuarantinedHandler

bp = Blueprint('watchlist', __name__, url_prefix='/w/')


@bp.route('/', methods=('GET', 'POST'))
def index():
    return render_template('watchlist/index.html')