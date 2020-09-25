INTRUDER_REDIRECT = "http://127.0.0.1:5000/auth/login/"

ITEM_CIPHER_KEY = b'APM1JDVgT8WDGOWBgQv6EIhvxl4vDYvUnVdg-Vjdt0o='

GRP_SUPPORTED_EXT = ("txt", "pdf", "docx") # add image extension to process images
EXT_CATEGORIES = {
    "documents": ("txt", "pdf", "docx"),
    "sheets": ("csv"),
    "images": ("png", "jpeg", "jpg", "tif"),
    "audios": ("mp3", "wav"),
    "audiovisual": ("mp4", "mkv")
}

CLIENT_FILES_DUMP_PATH = "flaskr/static/_file_dump/"
USER_CONFIG_FILE = "dict_user_config.json"
