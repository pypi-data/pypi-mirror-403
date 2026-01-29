"""Auto-generated MCP server with wrapper support.

Module: sqlite3
Server: sqlite3-mcp-server
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

import sqlite3

# Object store for handle-based types
_object_store: dict[str, Any] = {}
_handle_counter: int = 0


def _store_object(obj: Any, type_name: str) -> str:
    """Store an object and return a handle string."""
    global _handle_counter
    _handle_counter += 1
    handle = f"{type_name}_{_handle_counter}"
    _object_store[handle] = obj
    return handle


def _get_object(handle: str) -> Any:
    """Retrieve an object by its handle."""
    obj = _object_store.get(handle)
    if obj is None:
        raise ValueError(f"Invalid or expired handle: {handle}")
    return obj


mcp = FastMCP(name="sqlite3-mcp-server")

@mcp.tool(name="DateFromTicks")
def DateFromTicks() -> Any:
    """Tool: DateFromTicks"""
    return sqlite3.DateFromTicks()

@mcp.tool(name="TimeFromTicks")
def TimeFromTicks() -> Any:
    """Tool: TimeFromTicks"""
    return sqlite3.TimeFromTicks()

@mcp.tool(name="TimestampFromTicks")
def TimestampFromTicks() -> Any:
    """Tool: TimestampFromTicks"""
    return sqlite3.TimestampFromTicks()

@mcp.tool(name="adapt")
def adapt(obj: Any, proto: Any = None, alt: Any = None) -> Any:
    """Adapt given object to given protocol."""
    return sqlite3.adapt(obj=obj, proto=proto, alt=alt)

@mcp.tool(name="complete_statement")
def complete_statement(statement: Any) -> Any:
    """Checks if a string contains a complete SQL statement."""
    return sqlite3.complete_statement(statement=statement)

@mcp.tool(name="connect")
def connect(database: Any, timeout: Any = 5.0, detect_types: Any = 0, isolation_level: Any = '', check_same_thread: Any = True, factory: Any = None, cached_statements: Any = 128, uri: Any = False) -> str:
    """Opens a connection to the SQLite database file database."""
    result = sqlite3.connect(database=database, timeout=timeout, detect_types=detect_types, isolation_level=isolation_level, check_same_thread=check_same_thread, factory=factory, cached_statements=cached_statements, uri=uri)
    return _store_object(result, "Connection")

@mcp.tool(name="enable_callback_tracebacks")
def enable_callback_tracebacks(enable: Any) -> Any:
    """Enable or disable callback functions throwing errors to stderr."""
    return sqlite3.enable_callback_tracebacks(enable=enable)

@mcp.tool(name="enable_shared_cache")
def enable_shared_cache() -> Any:
    """Tool: enable_shared_cache"""
    return sqlite3.enable_shared_cache()

@mcp.tool(name="register_adapter")
def register_adapter(type: Any, adapter: Any) -> Any:
    """Register a function to adapt Python objects to SQLite values."""
    return sqlite3.register_adapter(type=type, adapter=adapter)

@mcp.tool(name="register_converter")
def register_converter(typename: Any, converter: Any) -> Any:
    """Register a function to convert SQLite values to Python objects."""
    return sqlite3.register_converter(typename=typename, converter=converter)

@mcp.tool(name="memoryview_cast")
def memoryview_cast(memoryview: str, format: Any, shape: Any = None) -> Any:
    """Cast a memoryview to a new format or shape."""
    _instance = _get_object(memoryview)
    return _instance.cast(format=format, shape=shape)

@mcp.tool(name="memoryview_hex")
def memoryview_hex(memoryview: str, sep: Any = None, bytes_per_sep: Any = 1) -> Any:
    """Return the data in the buffer as a str of hexadecimal numbers."""
    _instance = _get_object(memoryview)
    return _instance.hex(sep=sep, bytes_per_sep=bytes_per_sep)

@mcp.tool(name="memoryview_release")
def memoryview_release(memoryview: str) -> Any:
    """Release the underlying buffer exposed by the memoryview object."""
    _instance = _get_object(memoryview)
    return _instance.release()

@mcp.tool(name="memoryview_tobytes")
def memoryview_tobytes(memoryview: str, order: Any = 'C') -> Any:
    """Return the data in the buffer as a byte string."""
    _instance = _get_object(memoryview)
    return _instance.tobytes(order=order)

@mcp.tool(name="memoryview_tolist")
def memoryview_tolist(memoryview: str) -> Any:
    """Return the data in the buffer as a list of elements."""
    _instance = _get_object(memoryview)
    return _instance.tolist()

@mcp.tool(name="memoryview_toreadonly")
def memoryview_toreadonly(memoryview: str) -> Any:
    """Return a readonly version of the memoryview."""
    _instance = _get_object(memoryview)
    return _instance.toreadonly()

@mcp.tool(name="blob_close")
def blob_close(blob: str) -> Any:
    """Close the blob."""
    _instance = _get_object(blob)
    return _instance.close()

@mcp.tool(name="blob_read")
def blob_read(blob: str, length: Any = -1) -> Any:
    """Read data at the current offset position."""
    _instance = _get_object(blob)
    return _instance.read(length=length)

@mcp.tool(name="blob_seek")
def blob_seek(blob: str, offset: Any, origin: Any = 0) -> Any:
    """Set the current access position to offset."""
    _instance = _get_object(blob)
    return _instance.seek(offset=offset, origin=origin)

@mcp.tool(name="blob_tell")
def blob_tell(blob: str) -> Any:
    """Return the current access position for the blob."""
    _instance = _get_object(blob)
    return _instance.tell()

@mcp.tool(name="blob_write")
def blob_write(blob: str, data: Any) -> Any:
    """Write data at the current offset."""
    _instance = _get_object(blob)
    return _instance.write(data=data)

@mcp.tool(name="connection_backup")
def connection_backup(connection: str, target: Any, pages: Any = -1, progress: Any = None, name: Any = 'main', sleep: Any = 0.25) -> Any:
    """Makes a backup of the database."""
    _instance = _get_object(connection)
    return _instance.backup(target=target, pages=pages, progress=progress, name=name, sleep=sleep)

@mcp.tool(name="connection_blobopen")
def connection_blobopen(connection: str, table: Any, column: Any, row: Any, readonly: Any = False, name: Any = 'main') -> Any:
    """Open and return a BLOB object."""
    _instance = _get_object(connection)
    return _instance.blobopen(table=table, column=column, row=row, readonly=readonly, name=name)

@mcp.tool(name="connection_close")
def connection_close(connection: str) -> Any:
    """Close the database connection."""
    _instance = _get_object(connection)
    return _instance.close()

@mcp.tool(name="connection_commit")
def connection_commit(connection: str) -> Any:
    """Commit any pending transaction to the database."""
    _instance = _get_object(connection)
    return _instance.commit()

@mcp.tool(name="connection_create_aggregate")
def connection_create_aggregate(connection: str, name: Any, n_arg: Any, aggregate_class: Any) -> Any:
    """Creates a new aggregate."""
    _instance = _get_object(connection)
    return _instance.create_aggregate(name=name, n_arg=n_arg, aggregate_class=aggregate_class)

@mcp.tool(name="connection_create_collation")
def connection_create_collation(connection: str, name: Any, callback: Any) -> Any:
    """Creates a collation function."""
    _instance = _get_object(connection)
    return _instance.create_collation(name=name, callback=callback)

@mcp.tool(name="connection_create_function")
def connection_create_function(connection: str, name: Any, narg: Any, func: Any, deterministic: Any = False) -> Any:
    """Creates a new function."""
    _instance = _get_object(connection)
    return _instance.create_function(name=name, narg=narg, func=func, deterministic=deterministic)

@mcp.tool(name="connection_create_window_function")
def connection_create_window_function(connection: str, name: Any, num_params: Any, aggregate_class: Any) -> Any:
    """Creates or redefines an aggregate window function. Non-standard."""
    _instance = _get_object(connection)
    return _instance.create_window_function(name=name, num_params=num_params, aggregate_class=aggregate_class)

@mcp.tool(name="connection_cursor")
def connection_cursor(connection: str, factory: Any = None) -> str:
    """Return a cursor for the connection."""
    _instance = _get_object(connection)
    result = _instance.cursor(factory=factory)
    return _store_object(result, "Cursor")

@mcp.tool(name="connection_deserialize")
def connection_deserialize(connection: str, data: Any, name: Any = 'main') -> Any:
    """Load a serialized database."""
    _instance = _get_object(connection)
    return _instance.deserialize(data=data, name=name)

@mcp.tool(name="connection_enable_load_extension")
def connection_enable_load_extension(connection: str, enable: Any) -> Any:
    """Enable dynamic loading of SQLite extension modules."""
    _instance = _get_object(connection)
    return _instance.enable_load_extension(enable=enable)

@mcp.tool(name="connection_execute")
def connection_execute(connection: str, sql: Any, parameters: Any = None) -> str:
    """Executes an SQL statement."""
    _instance = _get_object(connection)
    result = _instance.execute(sql=sql, parameters=parameters)
    return _store_object(result, "Cursor")

@mcp.tool(name="connection_executemany")
def connection_executemany(connection: str, sql: Any, parameters: Any) -> str:
    """Repeatedly executes an SQL statement."""
    _instance = _get_object(connection)
    result = _instance.executemany(sql=sql, parameters=parameters)
    return _store_object(result, "Cursor")

@mcp.tool(name="connection_executescript")
def connection_executescript(connection: str, sql_script: Any) -> str:
    """Executes multiple SQL statements at once."""
    _instance = _get_object(connection)
    result = _instance.executescript(sql_script=sql_script)
    return _store_object(result, "Cursor")

@mcp.tool(name="connection_getlimit")
def connection_getlimit(connection: str, category: Any) -> Any:
    """Get connection run-time limits."""
    _instance = _get_object(connection)
    return _instance.getlimit(category=category)

@mcp.tool(name="connection_interrupt")
def connection_interrupt(connection: str) -> Any:
    """Abort any pending database operation."""
    _instance = _get_object(connection)
    return _instance.interrupt()

@mcp.tool(name="connection_iterdump")
def connection_iterdump(connection: str) -> Any:
    """Returns iterator to the dump of the database in an SQL text format."""
    _instance = _get_object(connection)
    return _instance.iterdump()

@mcp.tool(name="connection_load_extension")
def connection_load_extension(connection: str, name: Any) -> Any:
    """Load SQLite extension module."""
    _instance = _get_object(connection)
    return _instance.load_extension(name=name)

@mcp.tool(name="connection_rollback")
def connection_rollback(connection: str) -> Any:
    """Roll back to the start of any pending transaction."""
    _instance = _get_object(connection)
    return _instance.rollback()

@mcp.tool(name="connection_serialize")
def connection_serialize(connection: str, name: Any = 'main') -> Any:
    """Serialize a database into a byte string."""
    _instance = _get_object(connection)
    return _instance.serialize(name=name)

@mcp.tool(name="connection_set_authorizer")
def connection_set_authorizer(connection: str, authorizer_callback: Any) -> Any:
    """Sets authorizer callback."""
    _instance = _get_object(connection)
    return _instance.set_authorizer(authorizer_callback=authorizer_callback)

@mcp.tool(name="connection_set_progress_handler")
def connection_set_progress_handler(connection: str, progress_handler: Any, n: Any) -> Any:
    """Sets progress handler callback."""
    _instance = _get_object(connection)
    return _instance.set_progress_handler(progress_handler=progress_handler, n=n)

@mcp.tool(name="connection_set_trace_callback")
def connection_set_trace_callback(connection: str, trace_callback: Any) -> Any:
    """Sets a trace callback called for each SQL statement (passed as unicode)."""
    _instance = _get_object(connection)
    return _instance.set_trace_callback(trace_callback=trace_callback)

@mcp.tool(name="connection_setlimit")
def connection_setlimit(connection: str, category: Any, limit: Any) -> Any:
    """Set connection run-time limits."""
    _instance = _get_object(connection)
    return _instance.setlimit(category=category, limit=limit)

@mcp.tool(name="cursor_close")
def cursor_close(cursor: str) -> Any:
    """Closes the cursor."""
    _instance = _get_object(cursor)
    return _instance.close()

@mcp.tool(name="cursor_execute")
def cursor_execute(cursor: str, sql: Any, parameters: Any = ()) -> str:
    """Executes an SQL statement."""
    _instance = _get_object(cursor)
    result = _instance.execute(sql=sql, parameters=parameters)
    return _store_object(result, "Cursor")

@mcp.tool(name="cursor_executemany")
def cursor_executemany(cursor: str, sql: Any, seq_of_parameters: Any) -> str:
    """Repeatedly executes an SQL statement."""
    _instance = _get_object(cursor)
    result = _instance.executemany(sql=sql, seq_of_parameters=seq_of_parameters)
    return _store_object(result, "Cursor")

@mcp.tool(name="cursor_executescript")
def cursor_executescript(cursor: str, sql_script: Any) -> str:
    """Executes multiple SQL statements at once."""
    _instance = _get_object(cursor)
    result = _instance.executescript(sql_script=sql_script)
    return _store_object(result, "Cursor")

@mcp.tool(name="cursor_fetchall")
def cursor_fetchall(cursor: str) -> Any:
    """Fetches all rows from the resultset."""
    _instance = _get_object(cursor)
    return _instance.fetchall()

@mcp.tool(name="cursor_fetchmany")
def cursor_fetchmany(cursor: str, size: Any = 1) -> Any:
    """Fetches several rows from the resultset."""
    _instance = _get_object(cursor)
    return _instance.fetchmany(size=size)

@mcp.tool(name="cursor_fetchone")
def cursor_fetchone(cursor: str) -> Any:
    """Fetches one row from the resultset."""
    _instance = _get_object(cursor)
    return _instance.fetchone()

@mcp.tool(name="cursor_setinputsizes")
def cursor_setinputsizes(cursor: str, sizes: Any) -> Any:
    """Required by DB-API. Does nothing in sqlite3."""
    _instance = _get_object(cursor)
    return _instance.setinputsizes(sizes=sizes)

@mcp.tool(name="cursor_setoutputsize")
def cursor_setoutputsize(cursor: str, size: Any, column: Any = None) -> Any:
    """Required by DB-API. Does nothing in sqlite3."""
    _instance = _get_object(cursor)
    return _instance.setoutputsize(size=size, column=column)

@mcp.tool(name="dataerror_add_note")
def dataerror_add_note(dataerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(dataerror)
    return _instance.add_note()

@mcp.tool(name="dataerror_with_traceback")
def dataerror_with_traceback(dataerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(dataerror)
    return _instance.with_traceback()

@mcp.tool(name="databaseerror_add_note")
def databaseerror_add_note(databaseerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(databaseerror)
    return _instance.add_note()

@mcp.tool(name="databaseerror_with_traceback")
def databaseerror_with_traceback(databaseerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(databaseerror)
    return _instance.with_traceback()

@mcp.tool(name="date_ctime")
def date_ctime(date: str) -> Any:
    """Return ctime() style string."""
    _instance = _get_object(date)
    return _instance.ctime()

@mcp.tool(name="date_fromisocalendar")
def date_fromisocalendar(date: str) -> Any:
    """int, int, int -> Construct a date from the ISO year, week number and weekday."""
    _instance = _get_object(date)
    return _instance.fromisocalendar()

@mcp.tool(name="date_fromisoformat")
def date_fromisoformat(date: str) -> Any:
    """str -> Construct a date from a string in ISO 8601 format."""
    _instance = _get_object(date)
    return _instance.fromisoformat()

@mcp.tool(name="date_fromordinal")
def date_fromordinal(date: str) -> Any:
    """int -> date corresponding to a proleptic Gregorian ordinal."""
    _instance = _get_object(date)
    return _instance.fromordinal()

@mcp.tool(name="date_fromtimestamp")
def date_fromtimestamp(date: str, timestamp: Any) -> Any:
    """Create a date from a POSIX timestamp."""
    _instance = _get_object(date)
    return _instance.fromtimestamp(timestamp=timestamp)

@mcp.tool(name="date_isocalendar")
def date_isocalendar(date: str) -> Any:
    """Return a named tuple containing ISO year, week number, and weekday."""
    _instance = _get_object(date)
    return _instance.isocalendar()

@mcp.tool(name="date_isoformat")
def date_isoformat(date: str) -> Any:
    """Return string in ISO 8601 format, YYYY-MM-DD."""
    _instance = _get_object(date)
    return _instance.isoformat()

@mcp.tool(name="date_isoweekday")
def date_isoweekday(date: str) -> Any:
    """Return the day of the week represented by the date."""
    _instance = _get_object(date)
    return _instance.isoweekday()

@mcp.tool(name="date_replace")
def date_replace(date: str) -> Any:
    """Return date with new specified fields."""
    _instance = _get_object(date)
    return _instance.replace()

@mcp.tool(name="date_strftime")
def date_strftime(date: str) -> Any:
    """format -> strftime() style string."""
    _instance = _get_object(date)
    return _instance.strftime()

@mcp.tool(name="date_timetuple")
def date_timetuple(date: str) -> Any:
    """Return time tuple, compatible with time.localtime()."""
    _instance = _get_object(date)
    return _instance.timetuple()

@mcp.tool(name="date_today")
def date_today(date: str) -> Any:
    """Current date or datetime:  same as self.__class__.fromtimestamp(time.time())."""
    _instance = _get_object(date)
    return _instance.today()

@mcp.tool(name="date_toordinal")
def date_toordinal(date: str) -> Any:
    """Return proleptic Gregorian ordinal.  January 1 of year 1 is day 1."""
    _instance = _get_object(date)
    return _instance.toordinal()

@mcp.tool(name="date_weekday")
def date_weekday(date: str) -> Any:
    """Return the day of the week represented by the date."""
    _instance = _get_object(date)
    return _instance.weekday()

@mcp.tool(name="error_add_note")
def error_add_note(error: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(error)
    return _instance.add_note()

@mcp.tool(name="error_with_traceback")
def error_with_traceback(error: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(error)
    return _instance.with_traceback()

@mcp.tool(name="integrityerror_add_note")
def integrityerror_add_note(integrityerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(integrityerror)
    return _instance.add_note()

@mcp.tool(name="integrityerror_with_traceback")
def integrityerror_with_traceback(integrityerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(integrityerror)
    return _instance.with_traceback()

@mcp.tool(name="interfaceerror_add_note")
def interfaceerror_add_note(interfaceerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(interfaceerror)
    return _instance.add_note()

@mcp.tool(name="interfaceerror_with_traceback")
def interfaceerror_with_traceback(interfaceerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(interfaceerror)
    return _instance.with_traceback()

@mcp.tool(name="internalerror_add_note")
def internalerror_add_note(internalerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(internalerror)
    return _instance.add_note()

@mcp.tool(name="internalerror_with_traceback")
def internalerror_with_traceback(internalerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(internalerror)
    return _instance.with_traceback()

@mcp.tool(name="notsupportederror_add_note")
def notsupportederror_add_note(notsupportederror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(notsupportederror)
    return _instance.add_note()

@mcp.tool(name="notsupportederror_with_traceback")
def notsupportederror_with_traceback(notsupportederror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(notsupportederror)
    return _instance.with_traceback()

@mcp.tool(name="operationalerror_add_note")
def operationalerror_add_note(operationalerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(operationalerror)
    return _instance.add_note()

@mcp.tool(name="operationalerror_with_traceback")
def operationalerror_with_traceback(operationalerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(operationalerror)
    return _instance.with_traceback()

@mcp.tool(name="programmingerror_add_note")
def programmingerror_add_note(programmingerror: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(programmingerror)
    return _instance.add_note()

@mcp.tool(name="programmingerror_with_traceback")
def programmingerror_with_traceback(programmingerror: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(programmingerror)
    return _instance.with_traceback()

@mcp.tool(name="row_keys")
def row_keys(row: str) -> Any:
    """Returns the keys of the row."""
    _instance = _get_object(row)
    return _instance.keys()

@mcp.tool(name="time_dst")
def time_dst(time: str) -> Any:
    """Return self.tzinfo.dst(self)."""
    _instance = _get_object(time)
    return _instance.dst()

@mcp.tool(name="time_fromisoformat")
def time_fromisoformat(time: str) -> Any:
    """string -> time from a string in ISO 8601 format"""
    _instance = _get_object(time)
    return _instance.fromisoformat()

@mcp.tool(name="time_isoformat")
def time_isoformat(time: str) -> Any:
    """Return string in ISO 8601 format, [HH[:MM[:SS[.mmm[uuu]]]]][+HH:MM]."""
    _instance = _get_object(time)
    return _instance.isoformat()

@mcp.tool(name="time_replace")
def time_replace(time: str) -> Any:
    """Return time with new specified fields."""
    _instance = _get_object(time)
    return _instance.replace()

@mcp.tool(name="time_strftime")
def time_strftime(time: str) -> Any:
    """format -> strftime() style string."""
    _instance = _get_object(time)
    return _instance.strftime()

@mcp.tool(name="time_tzname")
def time_tzname(time: str) -> Any:
    """Return self.tzinfo.tzname(self)."""
    _instance = _get_object(time)
    return _instance.tzname()

@mcp.tool(name="time_utcoffset")
def time_utcoffset(time: str) -> Any:
    """Return self.tzinfo.utcoffset(self)."""
    _instance = _get_object(time)
    return _instance.utcoffset()

@mcp.tool(name="datetime_astimezone")
def datetime_astimezone(datetime: str) -> Any:
    """tz -> convert to local time in new timezone tz"""
    _instance = _get_object(datetime)
    return _instance.astimezone()

@mcp.tool(name="datetime_combine")
def datetime_combine(datetime: str) -> Any:
    """date, time -> datetime with same date and time fields"""
    _instance = _get_object(datetime)
    return _instance.combine()

@mcp.tool(name="datetime_ctime")
def datetime_ctime(datetime: str) -> Any:
    """Return ctime() style string."""
    _instance = _get_object(datetime)
    return _instance.ctime()

@mcp.tool(name="datetime_date")
def datetime_date(datetime: str) -> Any:
    """Return date object with same year, month and day."""
    _instance = _get_object(datetime)
    return _instance.date()

@mcp.tool(name="datetime_dst")
def datetime_dst(datetime: str) -> Any:
    """Return self.tzinfo.dst(self)."""
    _instance = _get_object(datetime)
    return _instance.dst()

@mcp.tool(name="datetime_fromisocalendar")
def datetime_fromisocalendar(datetime: str) -> Any:
    """int, int, int -> Construct a date from the ISO year, week number and weekday."""
    _instance = _get_object(datetime)
    return _instance.fromisocalendar()

@mcp.tool(name="datetime_fromisoformat")
def datetime_fromisoformat(datetime: str) -> Any:
    """string -> datetime from a string in most ISO 8601 formats"""
    _instance = _get_object(datetime)
    return _instance.fromisoformat()

@mcp.tool(name="datetime_fromordinal")
def datetime_fromordinal(datetime: str) -> Any:
    """int -> date corresponding to a proleptic Gregorian ordinal."""
    _instance = _get_object(datetime)
    return _instance.fromordinal()

@mcp.tool(name="datetime_fromtimestamp")
def datetime_fromtimestamp(datetime: str) -> Any:
    """timestamp[, tz] -> tz's local time from POSIX timestamp."""
    _instance = _get_object(datetime)
    return _instance.fromtimestamp()

