import os, hashlib, shutil, json, re, time, sys, subprocess, stat
from definitions import CLIENT_FILES_DUMP_PATH, GRP_SUPPORTED_EXT, EXT_CATEGORIES
from packages.func import gen_folder_key
from pathlib import PurePath
from threading import Thread
from textblob import TextBlob, Word
from .operators import Quarantine, Collections, Watch, Tags, Favourite

from packages.grouping import KMeansClustering
from packages.extractors import (
    ExtractFromDocument, ExtractFromImage, ExtractFromAudio, ExtractFromAudiovisual
)


quarantine = Quarantine()
collections = Collections()
watch = Watch()
tags = Tags()
favourite = Favourite()


SAVED_DATA_ROOT_FOLDER = "_user_folders/"

ASSOC_RAW_CONTENT_KEY = {
    "documents": "raw_text"
}


def delete_dir_contents(path):
    if os.path.exists(path):
        for file in os.listdir(path):
            f_path = os.path.join(path, file)

            try:
                if os.path.isfile(f_path):
                    os.unlink(f_path)
                elif os.path.isdir(f_path):
                    shutil.rmtree(f_path)
            except Exception as e:
                print(e)


class FileSysHandler(object):
    def __init__(self, root_path):
        self.session_fields = {
            "cached_skel_path": {
                "folders": [],
                "files": []
            },
            "cached_grouped": {},
            "cached_files": {},
            "cached_folders": {},
            "last_organised": False
        }
        self.ctx_package = {
            "stage_1": False,
            "stage_2a": False,
            "stage_2b": False,
            "phase_1": False,
            "phase_2a": False,
            "phase_2b": False
        }

        self.syncing = True
        self.recalibrate = False

        if os.path.exists(root_path):
            self.root_path = root_path
        else:
            raise Exception("Error. Path [root_path] does not exist. Given: " + root_path)

        self.skeleton = self.gen_skeleton(self.root_path)
        Thread(target=self.sync, name="filesys_sync").start()

    def sync(self):
        while self.syncing:
            new_skel = self.gen_skeleton(self.root_path)
            recal = False
            for root, skel_path in new_skel.items():
                if not self.path_not_changed(cached_skel_path=self.skeleton[root], new_skel_path=skel_path):
                    # update outdated
                    self.skeleton[root] = skel_path
                    recal = True
                    print("Change noticed in "+root)
            self.recalibrate = recal

    def arrange(self, path, organized=False, num_groups=None):
        if os.path.exists(path):
            try:
                # del  content of client file dump folder
                delete_dir_contents(CLIENT_FILES_DUMP_PATH)
            except OSError as e:
                print(e)

            if path in self.skeleton:
                if self.path_not_changed(self.session_fields["cached_skel_path"], self.skeleton[path]) and \
                        (organized and self.session_fields["last_organised"]):

                    self.recalibrate = False
                    print("Used cached arrangement...")

                    return self.session_fields["cached_grouped"], \
                           self.session_fields["cached_folders"], \
                           self.session_fields["cached_files"]
                else:
                    print("Recalibrating arrangement...")
                    grouped = {}

                    if organized:
                        grp_supported, grp_unsupported = self.split_grp_supported(self.skeleton[path]["files"])

                        for file_category, file_list in grp_supported.items():
                            if file_category in ASSOC_RAW_CONTENT_KEY:
                                extracted_content, leftovers = self.update_extracted(file_list)
                                del file_list
                                grp_unsupported[file_category].extend(leftovers)
                                files_raw_text = []
                                for file in extracted_content:
                                    files_raw_text.append(file[ASSOC_RAW_CONTENT_KEY[file_category]])
                                files_raw_text = self.preprocess_raw_text(files_raw_text)
                                grp_list = KMeansClustering().cluster_text(
                                    text_list=files_raw_text,
                                    verbose=True,
                                    num_clusters=num_groups,
                                )
                                grouped.update({file_category: self.filter_into_groups(grp_list, extracted_content)})

                        files = grp_unsupported
                    else:
                        files = self.arrange_files_into_categories((self.skeleton[path]["files"]))

                    folders = self.skeleton[path]["folders"]

                    # cache data
                    self.session_fields["last_organised"] = organized
                    self.session_fields["cached_skel_path"] = self.skeleton[path]
                    self.session_fields["cached_grouped"] = grouped
                    self.session_fields["cached_folders"] = folders
                    self.session_fields["cached_files"] = files

                    self.recalibrate = False

                    return grouped, folders, files
            else:
                raise Exception("Error. [path] does not exist in skeleton. Given: " + path)
        else:
            raise Exception("Error. [path] does not exist. Given: " + path)

    def gen_skeleton(self, root_path):
        if os.path.exists(root_path):
            skeleton = {}

            for root, folders, files in os.walk(root_path):
                skeleton.update(self.add_skeleton_path(root, folders, files))

            return skeleton
        else:
            raise Exception("Error. [root_path] does not exist in skeleton. Given: " + root_path)

    def add_skeleton_path(self, root, folders, files):
        skel_path = {
            root: {
                "folders": [],
                "files": []
            }
        }

        for folder in folders:
            location = os.path.join(root, folder)
            skel_path[root]["folders"].append(self.add_folder_item(location))

        for file in files:
            location = os.path.join(root, file)
            file_item = self.add_file_item(location)
            # Add to skeleton
            skel_path[root]["files"].append(file_item)

        return skel_path

    def add_folder_item(self, location):
        if os.path.exists(location):
            path, name = os.path.split(location)

            return {
                "key": gen_folder_key(location),
                "name": name,
                "path": path,
                "location": location,
                "mtime": time.ctime(os.path.getmtime(location)),
                "ctime": time.ctime(os.path.getctime(location)),
                "size": os.stat(location).st_size,
                "watch": os.stat(location).st_size
            }
        else:
            raise Exception("Error. [location] does not exist in skeleton. Given: " + location)

    def add_file_item(self, location):
        if os.path.exists(location):
            path, name = os.path.split(location)
            size = os.stat(location).st_size
            hash_str = self.gen_file_hash(location)

            grp_supported, file_type = self.is_grp_supported(name), self.file_category(name)

            file_dict = {
                "hash": hash_str,
                "name": name,
                "path": path,
                "location": location,
                "mtime": time.ctime(os.path.getmtime(location)),
                "ctime": time.ctime(os.path.getctime(location)),
                "size": size,
                "type": file_type,
                "grp_supported": grp_supported,
                "quarantined": False,
                "favourite": False
            }
            if file_type in ("images", "documents"):
                try:
                    shutil.copy2(src=location, dst=CLIENT_FILES_DUMP_PATH)
                except OSError as e:
                    print(e)

            return file_dict
        else:
            raise Exception("Error. [location] does not exist. Given: " + location)

    def split_grp_supported(self, files_list):
        categories = self.category_set_from_list(files_list)
        grp_supported = {}
        grp_unsupported = {}

        # sort into categories
        for category in categories:
            grp_supported.update({category: []})
            grp_unsupported.update({category: []})

            for file in files_list:
                if category == file["type"]:
                    if file["grp_supported"]:
                        grp_supported[category].append(file)
                    else:
                        grp_unsupported[category].append(file)
        return grp_supported, grp_unsupported

    def preprocess_raw_text(self, text_list):
        for i in range(len(text_list)):
            processed = ""
            text_list[i] = re.sub(' +', ' ', text_list[i].replace("\n", ""))
            for word in text_list[i].split(" "):
                if len(word) > 1:
                    processed += " "+word
                    
            processed = processed.strip(" ").replace("'s", "")
            text_list[i] = processed

        return text_list

    def arrange_files_into_categories(self, files_list):
        categories = self.category_set_from_list(files_list)
        files = {}

        for category in categories:
            files.update({category: []})

            for file in files_list:
                if category == file["type"]:
                    files[category].append(file)

        return files

    def dissect_path(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                path = os.path.relpath(path, self.root_path)

                path_items = [{"name": "Root", "location": str(self.root_path)}]
                path_parts = list(PurePath(path).parts)

                if len(path_parts) > 0:
                    curr_path = path_parts[0]

                    for i, part in enumerate(path_parts):
                        path_items.append({
                            "name": part,
                            "location": os.path.join(self.root_path, curr_path)
                        })
                        curr_path = os.path.join(curr_path, part)
                return path_items
            else:
                raise Exception("Error. [path] not directory. Given: " + path)
        else:
            raise Exception("Error. [path] does not exist. Given: " + path)

    @staticmethod
    def update_extracted(file_list):
        leftovers = []
        files = []

        for file in file_list:
            if file["type"] == "documents" and file["grp_supported"]:
                extracted = ExtractFromDocument().get_content(file_path=file["location"])

                if extracted is not None and extracted.replace("\n", "").strip(" ") != "":
                    file.update({
                        ASSOC_RAW_CONTENT_KEY["documents"]: extracted
                    })
                    files.append(file)
                else:
                    file["grp_supported"] = False
                    leftovers.append(file)

        return files, leftovers

    @staticmethod
    def filter_into_groups(grp_list, files_list):
        if type(grp_list) is list and type(files_list) is list:
            if len(grp_list) == len(files_list):
                groups = {}

                for grp in list(set(grp_list)):
                    groups.update({grp: []})
                    for i, file_grp in enumerate(grp_list):
                        if grp == file_grp:
                            groups[grp].append(files_list[i])

                return groups
            else:
                raise \
                    Exception("Error. [grp_list] (" +
                              str(len(grp_list)) + ") and [files_list] (" +
                              str(len(files_list)) + ") are not parallel")
        else:
            raise Exception(
                "Error. Invalid types provided for [grp_list] or/and [files_list]. Given: " + str(type(grp_list)))

    @staticmethod
    def category_set_from_list(files_list):
        return list(set([file["type"] for file in files_list]))

    @staticmethod
    def path_not_changed(cached_skel_path, new_skel_path):
        # check if paths in skeleton is not empty
        if bool(new_skel_path) and bool(new_skel_path):
            # check if both have the same number of folders and files
            if (len(new_skel_path["folders"]) == len(cached_skel_path["folders"])) and \
                    (len(new_skel_path["files"]) == len(cached_skel_path["files"])):
                # check names and checksums
                for i, folder in enumerate(cached_skel_path["folders"]):
                    if folder["name"] != new_skel_path["folders"][i]["name"]:
                        return False
                for i, file in enumerate(cached_skel_path["files"]):
                    if file["name"] != new_skel_path["files"][i]["name"]:
                        return False
                    elif file["hash"] != new_skel_path["files"][i]["hash"]:
                        return False

                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def file_category(name):
        ext = name.split(".")[-1]

        for category, exts in EXT_CATEGORIES.items():
            if ext in exts:
                return category

        return "Exotics"

    @staticmethod
    def is_grp_supported(name):
        return name.split(".")[-1] in GRP_SUPPORTED_EXT

    @staticmethod
    def gen_file_hash(path):
        hasher = hashlib.md5()

        with open(path, 'rb') as f:
            hasher.update(f.read())

        return hasher.hexdigest()

    @staticmethod
    def file_ext(name):
        return name.split(".")[-1]


class FolderH(object):
    def __init__(self, location):
        if not os.path.exists(location):
            raise Exception("Error. File location does not exist. Given: "+location)

        self.loc = location

    def open(self):
        file_path = self.loc

        if sys.platform.startswith('darwin'):
            subprocess.call(('open', file_path))
        elif os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', file_path))
        else:
            return False
        return True

    def info(self):
        loc = self.loc
        path, file_name = os.path.split(loc)
        file_stats = os.stat(file_name)

        return {
            'name': file_name,
            'sie': file_stats[stat.ST_SIZE],
            'last_modified': time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(file_stats[stat.ST_MTIME])),
            'last_accessed': time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(file_stats[stat.ST_ATIME])),
            'creation_time': time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(file_stats[stat.ST_CTIME]))
        }

    def move(self, dst):
        location = self.loc
        path, name = os.path.split(location)
        new_location = os.path.join(dst, name)
        os.rename(location, new_location)

        if os.path.exists(new_location) and not os.path.exists(location):
            self.loc = new_location
            return True
        else:
            return False

    def copy(self, dst):
        location = self.loc
        path, name = os.path.split(location)
        new_location = os.path.join(dst, name)
        shutil.copy(location, new_location)

        if os.path.exists(new_location) and os.path.exists(location):
            return True
        else:
            return False

    def rename(self, name):
        location = self.loc
        path, old_name = os.path.split(location)
        new_location = os.path.join(path, name)
        os.rename(location, new_location)

        if os.path.exists(new_location) and not os.path.exists(location):
            self.loc = new_location
            return True
        else:
            return False

    def delete(self):
        location = self.loc
        os.remove(location)
        if os.path.exists(location):
            return False
        else:
            return True

    def add_tag(self, tag):
        pass

    def remove_tag(self, tag):
        pass

    def quarantine(self, expiration_datetime):
        pass

    def favourite(self):
        pass


