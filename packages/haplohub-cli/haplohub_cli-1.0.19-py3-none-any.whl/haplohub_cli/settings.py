from os import environ
from posixpath import expanduser, join

# File paths
CONFIG_DIR = expanduser("~/.haplohub")
CONFIG_FILE = join(CONFIG_DIR, "config.json")
CREDENTIALS_FILE = join(CONFIG_DIR, "credentials.json")

# Authentication
REDIRECT_PORT = 8088
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/"
API_URL = "https://api.haplohub.com"

environ["DOCKER_CONFIG"] = join(CONFIG_DIR, "docker")