@mcp.tool(name="datetime_isocalendar")
def datetime_isocalendar(datetime: str) -> Any:
    """Return a named tuple containing ISO year, week number, and weekday."""
    _instance = _get_object(datetime)
    return _instance.isocalendar()

@mcp.tool(name="datetime_isoformat")
def datetime_isoformat(datetime: str) -> Any:
    """[sep] -> string in ISO 8601 format, YYYY-MM-DDT[HH[:MM[:SS[.mmm[uuu]]]]][+HH:MM]."""
    _instance = _get_object(datetime)
    return _instance.isoformat()

@mcp.tool(name="datetime_isoweekday")
def datetime_isoweekday(datetime: str) -> Any:
    """Return the day of the week represented by the date."""
    _instance = _get_object(datetime)
    return _instance.isoweekday()

@mcp.tool(name="datetime_now")
def datetime_now(datetime: str, tz: Any = None) -> Any:
    """Returns new datetime object representing current time local to tz."""
    _instance = _get_object(datetime)
    return _instance.now(tz=tz)

@mcp.tool(name="datetime_replace")
def datetime_replace(datetime: str) -> Any:
    """Return datetime with new specified fields."""
    _instance = _get_object(datetime)
    return _instance.replace()

@mcp.tool(name="datetime_strftime")
def datetime_strftime(datetime: str) -> Any:
    """format -> strftime() style string."""
    _instance = _get_object(datetime)
    return _instance.strftime()

