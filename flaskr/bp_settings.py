from flask import (
    Blueprint, request, redirect, render_template
)
from textblob import TextBlob
import os, cryptography

from definitions import *
from packages.testing import exec_time

from packages import SavedDataHandler


'''Retrieve user configurations'''
sdh = SavedDataHandler()
USER_CONFIG_DICT = sdh.get_data(USER_CONFIG_FILE)
del USER_CONFIG_FILE

bp = Blueprint('settings', __name__, url_prefix='/settings/')


@bp.route('/', methods=('GET', 'POST'))
def index():
    return render_template(
        'settings/index.html',

        root=USER_CONFIG_DICT["root"]
    )
