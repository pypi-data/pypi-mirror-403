'''
https://peps.python.org/pep-0249/#introduction
'''

import logging

from tdlc_connector import connections, version

from tdlc_connector.constants import DataType

from tdlc_connector.exceptions import (
    Error,
    Warning,
    InterfaceError,
    DatabaseError,
    InternalError,
    OperationalError,
    ProgrammingError,
    IntegrityError,
    DataError,
    NotSupportedError,
)

from tdlc_connector.formats import (
    Date,
    Time,
    Timestamp,
    DateFromTicks,
    TimeFromTicks,
    TimestampFromTicks,
    Binary,
)

VERSION = version.VERSION


apilevel = '2.0'

'''
threadsafety	Meaning
    0	        Threads may not share the module.
    1	        Threads may share the module, but not connections.
    2	        Threads may share the module and connections.
    3	        Threads may share the module, connections and cursors.
'''
threadsafety = 1


'''
paramstyle	    Meaning
    qmark	    Question mark style, e.g. ...WHERE name=?
    numeric	    Numeric, positional style, e.g. ...WHERE name=:1
    named	    Named style, e.g. ...WHERE name=:name
    format	    ANSI C printf format codes, e.g. ...WHERE name=%s
    pyformat	Python extended format codes, e.g. ...WHERE name=%(name)s
'''


paramstyle = "pyformat"

# 用户可以通过 logging.getLogger('tdlc_connector').setLevel(logging.DEBUG) 来启用日志
logging.getLogger(__name__).addHandler(logging.NullHandler())


class DBAPISet(frozenset):
    def __ne__(self, other):
        if isinstance(other, set):
            return frozenset.__ne__(self, other)
        else:
            return other not in self

    def __eq__(self, other):
        if isinstance(other, frozenset):
            return frozenset.__eq__(self, other)
        else:
            return other in self

    def __hash__(self):
        return frozenset.__hash__(self)


STRING = DBAPISet([
    DataType.CHAR, 
    DataType.VARCHAR,
    DataType.STRING,
    DataType.TINYTEXT,
    DataType.MEDIUMTEXT,
    DataType.LONGTEXT,
    DataType.ENUM
    ])
                
BINARY = DBAPISet([
    DataType.TINYBLOB,
    DataType.BLOB,
    DataType.MEDIUMBLOB,
    DataType.LONGBLOB
    ])

NUMBER = DBAPISet([
    DataType.TINYINT,
    DataType.SMALLINT,
    DataType.MEDIUMINT,
    DataType.INT,
    DataType.INTEGER,
    DataType.BIGINT,
    DataType.LONG,
    DataType.DECIMAL,
    DataType.FLOAT,
    DataType.DOUBLE
])

DATE = DBAPISet([DataType.DATE])
TIME = DBAPISet([DataType.TIME])
TIMESTAMP = DBAPISet([DataType.TIMESTAMP, DataType.DATETIME])
DATETIME = TIMESTAMP
ROWID = DBAPISet()


connect = connections.DlcConnection


__all__ = (

    "VERSION",
    "apilevel",
    "threadsafety",
    "paramstyle",

    "Error",
    "Warning",
    "InterfaceError",
    "DatabaseError",
    "InternalError",
    "OperationalError",
    "ProgrammingError",
    "IntegrityError",
    "DataError",
    "NotSupportedError",

    "Date",
    "Time",
    "Timestamp",
    "DateFromTicks",
    "TimeFromTicks",
    "TimestampFromTicks",
    "Binary",
    "STRING",
    "BINARY",
    "NUMBER",
    "DATE",
    "TIME",
    "TIMESTAMP",
    "DATETIME",
    "ROWID",
    "connect",
    "connections",
    "cursors",
)