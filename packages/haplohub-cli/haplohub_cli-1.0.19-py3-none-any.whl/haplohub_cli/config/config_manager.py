import os
from genericpath import exists
from os import path

import requests

from haplohub_cli.config.config import Config

from .. import settings


class ConfigManager:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self._config = self.read_config()

    def init_config(self):
        if exists(self.config_file):
            return

        self.switch_environment(settings.API_URL)

    def read_config(self) -> Config:
        if not exists(self.config_file):
            self.init_config()

        return Config.parse_file(self.config_file)

    def switch_environment(self, api_url: str):
        response = requests.get(f"{api_url}/api/v1/config/")
        response.raise_for_status()
        data = response.json()

        if data["status"] != "success":
            raise Exception(data.get("error", "Unknown error"))

        new_config = {"redirect_port": settings.REDIRECT_PORT, "api_url": api_url, **data["result"]["cli"]}

        self._config = Config(**new_config)

        self.save()

    def save(self):
        os.makedirs(path.dirname(self.config_file), exist_ok=True)

        with open(self.config_file, "wt") as f:
            f.write(self._config.json(indent=4))

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = self.read_config()

        return self._config


config_manager = ConfigManager(config_file=settings.CONFIG_FILE)
