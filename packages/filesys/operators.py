import os
from packages import SavedDataHandler
from packages.func import item_properties_list


sdh = SavedDataHandler()


class Quarantine(object):
    def __init__(self):
        self.save_path = "list_quarantined.json"

    def add(self, location, expire_datetime):
        if os.path.exists(location):
            q_data = list(sdh.get_data(self.save_path))
            q_data.append({
                "location": location,
                "expire_datetime": expire_datetime
            })
            sdh.save_data(self.save_path, q_data)

    def remove(self, location):
        if os.path.exists(location):
            q_data = list(sdh.get_data(self.save_path))

    def is_quarantined(self, location):
        if os.path.exists(location):
            q_data = list(sdh.get_data(self.save_path))

            for dict_item in q_data:
                if dict_item["location"] == location:
                    return True

            return False

    def expired(self, location):
        pass


class Collections(object):
    def __init__(self):
        self.save_path = "list_collection.json"

    def add(self, name, location):
        if os.path.exists(location):
            data = list(sdh.get_data(self.save_path))
            collections = set(item_properties_list(data, "name"))

            if name not in collections:
                data.append({
                    "name": name,
                    "items": None,
                    "tags": []
                })

                return sdh.save_data(self.save_path, data)

            else:
                return False

    def remove(self, collection, location):
        pass

    def add_collection(self, collection):
        pass

    def remove_collection(self, collection):
        pass


class Watch(object):
    def __init__(self):
        self.save_path = "dict_watch.json"

    def add_folder(self, location):
        pass

    def remove_folder(self, location):
        pass

    def is_watching(self, location):
        if os.path.exists(location):
            q_data = list(sdh.get_data(self.save_path))

            for dict_item in q_data:
                if dict_item["location"] == location:
                    return True

            return False


class Tags(object):
    def __init__(self):
        self.save_path = "dict_tags.json"

    def add_tag(self, location, tag):
        pass

    def remove_tag(self, location, tag):
        pass

    def tags(self, location):
        pass


class Favourite(object):
    def __init__(self):
        self.save_path = "list_favourites.json"

    def add(self, location):
        if os.path.exists(location):
            q_data = list(sdh.get_data(self.save_path))
            q_data.append(location)
            sdh.save_data(self.save_path, q_data)

    def remove(self, location):
        if os.path.exists(location):
            q_data = list(sdh.get_data(self.save_path))
            new_llst = []

            for item in q_data:
                if item != location:
                    new_llst.append(location)

            sdh.save_data(self.save_path, new_llst)

    def is_favourite(self, location):
        if os.path.exists(location):
            q_data = set(list(sdh.get_data(self.save_path)))
            return location in q_data
