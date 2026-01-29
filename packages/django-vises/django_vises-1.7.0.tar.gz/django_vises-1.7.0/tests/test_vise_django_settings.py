from pathlib import Path

import pytest

from django_vises.django_settings.helpers import parser_database_uri


def test_parser_database_uri_sqlite():
    # sqlite ---
    # --- default
    assert parser_database_uri("sqlite://") == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }

    assert parser_database_uri("sqlite://", base_dir=Path("/data")) == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/data/db.sqlite3",
    }

    # --- match http hostname
    assert parser_database_uri("sqlite://db_v2.sqlite3") == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db_v2.sqlite3",
    }

    assert parser_database_uri("sqlite://db_v2.sqlite3", base_dir=Path("/data")) == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/data/db_v2.sqlite3",
    }

    # --- match http path
    assert parser_database_uri("sqlite:///data/db.sqlite3") == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/data/db.sqlite3",
    }

    assert parser_database_uri("sqlite:///data/db.sqlite3", base_dir=Path("/data")) == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/data/db.sqlite3",  # base_dir is ignored
    }

    # --- with options, exeample: Enabling WAL
    assert parser_database_uri(
        "sqlite://db.sqlite3?init_command=PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;"
    ) == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;"
        },
    }

    assert parser_database_uri(
        "sqlite://?init_command=PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;"
    ) == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;"
        },
    }


def test_parser_database_uri_postgresql():
    assert parser_database_uri("postgresql://user:password@localhost:5432/db") == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "db",
        "USER": "user",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": 5432,
    }

    assert parser_database_uri("postgres://user:password@localhost:5432/db") == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "db",
        "USER": "user",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": 5432,
    }

    # pool - default
    assert parser_database_uri(
        "postgres://user:password@localhost:5432/db?pool=true"
    ) == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "db",
        "USER": "user",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": 5432,
        "OPTIONS": {
            # 设置为 True 使用默认值
            "pool": True
        },
    }

    # pool - custom
    assert parser_database_uri(
        "postgres://user:password@localhost:5432/db?pool.min_size=1&pool.max_size=10&pool.timeout=60"
    ) == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "db",
        "USER": "user",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": 5432,
        "OPTIONS": {
            "pool": {
                # 这是传递给 psycopg.ConnectionPool 的参数
                "min_size": 1,  # 最小连接数
                "max_size": 10,  # 最大连接数 (根据你的需求调整)
                "timeout": 60,  # 连接超时时间 (秒)
            }
        },
    }


def test_parser_database_uri_unknown():
    pytest.raises(
        ValueError,
        parser_database_uri,
        "unknow://",
    )
