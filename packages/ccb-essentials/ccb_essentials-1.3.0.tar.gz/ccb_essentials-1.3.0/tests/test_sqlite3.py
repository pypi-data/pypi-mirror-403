"""Unit tests"""

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import pytest

from ccb_essentials.filesystem import real_path, temporary_path
from ccb_essentials.sqlite3 import (
    DatabaseApplicationIdError,
    DatabaseMigrationError,
    DatabaseVersionError,
    Sqlite3,
    SqlObjectFrozen,
)


memory = ":memory:"


def _migration_0to1(conn: sqlite3.Connection, db_version: int) -> bool:
    """Test migration."""
    assert db_version == 0
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (test_id int NOT NULL)")
    cursor.execute("INSERT INTO test values (123)")
    return True


def _migration_1to2(conn: sqlite3.Connection, db_version: int) -> bool:
    """Test migration."""
    assert db_version == 1
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE test ADD string1 text NOT NULL DEFAULT 'x'")
    cursor.execute("ALTER TABLE test ADD string2 text")
    cursor.execute("CREATE TABLE test2 (test2_id int NOT NULL)")
    return True


def _test_id(conn: sqlite3.Connection, test_id: int) -> int | None:
    """Select a record from _migration_0to1()."""
    cursor = conn.cursor()
    cursor.execute("select test_id from test where test_id = ?", [test_id])
    result = cursor.fetchone()
    if result and isinstance(result[0], int):
        return result[0]
    return None


def _bad_migration(_conn: sqlite3.Connection, _db_version: int) -> bool:
    """Test migration."""
    return False


class TestSqlite3:
    """Unit tests"""

    @staticmethod
    def test_init() -> None:
        """It should initialize a Sqlite3 class and file on the filesystem."""
        with temporary_path() as path:
            assert not path.is_file()
            db = Sqlite3(path, [])
            assert path.is_file()
            assert db.db_version == 0

    @staticmethod
    def test_db_name() -> None:
        """It should know its name."""
        db = Sqlite3(memory, [])
        assert db.db_name == memory

        with temporary_path() as path:
            db = Sqlite3(path, [])
            assert db.db_name == str(real_path(path))

    @staticmethod
    def test_migration() -> None:
        """It should initialize a schema."""
        db = Sqlite3(memory, [_migration_0to1])
        assert db.db_version == 1
        result = _test_id(db.con, 123)
        assert isinstance(result, int)
        assert result == 123

    @staticmethod
    def test_migration_failed() -> None:
        """It should not advance the schema version if a migration fails."""
        with pytest.raises(DatabaseMigrationError):
            db = Sqlite3(memory, [_bad_migration])
            assert db.db_version == 0

    @staticmethod
    def test_future_database() -> None:
        """It should fail when the schema version is greater than the application's version."""
        db = Sqlite3(memory, [_migration_0to1, _migration_1to2])
        assert db.db_version == 2
        with pytest.raises(DatabaseVersionError):
            Sqlite3(db.con, [_migration_0to1])  # implies application version==1

    @staticmethod
    def test_version_requirements() -> None:
        """It should constrain the application to use a database with a range of required versions."""
        db = Sqlite3(memory, [_migration_0to1, _migration_1to2])
        Sqlite3(db.con, db_versions=[2])
        Sqlite3(db.con, db_versions=[2, 3])

    @staticmethod
    def test_version_requirements_failed() -> None:
        """It should fail when the database version doesn't match one of the required versions."""
        db = Sqlite3(memory, [_migration_0to1, _migration_1to2])
        with pytest.raises(DatabaseVersionError):
            Sqlite3(db.con, db_versions=[1])
        with pytest.raises(DatabaseVersionError):
            Sqlite3(db.con, db_versions=[3, 4])

    @staticmethod
    def test_application_id() -> None:
        """It should set a unique application_id for the database."""
        db = Sqlite3(memory, [_migration_0to1])
        assert db.application_id == 0

        application_id = 12345678
        db = Sqlite3(memory, [_migration_0to1], application_id=application_id)
        assert db.application_id == application_id

    @staticmethod
    def test_application_id_mismatch() -> None:
        """It should fail if the required application_id does not match the database."""
        application_id = 12345678
        db = Sqlite3(memory, [], application_id=application_id)
        with pytest.raises(DatabaseApplicationIdError):
            Sqlite3(db.con, [], application_id=application_id + 1)


@dataclass(frozen=True)
class SomeData(SqlObjectFrozen):
    test_id: int
    string1: str
    string2: str | None

    @classmethod
    def from_mapping(cls, fields: Mapping[str, Any]) -> 'SomeData':  # noqa: UP037
        return SomeData(
            test_id=fields['test_id'],
            string1=fields['string1'],
            string2=fields['string2'],
        )


def fixture_some_data() -> SomeData:
    """Populate a dataclass instance from a row of data."""
    db = Sqlite3(memory, [_migration_0to1, _migration_1to2])
    row = db.con.execute("SELECT test_id, string1, string2 FROM test").fetchone()
    data = SomeData.from_mapping(row)
    assert data.test_id == 123
    assert data.string1 == 'x'
    assert data.string2 is None
    return data


class TestSqlObject:
    """Unit tests"""

    @staticmethod
    def test_values() -> None:
        """It should present the underlying row of data as a list of values."""
        assert fixture_some_data().values == [123, 'x', None]

    @staticmethod
    def test_fields_list() -> None:
        """It should present the underlying row of data as a list of field names."""
        assert fixture_some_data().fields_list() == ['test_id', 'string1', 'string2']

    @staticmethod
    def test_fields_bindings() -> None:
        """It should present the underlying row of data as placeholders for binding values to a query."""
        assert fixture_some_data().fields_bindings() == '?, ?, ?'

    @staticmethod
    def test_fields_str() -> None:
        """It should present the underlying row of data as field names for constructing a query."""
        assert fixture_some_data().fields_str() == 'test_id, string1, string2'
