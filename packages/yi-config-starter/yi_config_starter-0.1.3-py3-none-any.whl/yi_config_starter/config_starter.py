"""
Startup myutils
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from threading import RLock
from typing import Optional, Tuple, Dict

import yaml  # pip install pyyaml


class ApplicationConfiguration:
    """
    ApplicationConfiguration: Singleton class, use constructor or static method get_instance.
    Pass environment='prod', 'real' or 'production' for loading prod environment config, else sandbox config will be
    loaded.
    """
    __instance = None
    __lock = RLock()

    # noinspection PyUnusedLocal
    def __init__(self, *args, **kwargs):
        if not hasattr(ApplicationConfiguration.__instance, 'inited'):
            self.inited = True
            self._logger = logging.getLogger(__name__)
            self.__config_dict = {}
            config_params = {}
            if kwargs.get('filename'):
                config_params['filename'] = kwargs.get('filename')
            if kwargs.get('env_var'):
                config_params['env_var'] = kwargs.get('env_var')
            if kwargs.get('path'):
                config_params['path'] = kwargs.get('path')
            if kwargs.get('app_name'):
                config_params['app_name'] = kwargs.get('app_name')
            if kwargs.get('extra_placeholders'):
                config_params['extra_placeholders'] = kwargs.get('extra_placeholders')
            self.config_path, self.__config = self.__find_config(**config_params)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__lock.acquire()
            if not cls.__instance:
                cls.__instance = super().__new__(cls)
        return cls.__instance

    @staticmethod
    def get_placeholder_values():
        """
        Utility value for replacing values in config.yml template
        @return:
        """
        return {
            'HOME': os.path.expanduser("~"),
            'separator': os.path.sep,
        }

    @staticmethod
    def get_instance(*args, **kwargs):
        """
        Get singleton instance of this class

        @param args:
        @param kwargs:
        @return:
        """
        if not ApplicationConfiguration.__instance:
            ApplicationConfiguration.__lock.acquire()
            if not ApplicationConfiguration.__instance:
                ApplicationConfiguration.__instance = ApplicationConfiguration(*args, **kwargs)
        return ApplicationConfiguration.__instance

    def __find_config(
            self,
            *,
            filename: str = "config.yml",
            env_var: str = "TRADIER_CONFIG",
            path: Optional[str | Path] = None,
            app_name: str = "tradier",
            extra_placeholders: Optional[Dict[str, str]] = None,
    ) -> Tuple[Path, dict]:
        """
        Find and load the first config YAML from these locations (in order):
          1) explicit `path=`
          2) env var path `env_var`
          3) cwd -> parents (filename)
          4) user config (~/.config/<app_name>/<filename> or %APPDATA%\\<app_name>\\)
          5) anywhere on sys.path (recursive)
        Returns (path, data_dict). Preprocesses {{TOKENS}} before parsing.
        """
        # 1) explicit path
        if path:
            p = Path(path).expanduser()
            if not p.is_file():
                raise FileNotFoundError(f"Config not found at explicit path: {p}")
            return p, self._read_yaml(p, extra_placeholders)

        # 2) env var path
        env_val = os.getenv(env_var)
        if env_val:
            p = Path(env_val).expanduser()
            if p.is_file():
                return p, self._read_yaml(p, extra_placeholders)

        # 3) cwd -> parents
        p = self._walk_up_for_file(Path.cwd(), filename)
        if p:
            return p, self._read_yaml(p, extra_placeholders)

        # 4) user config dir
        uc = self._user_config_candidate(app_name) / filename
        if uc.is_file():
            return uc, self._read_yaml(uc, extra_placeholders)

        # 5) sys.path
        sp = self._search_sys_path(filename)
        if sp:
            return sp, self._read_yaml(sp, extra_placeholders)

        raise FileNotFoundError(
            f"Could not find {filename!r}. Set {env_var} to a file path or pass `path=`."
        )

    # noinspection PyMethodMayBeStatic
    def _search_sys_path(self, filename: str) -> Optional[Path]:
        filename = Path(filename).name
        for entry in sys.path:
            if not entry:
                continue
            p = Path(entry)
            if p.is_dir():
                cand = p / filename
                if cand.is_file():
                    return cand
                for root, _, files in os.walk(p):
                    if filename in files:
                        return Path(root) / filename
        return None

    # noinspection PyMethodMayBeStatic
    def _user_config_candidate(self, app_name: str) -> Path:
        if os.name == "nt":
            base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
            return Path(base) / app_name
        return Path.home() / ".config" / app_name

    # noinspection PyMethodMayBeStatic
    def _walk_up_for_file(self, start: Path, filename: str) -> Optional[Path]:
        start = start.resolve()
        for p in (start, *start.parents):
            cand = p / filename
            if cand.is_file():
                return cand
        return None

    # noinspection PyMethodMayBeStatic
    def _preprocess_yaml_text(self, text: str, extra_placeholders: Optional[Dict[str, str]] = None) -> str:
        """
        Replace {{PLACEHOLDER}} tokens with platform-specific values *before* YAML parsing.
        Built-ins:
          {{HOME}}         -> str(Path.home())
          {{separator}}    -> os.sep
          {{APPDATA}}      -> Windows %APPDATA% or "~/.config" fallback
          {{XDG_CONFIG}}   -> $XDG_CONFIG_HOME or "~/.config"
          {{ENV:VAR_NAME}} -> value of environment variable VAR_NAME (empty if missing)
        You can pass extra_placeholders to override or add tokens.
        """
        # base mapping
        appdata = os.environ.get("APPDATA") or str(Path.home() / ".config")
        xdg_config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        mapping = {
            "HOME": str(Path.home()),
            "separator": os.sep,
            "APPDATA": appdata,
            "XDG_CONFIG": xdg_config,
        }
        if extra_placeholders:
            mapping.update(extra_placeholders)

        # Fast path if no tokens at all
        if "{{" not in text:
            return text

        # Replace simple {{KEY}} tokens
        for k, v in mapping.items():
            text = text.replace(f"{{{{{k}}}}}", v)

        # Replace {{ENV:NAME}} tokens
        # Simple scan to avoid regex: find all occurrences of {{ENV:...}}
        start = 0
        while True:
            i = text.find("{{ENV:", start)
            if i == -1:
                break
            j = text.find("}}", i + 6)
            if j == -1:
                break  # unmatched; let YAML error out naturally
            env_key = text[i + 6: j].strip()  # after "ENV:"
            env_val = os.environ.get(env_key, "")
            text = text[:i] + env_val + text[j + 2:]
            start = i + len(env_val)

        return text

    def _read_yaml(self, path: Path, extra_placeholders: Optional[Dict[str, str]] = None) -> dict:
        raw = path.read_text(encoding="utf-8")
        pre = self._preprocess_yaml_text(raw, extra_placeholders)
        data = yaml.safe_load(pre) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML at {path} is not a mapping/object")
        return data

    def get_config(self):
        """
        Get the global config

        @return:
        """
        return self.__config

    def get_config_value(self, key: str):
        """
        Pass in a dot (.) separated string and this will fetch the property value
        """
        keys = key.split('.')
        last_val = self.__config
        for k in keys:
            try:
                last_val = last_val[k]
            except Exception:
                self._logger.error(f'Key error: {k}')
                raise
        return last_val

    @staticmethod
    def get_value_from_config(config: dict, key: str):
        """
        Takes a config (dict) and a key as dot delimited string and returns its value.
        Use get_config function to read the global config.
        If just reading from the global config, use the get_value function.
        """
        keys = key.split('.')
        last_val = config
        for k in keys:
            try:
                last_val = last_val[k]
            except Exception:
                logging.error(f'Key error: {k}')
                raise
        return last_val