@mcp.tool(name="datetime_strptime")
def datetime_strptime(datetime: str) -> Any:
    """string, format -> new datetime parsed from a string (like time.strptime())."""
    _instance = _get_object(datetime)
    return _instance.strptime()

@mcp.tool(name="datetime_time")
def datetime_time(datetime: str) -> Any:
    """Return time object with same time but with tzinfo=None."""
    _instance = _get_object(datetime)
    return _instance.time()

@mcp.tool(name="datetime_timestamp")
def datetime_timestamp(datetime: str) -> Any:
    """Return POSIX timestamp as float."""
    _instance = _get_object(datetime)
    return _instance.timestamp()

@mcp.tool(name="datetime_timetuple")
def datetime_timetuple(datetime: str) -> Any:
    """Return time tuple, compatible with time.localtime()."""
    _instance = _get_object(datetime)
    return _instance.timetuple()

@mcp.tool(name="datetime_timetz")
def datetime_timetz(datetime: str) -> Any:
    """Return time object with same time and tzinfo."""
    _instance = _get_object(datetime)
    return _instance.timetz()

@mcp.tool(name="datetime_today")
def datetime_today(datetime: str) -> Any:
    """Current date or datetime:  same as self.__class__.fromtimestamp(time.time())."""
    _instance = _get_object(datetime)
    return _instance.today()

