from flask import (
    Blueprint, request, redirect, render_template
)
from textblob import TextBlob
import os, cryptography, pathlib, json, time

from definitions import *
from packages import SavedDataHandler

from packages.testing import exec_time
from packages.func import gen_folder_key, decrypt_folder_key, get_size_string, file_ext, terms_string

from packages.filesys import FileSys, FileH as file_h


'''Retrieve user configurations'''
sdh = SavedDataHandler()
USER_CONFIG_DICT = sdh.get_data(USER_CONFIG_FILE)

bp = Blueprint('files', __name__, url_prefix='/f/')

fsys = FileSys()
fsys.set_root(USER_CONFIG_DICT["root"])
fsys.build_init_skeleton()


@bp.route('/', methods=('GET', 'POST'))
def index():
    # get last visited directory
    USER_CONFIG_DICT = sdh.get_data(USER_CONFIG_FILE)
    last_path = USER_CONFIG_DICT["last_visited"]

    if last_path is None:
        return redirect("/f/"+gen_folder_key(USER_CONFIG_DICT["root"]))
    else:
        if os.path.exists(last_path):
            print(last_path)
            return redirect("/f/"+gen_folder_key(last_path))
        else:
            return redirect("/f/"+gen_folder_key(USER_CONFIG_DICT["root"]))

@bp.route('/<dir_key>', methods=('GET', 'POST'))
@exec_time
def view(dir_key):
    try:
        current_dir = str(decrypt_folder_key(dir_key)).rstrip("\\")

        if os.path.exists(current_dir):
            view_type = "list"

            if request.method == "GET":
                view_type = request.args.get("v")

                if request.args.get("a") == "organized":
                    organized = True
                else:
                    organized = False
            else:
                organized = False

            fsys.visit_folder(current_dir)
            terms = []

            if organized and current_dir in set(fsys.session["group_paths"]):
                grouped, folders, files = fsys.organized_view()
                terms = terms_string(fsys.session["path_grp_terms"][current_dir])
            else:
                grouped, folders, files = fsys.existing_view(None)
                organized = False

            return render_template(
                'files/view.html',
                current_path=current_dir,
                rev_path_parts=list(reversed(fsys.dissect_path(current_dir))),

                organized=organized,
                view_type=view_type,
                file_path_key=dir_key,
                terms=terms,
                grouped=grouped,
                folders=folders,
                files=files,

                tb=TextBlob,
                path=pathlib.Path,

                ext=file_ext,
                get_size_string=get_size_string,
                get_folder_key=gen_folder_key,
                join=os.path.join,
                listdir=os.listdir,
                len=len,
                str=str,
                enumerate=enumerate,
                range=range,
                datetime_format=time.ctime
            )
        else:
            return "Error. Directory does not exist: "+current_dir
    except cryptography.fernet.InvalidToken:
        return "Error. Key invalid."


@bp.route("/ping_changes/", methods=('GET', 'POST'))
def ping_changes():
    dir_key = request.form["dir_key"]
    #if dir_key is not None:
        #if fsysh.recalibrate:
            #print("Recalibrating...")
            #return "y"
        #else:
            #return "n"


# Request by client
'''Open'''
@bp.route('/req_open_file/', methods=('GET', 'POST'))
def req_open_file():
    location = request.form["location"]

    if location is not None:
        if file_h(location).open():
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


'''Move'''
@bp.route('/req_move_file/', methods=('GET', 'POST'))
def req_move_file():
    location = request.form["location"]
    dest = request.form["dest"]

    if location is not None:
        if file_h(location).move(dest):
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


'''Copy'''
@bp.route('/req_copy_file/', methods=('GET', 'POST'))
def req_copy_file():
    location = request.form["location"]
    dest = request.form["dest"]

    if location is not None:
        if file_h(location).copy(dest):
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


'''Rename'''
@bp.route('/req_rename_file/', methods=('GET', 'POST'))
def req_rename_file():
    location = request.form["location"]
    new_name = request.form["name"]

    if location is not None:
        if file_h(location).rename(new_name):
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


'''Delete'''
@bp.route('/req_delete_file/', methods=('GET', 'POST'))
def req_delete_file():
    location = request.form["location"]

    if location is not None:
        if file_h(location).delete():
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


'''Collections'''
@bp.route('/req_add_to_collection_file/', methods=('GET', 'POST'))
def req_add_to_collection_file():
    location = request.form["location"]
    collection = request.form["collection"]

    if location is not None:
        if file_h(location).add_to_collection(collection):
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


# quarantine file
@bp.route('/req_add_quarantine_file/', methods=('GET', 'POST'))
def req_add_quarantine_file():
    location = request.form["location"]
    exp_datetime = request.form["exp_datetime"]

    if location is not None:
        if file_h(location).add_quarantine(exp_datetime):
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


# add as favourite file
@bp.route('/req_add_favourite_file/', methods=('GET', 'POST'))
def req_add_favourite_file():
    location = request.form["location"]

    if location is not None:
        if file_h(location).add_favourite():
            return "success"
        else:
            return "failed"
    else:
        return "Request attempt failed. Post data required."


# remove file as favourite
@bp.route('/req_remove_favourite_file/', methods=('GET', 'POST'))
def req_remove_favourite_file():
    location = request.form["location"]

    if location is not None:
        if file_h(location).remove_favourite():
            print("favourite added: "+location)
            return "success"
        else:
            print("Unable to favourite file: "+location)
            return "failed"
    else:
        print("Request attempt failed. Post data required.")
        return "Request attempt failed. Post data required."


# information on file
@bp.route('/req_info_file/', methods=('GET', 'POST'))
def req_info_file():
    location = request.form["location"]

    if location is not None:
        return json.dumps(file_h(location).info())
    else:
        return "Request attempt failed. Post data required."