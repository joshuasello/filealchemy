import os, time, json, hashlib
from pathlib import PurePath
from shutil import copy2
from definitions import *
from cryptography.fernet import Fernet

from packages.extractors import (
    ExtractFromDocument, ExtractFromImage, ExtractFromAudio, ExtractFromAudiovisual
)
from packages.user import UserHandler

from packages.grouping import KMeansClustering

extract_from_doc = ExtractFromDocument
user = UserHandler()


class NativeLayerHandler(object):
    def __init__(self):
        self._saved_data_location = "_user_folders/"

        self.current_dir = None
        self.saved_data = self._get_saved_data()

        self.cipher = Fernet(ITEM_CIPHER_KEY)

    def list_folder(self, folder_path, recursive=False):
        if os.path.exists(folder_path):
            folders = []
            files = []
            user.change_config(file="_user_config.json", key="last_dir", value=folder_path)

            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)

                if os.path.isfile(item_path):
                    files.append(self.get_file_item(folder_path, item))
                else:
                    if not recursive:
                        folders.append(self.get_folder_item(folder_path, item))
                    else:
                        pass

            return folders, files
        else:
            raise Exception("Error. Directory does not exist: "+folder_path)

    def get_folder_item(self, folder_path, folder):
        item_path = os.path.join(folder_path, folder)
        return {
            "key": self.get_item_key(folder_path),
            "item": folder,
            "path": folder_path,
            "mtime": time.ctime(os.path.getmtime(item_path)),
            "ctime": time.ctime(os.path.getctime(item_path)),
            "size": os.stat(item_path).st_size,
        }

    def get_file_item(self, folder_path, file):
        item_path = os.path.join(folder_path, file)
        group_supported, category = self.get_file_category(file)

        file_item = {
            "checksum": self.get_file_checksum(item_path),
            "item": file,
            "path": folder_path,
            "mtime": time.ctime(os.path.getmtime(item_path)),
            "ctime": time.ctime(os.path.getctime(item_path)),
            "size": os.stat(item_path).st_size,
            "type": category,
            "description": "",
            "tags": [],
            "group_supported": group_supported,
        }

        if category == "document" and group_supported:
            file_item.update({
                "text_content": ExtractFromDocument().get_content(file_path=item_path)
            })
        if category == "image":
            copy2(src=item_path, dst=IMAGE_FILE_DUMP_PATH)

        return file_item

    def get_item_key(self, file_path):
        """Takes file path and creates an unique id."""
        return self.cipher.encrypt(str.encode(file_path)).decode()

    def get_decrypted_key(self, file_path):
        return self.cipher.decrypt(str.encode(file_path)).decode()

    def _get_saved_data(self):
        if os.path.exists(self._saved_data_location):
            data = {}

            for file in os.listdir(self._saved_data_location):
                file_path = os.path.join(self._saved_data_location, file)

                if os.path.isfile(file_path):
                    file = file.split(".")
                    file_ext = file[-1]
                    file = file[0]

                    with open(file_path, "r") as f:
                        if file_ext == "json":
                            data.update({file: json.load(f)})
            return data
        else:
            raise Exception("Error. Location for saved data does not exist: "+self._saved_data_location)

    def change_saved_data(self, file, value, key=None):
        """Change the local configuration value of a user"""

        if os.path.exists(self._saved_data_location):
            file_path = os.path.join(self._saved_data_location, file)

            if os.path.exists(file_path):
                data = open(file_path)
                data = json.load(data)

                if key is not None:
                    if key in data:
                        data[key] = value
                    else:
                        raise Exception("Key does not exist.")
                else:
                    data = value
                with open(file_path, "w") as f:
                    f.write(json.dumps(data))

                self.saved_data = self._get_saved_data()
            else:
                raise Exception("User config file folder does not exist.")
        else:
            raise Exception("User config file folder does not exist.")

    def append_saved_data(self, file,  value, key=None):
        """Change the local configuration value of a user"""

        if os.path.exists(self._saved_data_location):
            file_path = os.path.join(self._saved_data_location, file)

            if os.path.exists(file_path):
                data = json.load(open(file_path))

                if type(data) is list:
                    data.append(value)
                elif type(data) is dict:
                    if key is not None:
                        data.update({key: value})
                    else:
                        raise Exception("Error. Value key needs a value.")
                else:
                    raise Exception("Error. Invalid data type from json file.")

                with open(file_path, "w") as f:
                    data = json.dumps(data)
                    f.write(data)
                    self.saved_data = self._get_saved_data()
            else:
                raise Exception("User config file folder does not exist.")
        else:
            raise Exception("User config file folder does not exist.")

    def get_file_category(self, file):
        ext = self.get_file_ext(file)

        for category_key, category in FILE_CATEGORIES.items():
            for groups_status, extensions in category.items():
                if ext in extensions:
                    if groups_status == "group_supported":
                        return True, category_key
                    else:
                        return False, category_key

        return False, "exotic"

    def folder_checksums(self, folder_path, recursive=False):
        files = []
        if os.path.exists(folder_path):
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)

                if os.path.isfile(item_path):
                    files.append(self.get_file_checksum(item_path))
            return files
        return None

    def folder_changed(self, old, new):
        old, new = list(old), list(new)

        if len(old) == len(new):
            for i, old_checksum in enumerate(old):
                if old_checksum != new[i]:
                    return True
        else:
            return True

        return False

    @staticmethod
    def path_parts(path):
        # Windows path format: C:\\path\\to\\folder\\
        folders = []

        if os.path.isabs(path):
            parts = PurePath(path).parts

            for folder in list(parts):
                folders.append({
                    "name": folder,
                    "path": path
                })
                d, path = os.path.split(path)

        return folders

    @staticmethod
    def get_file_checksum(item_path):
        hasher = hashlib.md5()

        with open(item_path, 'rb') as f:
            hasher.update(f.read())

        return hasher.hexdigest()

    @staticmethod
    def get_document_content_list(document_file_list):
        content_list = []

        for file in document_file_list:
            content_list.append(file["text_content"])

        return content_list

    @staticmethod
    def get_file_ext(file):
        return str(file).strip(" ").lower().split(".")[-1]