@mcp.tool(name="datetime_toordinal")
def datetime_toordinal(datetime: str) -> Any:
    """Return proleptic Gregorian ordinal.  January 1 of year 1 is day 1."""
    _instance = _get_object(datetime)
    return _instance.toordinal()

@mcp.tool(name="datetime_tzname")
def datetime_tzname(datetime: str) -> Any:
    """Return self.tzinfo.tzname(self)."""
    _instance = _get_object(datetime)
    return _instance.tzname()

@mcp.tool(name="datetime_utcfromtimestamp")
def datetime_utcfromtimestamp(datetime: str) -> Any:
    """Construct a naive UTC datetime from a POSIX timestamp."""
    _instance = _get_object(datetime)
    return _instance.utcfromtimestamp()

@mcp.tool(name="datetime_utcnow")
def datetime_utcnow(datetime: str) -> Any:
    """Return a new datetime representing UTC day and time."""
    _instance = _get_object(datetime)
    return _instance.utcnow()

@mcp.tool(name="datetime_utcoffset")
def datetime_utcoffset(datetime: str) -> Any:
    """Return self.tzinfo.utcoffset(self)."""
    _instance = _get_object(datetime)
    return _instance.utcoffset()

@mcp.tool(name="datetime_utctimetuple")
def datetime_utctimetuple(datetime: str) -> Any:
    """Return UTC time tuple, compatible with time.localtime()."""
    _instance = _get_object(datetime)
    return _instance.utctimetuple()

@mcp.tool(name="datetime_weekday")
def datetime_weekday(datetime: str) -> Any:
    """Return the day of the week represented by the date."""
    _instance = _get_object(datetime)
    return _instance.weekday()

@mcp.tool(name="warning_add_note")
def warning_add_note(warning: str) -> Any:
    """Exception.add_note(note) --"""
    _instance = _get_object(warning)
    return _instance.add_note()

@mcp.tool(name="warning_with_traceback")
def warning_with_traceback(warning: str) -> Any:
    """Exception.with_traceback(tb) --"""
    _instance = _get_object(warning)
    return _instance.with_traceback()


if __name__ == "__main__":
    mcp.run()