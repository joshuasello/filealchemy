import os, json


class SavedDataHandler(object):
    def __init__(self, root="FILEALCHEMY_SAVED_DATA/"):
        self.root = root

    def change_root(self, new_root):
        if os.path.exists(new_root):
            self.root = new_root
        else:
            # create root folder
            pass

    def get_data(self, path):
        root = self.root
        location = os.path.join(root, path)

        if os.path.exists(location):
            data = None
            ext = location.split(".")[-1]

            with open(location, "r") as data_f:
                if ext == "json":
                    data = json.load(data_f)

            return data
        else:
            raise Exception("Error. Location for file does not exist. Given: " + location)

    def save_data(self, path, data):
        root = self.root
        location = os.path.join(root, path)

        if os.path.exists(location):
            with open(location, 'w') as outfile:
                json.dump(data, outfile)
                return True
        else:
            return False