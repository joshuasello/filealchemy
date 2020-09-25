import os, json


'''Core functionality objects'''


class CollectionsHandler(object):
    def __init__(self):
        self.config = {
            "saved_file": "_saved_data/_collections.json"
        }
        self.collections = None

    def add_collection(self, collection):
        self.load_data()

        if collection not in self.collections:
            self.collections.update({
                collection: {
                    "items": [],
                    "tags": [],
                    "description": ""
                }
            })
            print("Added collection: "+collection)

        self.save_collections_state()

    def add_to_collection(self, collection, item_path):
        self.load_data()

        if collection in self.collections:
            if os.path.exists(item_path):
                self.collections[collection]["items"].append(item_path)
                print("Added item ("+item_path+") to collection: "+collection)

        self.save_collections_state()

    def load_data(self):
        file_path = self.config["saved_file"]

        if os.path.isfile(file_path):
            f = open(file_path, "r")
            file_ext = file_path.split(".")[-1]

            if file_ext == "json":
                self.collections = json.load(f)
                print("Loaded collection data")
            f.close()

    def save_collections_state(self):
        file_path = self.config["saved_file"]
        data_dict = self.collections

        if type(data_dict) is dict:
            if os.path.isfile(file_path):
                f = open(file_path, "w")
                file_ext = file_path.split(".")[-1]
                f.write(json.dumps(data_dict))
                f.close()
                print("Saved collection data")


class QuarantinedHandler(object):
    pass


class FeaturesHandler(object):
    pass


class SettingsHandler(object):
    pass


class ProfileHandler(object):
    pass
