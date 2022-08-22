import yaml


def get_creds(filepath="creds.yaml"):
    with open(filepath, "r", encoding="utf-8") as stream:
        data_loaded = yaml.safe_load(stream)
    return data_loaded
