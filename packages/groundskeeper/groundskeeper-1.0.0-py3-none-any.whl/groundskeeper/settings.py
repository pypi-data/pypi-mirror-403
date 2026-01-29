from __future__ import annotations

import copy
from collections.abc import Callable, Iterable, KeysView, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from json import dumps

from groundskeeper._loop import loop_last
from groundskeeper.settings_schema import SchemaDict


@dataclass
class Setting:
    """A setting or group of settings."""

    key: str
    title: str
    type: str = "object"
    help: str = ""
    choices: list[str] | list[tuple[str, str]] | None = None
    default: object | None = None
    validate: list[dict] | None = None
    children: dict[str, Setting] | None = None
    editable: bool = True


type SettingsType = dict[str, object]

INPUT_TYPES = {"boolean", "integer", "number", "string", "choices", "text"}


class SettingsError(Exception):
    """Base class for settings related errors."""


class InvalidKey(SettingsError):
    """The key is not in the schema."""


class InvalidValue(SettingsError):
    """The value was not of the expected type."""


def parse_key(key: str) -> Sequence[str]:
    """Parse a dot-delimited key into components.

    Args:
        key: Dot-delimited key string (e.g., "ui.theme")

    Returns:
        Sequence of key components
    """
    return key.split(".")


def get_setting[ExpectType](
    settings: dict[str, object], key: str, expect_type: type[ExpectType]
) -> ExpectType:
    """Get a key from a settings structure.

    Args:
        settings: A settings dictionary.
        key: A dot delimited key, e.g. "ui.column"
        expect_type: The expected type of the value.

    Raises:
        InvalidValue: If the value is not the expected type.
        KeyError: If the key doesn't exist in settings.

    Returns:
        The value matching the key.
    """
    for last, key_component in loop_last(parse_key(key)):
        if last:
            result = settings[key_component]
            if not isinstance(result, expect_type):
                raise InvalidValue(f"Expected {expect_type.__name__} type; found {result!r}")
            return result
        else:
            sub_settings = settings.setdefault(key_component, {})
            assert isinstance(sub_settings, dict)
            settings = sub_settings
    raise KeyError(key)


class Schema:
    """Schema for settings validation and defaults computation."""

    def __init__(self, schema: list[SchemaDict]) -> None:
        """Initialize schema.

        Args:
            schema: List of schema dictionaries defining the settings structure.
        """
        self.schema = schema

    def set_value(self, settings: SettingsType, key: str, value: object) -> None:
        """Set a value in settings with validation.

        Args:
            settings: Settings dictionary to update.
            key: Dot-delimited key.
            value: Value to set.

        Raises:
            InvalidKey: If the key is not in the schema.
        """
        schema = self.schema
        keys = parse_key(key)
        for last, key in loop_last(keys):
            if last:
                settings[key] = value
            if key not in schema:
                raise InvalidKey()
            schema = schema[key]
            assert isinstance(schema, dict)
            if key not in settings:
                settings = settings[key] = {}

    def get_default(self, key: str) -> object | None:
        """Get a default for the given key.

        Args:
            key: Key in dotted notation

        Returns:
            Default, or None.
        """
        defaults = self.defaults

        schema_object = defaults
        for last, sub_key in loop_last(parse_key(key)):
            if last:
                return schema_object.get(sub_key, None)
            else:
                if isinstance(schema_object, dict):
                    schema_object = schema_object.get(sub_key, {})
                else:
                    return None
        return None

    @cached_property
    def defaults(self) -> dict[str, object]:
        """Compute defaults from schema.

        Returns:
            Dictionary of default settings.
        """
        settings: dict[str, object] = {}

        def set_defaults(schema: list[SchemaDict], settings: dict[str, object]) -> None:
            sub_settings: SettingsType
            for sub_schema in schema:
                key = sub_schema["key"]
                assert isinstance(sub_schema, dict)
                type = sub_schema["type"]

                if type == "object":
                    if fields := sub_schema.get("fields"):
                        sub_settings = settings[key] = {}
                        set_defaults(fields, sub_settings)

                else:
                    if (default := sub_schema.get("default")) is not None:
                        settings[key] = default

        set_defaults(self.schema, settings)
        return settings

    @cached_property
    def key_to_type(self) -> Mapping[str, type]:
        """Map keys to their expected types.

        Returns:
            Mapping from key to Python type.
        """
        TYPE_MAP = {
            "object": dict,
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "choices": str,
            "text": str,
        }

        def get_keys(setting: Setting) -> Iterable[tuple[str, type]]:
            if setting.type == "object" and setting.children:
                for child in setting.children.values():
                    yield from get_keys(child)
            else:
                yield (setting.key, TYPE_MAP[setting.type])

        keys = {
            key: value_type
            for setting in self.settings_map.values()
            for key, value_type in get_keys(setting)
        }
        return keys

    @property
    def keys(self) -> KeysView:
        """Get all valid keys in the schema.

        Returns:
            View of all valid keys.
        """
        return self.key_to_type.keys()

    @cached_property
    def settings_map(self) -> dict[str, Setting]:
        """Build a map of settings from the schema.

        Returns:
            Dictionary mapping setting keys to Setting objects.
        """
        form_settings: dict[str, Setting] = {}

        def build_settings(name: str, schema: SchemaDict, default: object = None) -> Setting:
            schema_type = schema.get("type")
            assert schema_type is not None
            if schema_type == "object":
                return Setting(
                    name,
                    schema["title"],
                    schema_type,
                    help=schema.get("help") or "",
                    default=schema.get("default", default),
                    validate=schema.get("validate"),
                    children={
                        schema["key"]: build_settings(f"{name}.{schema['key']}", schema)
                        for schema in schema.get("fields", [])
                    },
                    editable=schema.get("editable", True),
                )
            else:
                return Setting(
                    name,
                    schema["title"],
                    schema_type,
                    choices=schema.get("choices"),
                    help=schema.get("help") or "",
                    default=schema.get("default", default),
                    validate=schema.get("validate"),
                    editable=schema.get("editable", True),
                )

        for sub_schema in self.schema:
            form_settings[sub_schema["key"]] = build_settings(sub_schema["key"], sub_schema)
        return form_settings