class FileH(object):
    def __init__(self, location):
        if not os.path.exists(location):
            raise Exception("Error. File location does not exist. Given: " + location)

        self.loc = location

    def open(self):
        file_path = self.loc

        if sys.platform.startswith('darwin'):
            subprocess.call(('open', file_path))
        elif os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', file_path))
        else:
            return False
        return True

    def info(self):
        loc = self.loc
        path, file_name = os.path.split(loc)
        file_stats = os.stat(file_name)

        return {
            'name': file_name,
            'sie': file_stats[stat.ST_SIZE],
            'last_modified': time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(file_stats[stat.ST_MTIME])),
            'last_accessed': time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(file_stats[stat.ST_ATIME])),
            'creation_time': time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(file_stats[stat.ST_CTIME]))
        }

    def move(self, dst):
        location = self.loc
        path, name = os.path.split(location)
        new_location = os.path.join(dst, name)
        os.rename(location, new_location)

        if os.path.exists(new_location) and not os.path.exists(location):
            self.loc = new_location
            return True
        else:
            return False

    def copy(self, dst):
        location = self.loc
        path, name = os.path.split(location)
        new_location = os.path.join(dst, name)
        shutil.copy(location, new_location)

        if os.path.exists(new_location) and os.path.exists(location):
            return True
        else:
            return False

    def rename(self, name):
        location = self.loc
        path, old_name = os.path.split(location)
        new_location = os.path.join(path, name)
        os.rename(location, new_location)

        if os.path.exists(new_location) and not os.path.exists(location):
            self.loc = new_location
            return True
        else:
            return False

    def delete(self):
        location = self.loc
        os.remove(location)
        if os.path.exists(location):
            return False
        else:
            return True

    def add_tag(self, tag):
        pass

    def remove_tag(self, tag):
        pass

    def add_quarantine(self, expiration_datetime):
        pass

    def add_to_collection(self, collection):
        pass

    def add_favourite(self):
        pass

