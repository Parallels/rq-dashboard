from os.path import exists

from dotenv import load_dotenv

dotenv_path = '/etc/environment'
if exists(dotenv_path):
    print("loading environment variables from /etc/environment file..")
    load_dotenv(dotenv_path)

# flake8: noqa
from . import default_settings
from .web import blueprint
