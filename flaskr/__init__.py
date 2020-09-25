import os, time
from flask import (
    Flask, render_template, request, make_response, redirect, flash
)
from definitions import *
from packages.func import gen_folder_key, decrypt_folder_key, get_size_string, file_ext

from packages import SavedDataHandler
from packages.filesys import FileSys, FileH as file_h


'''Retrieve user configurations'''
sdh = SavedDataHandler()
USER_CONFIG_DICT = sdh.get_data(USER_CONFIG_FILE)

fsys = FileSys()
fsys.set_root(USER_CONFIG_DICT["root"])
fsys.build_init_skeleton()
root_files_list = fsys.root_files()


def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Blue prints
    from . import bp_files
    app.register_blueprint(bp_files.bp)

    from . import bp_collections
    app.register_blueprint(bp_collections.bp)

    from . import bp_quarantined
    app.register_blueprint(bp_quarantined.bp)

    from . import bp_watchlist
    app.register_blueprint(bp_watchlist.bp)

    from . import bp_settings
    app.register_blueprint(bp_settings.bp)

    from . import bp_help
    app.register_blueprint(bp_help.bp)

    # Request Handlers that don't belong to a Blueprint
    @app.route('/', methods=('GET', 'POST'))
    def index():
        return render_template("index.html")

    @app.route('/home/', methods=('GET', 'POST'))
    def home():
        recent_files_list = list(reversed(fsys.sort_items(root_files_list, "mtime")))[:4]
        favourites_list = fsys.filter_items(root_files_list, field="favourite", value=True)
        print(favourites_list)
        return render_template(
            'home.html',

            favourites_list=favourites_list,
            recent_files_list=recent_files_list,

            get_size_string=get_size_string,
            join=os.path.join,
            ext=file_ext,
            datetime_format=time.ctime
        )

    return app

