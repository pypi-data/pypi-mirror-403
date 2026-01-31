# yi-config-starter

A lightweight YAML configuration loader with automatic config discovery, placeholder substitution, and a thread-safe singleton interface.

This library is intended to centralize configuration loading logic while keeping application code clean and portable across environments.

---

## Installation

```bash
pip install yi-config-starter
````

---

## Quick Start

```python
from yi_config_starter import ApplicationConfiguration

cfg = ApplicationConfiguration.get_instance()
config = cfg.get_config()

db_host = cfg.get_config_value("db.datasource.config.host")
print(db_host)
```

You may also initialize it explicitly (still resolves to a singleton internally):

```python
from yi_config_starter import ApplicationConfiguration
cfg = ApplicationConfiguration(
    filename="config.yml",
    env_var="MY_APP_CONFIG",
    app_name="my-app",
    # path="/absolute/or/~/path/to/config.yml",
    # extra_placeholders={"PROJECT_ROOT": "/some/path"},
)
```

---

## Configuration File Discovery

By default, the loader searches for `config.yml` in the following order:

1. Explicit path passed to the constructor (`path=...`)
2. Path provided via environment variable
3. Current working directory, then parent directories (walking upward)
4. User configuration directory

   * Windows: `%APPDATA%\<app_name>\config.yml`
   * Linux/macOS: `~/.config/<app_name>/config.yml`
5. Entries on `sys.path` (recursive search)

If no configuration file is found, a `FileNotFoundError` is raised.

---

## Placeholder Substitution

Before parsing YAML, placeholders in the configuration file are substituted.

### Built-in Placeholders

| Placeholder        | Description                                    |
| ------------------ | ---------------------------------------------- |
| `{{HOME}}`         | User home directory                            |
| `{{separator}}`    | OS path separator (`/` or `\`)                 |
| `{{APPDATA}}`      | Windows `%APPDATA%` or fallback to `~/.config` |
| `{{XDG_CONFIG}}`   | `$XDG_CONFIG_HOME` or `~/.config`              |
| `{{ENV:VAR_NAME}}` | Value of environment variable `VAR_NAME`       |

Custom placeholders may be supplied via `extra_placeholders`.

### Example

```yaml
paths:
  data_dir: "{{HOME}}{{separator}}data"
  cache_dir: "{{XDG_CONFIG}}{{separator}}my-app{{separator}}cache"
  api_key: "{{ENV:MY_API_KEY}}"
```

---

## API Reference

### `ApplicationConfiguration.get_instance(...)`

Returns the singleton configuration instance (thread-safe).

---

### `cfg.get_config() -> dict`

Returns the entire configuration as a dictionary.

---

### `cfg.get_config_value("a.b.c")`

Returns a nested configuration value using dot-separated keys.

---

### `ApplicationConfiguration.get_value_from_config(config: dict, key: str)`

Static helper for retrieving nested values from an arbitrary dictionary.

---

## Versioning

The package version is resolved dynamically from:

```
import yi_config_starter
yi_config_starter.__version__
```

Defined in:

```
/yi_config_starter/__init__.py
```

---

## License

MIT License — see the `LICENSE` file.

