import os, hashlib, shutil, time, sys, subprocess, stat, json
from definitions import CLIENT_FILES_DUMP_PATH, GRP_SUPPORTED_EXT, EXT_CATEGORIES, USER_CONFIG_FILE
from packages.func import gen_folder_key, delete_dir_contents
from pathlib import PurePath
from threading import Thread
from .operators import Quarantine, Collections, Watch, Tags, Favourite

from packages.grouping import DocumentCluster, ImageCluster
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
    "documents": "text",
    "images": "sparse_array"
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
            "group_paths": [],
            "path_terms_dict": {},
            "path_grp_terms": {}
        }
        self.config = {
            "num_groups": None
        }
        self.syncing = True
        self.recalibrate = False
        self.root_path = None
        self._do_skeleton_processing = True
        self.skeleton = {}
        self._thread_intit_routine = Thread(target=self._skeleton_processing, name="intit_routine")
        self._thread_watch_root = Thread(target=self.watch_root, name="watch_root")

    def watch_root(self):
        while True:
            current_skel = self.build_skeleton(self.root_path)
            old_skel = self.skeleton

            if self.check_changed(old_skel, current_skel) and not self._do_skeleton_processing:
                print(json.dumps(current_skel))
                print(json.dumps(old_skel))
                if bool(old_skel):
                    print("Changes noticed in root. Restructuring...")
                    self.skeleton = current_skel
                    self._do_skeleton_processing = True  # will turn off when done
                    print("Restructuring complete.")

    def existing_view(self, order=None, filter_favourite=None):
        if self.session["check"]["S3"]:
            path_item = self.skeleton[self.session["visiting"]]
            folders = path_item["folders"]
            files = self.sort_into_types(path_item["files"])

            return {}, folders, files
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def organized_view(self, order=None, filter_favourite=None):
        path_item = self.skeleton[self.session["visiting"]]
        folders = path_item["folders"]
        groups, files = self.organised_view_files_split(path_item["files"])

        return groups, folders, files

    def organised_view_files_split(self, files):
        files_list = []
        groups_list = []

        for item in files:
            if item["grp_supported"]:
                groups_list.append(item)
            else:
                files_list.append(item)

        groups = self.sort_into_types(groups_list)

        for item_type, items in groups.items():
            groups[item_type] = self.filter_into_groups(self.get_field_list(items, "local_grp_no"), items)

        return groups, self.sort_into_types(files_list)

    def _skeleton_processing(self):
        #will run on start
        while self._do_skeleton_processing:
            self.extract_from_visit_folder()
            print("Extracted in visiting folder.")
            self.group_in_visit_folder()
            print("Grouped in visiting folder.")
            self.extract_fron_skeleton()
            print("Extracted all in skeleton.")
            self.group_fron_skeleton()
            print("Grouped all in skeleton.")
            self._do_skeleton_processing = False

    def set_root(self, path):
        """Set the skeleton root"""
        if os.path.exists(path):
            if os.path.isdir(path):
                self.root_path = path
                self.session["check"]["S1"] = True

                print("Initiating watch_root Thread...")

                print("Root set.")
            else:
                raise Exception("Error. Path [path] is not a folder. Given: " + path)
        else:
            raise Exception("Error. Path [path] does not exist. Given: " + path)

    def build_init_skeleton(self):
        if self.root_path is not None and self.session["check"]["S1"]:
            if not bool(self.skeleton):
                self.skeleton = self.build_skeleton(self.root_path)
                self.cache_root_media(self.skeleton)

            self.session["check"]["S2"] = True
            print("Skeleton built.")
        else:
            raise Exception("Error. Could not build root. Make sure you set a root before building.")

    def build_skeleton(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
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
                "files": []
            }
        }

        for folder in folders:
            loc = os.path.join(root, folder)
            # add all folder items to the "folders" key in the current skeleton path
            path_item[root]["folders"].append(self.add_basic_folder_item(loc))

        for file in files:
            loc = os.path.join(root, file)
            # add all file items to the "file" key in the current skeleton path
            path_item[root]["files"].append(self.add_basic_file_item(loc))

        return path_item

    @staticmethod
    def add_basic_folder_item(location):
        if os.path.exists(location):
            path, name = os.path.split(location)

            # fields associated with the folder
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

            return {
                "hash": hash_str,
                "name": name,
                "path": path,
                "location": location,
                "mtime": os.path.getmtime(location),
                "ctime": os.path.getctime(location),
                "size": size,
                "type": file_type,
                "grp_supported": grp_supported,
                "global_grp_no": None,
                "local_grp_no": None,
                "quarantined": quarantine.is_quarantined(location),
                "favourite": favourite.is_favourite(location)
            }

    def visit_folder(self, path):
        if self.session["check"]["S2"]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    if path in self.skeleton:
                        self.session["check"]["S3"] = True
                        self.session["visiting"] = path

                        if not self.session["init"]:
                            self._thread_intit_routine.start()
                            self.session["init"] = True
                            # start watch thread
                            #self._thread_watch_root.start()

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
            if path not in set(self.session["extracted_paths"]):
                self.extract(path)
                self.session["extracted_paths"].append(path)
            else:
                print("Path exists in extracted paths")

            self.session["check"]["S4"] = True
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def extract_fron_skeleton(self):
        if self.session["check"]["S5"]:
            for path in self.skeleton:
                if path != self.session["visiting"]:
                    self.extract(path)
                    self.session["extracted_paths"].append(path)

            self.session["check"]["S6"] = True
        else:
            raise Exception("Error. Make sure you grouped the visiting folder before hand.")

    def extract(self, path):
        # if the type is not a list then this path has already be extracted
        files = self.skeleton[path]["files"]
        if type(files) is list:
            for i, item in enumerate(files):
                if item["grp_supported"]:
                    if item["type"] == "documents":
                        extracted = ExtractFromDocument(item["location"]).get_content()

                        if extracted is not None and extracted.replace(" ", "") != "":
                            self.skeleton[path]["files"][i].update({ASSOC_RAW_CONTENT_KEY[item["type"]]: extracted})
                        else:
                            # correct the impostor
                            self.skeleton[path]["files"][i]["grp_supported"] = False
                            self.skeleton[path]["files"][i]["global_grp_no"] = None
                            self.skeleton[path]["files"][i]["local_grp_no"] = None
                    elif item["type"] == "images":
                        print(item["name"])
                        extracted = ExtractFromImage(item["location"]).get_content()
                        self.skeleton[path]["files"][i].update({ASSOC_RAW_CONTENT_KEY[item["type"]]: extracted})

        else:
            raise TypeError

    def group_in_visit_folder(self):
        if self.session["check"]["S4"]:
            path = self.session["visiting"]
            self.group(path)
            self.session["group_paths"].append(path)
            self.session["check"]["S5"] = True
        else:
            raise Exception("Error. Make sure you built the skeleton before visiting a folder.")

    def group_fron_skeleton(self):
        if self.session["check"]["S6"]:
            for path in self.skeleton:
                if path != self.session["visiting"]:
                    self.group(path)
                    self.session["group_paths"].append(path)

            self.session["check"]["S7"] = True
        else:
            raise Exception("Error. Make sure you extracted from entire skeleton previously.")

    def group(self, path):
        # GSD: Group Supported Document(s)
        gsd_items_list = []
        gsi_items_list = []

        for item in self.skeleton[path]["files"]:
            if item["grp_supported"] and ASSOC_RAW_CONTENT_KEY[item["type"]] in item:
                if item["type"] == "documents":
                    gsd_items_list.append(item)
                elif item["type"] == "images":
                    gsi_items_list.append(item)

        if len(gsd_items_list) > 1:
            dc = DocumentCluster(gsd_items_list)
            grp_no_list, loc_list = dc.cluster_list()

            if len(grp_no_list) != len(loc_list):
                raise Exception(
                    "[grp_no_list] and [loc_list] are not parallel: ("+str(len(grp_no_list))+","+str(len(loc_list))+")"
                )

            for i in range(len(self.skeleton[path]["files"])):
                for j in range(len(loc_list)):
                    if self.skeleton[path]["files"][i]["location"] == loc_list[j]:
                        self.skeleton[path]["files"][i]["local_grp_no"] = grp_no_list[j]

            self.session["path_grp_terms"].update({path: dc.terms(5)})

        if len(gsi_items_list) > 1:
            ic = ImageCluster(gsi_items_list)
            grp_no_list, loc_list = ic.cluster_list()

            if len(grp_no_list) != len(loc_list):
                raise Exception(
                    "[grp_no_list] and [loc_list] are not parallel: (" + str(len(grp_no_list)) + "," + str(
                        len(loc_list)) + ")"
                )

            for i in range(len(self.skeleton[path]["files"])):
                for j in range(len(loc_list)):
                    if self.skeleton[path]["files"][i]["location"] == loc_list[j]:
                        self.skeleton[path]["files"][i]["local_grp_no"] = grp_no_list[j]

    def root_folders(self):
        folders = []

        for path_items in self.skeleton.values():
            folders.extend(path_items["folders"])

        return folders

    def root_files(self):
        files = []

        for path_items in self.skeleton.values():
            files.extend(path_items["files"])

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
    def check_changed(old_skeleton, new_skeleton):
        if type(old_skeleton) is dict and type(new_skeleton) is dict:
            # check number of paths changed
            if len(old_skeleton) == len(new_skeleton):
                for path, items in new_skeleton.items():
                    # check if a path in new skeleton doesnt exist in old
                    if path not in old_skeleton:
                        return True

                    # check if number of folders and files match up
                    if len(items["folders"]) != old_skeleton[path]["folders"] or\
                            len(items["files"]) != old_skeleton[path]["files"]:
                        return True

                    for i, item in enumerate(items["folders"]):
                        if item["location"] != old_skeleton[path]["folders"][i]["location"]:
                            return True

                    for i, item in enumerate(items["files"]):
                        if item["location"] != old_skeleton[path]["files"][i]["location"]:
                            return True

                return False
            else:
                return True
        else:
            raise TypeError

    @staticmethod
    def cache_root_media(skeleton):
        if type(skeleton) is dict:
            try:
                # del  content of client file dump folder
                delete_dir_contents(CLIENT_FILES_DUMP_PATH)
            except OSError as e:
                print(e)

            for file_items in skeleton.values():
                for item in file_items["files"]:
                    ext = item["name"].split(".")[-1]

                    # save images and documents to a folder running on the server so that its accessible through the browser
                    if ext in ("png", "jpeg", "jpg", "pdf", "txt"):
                        try:
                            shutil.copy2(src=item["location"], dst=CLIENT_FILES_DUMP_PATH)
                        except OSError as e:
                            print(e)
        else:
            print(skeleton)
            raise TypeError

    @staticmethod
    def sort_items(items_list, field, n=None):
        if type(items_list) is list:
            for i in range(len(items_list)):
                for k in range(len(items_list) - 1):
                    if float(items_list[k][str(field)]) > float(items_list[k + 1][str(field)]):
                        items_list[k], items_list[k + 1] = items_list[k + 1], items_list[k]

            if type(n) is int:
                return items_list[:n]
            else:
                return items_list
        else:
            print(items_list)
            raise TypeError

    @staticmethod
    def filter_items(items_list, field, value, n=None):
        if type(items_list) is list:
            filtered = []

            for item in items_list:
                if item[field] == value:
                    filtered.append(item)

            if type(n) is int:
                return filtered[:n]
            else:
                return filtered
        else:
            print(items_list)
            raise TypeError

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

            for item in file_item_list:
                if type(item) is dict:
                    if item["type"] not in sorted_items:
                        sorted_items.update({item["type"]: []})

                    sorted_items[item["type"]].append(item)
                else:
                    print(item)
                    raise TypeError

            return sorted_items
        else:
            print(file_item_list)
            raise TypeError

    @staticmethod
    def update_extracted(file_list):
        leftovers = []
        files = []

        for file in file_list:
            if file["type"] == "documents" and file["grp_supported"]:
                extracted = ExtractFromDocument(file["location"]).get_content()

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
            print(files_list)
            print(grp_list)
            raise TypeError

    @staticmethod
    def get_field_list(items, field):
        if type(items) is list and type(field) is str:
            field_list = []
            for item in items:
                field_list.append(item[field])

            return field_list
        else:
            print(items)
            print(field)
            raise TypeError

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

