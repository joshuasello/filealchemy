import os, hashlib, shutil, time, sys, subprocess, stat
from definitions import CLIENT_FILES_DUMP_PATH, GRP_SUPPORTED_EXT, EXT_CATEGORIES, USER_CONFIG_FILE
from packages.func import gen_folder_key, delete_dir_contents
from pathlib import PurePath
from threading import Thread
from .operators import Quarantine, Collections, Watch, Tags, Favourite

from packages.grouping import DocumentCluster
from packages.extractors import (
    ExtractFromDocument, ExtractFromImage, ExtractFromAudio, ExtractFromAudiovisual
)
from packages import SavedDataHandler

quarantine = Quarantine()
collections = Collections()
watch = Watch()
tags = Tags()
favourite = Favourite()

ASSOC_RAW_CONTENT_KEY = {
    "documents": "raw_text"
}

'''Retrieve user configurations'''
sdh = SavedDataHandler()
USER_CONFIG_DICT = sdh.get_data(USER_CONFIG_FILE)


class FileSys(object):
    def __init__(self):
        '''
        SESSION ROUTINE STEPS:
        1 - SET root
        2 - BUILD entire skeleton from root
        3 - VISIT folder
        4 - EXTRACT relevant content that exists in visiting folder
        5 - GROUP relevant content items in visiting folder
        7 - EXTRACT relevant content across entire skeleton
        8 - GROUP relevant content across entire skeleton
        '''
        self.session = {
            "visiting": None,
            "init": False,
            "check": {
                "S1": False,
                "S2": False,
                "S3": False,
                "S4": False,
                "S5": False,
                "S6": False,
                "S7": False
            },
            "visited_paths": [],
            "extracted_paths": [],
            "group_paths": []
        }
        self.config = {
            "num_groups": None
        }
        self.syncing = True
        self.recalibrate = False
        self.root_path = None
        self.skeleton = {}

    def existing_view(self, order=None, filter_favourite=None):
        if self.session["check"]["S3"]:
            path_item = self.skeleton[self.session["visiting"]]
            folders = path_item["folders"]
            files = path_item["files"]
            groups = self.sort_into_types(path_item["raw_groups"])
            files.update(groups)
            groups = {}

            return groups, folders, files
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def organized_view(self, order=None, filter_favourite=None):
        path_item = self.skeleton[self.session["visiting"]]
        folders = path_item["folders"]
        files = self.exclude_group_supported(path_item["files"])
        groups = self.sort_into_types(path_item["groups"])

        return groups, folders, files

    def group_protocol(self):
        self.extract_from_visit_folder()
        self.group_in_visit_folder()
        self.extract_fron_skeleton()
        self.group_fron_skeleton()

    def set_root(self, path):
        """Set the skeleton root"""
        if os.path.exists(path):
            if os.path.isdir(path):
                self.root_path = path
                self.session["check"]["S1"] = True
                print("Root set.")
            else:
                raise Exception("Error. Path [path] is not a folder. Given: " + path)
        else:
            raise Exception("Error. Path [path] does not exist. Given: " + path)

    def build_init_skeleton(self):
        if self.root_path is not None and self.session["check"]["S1"]:
            if not bool(self.skeleton):
                self.skeleton = self.build_skeleton(self.root_path)
            self.session["check"]["S2"] = True
            print("Skeleton built.")
        else:
            raise Exception("Error. Could not build root. Make sure you set a root before building.")

    def build_skeleton(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                try:
                    # del  content of client file dump folder
                    delete_dir_contents(CLIENT_FILES_DUMP_PATH)
                except OSError as e:
                    print(e)

                skeleton = {}

                for root, folders, files in os.walk(path):
                    skeleton.update(self.add_skeleton_path(root, folders, files))

                return skeleton
            else:
                raise Exception("Error. Path [path] is not a folder. Given: " + path)
        else:
            raise Exception("Error. [path] does not exist in skeleton. Given: " + path)

    def add_skeleton_path(self, root, folders, files):
        """Returns a folder path item"""
        path_item = {
            root: {
                "folders": [],
                "files": [],
                "raw_groups": [],
                "groups": {}
            }
        }

        for folder in folders:
            loc = os.path.join(root, folder)
            path_item[root]["folders"].append(self.add_basic_folder_item(loc))

        for file in files:
            loc = os.path.join(root, file)
            file_item = self.add_basic_file_item(loc)

            if file_item["grp_supported"]:
                path_item[root]["raw_groups"].append(file_item)
            else:
                path_item[root]["files"].append(file_item)

        path_item[root]["files"] = self.sort_into_types(path_item[root]["files"])

        return path_item

    @staticmethod
    def add_basic_folder_item(location):
        if os.path.exists(location):
            path, name = os.path.split(location)

            return {
                "key": gen_folder_key(location),
                "name": name,
                "path": path,
                "location": location,
                "mtime": os.path.getmtime(location),
                "ctime": os.path.getctime(location),
                "size": os.stat(location).st_size,
                "favourite": favourite.is_favourite(location),
                "watch": watch.is_watching(location)
            }
        else:
            raise Exception("Error. [location] does not exist in skeleton. Given: " + location)

    def add_basic_file_item(self, location):
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
                "mtime": os.path.getmtime(location),
                "ctime": os.path.getctime(location),
                "size": size,
                "type": file_type,
                "grp_supported": grp_supported,
                "quarantined": quarantine.is_quarantined(location),
                "favourite": favourite.is_favourite(location)
            }

            # save images and documents to a folder running on the server so that its accessible through the browser
            if file_type in ("images", "documents"):
                try:
                    shutil.copy2(src=location, dst=CLIENT_FILES_DUMP_PATH)
                except OSError as e:
                    print(e)

            return file_dict

    def visit_folder(self, path):
        if self.session["check"]["S2"]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    if path in self.skeleton:
                        self.session["check"]["S3"] = True
                        self.session["visiting"] = path

                        if not self.session["init"]:
                            Thread(target=self.group_protocol, name="fsys_group_protocol").start()
                            self.session["init"] = True

                        if path not in set(self.session["visited_paths"]):
                            self.session["visited_paths"].append(path)

                        USER_CONFIG_DICT["last_visited"] = path
                        sdh.save_data(path=USER_CONFIG_FILE, data=USER_CONFIG_DICT)
                        print("Visiting folder: "+path)

                else:
                    raise Exception("Error. Path [path] is not a folder. Given: " + path)
            else:
                raise Exception("Error. [path] does not exist in skeleton. Given: " + path)
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def extract_from_visit_folder(self):
        if self.session["check"]["S3"]:
            path = self.session["visiting"]
            self.extract(path)
            self.session["extracted_paths"].append(path)
            self.session["check"]["S4"] = True
            print("Extracted in visiting folder.")
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def extract_fron_skeleton(self):
        if self.session["check"]["S5"]:
            for path in self.skeleton:
                if path != self.session["visiting"]:
                    self.extract(path)
                    self.session["extracted_paths"].append(path)

            self.session["check"]["S6"] = True
            print("Extracted all in skeleton.")
        else:
            raise Exception("Error. Make sure you grouped the visiting folder before hand.")

    def extract(self, path):
        # if the type is not a list then this path has already be extracted
        if type(self.skeleton[path]["raw_groups"]) is list:
            for i, item in enumerate(self.skeleton[path]["raw_groups"]):
                if item is not None:
                    if item["grp_supported"]:
                        if item["type"] == "documents":
                            extracted = ExtractFromDocument().get_content(file_path=item["location"])

                            if extracted is not None:
                                self.skeleton[path]["raw_groups"][i].update({ASSOC_RAW_CONTENT_KEY["documents"]: extracted})
                            else:
                                if item["type"] not in self.skeleton[path]["files"]:
                                    self.skeleton[path]["files"].update({item["type"]: []})
                                self.skeleton[path]["files"][item["type"]].append(item)
                                self.skeleton[path]["raw_groups"][i] = None

    def group_in_visit_folder(self):
        if self.session["check"]["S4"]:
            path = self.session["visiting"]
            self.group(path)
            self.session["group_paths"].append(path)
            self.session["check"]["S5"] = True
            print("Grouped in visiting folder.")
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def group_fron_skeleton(self):
        if self.session["check"]["S6"]:
            for path in self.skeleton:
                if path != self.session["visiting"]:
                    self.group(path)
                    self.session["group_paths"].append(path)

            self.session["check"]["S7"] = True
            print("Grouped all in skeleton.")
        else:
            raise Exception("Error. Make sure you extracted from entire skeleton previously.")

    def group(self, path):
        self.skeleton[path]["groups"] = self.sort_into_types(self.filter_out_none(self.skeleton[path]["raw_groups"]))

        for item_type, items in self.skeleton[path]["groups"].items():
            if item_type == "documents":
                text_list = self.get_text_list(items)
                dc = DocumentCluster(text_list)
                grp_list = dc.cluster_list()
                print(dc.terms(5))
                grp_terms = dc.terms(5)

                self.skeleton[path]["groups"][item_type] = self.filter_into_groups(grp_list, items)

    def build_corpus(self, path_in_skel):
        if path_in_skel in self.skeleton:
            pass

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
    def exclude_group_supported(path_dict):
        excluded = {}

        if type(path_dict) is dict:
            for item_type, items in path_dict.items():
                if item_type not in excluded:
                    excluded.update({item_type: []})
                for item in items:
                    if not item["grp_supported"] and ASSOC_RAW_CONTENT_KEY["documents"] not in item:
                        excluded[item_type].append(item)

            return excluded
        else:
            raise TypeError

    @staticmethod
    def filter_out_none(items):
        filtered = []

        for item in items:
            if item is not None:
                filtered.append(items)

        return filtered

    @staticmethod
    def get_text_list(file_items_list):
        text_list = []

        for doc in file_items_list:
            if ASSOC_RAW_CONTENT_KEY["documents"] in doc:
                text_list.append(doc[ASSOC_RAW_CONTENT_KEY["documents"]])
            else:
                print(doc["name"])

        return text_list

    @staticmethod
    def sort_into_types(file_item_list):
        if type(file_item_list) is list:
            sorted_items = {}

            if len(file_item_list) > 0:
                if type(file_item_list[0]) is list:
                    file_item_list = file_item_list[0]

            for item in file_item_list:
                if item is not None:
                    if item["type"] not in sorted_items:
                        sorted_items.update({item["type"]: []})

                    sorted_items[item["type"]].append(item)

            return sorted_items
        elif type(file_item_list) is dict:
            return file_item_list
        else:
            print(file_item_list)
            raise TypeError

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


class FolderH(object):
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
        favourite.add(self.loc)
        return True

    def remove_favourite(self):
        favourite.remove(self.loc)
        return True

