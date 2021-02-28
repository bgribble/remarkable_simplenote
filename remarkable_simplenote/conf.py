import os
import configparser

config = {}

def load_config(local_storage):
    global config
    conffile = f'{local_storage}/config'
    if os.path.exists(conffile):
        configobj = configparser.ConfigParser()
        configobj.read(conffile)

        for key, value in configobj['default'].items():
            config[key] = value

    config['local_storage'] = local_storage
    return config