class OrganizedLayer(object):
    def __init__(self, verbose=True):
        self.current_dir = None
        '''The structure is a representation of the synthesised files & folder organization.'''
        self.structure = None
        self.ph1_ini_run = True
        self.ph2_ini_run = True

    def organise(self, folder_path, organised=True, num_groups=None, recursive=False):
        def process(folders, files):
            categories = list(set([file["type"] for file in files]))
            group_comp = {}
            group_incomp = {"folder": folders}

            # sort into categories
            for category in categories:
                group_comp.update({category: []})
                group_incomp.update({category: []})

                for file in files:
                    if category == file["type"]:
                        # split
                        if file["group_supported"]:
                            group_comp[category].append(file)
                        else:
                            group_incomp[category].append(file)

            return group_comp, group_incomp

        if os.path.exists(folder_path):
            nl = NativeLayerHandler()
            # Checksum of folder constituencies
            new_cs_list = nl.folder_checksums(folder_path)

            structure = {
                "grouped": {},
                "non_grouped": {},
            }
            if nl.folder_changed(old=nl.saved_data["_last_cs_list"], new=new_cs_list) or self.ph1_ini_run:  # check if recurrent folder
                folders, files = nl.list_folder(folder_path=folder_path, recursive=recursive)
                group_comp, group_incomp = process(folders, files)

                nl.change_saved_data("_group_comp.json", value=group_comp)
                nl.change_saved_data("_group_incomp.json", value=group_incomp)

                self.ph1_ini_run = False
            else:
                group_comp = nl.saved_data["_group_comp"]
                group_incomp = nl.saved_data["_group_incomp"]

            if organised:
                if self.change_group(nl.saved_data["_group_comp"], group_comp) or self.ph2_ini_run:
                    document_group_list, document_main_terms = KMeansClustering().cluster_text(
                        text_list=nl.get_document_content_list(group_comp["document"]),
                        verbose=True,
                        num_clusters=num_groups,
                    )
                    structure["grouped"].update({
                        "document": self.filter_into_groups(document_group_list, group_comp["document"])
                    })
                    nl.change_saved_data("_last_structure_grouped.json", value=structure["grouped"])

                    self.ph2_ini_run = False
                else:
                    structure["grouped"] = nl.saved_data["_last_structure_grouped"]
            else:
                for category, item_list in group_comp.items():
                    group_incomp[category].extend(item_list)
                nl.change_saved_data("_last_structure_grouped.json", value=structure["grouped"])

            structure["non_grouped"] = group_incomp

            return structure["grouped"], structure["non_grouped"]

    @staticmethod
    def change_group(old, new):
        old, new = dict(old), dict(new)
        for cat, cat_list in new.items():
            if cat not in old:
                return True
            else:
                for i, item in enumerate(cat_list):
                    new_item_path = os.path.join(item["path"], item["item"])
                    old_item_path = os.path.join(cat_list[i]["path"], cat_list[i]["item"])

                    if os.path.exists(new_item_path) and os.path.exists(old_item_path):
                        if item["checksum"] != cat_list[i]["checksum"]:
                            return True
                    else:
                        return True
        return False

    @staticmethod
    def filter_into_groups(group_list, file_list):
        groups = {}

        if len(group_list) == len(file_list):
            for g in set(group_list):
                groups.update({str(g): []})

                for i, file in enumerate(file_list):
                    if int(group_list[i]) == g:
                        groups[str(g)].append(file)
        else:
            raise Exception(
                'Error. file_list ('+str(len(file_list))+') does not match with group_list ('+str(len(group_list))+')'
            )
        return groups

    def implement(self, structure, path):
        pass

    def title_file(self):
        pass

    def classify_to_collection(self):
        pass

