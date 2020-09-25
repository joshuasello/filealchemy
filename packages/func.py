import os, datetime
from cryptography.fernet import Fernet
from definitions import ITEM_CIPHER_KEY


cipher = Fernet(ITEM_CIPHER_KEY)


def item_properties_list(items, item_property):
    if type(items) is list:
        if len(items) > 0:
            p_list = []

            for item in items:
                if type(item) is dict:
                    if item_property in item:
                        p_list.append(item[item_property])
                    else:
                        raise Exception("Provided property does not exist in all items in [items]")
                else:
                    raise Exception("Structure of [items] needs to be a list of dicts")

            return p_list
        else:
            return []
    else:
        raise Exception("Structure of [items] needs to be a list of dicts")


def gen_folder_key(path):
    if os.path.exists(path):
        return cipher.encrypt(str.encode(path)).decode()
    else:
        raise Exception("Error. [path] does not exist in skeleton. Given: " + path)


def decrypt_folder_key(path):
    return cipher.decrypt(str.encode(path)).decode()


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


def get_size_string(size):
    size = float(size)

    if size > 1000000000000:
        size /= 1000000000000
        amount = "TB"
    elif size > 1000000000:
        size /= 1000000000
        amount = "GB"
    elif size > 1000000:
        size /= 1000000
        amount = "MB"
    elif size > 1000:
        size /= 1000
        amount = "KB"
    else:
        amount = "B"
    return str(round(size, 1)) + amount


def file_ext(name):
    return name.split(".")[-1]


def terms_string(term_list):
    processed = []

    for terms in term_list:
        processed.append(", ".join(terms))

    return processed