class Settings:
    """Stores schema backed settings with validation and callbacks."""

    def __init__(
        self,
        schema: Schema,
        settings: dict[str, object],
        on_set_callback: Callable[[str, object]] | None = None,
    ) -> None:
        """Initialize settings.

        Args:
            schema: Schema instance for validation.
            settings: Initial settings dictionary.
            on_set_callback: Optional callback invoked on setting changes.
        """
        self._schema = schema
        self._settings = settings
        self._on_set_callback = on_set_callback
        self._changed: bool = False

    @property
    def changed(self) -> bool:
        """Check if settings have been modified.

        Returns:
            True if settings have changed since last up_to_date() call.
        """
        return self._changed

    @property
    def schema(self) -> Schema:
        """Get the schema.

        Returns:
            Schema instance.
        """
        return self._schema

    def up_to_date(self) -> None:
        """Mark settings as up to date (clears changed flag)."""
        self._changed = False

    @property
    def json(self) -> str:
        """Get settings in JSON form.

        Returns:
            JSON string representation of settings.
        """
        settings_json = dumps(self._settings, indent=4, separators=(", ", ": "))
        return settings_json

    def set_all(self) -> None:
        """Invoke callback for all settings (useful for initialization)."""
        if self._on_set_callback is not None:
            for key in self._schema.keys:
                self._on_set_callback(key, self.get(key))

    def get[ExpectType](
        self,
        key: str,
        expect_type: type[ExpectType] | None = None,
        *,
        expand: bool = True,
    ) -> ExpectType | object:
        """Get a setting value with type coercion.

        Args:
            key: Dot-delimited key (e.g., "ui.theme").
            expect_type: Expected type of the value (optional).
            expand: Whether to expand environment variables in strings.

        Returns:
            Setting value, coerced to expected type if provided.

        Raises:
            InvalidValue: If value cannot be coerced to expected type.
        """
        from os.path import expandvars

        sub_settings: dict[str, object] = self._settings

        for last, sub_key in loop_last(parse_key(key)):
            if last:
                value = sub_settings.get(sub_key)
                if value is None:
                    default = self._schema.get_default(key)
                    if default is None and expect_type is not None:
                        default = expect_type()
                    if default is not None and expect_type is not None:
                        if not isinstance(default, expect_type):
                            default = expect_type(default)
                    return default  # type: ignore

                if isinstance(value, str) and expand:
                    value = expandvars(value)

                if expect_type is not None:
                    if not isinstance(value, expect_type):
                        value = expect_type(value)  # type: ignore
                    if not isinstance(value, expect_type):
                        raise InvalidValue(
                            f"key {sub_key!r} is not of expected type {expect_type.__name__}"
                        )
                return value  # type: ignore

            next_settings = sub_settings.get(sub_key, {})
            if not isinstance(next_settings, dict):
                default = self._schema.get_default(key)
                if default is None and expect_type is not None:
                    default = expect_type()
                if default is not None and expect_type is not None:
                    if not isinstance(default, expect_type):
                        default = expect_type(default)
                return default  # type: ignore
            sub_settings = next_settings
        raise AssertionError("Can't get here")

    def set(self, key: str, value: object) -> None:
        """Set a setting value with validation and callback invocation.

        Args:
            key: Key in dot notation.
            value: New value.
        """
        current_value = self.get(key, expand=False)

        updated_settings = copy.deepcopy(self._settings)

        setting = updated_settings
        for last, sub_key in loop_last(parse_key(key)):
            if last:
                if current_value != value:
                    self._changed = True
                    self._settings = updated_settings
                assert isinstance(setting, dict)
                setting[sub_key] = value
            else:
                setting_node = setting.setdefault(sub_key, {})
                if isinstance(setting_node, dict):
                    setting = setting_node
                else:
                    assert isinstance(setting, dict)
                    setting[sub_key] = {}
                    setting = setting[sub_key]

        if self._on_set_callback is not None:
            self._on_set_callback(key, value)


if __name__ == "__main__":
    from rich import print

    from groundskeeper.settings_schema import SCHEMA

    schema = Schema(SCHEMA)
    settings = schema.defaults
    print(settings)

    print(schema.settings_map)

    print(schema.key_to_type)
