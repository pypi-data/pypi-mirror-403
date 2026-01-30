"""
Thin wrapper around BlitzDB's SQL backend to support SQLite/SQL engines.
"""

import inspect
from contextlib import contextmanager
from blitzdb.backends.sql.backend import Backend as BlitzSQLBackend


def _patch_blitzdb_queryset():
    try:
        from blitzdb.backends.sql import queryset as blitz_queryset
        if getattr(blitz_queryset, "_checkmate_patched", False):
            return
        import sqlalchemy
        from collections import OrderedDict
        from blitzdb.fields import ManyToManyField, OneToManyField
        from blitzdb.backends.sql.queryset import get_value
    except Exception:
        return

    def get_objects(self):
        def build_field_map(params, path=None, current_map=None):
            def m2m_o2m_getter(join_params, name, pk_key):
                def f(d, obj):
                    pk_value = obj[pk_key]
                    try:
                        v = d[name]
                    except KeyError:
                        v = d[name] = OrderedDict()
                    if pk_value is None:
                        return None

                    if pk_value not in v:
                        v[pk_value] = {}
                    if "__lazy__" not in v[pk_value]:
                        v[pk_value]["__lazy__"] = join_params["lazy"]
                    if "__collection__" not in v[pk_value]:
                        v[pk_value]["__collection__"] = join_params["collection"]
                    return v[pk_value]

                return f

            def fk_getter(join_params, key):
                def f(d, obj):
                    pk_value = obj[join_params["table_fields"]["pk"]]
                    if pk_value is None:
                        # we set the key value to "None", to indicate that the FK is None
                        d[key] = None
                        return None

                    if not key in d:
                        d[key] = {}
                    v = d[key]
                    if "__lazy__" not in v:
                        v["__lazy__"] = join_params["lazy"]
                    if "__collection__" not in v:
                        v["__collection__"] = join_params["collection"]
                    return v

                return f

            if current_map is None:
                current_map = {}
            if path is None:
                path = []
            for key, field in params["table_fields"].items():
                if key in params["joins"]:
                    continue

                current_map[field] = path + [key]
            for name, join_params in params["joins"].items():
                if name in current_map:
                    del current_map[name]
                if isinstance(
                    join_params["relation"]["field"], (ManyToManyField, OneToManyField)
                ):
                    build_field_map(
                        join_params,
                        path
                        + [
                            m2m_o2m_getter(
                                join_params, name, join_params["table_fields"]["pk"]
                            )
                        ],
                        current_map,
                    )
                else:
                    build_field_map(
                        join_params, path + [fk_getter(join_params, name)], current_map
                    )
            return current_map

        def replace_ordered_dicts(d):
            for key, value in d.items():
                if isinstance(value, OrderedDict):
                    replace_ordered_dicts(value)
                    d[key] = list(value.values())
                elif isinstance(value, dict):
                    d[key] = replace_ordered_dicts(value)
            return d

        s = self.get_select()
        field_map = build_field_map(self.include_joins)

        with self.backend.transaction():
            try:
                result = self.backend.connection.execute(s)
                if result.returns_rows:
                    try:
                        objects = list(result.mappings().all())
                    except Exception:
                        rows = list(result.fetchall())
                        keys = list(result.keys())
                        objects = [dict(zip(keys, row)) for row in rows]
                else:
                    objects = []
            except sqlalchemy.exc.ResourceClosedError:
                objects = None
                raise

        # we "fold" the objects back into one list structure
        self.objects = []
        pks = []

        unpacked_objects = OrderedDict()
        for obj in objects:
            if not obj["pk"] in unpacked_objects:
                unpacked_objects[obj["pk"]] = {
                    "__lazy__": self.include_joins["lazy"],
                    "__collection__": self.include_joins["collection"],
                }
            unpacked_obj = unpacked_objects[obj["pk"]]
            for key, path in field_map.items():
                d = unpacked_obj
                for element in path[:-1]:
                    if callable(element):
                        d = element(d, obj)
                        if d is None:
                            break

                    else:
                        d = get_value(d, element, create=True)
                else:
                    d[path[-1]] = obj[key]

        self.objects = [
            replace_ordered_dicts(unpacked_obj)
            for unpacked_obj in unpacked_objects.values()
        ]
        self.pop_objects = list(self.objects)[:]

    blitz_queryset.QuerySet.get_objects = get_objects
    blitz_queryset._checkmate_patched = True


class SQLBackend:
    def __init__(self, engine):
        """
        Initialize with a SQLAlchemy engine. BlitzDB handles schema creation.
        """
        _patch_blitzdb_queryset()
        self.engine = engine
        self.backend = BlitzSQLBackend(engine)
        # Ensure tables exist (if method is available)
        self.init_schema()

    def init_schema(self):
        """
        Initialize backend schema for supported BlitzDB versions.
        """
        try:
            from checkmate.lib import models as cm_models
            from checkmate.lib.models import BaseDocument
            modules = [cm_models]
            try:
                from checkmate.contrib.plugins.git import models as git_models
                modules.append(git_models)
            except Exception:
                pass

            for module in modules:
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if not issubclass(cls, BaseDocument):
                        continue
                    if getattr(cls, "__abstract__", False):
                        continue
                    try:
                        self.backend.register(cls)
                    except Exception:
                        continue
        except Exception:
            pass

        init_method = getattr(self.backend, "init_schema", None)
        if callable(init_method):
            try:
                init_method()
            except Exception:
                pass

        create_method = getattr(self.backend, "create_schema", None)
        if callable(create_method):
            try:
                create_method()
                return None
            except Exception:
                pass

        for method_name in ("create_tables", "init_tables"):
            method = getattr(self.backend, method_name, None)
            if callable(method):
                try:
                    method()
                    return None
                except Exception:
                    pass

        # Fallback: touch tables for known models to trigger creation.
        try:
            from checkmate.lib import models as cm_models
            from checkmate.lib.models import BaseDocument

            for _, cls in inspect.getmembers(cm_models, inspect.isclass):
                if not issubclass(cls, BaseDocument):
                    continue
                if getattr(cls, "__abstract__", False):
                    continue
                try:
                    self.get_table(cls)
                except Exception:
                    continue
        except Exception:
            # Best-effort fallback; schema may be created lazily later.
            return None

        # If schema helpers exist, ensure tables are created.
        method = getattr(self.backend, "create_schema", None)
        if callable(method):
            try:
                method()
            except Exception:
                pass

        return None

    def _is_datetime_serialization_error(self, exc):
        message = str(exc)
        return "fromisoformat" in message or "argument must be str" in message

    def _coerce_datetime_columns(self, cls):
        engine = getattr(self.backend, "engine", None) or getattr(self, "engine", None)
        if not engine or getattr(engine.dialect, "name", None) != "sqlite":
            return False
        try:
            table = self.get_table(cls)
        except Exception:
            return False
        try:
            from sqlalchemy import text
        except Exception:
            return False

        updated = False
        for column in table.columns:
            col_name = column.name
            col_type = column.type.__class__.__name__
            if col_name not in ("created_at", "updated_at") and col_type != "DateTime":
                continue
            try:
                db_path = getattr(engine.url, "database", None)
                if db_path:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE {table} SET {col} = datetime({col}, 'unixepoch') "
                        "WHERE {col} IS NOT NULL AND typeof({col}) != 'text'"
                        .format(table=table.name, col=col_name)
                    )
                    conn.commit()
                    conn.close()
                else:
                    stmt = text(
                        "UPDATE {table} SET {col} = datetime({col}, 'unixepoch') "
                        "WHERE {col} IS NOT NULL AND typeof({col}) != 'text'"
                        .format(table=table.name, col=col_name)
                    )
                    with engine.begin() as conn:
                        conn.execute(stmt)
                updated = True
            except Exception:
                continue
        return updated

    @contextmanager
    def transaction(self):
        if hasattr(self.backend, "transaction"):
            try:
                # Avoid nested begin() when a transaction is already active.
                if getattr(self.backend, "current_transaction", None):
                    yield
                    return
                with self.backend.transaction():
                    yield
                return
            except AttributeError as exc:
                if "begin" not in str(exc):
                    raise
        # Fallback: no-op transaction when backend lacks support
        yield

    def save(self, obj):
        return self.backend.save(obj)

    def commit(self):
        if hasattr(self.backend, "commit"):
            return self.backend.commit()
        return None

    def get(self, cls, query, include=None):
        def _get():
            if include is None:
                return self.backend.get(cls, query)
            try:
                return self.backend.get(cls, query, include=include)
            except TypeError:
                return self.backend.get(cls, query)

        try:
            return _get()
        except Exception as exc:
            if self._is_datetime_serialization_error(exc) and self._coerce_datetime_columns(cls):
                return _get()
            raise

    def filter(self, cls, query, **kwargs):
        include = kwargs.pop("include", None)
        def _filter():
            if include is None:
                try:
                    result = self.backend.filter(cls, query, **kwargs)
                    return [] if result is None else result
                except TypeError:
                    if isinstance(query, dict):
                        merged = dict(query)
                        merged.update(kwargs)
                        result = self.backend.filter(cls, **merged)
                        return [] if result is None else result
                    raise
            try:
                result = self.backend.filter(cls, query, include=include, **kwargs)
                return [] if result is None else result
            except TypeError:
                if isinstance(query, dict):
                    merged = dict(query)
                    merged.update(kwargs)
                    result = self.backend.filter(cls, **merged)
                    return [] if result is None else result
                result = self.backend.filter(cls, query, **kwargs)
                return [] if result is None else result

        try:
            return _filter()
        except Exception as exc:
            if self._is_datetime_serialization_error(exc) and self._coerce_datetime_columns(cls):
                return _filter()
            raise

    def update(self, obj, fields):
        return self.backend.update(obj, fields)

    def serialize(self, obj):
        return self.backend.serialize(obj)

    @property
    def connection(self):
        return self.backend.connection

    def get_table(self, model):
        # BlitzDB SQL backend keeps metadata in backend tables
        if hasattr(self.backend, "get_table"):
            return self.backend.get_table(model)
        if hasattr(self.backend, "table"):
            return self.backend.table(model)
        raise NotImplementedError("Underlying backend does not expose get_table")


