"""Auto-generated MCP server with wrapper support.

Module: pandas
Server: pandas-mcp-server
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

import pandas

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


mcp = FastMCP(name="pandas-mcp-server")

@mcp.tool(name="array")
def array() -> Any:
    """Create an array."""
    return pandas.array()

@mcp.tool(name="bdate_range")
def bdate_range() -> Any:
    """Return a fixed frequency DatetimeIndex with business day as the default."""
    return pandas.bdate_range()

@mcp.tool(name="concat")
def concat() -> Any:
    """Concatenate pandas objects along a particular axis."""
    return pandas.concat()

@mcp.tool(name="crosstab")
def crosstab() -> Any:
    """Compute a simple cross tabulation of two (or more) factors."""
    return pandas.crosstab()

@mcp.tool(name="cut")
def cut() -> Any:
    """Bin values into discrete intervals."""
    return pandas.cut()

@mcp.tool(name="date_range")
def date_range() -> Any:
    """Return a fixed frequency DatetimeIndex."""
    return pandas.date_range()

@mcp.tool(name="describe_option")
def describe_option(pat: Any, _print_desc: Any = False) -> Any:
    """describe_option(pat, _print_desc=False)"""
    return pandas.describe_option(pat=pat, _print_desc=_print_desc)

@mcp.tool(name="eval")
def eval() -> Any:
    """Evaluate a Python expression as a string using various backends."""
    return pandas.eval()

@mcp.tool(name="factorize")
def factorize() -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    return pandas.factorize()

@mcp.tool(name="from_dummies")
def from_dummies() -> Any:
    """Create a categorical ``DataFrame`` from a ``DataFrame`` of dummy variables."""
    return pandas.from_dummies()

@mcp.tool(name="get_dummies")
def get_dummies() -> Any:
    """Convert categorical variable into dummy/indicator variables."""
    return pandas.get_dummies()

@mcp.tool(name="get_option")
def get_option(pat: Any) -> Any:
    """get_option(pat)"""
    return pandas.get_option(pat=pat)

@mcp.tool(name="infer_freq")
def infer_freq() -> Any:
    """Infer the most likely frequency given the input index."""
    return pandas.infer_freq()

@mcp.tool(name="interval_range")
def interval_range() -> Any:
    """Return a fixed frequency IntervalIndex."""
    return pandas.interval_range()

@mcp.tool(name="isna")
def isna() -> Any:
    """Detect missing values for an array-like object."""
    return pandas.isna()

@mcp.tool(name="isnull")
def isnull() -> Any:
    """Detect missing values for an array-like object."""
    return pandas.isnull()

@mcp.tool(name="json_normalize")
def json_normalize() -> Any:
    """Normalize semi-structured JSON data into a flat table."""
    return pandas.json_normalize()

@mcp.tool(name="lreshape")
def lreshape() -> Any:
    """Reshape wide-format data to long. Generalized inverse of DataFrame.pivot."""
    return pandas.lreshape()

@mcp.tool(name="melt")
def melt() -> Any:
    """Unpivot a DataFrame from wide to long format, optionally leaving identifiers set."""
    return pandas.melt()

@mcp.tool(name="merge")
def merge() -> Any:
    """Merge DataFrame or named Series objects with a database-style join."""
    return pandas.merge()

@mcp.tool(name="merge_asof")
def merge_asof() -> Any:
    """Perform a merge by key distance."""
    return pandas.merge_asof()

@mcp.tool(name="merge_ordered")
def merge_ordered() -> Any:
    """Perform a merge for ordered data with optional filling/interpolation."""
    return pandas.merge_ordered()

@mcp.tool(name="notna")
def notna() -> Any:
    """Detect non-missing values for an array-like object."""
    return pandas.notna()

@mcp.tool(name="notnull")
def notnull() -> Any:
    """Detect non-missing values for an array-like object."""
    return pandas.notnull()

@mcp.tool(name="period_range")
def period_range() -> Any:
    """Return a fixed frequency PeriodIndex."""
    return pandas.period_range()

@mcp.tool(name="pivot")
def pivot() -> Any:
    """Return reshaped DataFrame organized by given index / column values."""
    return pandas.pivot()

@mcp.tool(name="pivot_table")
def pivot_table() -> Any:
    """Create a spreadsheet-style pivot table as a DataFrame."""
    return pandas.pivot_table()

@mcp.tool(name="qcut")
def qcut() -> Any:
    """Quantile-based discretization function."""
    return pandas.qcut()

@mcp.tool(name="read_clipboard")
def read_clipboard() -> Any:
    """Read text from clipboard and pass to :func:`~pandas.read_csv`."""
    return pandas.read_clipboard()

@mcp.tool(name="read_csv")
def read_csv() -> Any:
    """Read a comma-separated values (csv) file into DataFrame."""
    return pandas.read_csv()

@mcp.tool(name="read_excel")
def read_excel() -> Any:
    """Read an Excel file into a ``pandas`` ``DataFrame``."""
    return pandas.read_excel()

@mcp.tool(name="read_feather")
def read_feather() -> Any:
    """Load a feather-format object from the file path."""
    return pandas.read_feather()

@mcp.tool(name="read_fwf")
def read_fwf() -> Any:
    """Read a table of fixed-width formatted lines into DataFrame."""
    return pandas.read_fwf()

@mcp.tool(name="read_gbq")
def read_gbq() -> Any:
    """Load data from Google BigQuery."""
    return pandas.read_gbq()

@mcp.tool(name="read_hdf")
def read_hdf() -> Any:
    """Read from the store, close it if we opened it."""
    return pandas.read_hdf()

@mcp.tool(name="read_html")
def read_html() -> Any:
    """Read HTML tables into a ``list`` of ``DataFrame`` objects."""
    return pandas.read_html()

@mcp.tool(name="read_json")
def read_json() -> Any:
    """Convert a JSON string to pandas object."""
    return pandas.read_json()

@mcp.tool(name="read_orc")
def read_orc() -> Any:
    """Load an ORC object from the file path, returning a DataFrame."""
    return pandas.read_orc()

@mcp.tool(name="read_parquet")
def read_parquet() -> Any:
    """Load a parquet object from the file path, returning a DataFrame."""
    return pandas.read_parquet()

@mcp.tool(name="read_pickle")
def read_pickle() -> Any:
    """Load pickled pandas object (or any object) from file."""
    return pandas.read_pickle()

@mcp.tool(name="read_sas")
def read_sas() -> Any:
    """Read SAS files stored as either XPORT or SAS7BDAT format files."""
    return pandas.read_sas()

@mcp.tool(name="read_spss")
def read_spss() -> Any:
    """Load an SPSS file from the file path, returning a DataFrame."""
    return pandas.read_spss()

@mcp.tool(name="read_sql")
def read_sql() -> Any:
    """Read SQL query or database table into a DataFrame."""
    return pandas.read_sql()

@mcp.tool(name="read_sql_query")
def read_sql_query() -> Any:
    """Read SQL query into a DataFrame."""
    return pandas.read_sql_query()

@mcp.tool(name="read_sql_table")
def read_sql_table() -> Any:
    """Read SQL database table into a DataFrame."""
    return pandas.read_sql_table()

@mcp.tool(name="read_stata")
def read_stata() -> Any:
    """Read Stata file into DataFrame."""
    return pandas.read_stata()

@mcp.tool(name="read_table")
def read_table() -> Any:
    """Read general delimited file into DataFrame."""
    return pandas.read_table()

@mcp.tool(name="read_xml")
def read_xml() -> Any:
    """Read XML document into a :class:`~pandas.DataFrame` object."""
    return pandas.read_xml()

@mcp.tool(name="reset_option")
def reset_option(pat: Any) -> Any:
    """reset_option(pat)"""
    return pandas.reset_option(pat=pat)

@mcp.tool(name="set_eng_float_format")
def set_eng_float_format() -> Any:
    """Format float representation in DataFrame with SI notation."""
    return pandas.set_eng_float_format()

@mcp.tool(name="set_option")
def set_option(pat: Any, value: Any) -> Any:
    """set_option(pat, value)"""
    return pandas.set_option(pat=pat, value=value)

@mcp.tool(name="show_versions")
def show_versions() -> Any:
    """Provide useful information, important for bug reports."""
    return pandas.show_versions()

@mcp.tool(name="test")
def test() -> Any:
    """Run the pandas test suite using pytest."""
    return pandas.test()

@mcp.tool(name="timedelta_range")
def timedelta_range() -> Any:
    """Return a fixed frequency TimedeltaIndex with day as the default."""
    return pandas.timedelta_range()

@mcp.tool(name="to_datetime")
def to_datetime() -> Any:
    """Convert argument to datetime."""
    return pandas.to_datetime()

@mcp.tool(name="to_numeric")
def to_numeric() -> Any:
    """Convert argument to a numeric type."""
    return pandas.to_numeric()

@mcp.tool(name="to_pickle")
def to_pickle() -> Any:
    """Pickle (serialize) object to file."""
    return pandas.to_pickle()

@mcp.tool(name="to_timedelta")
def to_timedelta() -> Any:
    """Convert argument to timedelta."""
    return pandas.to_timedelta()

@mcp.tool(name="unique")
def unique() -> Any:
    """Return unique values based on a hash table."""
    return pandas.unique()

@mcp.tool(name="value_counts")
def value_counts() -> Any:
    """Compute a histogram of the counts of non-null values."""
    return pandas.value_counts()

@mcp.tool(name="wide_to_long")
def wide_to_long() -> Any:
    """Unpivot a DataFrame from wide to long format."""
    return pandas.wide_to_long()

@mcp.tool(name="arrowdtype_construct_array_type")
def arrowdtype_construct_array_type(arrowdtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(arrowdtype)
    return _instance.construct_array_type()

@mcp.tool(name="arrowdtype_construct_from_string")
def arrowdtype_construct_from_string(arrowdtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(arrowdtype)
    return _instance.construct_from_string()

@mcp.tool(name="arrowdtype_empty")
def arrowdtype_empty(arrowdtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(arrowdtype)
    return _instance.empty()

@mcp.tool(name="arrowdtype_is_dtype")
def arrowdtype_is_dtype(arrowdtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(arrowdtype)
    return _instance.is_dtype()

@mcp.tool(name="booleandtype_construct_array_type")
def booleandtype_construct_array_type(booleandtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(booleandtype)
    return _instance.construct_array_type()

@mcp.tool(name="booleandtype_construct_from_string")
def booleandtype_construct_from_string(booleandtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(booleandtype)
    return _instance.construct_from_string()

@mcp.tool(name="booleandtype_empty")
def booleandtype_empty(booleandtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(booleandtype)
    return _instance.empty()

@mcp.tool(name="booleandtype_from_numpy_dtype")
def booleandtype_from_numpy_dtype(booleandtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(booleandtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="booleandtype_is_dtype")
def booleandtype_is_dtype(booleandtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(booleandtype)
    return _instance.is_dtype()

@mcp.tool(name="categorical_add_categories")
def categorical_add_categories(categorical: str) -> Any:
    """Add new categories."""
    _instance = _get_object(categorical)
    return _instance.add_categories()

@mcp.tool(name="categorical_argmax")
def categorical_argmax(categorical: str) -> Any:
    """Return the index of maximum value."""
    _instance = _get_object(categorical)
    return _instance.argmax()

@mcp.tool(name="categorical_argmin")
def categorical_argmin(categorical: str) -> Any:
    """Return the index of minimum value."""
    _instance = _get_object(categorical)
    return _instance.argmin()

@mcp.tool(name="categorical_argsort")
def categorical_argsort(categorical: str) -> Any:
    """Return the indices that would sort the Categorical."""
    _instance = _get_object(categorical)
    return _instance.argsort()

@mcp.tool(name="categorical_as_ordered")
def categorical_as_ordered(categorical: str) -> Any:
    """Set the Categorical to be ordered."""
    _instance = _get_object(categorical)
    return _instance.as_ordered()

@mcp.tool(name="categorical_as_unordered")
def categorical_as_unordered(categorical: str) -> Any:
    """Set the Categorical to be unordered."""
    _instance = _get_object(categorical)
    return _instance.as_unordered()

@mcp.tool(name="categorical_astype")
def categorical_astype(categorical: str) -> Any:
    """Coerce this type to another dtype"""
    _instance = _get_object(categorical)
    return _instance.astype()

@mcp.tool(name="categorical_check_for_ordered")
def categorical_check_for_ordered(categorical: str) -> Any:
    """assert that we are ordered"""
    _instance = _get_object(categorical)
    return _instance.check_for_ordered()

@mcp.tool(name="categorical_copy")
def categorical_copy(categorical: str) -> Any:
    """Tool: categorical_copy"""
    _instance = _get_object(categorical)
    return _instance.copy()

@mcp.tool(name="categorical_delete")
def categorical_delete(categorical: str) -> Any:
    """Tool: categorical_delete"""
    _instance = _get_object(categorical)
    return _instance.delete()

@mcp.tool(name="categorical_describe")
def categorical_describe(categorical: str) -> Any:
    """Describes this Categorical"""
    _instance = _get_object(categorical)
    return _instance.describe()

@mcp.tool(name="categorical_dropna")
def categorical_dropna(categorical: str) -> Any:
    """Return ExtensionArray without NA values."""
    _instance = _get_object(categorical)
    return _instance.dropna()

@mcp.tool(name="categorical_duplicated")
def categorical_duplicated(categorical: str) -> Any:
    """Return boolean ndarray denoting duplicate values."""
    _instance = _get_object(categorical)
    return _instance.duplicated()

@mcp.tool(name="categorical_equals")
def categorical_equals(categorical: str) -> Any:
    """Returns True if categorical arrays are equal."""
    _instance = _get_object(categorical)
    return _instance.equals()

@mcp.tool(name="categorical_factorize")
def categorical_factorize(categorical: str) -> Any:
    """Encode the extension array as an enumerated type."""
    _instance = _get_object(categorical)
    return _instance.factorize()

@mcp.tool(name="categorical_fillna")
def categorical_fillna(categorical: str) -> Any:
    """Fill NA/NaN values using the specified method."""
    _instance = _get_object(categorical)
    return _instance.fillna()

@mcp.tool(name="categorical_from_codes")
def categorical_from_codes(categorical: str) -> Any:
    """Make a Categorical type from codes and categories or dtype."""
    _instance = _get_object(categorical)
    return _instance.from_codes()

@mcp.tool(name="categorical_insert")
def categorical_insert(categorical: str) -> Any:
    """Make new ExtensionArray inserting new item at location. Follows"""
    _instance = _get_object(categorical)
    return _instance.insert()

@mcp.tool(name="categorical_interpolate")
def categorical_interpolate(categorical: str) -> Any:
    """See DataFrame.interpolate.__doc__."""
    _instance = _get_object(categorical)
    return _instance.interpolate()

@mcp.tool(name="categorical_isin")
def categorical_isin(categorical: str) -> Any:
    """Check whether `values` are contained in Categorical."""
    _instance = _get_object(categorical)
    return _instance.isin()

@mcp.tool(name="categorical_isna")
def categorical_isna(categorical: str) -> Any:
    """Detect missing values"""
    _instance = _get_object(categorical)
    return _instance.isna()

@mcp.tool(name="categorical_isnull")
def categorical_isnull(categorical: str) -> Any:
    """Detect missing values"""
    _instance = _get_object(categorical)
    return _instance.isnull()

@mcp.tool(name="categorical_map")
def categorical_map(categorical: str) -> Any:
    """Map categories using an input mapping or function."""
    _instance = _get_object(categorical)
    return _instance.map()

@mcp.tool(name="categorical_max")
def categorical_max(categorical: str) -> Any:
    """The maximum value of the object."""
    _instance = _get_object(categorical)
    return _instance.max()

@mcp.tool(name="categorical_memory_usage")
def categorical_memory_usage(categorical: str) -> Any:
    """Memory usage of my values"""
    _instance = _get_object(categorical)
    return _instance.memory_usage()

@mcp.tool(name="categorical_min")
def categorical_min(categorical: str) -> Any:
    """The minimum value of the object."""
    _instance = _get_object(categorical)
    return _instance.min()

@mcp.tool(name="categorical_notna")
def categorical_notna(categorical: str) -> Any:
    """Inverse of isna"""
    _instance = _get_object(categorical)
    return _instance.notna()

@mcp.tool(name="categorical_notnull")
def categorical_notnull(categorical: str) -> Any:
    """Inverse of isna"""
    _instance = _get_object(categorical)
    return _instance.notnull()

@mcp.tool(name="categorical_ravel")
def categorical_ravel(categorical: str) -> Any:
    """Tool: categorical_ravel"""
    _instance = _get_object(categorical)
    return _instance.ravel()

@mcp.tool(name="categorical_remove_categories")
def categorical_remove_categories(categorical: str) -> Any:
    """Remove the specified categories."""
    _instance = _get_object(categorical)
    return _instance.remove_categories()

@mcp.tool(name="categorical_remove_unused_categories")
def categorical_remove_unused_categories(categorical: str) -> Any:
    """Remove categories which are not used."""
    _instance = _get_object(categorical)
    return _instance.remove_unused_categories()

@mcp.tool(name="categorical_rename_categories")
def categorical_rename_categories(categorical: str) -> Any:
    """Rename categories."""
    _instance = _get_object(categorical)
    return _instance.rename_categories()

@mcp.tool(name="categorical_reorder_categories")
def categorical_reorder_categories(categorical: str) -> Any:
    """Reorder categories as specified in new_categories."""
    _instance = _get_object(categorical)
    return _instance.reorder_categories()

@mcp.tool(name="categorical_repeat")
def categorical_repeat(categorical: str) -> Any:
    """Tool: categorical_repeat"""
    _instance = _get_object(categorical)
    return _instance.repeat()

@mcp.tool(name="categorical_reshape")
def categorical_reshape(categorical: str) -> Any:
    """Tool: categorical_reshape"""
    _instance = _get_object(categorical)
    return _instance.reshape()

@mcp.tool(name="categorical_searchsorted")
def categorical_searchsorted(categorical: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(categorical)
    return _instance.searchsorted()

@mcp.tool(name="categorical_set_categories")
def categorical_set_categories(categorical: str) -> Any:
    """Set the categories to the specified new categories."""
    _instance = _get_object(categorical)
    return _instance.set_categories()

@mcp.tool(name="categorical_set_ordered")
def categorical_set_ordered(categorical: str) -> Any:
    """Set the ordered attribute to the boolean value."""
    _instance = _get_object(categorical)
    return _instance.set_ordered()

@mcp.tool(name="categorical_shift")
def categorical_shift(categorical: str) -> Any:
    """Shift values by desired number."""
    _instance = _get_object(categorical)
    return _instance.shift()

@mcp.tool(name="categorical_sort_values")
def categorical_sort_values(categorical: str) -> Any:
    """Sort the Categorical by category value returning a new"""
    _instance = _get_object(categorical)
    return _instance.sort_values()

@mcp.tool(name="categorical_swapaxes")
def categorical_swapaxes(categorical: str) -> Any:
    """Tool: categorical_swapaxes"""
    _instance = _get_object(categorical)
    return _instance.swapaxes()

@mcp.tool(name="categorical_take")
def categorical_take(categorical: str) -> Any:
    """Take elements from an array."""
    _instance = _get_object(categorical)
    return _instance.take()

@mcp.tool(name="categorical_to_list")
def categorical_to_list(categorical: str) -> Any:
    """Alias for tolist."""
    _instance = _get_object(categorical)
    return _instance.to_list()

@mcp.tool(name="categorical_to_numpy")
def categorical_to_numpy(categorical: str) -> Any:
    """Convert to a NumPy ndarray."""
    _instance = _get_object(categorical)
    return _instance.to_numpy()

@mcp.tool(name="categorical_tolist")
def categorical_tolist(categorical: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(categorical)
    return _instance.tolist()

@mcp.tool(name="categorical_transpose")
def categorical_transpose(categorical: str) -> Any:
    """Tool: categorical_transpose"""
    _instance = _get_object(categorical)
    return _instance.transpose()

@mcp.tool(name="categorical_unique")
def categorical_unique(categorical: str) -> Any:
    """Return the ``Categorical`` which ``categories`` and ``codes`` are"""
    _instance = _get_object(categorical)
    return _instance.unique()

@mcp.tool(name="categorical_value_counts")
def categorical_value_counts(categorical: str) -> Any:
    """Return a Series containing counts of each category."""
    _instance = _get_object(categorical)
    return _instance.value_counts()

@mcp.tool(name="categorical_view")
def categorical_view(categorical: str) -> Any:
    """Return a view on the array."""
    _instance = _get_object(categorical)
    return _instance.view()

@mcp.tool(name="categoricaldtype_construct_array_type")
def categoricaldtype_construct_array_type(categoricaldtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(categoricaldtype)
    return _instance.construct_array_type()

@mcp.tool(name="categoricaldtype_construct_from_string")
def categoricaldtype_construct_from_string(categoricaldtype: str) -> Any:
    """Construct a CategoricalDtype from a string."""
    _instance = _get_object(categoricaldtype)
    return _instance.construct_from_string()

@mcp.tool(name="categoricaldtype_empty")
def categoricaldtype_empty(categoricaldtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(categoricaldtype)
    return _instance.empty()

@mcp.tool(name="categoricaldtype_is_dtype")
def categoricaldtype_is_dtype(categoricaldtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(categoricaldtype)
    return _instance.is_dtype()

@mcp.tool(name="categoricaldtype_reset_cache")
def categoricaldtype_reset_cache(categoricaldtype: str) -> Any:
    """clear the cache"""
    _instance = _get_object(categoricaldtype)
    return _instance.reset_cache()

@mcp.tool(name="categoricaldtype_update_dtype")
def categoricaldtype_update_dtype(categoricaldtype: str) -> Any:
    """Returns a CategoricalDtype with categories and ordered taken from dtype"""
    _instance = _get_object(categoricaldtype)
    return _instance.update_dtype()

@mcp.tool(name="categoricaldtype_validate_categories")
def categoricaldtype_validate_categories(categoricaldtype: str) -> Any:
    """Validates that we have good categories"""
    _instance = _get_object(categoricaldtype)
    return _instance.validate_categories()

@mcp.tool(name="categoricaldtype_validate_ordered")
def categoricaldtype_validate_ordered(categoricaldtype: str) -> Any:
    """Validates that we have a valid ordered parameter. If"""
    _instance = _get_object(categoricaldtype)
    return _instance.validate_ordered()

@mcp.tool(name="categoricalindex_add_categories")
def categoricalindex_add_categories(categoricalindex: str) -> Any:
    """Add new categories."""
    _instance = _get_object(categoricalindex)
    return _instance.add_categories()

@mcp.tool(name="categoricalindex_all")
def categoricalindex_all(categoricalindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(categoricalindex)
    return _instance.all()

@mcp.tool(name="categoricalindex_any")
def categoricalindex_any(categoricalindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(categoricalindex)
    return _instance.any()

@mcp.tool(name="categoricalindex_append")
def categoricalindex_append(categoricalindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(categoricalindex)
    return _instance.append()

@mcp.tool(name="categoricalindex_argmax")
def categoricalindex_argmax(categoricalindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(categoricalindex)
    return _instance.argmax()

@mcp.tool(name="categoricalindex_argmin")
def categoricalindex_argmin(categoricalindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(categoricalindex)
    return _instance.argmin()

@mcp.tool(name="categoricalindex_argsort")
def categoricalindex_argsort(categoricalindex: str) -> Any:
    """Return the indices that would sort the Categorical."""
    _instance = _get_object(categoricalindex)
    return _instance.argsort()

@mcp.tool(name="categoricalindex_as_ordered")
def categoricalindex_as_ordered(categoricalindex: str) -> Any:
    """Set the Categorical to be ordered."""
    _instance = _get_object(categoricalindex)
    return _instance.as_ordered()

@mcp.tool(name="categoricalindex_as_unordered")
def categoricalindex_as_unordered(categoricalindex: str) -> Any:
    """Set the Categorical to be unordered."""
    _instance = _get_object(categoricalindex)
    return _instance.as_unordered()

@mcp.tool(name="categoricalindex_asof")
def categoricalindex_asof(categoricalindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(categoricalindex)
    return _instance.asof()

@mcp.tool(name="categoricalindex_asof_locs")
def categoricalindex_asof_locs(categoricalindex: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(categoricalindex)
    return _instance.asof_locs()

@mcp.tool(name="categoricalindex_astype")
def categoricalindex_astype(categoricalindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(categoricalindex)
    return _instance.astype()

@mcp.tool(name="categoricalindex_copy")
def categoricalindex_copy(categoricalindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(categoricalindex)
    return _instance.copy()

@mcp.tool(name="categoricalindex_delete")
def categoricalindex_delete(categoricalindex: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(categoricalindex)
    return _instance.delete()

@mcp.tool(name="categoricalindex_diff")
def categoricalindex_diff(categoricalindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(categoricalindex)
    return _instance.diff()

@mcp.tool(name="categoricalindex_difference")
def categoricalindex_difference(categoricalindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(categoricalindex)
    return _instance.difference()

@mcp.tool(name="categoricalindex_drop")
def categoricalindex_drop(categoricalindex: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(categoricalindex)
    return _instance.drop()

@mcp.tool(name="categoricalindex_drop_duplicates")
def categoricalindex_drop_duplicates(categoricalindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(categoricalindex)
    return _instance.drop_duplicates()

@mcp.tool(name="categoricalindex_droplevel")
def categoricalindex_droplevel(categoricalindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(categoricalindex)
    return _instance.droplevel()

@mcp.tool(name="categoricalindex_dropna")
def categoricalindex_dropna(categoricalindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(categoricalindex)
    return _instance.dropna()

@mcp.tool(name="categoricalindex_duplicated")
def categoricalindex_duplicated(categoricalindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(categoricalindex)
    return _instance.duplicated()

@mcp.tool(name="categoricalindex_equals")
def categoricalindex_equals(categoricalindex: str) -> Any:
    """Determine if two CategoricalIndex objects contain the same elements."""
    _instance = _get_object(categoricalindex)
    return _instance.equals()

@mcp.tool(name="categoricalindex_factorize")
def categoricalindex_factorize(categoricalindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(categoricalindex)
    return _instance.factorize()

@mcp.tool(name="categoricalindex_fillna")
def categoricalindex_fillna(categoricalindex: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(categoricalindex)
    return _instance.fillna()

@mcp.tool(name="categoricalindex_format")
def categoricalindex_format(categoricalindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(categoricalindex)
    return _instance.format()

@mcp.tool(name="categoricalindex_get_indexer")
def categoricalindex_get_indexer(categoricalindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(categoricalindex)
    return _instance.get_indexer()

@mcp.tool(name="categoricalindex_get_indexer_for")
def categoricalindex_get_indexer_for(categoricalindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(categoricalindex)
    return _instance.get_indexer_for()

@mcp.tool(name="categoricalindex_get_indexer_non_unique")
def categoricalindex_get_indexer_non_unique(categoricalindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(categoricalindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="categoricalindex_get_level_values")
def categoricalindex_get_level_values(categoricalindex: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(categoricalindex)
    return _instance.get_level_values()

@mcp.tool(name="categoricalindex_get_loc")
def categoricalindex_get_loc(categoricalindex: str) -> Any:
    """Get integer location, slice or boolean mask for requested label."""
    _instance = _get_object(categoricalindex)
    return _instance.get_loc()

@mcp.tool(name="categoricalindex_get_slice_bound")
def categoricalindex_get_slice_bound(categoricalindex: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(categoricalindex)
    return _instance.get_slice_bound()

@mcp.tool(name="categoricalindex_groupby")
def categoricalindex_groupby(categoricalindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(categoricalindex)
    return _instance.groupby()

@mcp.tool(name="categoricalindex_holds_integer")
def categoricalindex_holds_integer(categoricalindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(categoricalindex)
    return _instance.holds_integer()

@mcp.tool(name="categoricalindex_identical")
def categoricalindex_identical(categoricalindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(categoricalindex)
    return _instance.identical()

@mcp.tool(name="categoricalindex_infer_objects")
def categoricalindex_infer_objects(categoricalindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(categoricalindex)
    return _instance.infer_objects()

@mcp.tool(name="categoricalindex_insert")
def categoricalindex_insert(categoricalindex: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(categoricalindex)
    return _instance.insert()

@mcp.tool(name="categoricalindex_intersection")
def categoricalindex_intersection(categoricalindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(categoricalindex)
    return _instance.intersection()

@mcp.tool(name="categoricalindex_is_")
def categoricalindex_is_(categoricalindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(categoricalindex)
    return _instance.is_()

@mcp.tool(name="categoricalindex_is_boolean")
def categoricalindex_is_boolean(categoricalindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(categoricalindex)
    return _instance.is_boolean()

@mcp.tool(name="categoricalindex_is_categorical")
def categoricalindex_is_categorical(categoricalindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(categoricalindex)
    return _instance.is_categorical()

@mcp.tool(name="categoricalindex_is_floating")
def categoricalindex_is_floating(categoricalindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(categoricalindex)
    return _instance.is_floating()

@mcp.tool(name="categoricalindex_is_integer")
def categoricalindex_is_integer(categoricalindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(categoricalindex)
    return _instance.is_integer()

@mcp.tool(name="categoricalindex_is_interval")
def categoricalindex_is_interval(categoricalindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(categoricalindex)
    return _instance.is_interval()

@mcp.tool(name="categoricalindex_is_numeric")
def categoricalindex_is_numeric(categoricalindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(categoricalindex)
    return _instance.is_numeric()

@mcp.tool(name="categoricalindex_is_object")
def categoricalindex_is_object(categoricalindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(categoricalindex)
    return _instance.is_object()

@mcp.tool(name="categoricalindex_isin")
def categoricalindex_isin(categoricalindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(categoricalindex)
    return _instance.isin()

@mcp.tool(name="categoricalindex_isna")
def categoricalindex_isna(categoricalindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(categoricalindex)
    return _instance.isna()

@mcp.tool(name="categoricalindex_isnull")
def categoricalindex_isnull(categoricalindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(categoricalindex)
    return _instance.isnull()

@mcp.tool(name="categoricalindex_item")
def categoricalindex_item(categoricalindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(categoricalindex)
    return _instance.item()

@mcp.tool(name="categoricalindex_join")
def categoricalindex_join(categoricalindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(categoricalindex)
    return _instance.join()

@mcp.tool(name="categoricalindex_map")
def categoricalindex_map(categoricalindex: str) -> Any:
    """Map values using input an input mapping or function."""
    _instance = _get_object(categoricalindex)
    return _instance.map()

@mcp.tool(name="categoricalindex_max")
def categoricalindex_max(categoricalindex: str) -> Any:
    """The maximum value of the object."""
    _instance = _get_object(categoricalindex)
    return _instance.max()

@mcp.tool(name="categoricalindex_memory_usage")
def categoricalindex_memory_usage(categoricalindex: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(categoricalindex)
    return _instance.memory_usage()

@mcp.tool(name="categoricalindex_min")
def categoricalindex_min(categoricalindex: str) -> Any:
    """The minimum value of the object."""
    _instance = _get_object(categoricalindex)
    return _instance.min()

@mcp.tool(name="categoricalindex_notna")
def categoricalindex_notna(categoricalindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(categoricalindex)
    return _instance.notna()

@mcp.tool(name="categoricalindex_notnull")
def categoricalindex_notnull(categoricalindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(categoricalindex)
    return _instance.notnull()

@mcp.tool(name="categoricalindex_nunique")
def categoricalindex_nunique(categoricalindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(categoricalindex)
    return _instance.nunique()

@mcp.tool(name="categoricalindex_putmask")
def categoricalindex_putmask(categoricalindex: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(categoricalindex)
    return _instance.putmask()

@mcp.tool(name="categoricalindex_ravel")
def categoricalindex_ravel(categoricalindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(categoricalindex)
    return _instance.ravel()

@mcp.tool(name="categoricalindex_reindex")
def categoricalindex_reindex(categoricalindex: str) -> Any:
    """Create index with target's values (move/add/delete values as necessary)"""
    _instance = _get_object(categoricalindex)
    return _instance.reindex()

@mcp.tool(name="categoricalindex_remove_categories")
def categoricalindex_remove_categories(categoricalindex: str) -> Any:
    """Remove the specified categories."""
    _instance = _get_object(categoricalindex)
    return _instance.remove_categories()

@mcp.tool(name="categoricalindex_remove_unused_categories")
def categoricalindex_remove_unused_categories(categoricalindex: str) -> Any:
    """Remove categories which are not used."""
    _instance = _get_object(categoricalindex)
    return _instance.remove_unused_categories()

@mcp.tool(name="categoricalindex_rename")
def categoricalindex_rename(categoricalindex: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(categoricalindex)
    return _instance.rename()

@mcp.tool(name="categoricalindex_rename_categories")
def categoricalindex_rename_categories(categoricalindex: str) -> Any:
    """Rename categories."""
    _instance = _get_object(categoricalindex)
    return _instance.rename_categories()

@mcp.tool(name="categoricalindex_reorder_categories")
def categoricalindex_reorder_categories(categoricalindex: str) -> Any:
    """Reorder categories as specified in new_categories."""
    _instance = _get_object(categoricalindex)
    return _instance.reorder_categories()

@mcp.tool(name="categoricalindex_repeat")
def categoricalindex_repeat(categoricalindex: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(categoricalindex)
    return _instance.repeat()

@mcp.tool(name="categoricalindex_round")
def categoricalindex_round(categoricalindex: str) -> Any:
    """Round each value in the Index to the given number of decimals."""
    _instance = _get_object(categoricalindex)
    return _instance.round()

@mcp.tool(name="categoricalindex_searchsorted")
def categoricalindex_searchsorted(categoricalindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(categoricalindex)
    return _instance.searchsorted()

@mcp.tool(name="categoricalindex_set_categories")
def categoricalindex_set_categories(categoricalindex: str) -> Any:
    """Set the categories to the specified new categories."""
    _instance = _get_object(categoricalindex)
    return _instance.set_categories()

@mcp.tool(name="categoricalindex_set_names")
def categoricalindex_set_names(categoricalindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(categoricalindex)
    return _instance.set_names()

@mcp.tool(name="categoricalindex_shift")
def categoricalindex_shift(categoricalindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(categoricalindex)
    return _instance.shift()

@mcp.tool(name="categoricalindex_slice_indexer")
def categoricalindex_slice_indexer(categoricalindex: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(categoricalindex)
    return _instance.slice_indexer()

@mcp.tool(name="categoricalindex_slice_locs")
def categoricalindex_slice_locs(categoricalindex: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(categoricalindex)
    return _instance.slice_locs()

@mcp.tool(name="categoricalindex_sort")
def categoricalindex_sort(categoricalindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(categoricalindex)
    return _instance.sort()

@mcp.tool(name="categoricalindex_sort_values")
def categoricalindex_sort_values(categoricalindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(categoricalindex)
    return _instance.sort_values()

@mcp.tool(name="categoricalindex_sortlevel")
def categoricalindex_sortlevel(categoricalindex: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(categoricalindex)
    return _instance.sortlevel()

@mcp.tool(name="categoricalindex_symmetric_difference")
def categoricalindex_symmetric_difference(categoricalindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(categoricalindex)
    return _instance.symmetric_difference()

@mcp.tool(name="categoricalindex_take")
def categoricalindex_take(categoricalindex: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(categoricalindex)
    return _instance.take()

@mcp.tool(name="categoricalindex_to_flat_index")
def categoricalindex_to_flat_index(categoricalindex: str) -> Any:
    """Identity method."""
    _instance = _get_object(categoricalindex)
    return _instance.to_flat_index()

@mcp.tool(name="categoricalindex_to_frame")
def categoricalindex_to_frame(categoricalindex: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(categoricalindex)
    return _instance.to_frame()

@mcp.tool(name="categoricalindex_to_list")
def categoricalindex_to_list(categoricalindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(categoricalindex)
    return _instance.to_list()

@mcp.tool(name="categoricalindex_to_numpy")
def categoricalindex_to_numpy(categoricalindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(categoricalindex)
    return _instance.to_numpy()

@mcp.tool(name="categoricalindex_to_series")
def categoricalindex_to_series(categoricalindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(categoricalindex)
    return _instance.to_series()

@mcp.tool(name="categoricalindex_tolist")
def categoricalindex_tolist(categoricalindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(categoricalindex)
    return _instance.tolist()

@mcp.tool(name="categoricalindex_transpose")
def categoricalindex_transpose(categoricalindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(categoricalindex)
    return _instance.transpose()

@mcp.tool(name="categoricalindex_union")
def categoricalindex_union(categoricalindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(categoricalindex)
    return _instance.union()

@mcp.tool(name="categoricalindex_unique")
def categoricalindex_unique(categoricalindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(categoricalindex)
    return _instance.unique()

@mcp.tool(name="categoricalindex_value_counts")
def categoricalindex_value_counts(categoricalindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(categoricalindex)
    return _instance.value_counts()

@mcp.tool(name="categoricalindex_view")
def categoricalindex_view(categoricalindex: str) -> Any:
    """Tool: categoricalindex_view"""
    _instance = _get_object(categoricalindex)
    return _instance.view()

@mcp.tool(name="categoricalindex_where")
def categoricalindex_where(categoricalindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(categoricalindex)
    return _instance.where()

@mcp.tool(name="dataframe_abs")
def dataframe_abs(dataframe: str) -> Any:
    """Return a Series/DataFrame with absolute numeric value of each element."""
    _instance = _get_object(dataframe)
    return _instance.abs()

@mcp.tool(name="dataframe_add")
def dataframe_add(dataframe: str) -> Any:
    """Get Addition of dataframe and other, element-wise (binary operator `add`)."""
    _instance = _get_object(dataframe)
    return _instance.add()

@mcp.tool(name="dataframe_add_prefix")
def dataframe_add_prefix(dataframe: str) -> Any:
    """Prefix labels with string `prefix`."""
    _instance = _get_object(dataframe)
    return _instance.add_prefix()

@mcp.tool(name="dataframe_add_suffix")
def dataframe_add_suffix(dataframe: str) -> Any:
    """Suffix labels with string `suffix`."""
    _instance = _get_object(dataframe)
    return _instance.add_suffix()

@mcp.tool(name="dataframe_agg")
def dataframe_agg(dataframe: str) -> Any:
    """Aggregate using one or more operations over the specified axis."""
    _instance = _get_object(dataframe)
    return _instance.agg()

@mcp.tool(name="dataframe_aggregate")
def dataframe_aggregate(dataframe: str) -> Any:
    """Aggregate using one or more operations over the specified axis."""
    _instance = _get_object(dataframe)
    return _instance.aggregate()

@mcp.tool(name="dataframe_align")
def dataframe_align(dataframe: str) -> Any:
    """Align two objects on their axes with the specified join method."""
    _instance = _get_object(dataframe)
    return _instance.align()

@mcp.tool(name="dataframe_all")
def dataframe_all(dataframe: str) -> Any:
    """Return whether all elements are True, potentially over an axis."""
    _instance = _get_object(dataframe)
    return _instance.all()

@mcp.tool(name="dataframe_any")
def dataframe_any(dataframe: str) -> Any:
    """Return whether any element is True, potentially over an axis."""
    _instance = _get_object(dataframe)
    return _instance.any()

@mcp.tool(name="dataframe_apply")
def dataframe_apply(dataframe: str) -> Any:
    """Apply a function along an axis of the DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.apply()

@mcp.tool(name="dataframe_applymap")
def dataframe_applymap(dataframe: str) -> Any:
    """Apply a function to a Dataframe elementwise."""
    _instance = _get_object(dataframe)
    return _instance.applymap()

@mcp.tool(name="dataframe_asfreq")
def dataframe_asfreq(dataframe: str) -> Any:
    """Convert time series to specified frequency."""
    _instance = _get_object(dataframe)
    return _instance.asfreq()

@mcp.tool(name="dataframe_asof")
def dataframe_asof(dataframe: str) -> Any:
    """Return the last row(s) without any NaNs before `where`."""
    _instance = _get_object(dataframe)
    return _instance.asof()

@mcp.tool(name="dataframe_assign")
def dataframe_assign(dataframe: str) -> Any:
    """Assign new columns to a DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.assign()

@mcp.tool(name="dataframe_astype")
def dataframe_astype(dataframe: str) -> Any:
    """Cast a pandas object to a specified dtype ``dtype``."""
    _instance = _get_object(dataframe)
    return _instance.astype()

@mcp.tool(name="dataframe_at_time")
def dataframe_at_time(dataframe: str) -> Any:
    """Select values at particular time of day (e.g., 9:30AM)."""
    _instance = _get_object(dataframe)
    return _instance.at_time()

@mcp.tool(name="dataframe_backfill")
def dataframe_backfill(dataframe: str) -> Any:
    """Fill NA/NaN values by using the next valid observation to fill the gap."""
    _instance = _get_object(dataframe)
    return _instance.backfill()

@mcp.tool(name="dataframe_between_time")
def dataframe_between_time(dataframe: str) -> Any:
    """Select values between particular times of the day (e.g., 9:00-9:30 AM)."""
    _instance = _get_object(dataframe)
    return _instance.between_time()

@mcp.tool(name="dataframe_bfill")
def dataframe_bfill(dataframe: str) -> Any:
    """Fill NA/NaN values by using the next valid observation to fill the gap."""
    _instance = _get_object(dataframe)
    return _instance.bfill()

@mcp.tool(name="dataframe_bool")
def dataframe_bool(dataframe: str) -> Any:
    """Return the bool of a single element Series or DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.bool()

@mcp.tool(name="dataframe_boxplot")
def dataframe_boxplot(dataframe: str) -> Any:
    """Make a box plot from DataFrame columns."""
    _instance = _get_object(dataframe)
    return _instance.boxplot()

@mcp.tool(name="dataframe_clip")
def dataframe_clip(dataframe: str) -> Any:
    """Trim values at input threshold(s)."""
    _instance = _get_object(dataframe)
    return _instance.clip()

@mcp.tool(name="dataframe_combine")
def dataframe_combine(dataframe: str) -> Any:
    """Perform column-wise combine with another DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.combine()

@mcp.tool(name="dataframe_combine_first")
def dataframe_combine_first(dataframe: str) -> Any:
    """Update null elements with value in the same location in `other`."""
    _instance = _get_object(dataframe)
    return _instance.combine_first()

@mcp.tool(name="dataframe_compare")
def dataframe_compare(dataframe: str) -> Any:
    """Compare to another DataFrame and show the differences."""
    _instance = _get_object(dataframe)
    return _instance.compare()

@mcp.tool(name="dataframe_convert_dtypes")
def dataframe_convert_dtypes(dataframe: str) -> Any:
    """Convert columns to the best possible dtypes using dtypes supporting ``pd.NA``."""
    _instance = _get_object(dataframe)
    return _instance.convert_dtypes()

@mcp.tool(name="dataframe_copy")
def dataframe_copy(dataframe: str) -> Any:
    """Make a copy of this object's indices and data."""
    _instance = _get_object(dataframe)
    return _instance.copy()

@mcp.tool(name="dataframe_corr")
def dataframe_corr(dataframe: str) -> Any:
    """Compute pairwise correlation of columns, excluding NA/null values."""
    _instance = _get_object(dataframe)
    return _instance.corr()

@mcp.tool(name="dataframe_corrwith")
def dataframe_corrwith(dataframe: str) -> Any:
    """Compute pairwise correlation."""
    _instance = _get_object(dataframe)
    return _instance.corrwith()

@mcp.tool(name="dataframe_count")
def dataframe_count(dataframe: str) -> Any:
    """Count non-NA cells for each column or row."""
    _instance = _get_object(dataframe)
    return _instance.count()

@mcp.tool(name="dataframe_cov")
def dataframe_cov(dataframe: str) -> Any:
    """Compute pairwise covariance of columns, excluding NA/null values."""
    _instance = _get_object(dataframe)
    return _instance.cov()

@mcp.tool(name="dataframe_cummax")
def dataframe_cummax(dataframe: str) -> Any:
    """Return cumulative maximum over a DataFrame or Series axis."""
    _instance = _get_object(dataframe)
    return _instance.cummax()

@mcp.tool(name="dataframe_cummin")
def dataframe_cummin(dataframe: str) -> Any:
    """Return cumulative minimum over a DataFrame or Series axis."""
    _instance = _get_object(dataframe)
    return _instance.cummin()

@mcp.tool(name="dataframe_cumprod")
def dataframe_cumprod(dataframe: str) -> Any:
    """Return cumulative product over a DataFrame or Series axis."""
    _instance = _get_object(dataframe)
    return _instance.cumprod()

@mcp.tool(name="dataframe_cumsum")
def dataframe_cumsum(dataframe: str) -> Any:
    """Return cumulative sum over a DataFrame or Series axis."""
    _instance = _get_object(dataframe)
    return _instance.cumsum()

@mcp.tool(name="dataframe_describe")
def dataframe_describe(dataframe: str) -> Any:
    """Generate descriptive statistics."""
    _instance = _get_object(dataframe)
    return _instance.describe()

@mcp.tool(name="dataframe_diff")
def dataframe_diff(dataframe: str) -> Any:
    """First discrete difference of element."""
    _instance = _get_object(dataframe)
    return _instance.diff()

@mcp.tool(name="dataframe_div")
def dataframe_div(dataframe: str) -> Any:
    """Get Floating division of dataframe and other, element-wise (binary operator `truediv`)."""
    _instance = _get_object(dataframe)
    return _instance.div()

@mcp.tool(name="dataframe_divide")
def dataframe_divide(dataframe: str) -> Any:
    """Get Floating division of dataframe and other, element-wise (binary operator `truediv`)."""
    _instance = _get_object(dataframe)
    return _instance.divide()

@mcp.tool(name="dataframe_dot")
def dataframe_dot(dataframe: str) -> Any:
    """Compute the matrix multiplication between the DataFrame and other."""
    _instance = _get_object(dataframe)
    return _instance.dot()

@mcp.tool(name="dataframe_drop")
def dataframe_drop(dataframe: str) -> Any:
    """Drop specified labels from rows or columns."""
    _instance = _get_object(dataframe)
    return _instance.drop()

@mcp.tool(name="dataframe_drop_duplicates")
def dataframe_drop_duplicates(dataframe: str) -> Any:
    """Return DataFrame with duplicate rows removed."""
    _instance = _get_object(dataframe)
    return _instance.drop_duplicates()

@mcp.tool(name="dataframe_droplevel")
def dataframe_droplevel(dataframe: str) -> Any:
    """Return Series/DataFrame with requested index / column level(s) removed."""
    _instance = _get_object(dataframe)
    return _instance.droplevel()

@mcp.tool(name="dataframe_dropna")
def dataframe_dropna(dataframe: str) -> Any:
    """Remove missing values."""
    _instance = _get_object(dataframe)
    return _instance.dropna()

@mcp.tool(name="dataframe_duplicated")
def dataframe_duplicated(dataframe: str) -> Any:
    """Return boolean Series denoting duplicate rows."""
    _instance = _get_object(dataframe)
    return _instance.duplicated()

@mcp.tool(name="dataframe_eq")
def dataframe_eq(dataframe: str) -> Any:
    """Get Equal to of dataframe and other, element-wise (binary operator `eq`)."""
    _instance = _get_object(dataframe)
    return _instance.eq()

@mcp.tool(name="dataframe_equals")
def dataframe_equals(dataframe: str) -> Any:
    """Test whether two objects contain the same elements."""
    _instance = _get_object(dataframe)
    return _instance.equals()

@mcp.tool(name="dataframe_eval")
def dataframe_eval(dataframe: str) -> Any:
    """Evaluate a string describing operations on DataFrame columns."""
    _instance = _get_object(dataframe)
    return _instance.eval()

@mcp.tool(name="dataframe_ewm")
def dataframe_ewm(dataframe: str) -> Any:
    """Provide exponentially weighted (EW) calculations."""
    _instance = _get_object(dataframe)
    return _instance.ewm()

@mcp.tool(name="dataframe_expanding")
def dataframe_expanding(dataframe: str) -> Any:
    """Provide expanding window calculations."""
    _instance = _get_object(dataframe)
    return _instance.expanding()

@mcp.tool(name="dataframe_explode")
def dataframe_explode(dataframe: str) -> Any:
    """Transform each element of a list-like to a row, replicating index values."""
    _instance = _get_object(dataframe)
    return _instance.explode()

@mcp.tool(name="dataframe_ffill")
def dataframe_ffill(dataframe: str) -> Any:
    """Fill NA/NaN values by propagating the last valid observation to next valid."""
    _instance = _get_object(dataframe)
    return _instance.ffill()

@mcp.tool(name="dataframe_fillna")
def dataframe_fillna(dataframe: str) -> Any:
    """Fill NA/NaN values using the specified method."""
    _instance = _get_object(dataframe)
    return _instance.fillna()

@mcp.tool(name="dataframe_filter")
def dataframe_filter(dataframe: str) -> Any:
    """Subset the dataframe rows or columns according to the specified index labels."""
    _instance = _get_object(dataframe)
    return _instance.filter()

@mcp.tool(name="dataframe_first")
def dataframe_first(dataframe: str) -> Any:
    """Select initial periods of time series data based on a date offset."""
    _instance = _get_object(dataframe)
    return _instance.first()

@mcp.tool(name="dataframe_first_valid_index")
def dataframe_first_valid_index(dataframe: str) -> Any:
    """Return index for first non-NA value or None, if no non-NA value is found."""
    _instance = _get_object(dataframe)
    return _instance.first_valid_index()

@mcp.tool(name="dataframe_floordiv")
def dataframe_floordiv(dataframe: str) -> Any:
    """Get Integer division of dataframe and other, element-wise (binary operator `floordiv`)."""
    _instance = _get_object(dataframe)
    return _instance.floordiv()

@mcp.tool(name="dataframe_from_dict")
def dataframe_from_dict(dataframe: str) -> Any:
    """Construct DataFrame from dict of array-like or dicts."""
    _instance = _get_object(dataframe)
    return _instance.from_dict()

@mcp.tool(name="dataframe_from_records")
def dataframe_from_records(dataframe: str) -> Any:
    """Convert structured or record ndarray to DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.from_records()

@mcp.tool(name="dataframe_ge")
def dataframe_ge(dataframe: str) -> Any:
    """Get Greater than or equal to of dataframe and other, element-wise (binary operator `ge`)."""
    _instance = _get_object(dataframe)
    return _instance.ge()

@mcp.tool(name="dataframe_get")
def dataframe_get(dataframe: str) -> Any:
    """Get item from object for given key (ex: DataFrame column)."""
    _instance = _get_object(dataframe)
    return _instance.get()

@mcp.tool(name="dataframe_groupby")
def dataframe_groupby(dataframe: str) -> Any:
    """Group DataFrame using a mapper or by a Series of columns."""
    _instance = _get_object(dataframe)
    return _instance.groupby()

@mcp.tool(name="dataframe_gt")
def dataframe_gt(dataframe: str) -> Any:
    """Get Greater than of dataframe and other, element-wise (binary operator `gt`)."""
    _instance = _get_object(dataframe)
    return _instance.gt()

@mcp.tool(name="dataframe_head")
def dataframe_head(dataframe: str) -> Any:
    """Return the first `n` rows."""
    _instance = _get_object(dataframe)
    return _instance.head()

@mcp.tool(name="dataframe_hist")
def dataframe_hist(dataframe: str) -> Any:
    """Make a histogram of the DataFrame's columns."""
    _instance = _get_object(dataframe)
    return _instance.hist()

@mcp.tool(name="dataframe_idxmax")
def dataframe_idxmax(dataframe: str) -> Any:
    """Return index of first occurrence of maximum over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.idxmax()

@mcp.tool(name="dataframe_idxmin")
def dataframe_idxmin(dataframe: str) -> Any:
    """Return index of first occurrence of minimum over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.idxmin()

@mcp.tool(name="dataframe_infer_objects")
def dataframe_infer_objects(dataframe: str) -> Any:
    """Attempt to infer better dtypes for object columns."""
    _instance = _get_object(dataframe)
    return _instance.infer_objects()

@mcp.tool(name="dataframe_info")
def dataframe_info(dataframe: str) -> Any:
    """Print a concise summary of a DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.info()

@mcp.tool(name="dataframe_insert")
def dataframe_insert(dataframe: str) -> Any:
    """Insert column into DataFrame at specified location."""
    _instance = _get_object(dataframe)
    return _instance.insert()

@mcp.tool(name="dataframe_interpolate")
def dataframe_interpolate(dataframe: str) -> Any:
    """Fill NaN values using an interpolation method."""
    _instance = _get_object(dataframe)
    return _instance.interpolate()

@mcp.tool(name="dataframe_isetitem")
def dataframe_isetitem(dataframe: str) -> Any:
    """Set the given value in the column with position `loc`."""
    _instance = _get_object(dataframe)
    return _instance.isetitem()

@mcp.tool(name="dataframe_isin")
def dataframe_isin(dataframe: str) -> Any:
    """Whether each element in the DataFrame is contained in values."""
    _instance = _get_object(dataframe)
    return _instance.isin()

@mcp.tool(name="dataframe_isna")
def dataframe_isna(dataframe: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(dataframe)
    return _instance.isna()

@mcp.tool(name="dataframe_isnull")
def dataframe_isnull(dataframe: str) -> Any:
    """DataFrame.isnull is an alias for DataFrame.isna."""
    _instance = _get_object(dataframe)
    return _instance.isnull()

@mcp.tool(name="dataframe_items")
def dataframe_items(dataframe: str) -> Any:
    """Iterate over (column name, Series) pairs."""
    _instance = _get_object(dataframe)
    return _instance.items()

@mcp.tool(name="dataframe_iterrows")
def dataframe_iterrows(dataframe: str) -> Any:
    """Iterate over DataFrame rows as (index, Series) pairs."""
    _instance = _get_object(dataframe)
    return _instance.iterrows()

@mcp.tool(name="dataframe_itertuples")
def dataframe_itertuples(dataframe: str) -> Any:
    """Iterate over DataFrame rows as namedtuples."""
    _instance = _get_object(dataframe)
    return _instance.itertuples()

@mcp.tool(name="dataframe_join")
def dataframe_join(dataframe: str) -> Any:
    """Join columns of another DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.join()

@mcp.tool(name="dataframe_keys")
def dataframe_keys(dataframe: str) -> Any:
    """Get the 'info axis' (see Indexing for more)."""
    _instance = _get_object(dataframe)
    return _instance.keys()

@mcp.tool(name="dataframe_kurt")
def dataframe_kurt(dataframe: str) -> Any:
    """Return unbiased kurtosis over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.kurt()

@mcp.tool(name="dataframe_kurtosis")
def dataframe_kurtosis(dataframe: str) -> Any:
    """Return unbiased kurtosis over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.kurtosis()

@mcp.tool(name="dataframe_last")
def dataframe_last(dataframe: str) -> Any:
    """Select final periods of time series data based on a date offset."""
    _instance = _get_object(dataframe)
    return _instance.last()

@mcp.tool(name="dataframe_last_valid_index")
def dataframe_last_valid_index(dataframe: str) -> Any:
    """Return index for last non-NA value or None, if no non-NA value is found."""
    _instance = _get_object(dataframe)
    return _instance.last_valid_index()

@mcp.tool(name="dataframe_le")
def dataframe_le(dataframe: str) -> Any:
    """Get Less than or equal to of dataframe and other, element-wise (binary operator `le`)."""
    _instance = _get_object(dataframe)
    return _instance.le()

@mcp.tool(name="dataframe_lt")
def dataframe_lt(dataframe: str) -> Any:
    """Get Less than of dataframe and other, element-wise (binary operator `lt`)."""
    _instance = _get_object(dataframe)
    return _instance.lt()

@mcp.tool(name="dataframe_map")
def dataframe_map(dataframe: str) -> Any:
    """Apply a function to a Dataframe elementwise."""
    _instance = _get_object(dataframe)
    return _instance.map()

@mcp.tool(name="dataframe_mask")
def dataframe_mask(dataframe: str) -> Any:
    """Replace values where the condition is True."""
    _instance = _get_object(dataframe)
    return _instance.mask()

@mcp.tool(name="dataframe_max")
def dataframe_max(dataframe: str) -> Any:
    """Return the maximum of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.max()

@mcp.tool(name="dataframe_mean")
def dataframe_mean(dataframe: str) -> Any:
    """Return the mean of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.mean()

@mcp.tool(name="dataframe_median")
def dataframe_median(dataframe: str) -> Any:
    """Return the median of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.median()

@mcp.tool(name="dataframe_melt")
def dataframe_melt(dataframe: str) -> Any:
    """Unpivot a DataFrame from wide to long format, optionally leaving identifiers set."""
    _instance = _get_object(dataframe)
    return _instance.melt()

@mcp.tool(name="dataframe_memory_usage")
def dataframe_memory_usage(dataframe: str) -> Any:
    """Return the memory usage of each column in bytes."""
    _instance = _get_object(dataframe)
    return _instance.memory_usage()

@mcp.tool(name="dataframe_merge")
def dataframe_merge(dataframe: str) -> Any:
    """Merge DataFrame or named Series objects with a database-style join."""
    _instance = _get_object(dataframe)
    return _instance.merge()

@mcp.tool(name="dataframe_min")
def dataframe_min(dataframe: str) -> Any:
    """Return the minimum of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.min()

@mcp.tool(name="dataframe_mod")
def dataframe_mod(dataframe: str) -> Any:
    """Get Modulo of dataframe and other, element-wise (binary operator `mod`)."""
    _instance = _get_object(dataframe)
    return _instance.mod()

@mcp.tool(name="dataframe_mode")
def dataframe_mode(dataframe: str) -> Any:
    """Get the mode(s) of each element along the selected axis."""
    _instance = _get_object(dataframe)
    return _instance.mode()

@mcp.tool(name="dataframe_mul")
def dataframe_mul(dataframe: str) -> Any:
    """Get Multiplication of dataframe and other, element-wise (binary operator `mul`)."""
    _instance = _get_object(dataframe)
    return _instance.mul()

@mcp.tool(name="dataframe_multiply")
def dataframe_multiply(dataframe: str) -> Any:
    """Get Multiplication of dataframe and other, element-wise (binary operator `mul`)."""
    _instance = _get_object(dataframe)
    return _instance.multiply()

@mcp.tool(name="dataframe_ne")
def dataframe_ne(dataframe: str) -> Any:
    """Get Not equal to of dataframe and other, element-wise (binary operator `ne`)."""
    _instance = _get_object(dataframe)
    return _instance.ne()

@mcp.tool(name="dataframe_nlargest")
def dataframe_nlargest(dataframe: str) -> Any:
    """Return the first `n` rows ordered by `columns` in descending order."""
    _instance = _get_object(dataframe)
    return _instance.nlargest()

@mcp.tool(name="dataframe_notna")
def dataframe_notna(dataframe: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(dataframe)
    return _instance.notna()

@mcp.tool(name="dataframe_notnull")
def dataframe_notnull(dataframe: str) -> Any:
    """DataFrame.notnull is an alias for DataFrame.notna."""
    _instance = _get_object(dataframe)
    return _instance.notnull()

@mcp.tool(name="dataframe_nsmallest")
def dataframe_nsmallest(dataframe: str) -> Any:
    """Return the first `n` rows ordered by `columns` in ascending order."""
    _instance = _get_object(dataframe)
    return _instance.nsmallest()

@mcp.tool(name="dataframe_nunique")
def dataframe_nunique(dataframe: str) -> Any:
    """Count number of distinct elements in specified axis."""
    _instance = _get_object(dataframe)
    return _instance.nunique()

@mcp.tool(name="dataframe_pad")
def dataframe_pad(dataframe: str) -> Any:
    """Fill NA/NaN values by propagating the last valid observation to next valid."""
    _instance = _get_object(dataframe)
    return _instance.pad()

@mcp.tool(name="dataframe_pct_change")
def dataframe_pct_change(dataframe: str) -> Any:
    """Fractional change between the current and a prior element."""
    _instance = _get_object(dataframe)
    return _instance.pct_change()

@mcp.tool(name="dataframe_pipe")
def dataframe_pipe(dataframe: str) -> Any:
    """Apply chainable functions that expect Series or DataFrames."""
    _instance = _get_object(dataframe)
    return _instance.pipe()

@mcp.tool(name="dataframe_pivot")
def dataframe_pivot(dataframe: str) -> Any:
    """Return reshaped DataFrame organized by given index / column values."""
    _instance = _get_object(dataframe)
    return _instance.pivot()

@mcp.tool(name="dataframe_pivot_table")
def dataframe_pivot_table(dataframe: str) -> Any:
    """Create a spreadsheet-style pivot table as a DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.pivot_table()

@mcp.tool(name="dataframe_pop")
def dataframe_pop(dataframe: str) -> Any:
    """Return item and drop from frame. Raise KeyError if not found."""
    _instance = _get_object(dataframe)
    return _instance.pop()

@mcp.tool(name="dataframe_pow")
def dataframe_pow(dataframe: str) -> Any:
    """Get Exponential power of dataframe and other, element-wise (binary operator `pow`)."""
    _instance = _get_object(dataframe)
    return _instance.pow()

@mcp.tool(name="dataframe_prod")
def dataframe_prod(dataframe: str) -> Any:
    """Return the product of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.prod()

@mcp.tool(name="dataframe_product")
def dataframe_product(dataframe: str) -> Any:
    """Return the product of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.product()

@mcp.tool(name="dataframe_quantile")
def dataframe_quantile(dataframe: str) -> Any:
    """Return values at the given quantile over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.quantile()

@mcp.tool(name="dataframe_query")
def dataframe_query(dataframe: str) -> Any:
    """Query the columns of a DataFrame with a boolean expression."""
    _instance = _get_object(dataframe)
    return _instance.query()

@mcp.tool(name="dataframe_radd")
def dataframe_radd(dataframe: str) -> Any:
    """Get Addition of dataframe and other, element-wise (binary operator `radd`)."""
    _instance = _get_object(dataframe)
    return _instance.radd()

@mcp.tool(name="dataframe_rank")
def dataframe_rank(dataframe: str) -> Any:
    """Compute numerical data ranks (1 through n) along axis."""
    _instance = _get_object(dataframe)
    return _instance.rank()

@mcp.tool(name="dataframe_rdiv")
def dataframe_rdiv(dataframe: str) -> Any:
    """Get Floating division of dataframe and other, element-wise (binary operator `rtruediv`)."""
    _instance = _get_object(dataframe)
    return _instance.rdiv()

@mcp.tool(name="dataframe_reindex")
def dataframe_reindex(dataframe: str) -> Any:
    """Conform DataFrame to new index with optional filling logic."""
    _instance = _get_object(dataframe)
    return _instance.reindex()

@mcp.tool(name="dataframe_reindex_like")
def dataframe_reindex_like(dataframe: str) -> Any:
    """Return an object with matching indices as other object."""
    _instance = _get_object(dataframe)
    return _instance.reindex_like()

@mcp.tool(name="dataframe_rename")
def dataframe_rename(dataframe: str) -> Any:
    """Rename columns or index labels."""
    _instance = _get_object(dataframe)
    return _instance.rename()

@mcp.tool(name="dataframe_rename_axis")
def dataframe_rename_axis(dataframe: str) -> Any:
    """Set the name of the axis for the index or columns."""
    _instance = _get_object(dataframe)
    return _instance.rename_axis()

@mcp.tool(name="dataframe_reorder_levels")
def dataframe_reorder_levels(dataframe: str) -> Any:
    """Rearrange index levels using input order. May not drop or duplicate levels."""
    _instance = _get_object(dataframe)
    return _instance.reorder_levels()

@mcp.tool(name="dataframe_replace")
def dataframe_replace(dataframe: str) -> Any:
    """Replace values given in `to_replace` with `value`."""
    _instance = _get_object(dataframe)
    return _instance.replace()

@mcp.tool(name="dataframe_resample")
def dataframe_resample(dataframe: str) -> Any:
    """Resample time-series data."""
    _instance = _get_object(dataframe)
    return _instance.resample()

@mcp.tool(name="dataframe_reset_index")
def dataframe_reset_index(dataframe: str) -> Any:
    """Reset the index, or a level of it."""
    _instance = _get_object(dataframe)
    return _instance.reset_index()

@mcp.tool(name="dataframe_rfloordiv")
def dataframe_rfloordiv(dataframe: str) -> Any:
    """Get Integer division of dataframe and other, element-wise (binary operator `rfloordiv`)."""
    _instance = _get_object(dataframe)
    return _instance.rfloordiv()

@mcp.tool(name="dataframe_rmod")
def dataframe_rmod(dataframe: str) -> Any:
    """Get Modulo of dataframe and other, element-wise (binary operator `rmod`)."""
    _instance = _get_object(dataframe)
    return _instance.rmod()

@mcp.tool(name="dataframe_rmul")
def dataframe_rmul(dataframe: str) -> Any:
    """Get Multiplication of dataframe and other, element-wise (binary operator `rmul`)."""
    _instance = _get_object(dataframe)
    return _instance.rmul()

@mcp.tool(name="dataframe_rolling")
def dataframe_rolling(dataframe: str) -> Any:
    """Provide rolling window calculations."""
    _instance = _get_object(dataframe)
    return _instance.rolling()

@mcp.tool(name="dataframe_round")
def dataframe_round(dataframe: str) -> Any:
    """Round a DataFrame to a variable number of decimal places."""
    _instance = _get_object(dataframe)
    return _instance.round()

@mcp.tool(name="dataframe_rpow")
def dataframe_rpow(dataframe: str) -> Any:
    """Get Exponential power of dataframe and other, element-wise (binary operator `rpow`)."""
    _instance = _get_object(dataframe)
    return _instance.rpow()

@mcp.tool(name="dataframe_rsub")
def dataframe_rsub(dataframe: str) -> Any:
    """Get Subtraction of dataframe and other, element-wise (binary operator `rsub`)."""
    _instance = _get_object(dataframe)
    return _instance.rsub()

@mcp.tool(name="dataframe_rtruediv")
def dataframe_rtruediv(dataframe: str) -> Any:
    """Get Floating division of dataframe and other, element-wise (binary operator `rtruediv`)."""
    _instance = _get_object(dataframe)
    return _instance.rtruediv()

@mcp.tool(name="dataframe_sample")
def dataframe_sample(dataframe: str) -> Any:
    """Return a random sample of items from an axis of object."""
    _instance = _get_object(dataframe)
    return _instance.sample()

@mcp.tool(name="dataframe_select_dtypes")
def dataframe_select_dtypes(dataframe: str) -> Any:
    """Return a subset of the DataFrame's columns based on the column dtypes."""
    _instance = _get_object(dataframe)
    return _instance.select_dtypes()

@mcp.tool(name="dataframe_sem")
def dataframe_sem(dataframe: str) -> Any:
    """Return unbiased standard error of the mean over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.sem()

@mcp.tool(name="dataframe_set_axis")
def dataframe_set_axis(dataframe: str) -> Any:
    """Assign desired index to given axis."""
    _instance = _get_object(dataframe)
    return _instance.set_axis()

@mcp.tool(name="dataframe_set_flags")
def dataframe_set_flags(dataframe: str) -> Any:
    """Return a new object with updated flags."""
    _instance = _get_object(dataframe)
    return _instance.set_flags()

@mcp.tool(name="dataframe_set_index")
def dataframe_set_index(dataframe: str) -> Any:
    """Set the DataFrame index using existing columns."""
    _instance = _get_object(dataframe)
    return _instance.set_index()

@mcp.tool(name="dataframe_shift")
def dataframe_shift(dataframe: str) -> Any:
    """Shift index by desired number of periods with an optional time `freq`."""
    _instance = _get_object(dataframe)
    return _instance.shift()

@mcp.tool(name="dataframe_skew")
def dataframe_skew(dataframe: str) -> Any:
    """Return unbiased skew over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.skew()

@mcp.tool(name="dataframe_sort_index")
def dataframe_sort_index(dataframe: str) -> Any:
    """Sort object by labels (along an axis)."""
    _instance = _get_object(dataframe)
    return _instance.sort_index()

@mcp.tool(name="dataframe_sort_values")
def dataframe_sort_values(dataframe: str) -> Any:
    """Sort by the values along either axis."""
    _instance = _get_object(dataframe)
    return _instance.sort_values()

@mcp.tool(name="dataframe_squeeze")
def dataframe_squeeze(dataframe: str) -> Any:
    """Squeeze 1 dimensional axis objects into scalars."""
    _instance = _get_object(dataframe)
    return _instance.squeeze()

@mcp.tool(name="dataframe_stack")
def dataframe_stack(dataframe: str) -> Any:
    """Stack the prescribed level(s) from columns to index."""
    _instance = _get_object(dataframe)
    return _instance.stack()

@mcp.tool(name="dataframe_std")
def dataframe_std(dataframe: str) -> Any:
    """Return sample standard deviation over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.std()

@mcp.tool(name="dataframe_sub")
def dataframe_sub(dataframe: str) -> Any:
    """Get Subtraction of dataframe and other, element-wise (binary operator `sub`)."""
    _instance = _get_object(dataframe)
    return _instance.sub()

@mcp.tool(name="dataframe_subtract")
def dataframe_subtract(dataframe: str) -> Any:
    """Get Subtraction of dataframe and other, element-wise (binary operator `sub`)."""
    _instance = _get_object(dataframe)
    return _instance.subtract()

@mcp.tool(name="dataframe_sum")
def dataframe_sum(dataframe: str) -> Any:
    """Return the sum of the values over the requested axis."""
    _instance = _get_object(dataframe)
    return _instance.sum()

@mcp.tool(name="dataframe_swapaxes")
def dataframe_swapaxes(dataframe: str) -> Any:
    """Interchange axes and swap values axes appropriately."""
    _instance = _get_object(dataframe)
    return _instance.swapaxes()

@mcp.tool(name="dataframe_swaplevel")
def dataframe_swaplevel(dataframe: str) -> Any:
    """Swap levels i and j in a :class:`MultiIndex`."""
    _instance = _get_object(dataframe)
    return _instance.swaplevel()

@mcp.tool(name="dataframe_tail")
def dataframe_tail(dataframe: str) -> Any:
    """Return the last `n` rows."""
    _instance = _get_object(dataframe)
    return _instance.tail()

@mcp.tool(name="dataframe_take")
def dataframe_take(dataframe: str) -> Any:
    """Return the elements in the given *positional* indices along an axis."""
    _instance = _get_object(dataframe)
    return _instance.take()

@mcp.tool(name="dataframe_to_clipboard")
def dataframe_to_clipboard(dataframe: str) -> Any:
    """Copy object to the system clipboard."""
    _instance = _get_object(dataframe)
    return _instance.to_clipboard()

@mcp.tool(name="dataframe_to_csv")
def dataframe_to_csv(dataframe: str) -> Any:
    """Write object to a comma-separated values (csv) file."""
    _instance = _get_object(dataframe)
    return _instance.to_csv()

@mcp.tool(name="dataframe_to_dict")
def dataframe_to_dict(dataframe: str) -> Any:
    """Convert the DataFrame to a dictionary."""
    _instance = _get_object(dataframe)
    return _instance.to_dict()

@mcp.tool(name="dataframe_to_excel")
def dataframe_to_excel(dataframe: str) -> Any:
    """Write object to an Excel sheet."""
    _instance = _get_object(dataframe)
    return _instance.to_excel()

@mcp.tool(name="dataframe_to_feather")
def dataframe_to_feather(dataframe: str) -> Any:
    """Write a DataFrame to the binary Feather format."""
    _instance = _get_object(dataframe)
    return _instance.to_feather()

@mcp.tool(name="dataframe_to_gbq")
def dataframe_to_gbq(dataframe: str) -> Any:
    """Write a DataFrame to a Google BigQuery table."""
    _instance = _get_object(dataframe)
    return _instance.to_gbq()

@mcp.tool(name="dataframe_to_hdf")
def dataframe_to_hdf(dataframe: str) -> Any:
    """Write the contained data to an HDF5 file using HDFStore."""
    _instance = _get_object(dataframe)
    return _instance.to_hdf()

@mcp.tool(name="dataframe_to_html")
def dataframe_to_html(dataframe: str) -> Any:
    """Render a DataFrame as an HTML table."""
    _instance = _get_object(dataframe)
    return _instance.to_html()

@mcp.tool(name="dataframe_to_json")
def dataframe_to_json(dataframe: str) -> Any:
    """Convert the object to a JSON string."""
    _instance = _get_object(dataframe)
    return _instance.to_json()

@mcp.tool(name="dataframe_to_latex")
def dataframe_to_latex(dataframe: str) -> Any:
    """Render object to a LaTeX tabular, longtable, or nested table."""
    _instance = _get_object(dataframe)
    return _instance.to_latex()

@mcp.tool(name="dataframe_to_markdown")
def dataframe_to_markdown(dataframe: str) -> Any:
    """Print DataFrame in Markdown-friendly format."""
    _instance = _get_object(dataframe)
    return _instance.to_markdown()

@mcp.tool(name="dataframe_to_numpy")
def dataframe_to_numpy(dataframe: str) -> Any:
    """Convert the DataFrame to a NumPy array."""
    _instance = _get_object(dataframe)
    return _instance.to_numpy()

@mcp.tool(name="dataframe_to_orc")
def dataframe_to_orc(dataframe: str) -> Any:
    """Write a DataFrame to the ORC format."""
    _instance = _get_object(dataframe)
    return _instance.to_orc()

@mcp.tool(name="dataframe_to_parquet")
def dataframe_to_parquet(dataframe: str) -> Any:
    """Write a DataFrame to the binary parquet format."""
    _instance = _get_object(dataframe)
    return _instance.to_parquet()

@mcp.tool(name="dataframe_to_period")
def dataframe_to_period(dataframe: str) -> Any:
    """Convert DataFrame from DatetimeIndex to PeriodIndex."""
    _instance = _get_object(dataframe)
    return _instance.to_period()

@mcp.tool(name="dataframe_to_pickle")
def dataframe_to_pickle(dataframe: str) -> Any:
    """Pickle (serialize) object to file."""
    _instance = _get_object(dataframe)
    return _instance.to_pickle()

@mcp.tool(name="dataframe_to_records")
def dataframe_to_records(dataframe: str) -> Any:
    """Convert DataFrame to a NumPy record array."""
    _instance = _get_object(dataframe)
    return _instance.to_records()

@mcp.tool(name="dataframe_to_sql")
def dataframe_to_sql(dataframe: str) -> Any:
    """Write records stored in a DataFrame to a SQL database."""
    _instance = _get_object(dataframe)
    return _instance.to_sql()

@mcp.tool(name="dataframe_to_stata")
def dataframe_to_stata(dataframe: str) -> Any:
    """Export DataFrame object to Stata dta format."""
    _instance = _get_object(dataframe)
    return _instance.to_stata()

@mcp.tool(name="dataframe_to_string")
def dataframe_to_string(dataframe: str) -> Any:
    """Render a DataFrame to a console-friendly tabular output."""
    _instance = _get_object(dataframe)
    return _instance.to_string()

@mcp.tool(name="dataframe_to_timestamp")
def dataframe_to_timestamp(dataframe: str) -> Any:
    """Cast to DatetimeIndex of timestamps, at *beginning* of period."""
    _instance = _get_object(dataframe)
    return _instance.to_timestamp()

@mcp.tool(name="dataframe_to_xarray")
def dataframe_to_xarray(dataframe: str) -> Any:
    """Return an xarray object from the pandas object."""
    _instance = _get_object(dataframe)
    return _instance.to_xarray()

@mcp.tool(name="dataframe_to_xml")
def dataframe_to_xml(dataframe: str) -> Any:
    """Render a DataFrame to an XML document."""
    _instance = _get_object(dataframe)
    return _instance.to_xml()

@mcp.tool(name="dataframe_transform")
def dataframe_transform(dataframe: str) -> Any:
    """Call ``func`` on self producing a DataFrame with the same axis shape as self."""
    _instance = _get_object(dataframe)
    return _instance.transform()

@mcp.tool(name="dataframe_transpose")
def dataframe_transpose(dataframe: str) -> Any:
    """Transpose index and columns."""
    _instance = _get_object(dataframe)
    return _instance.transpose()

@mcp.tool(name="dataframe_truediv")
def dataframe_truediv(dataframe: str) -> Any:
    """Get Floating division of dataframe and other, element-wise (binary operator `truediv`)."""
    _instance = _get_object(dataframe)
    return _instance.truediv()

@mcp.tool(name="dataframe_truncate")
def dataframe_truncate(dataframe: str) -> Any:
    """Truncate a Series or DataFrame before and after some index value."""
    _instance = _get_object(dataframe)
    return _instance.truncate()

@mcp.tool(name="dataframe_tz_convert")
def dataframe_tz_convert(dataframe: str) -> Any:
    """Convert tz-aware axis to target time zone."""
    _instance = _get_object(dataframe)
    return _instance.tz_convert()

@mcp.tool(name="dataframe_tz_localize")
def dataframe_tz_localize(dataframe: str) -> Any:
    """Localize tz-naive index of a Series or DataFrame to target time zone."""
    _instance = _get_object(dataframe)
    return _instance.tz_localize()

@mcp.tool(name="dataframe_unstack")
def dataframe_unstack(dataframe: str) -> Any:
    """Pivot a level of the (necessarily hierarchical) index labels."""
    _instance = _get_object(dataframe)
    return _instance.unstack()

@mcp.tool(name="dataframe_update")
def dataframe_update(dataframe: str) -> Any:
    """Modify in place using non-NA values from another DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.update()

@mcp.tool(name="dataframe_value_counts")
def dataframe_value_counts(dataframe: str) -> Any:
    """Return a Series containing the frequency of each distinct row in the Dataframe."""
    _instance = _get_object(dataframe)
    return _instance.value_counts()

@mcp.tool(name="dataframe_var")
def dataframe_var(dataframe: str) -> Any:
    """Return unbiased variance over requested axis."""
    _instance = _get_object(dataframe)
    return _instance.var()

@mcp.tool(name="dataframe_where")
def dataframe_where(dataframe: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(dataframe)
    return _instance.where()

@mcp.tool(name="dataframe_xs")
def dataframe_xs(dataframe: str) -> Any:
    """Return cross-section from the Series/DataFrame."""
    _instance = _get_object(dataframe)
    return _instance.xs()

@mcp.tool(name="dateoffset_copy")
def dateoffset_copy(dateoffset: str) -> Any:
    """Return a copy of the frequency."""
    _instance = _get_object(dateoffset)
    return _instance.copy()

@mcp.tool(name="dateoffset_is_anchored")
def dateoffset_is_anchored(dateoffset: str) -> Any:
    """Return boolean whether the frequency is a unit frequency (n=1)."""
    _instance = _get_object(dateoffset)
    return _instance.is_anchored()

@mcp.tool(name="dateoffset_is_month_end")
def dateoffset_is_month_end(dateoffset: str) -> Any:
    """Return boolean whether a timestamp occurs on the month end."""
    _instance = _get_object(dateoffset)
    return _instance.is_month_end()

@mcp.tool(name="dateoffset_is_month_start")
def dateoffset_is_month_start(dateoffset: str) -> Any:
    """Return boolean whether a timestamp occurs on the month start."""
    _instance = _get_object(dateoffset)
    return _instance.is_month_start()

@mcp.tool(name="dateoffset_is_on_offset")
def dateoffset_is_on_offset(dateoffset: str) -> Any:
    """Tool: dateoffset_is_on_offset"""
    _instance = _get_object(dateoffset)
    return _instance.is_on_offset()

@mcp.tool(name="dateoffset_is_quarter_end")
def dateoffset_is_quarter_end(dateoffset: str) -> Any:
    """Return boolean whether a timestamp occurs on the quarter end."""
    _instance = _get_object(dateoffset)
    return _instance.is_quarter_end()

@mcp.tool(name="dateoffset_is_quarter_start")
def dateoffset_is_quarter_start(dateoffset: str) -> Any:
    """Return boolean whether a timestamp occurs on the quarter start."""
    _instance = _get_object(dateoffset)
    return _instance.is_quarter_start()

@mcp.tool(name="dateoffset_is_year_end")
def dateoffset_is_year_end(dateoffset: str) -> Any:
    """Return boolean whether a timestamp occurs on the year end."""
    _instance = _get_object(dateoffset)
    return _instance.is_year_end()

@mcp.tool(name="dateoffset_is_year_start")
def dateoffset_is_year_start(dateoffset: str) -> Any:
    """Return boolean whether a timestamp occurs on the year start."""
    _instance = _get_object(dateoffset)
    return _instance.is_year_start()

@mcp.tool(name="dateoffset_rollback")
def dateoffset_rollback(dateoffset: str) -> Any:
    """Roll provided date backward to next offset only if not on offset."""
    _instance = _get_object(dateoffset)
    return _instance.rollback()

@mcp.tool(name="dateoffset_rollforward")
def dateoffset_rollforward(dateoffset: str) -> Any:
    """Roll provided date forward to next offset only if not on offset."""
    _instance = _get_object(dateoffset)
    return _instance.rollforward()

@mcp.tool(name="datetimeindex_all")
def datetimeindex_all(datetimeindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(datetimeindex)
    return _instance.all()

@mcp.tool(name="datetimeindex_any")
def datetimeindex_any(datetimeindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(datetimeindex)
    return _instance.any()

@mcp.tool(name="datetimeindex_append")
def datetimeindex_append(datetimeindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(datetimeindex)
    return _instance.append()

@mcp.tool(name="datetimeindex_argmax")
def datetimeindex_argmax(datetimeindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(datetimeindex)
    return _instance.argmax()

@mcp.tool(name="datetimeindex_argmin")
def datetimeindex_argmin(datetimeindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(datetimeindex)
    return _instance.argmin()

@mcp.tool(name="datetimeindex_argsort")
def datetimeindex_argsort(datetimeindex: str) -> Any:
    """Return the integer indices that would sort the index."""
    _instance = _get_object(datetimeindex)
    return _instance.argsort()

@mcp.tool(name="datetimeindex_as_unit")
def datetimeindex_as_unit(datetimeindex: str) -> Any:
    """Tool: datetimeindex_as_unit"""
    _instance = _get_object(datetimeindex)
    return _instance.as_unit()

@mcp.tool(name="datetimeindex_asof")
def datetimeindex_asof(datetimeindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(datetimeindex)
    return _instance.asof()

@mcp.tool(name="datetimeindex_asof_locs")
def datetimeindex_asof_locs(datetimeindex: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(datetimeindex)
    return _instance.asof_locs()

@mcp.tool(name="datetimeindex_astype")
def datetimeindex_astype(datetimeindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(datetimeindex)
    return _instance.astype()

@mcp.tool(name="datetimeindex_ceil")
def datetimeindex_ceil(datetimeindex: str) -> Any:
    """Perform ceil operation on the data to the specified `freq`."""
    _instance = _get_object(datetimeindex)
    return _instance.ceil()

@mcp.tool(name="datetimeindex_copy")
def datetimeindex_copy(datetimeindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(datetimeindex)
    return _instance.copy()

@mcp.tool(name="datetimeindex_day_name")
def datetimeindex_day_name(datetimeindex: str) -> Any:
    """Return the day names with specified locale."""
    _instance = _get_object(datetimeindex)
    return _instance.day_name()

@mcp.tool(name="datetimeindex_delete")
def datetimeindex_delete(datetimeindex: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(datetimeindex)
    return _instance.delete()

@mcp.tool(name="datetimeindex_diff")
def datetimeindex_diff(datetimeindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(datetimeindex)
    return _instance.diff()

@mcp.tool(name="datetimeindex_difference")
def datetimeindex_difference(datetimeindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(datetimeindex)
    return _instance.difference()

@mcp.tool(name="datetimeindex_drop")
def datetimeindex_drop(datetimeindex: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(datetimeindex)
    return _instance.drop()

@mcp.tool(name="datetimeindex_drop_duplicates")
def datetimeindex_drop_duplicates(datetimeindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(datetimeindex)
    return _instance.drop_duplicates()

@mcp.tool(name="datetimeindex_droplevel")
def datetimeindex_droplevel(datetimeindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(datetimeindex)
    return _instance.droplevel()

@mcp.tool(name="datetimeindex_dropna")
def datetimeindex_dropna(datetimeindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(datetimeindex)
    return _instance.dropna()

@mcp.tool(name="datetimeindex_duplicated")
def datetimeindex_duplicated(datetimeindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(datetimeindex)
    return _instance.duplicated()

@mcp.tool(name="datetimeindex_equals")
def datetimeindex_equals(datetimeindex: str) -> Any:
    """Determines if two Index objects contain the same elements."""
    _instance = _get_object(datetimeindex)
    return _instance.equals()

@mcp.tool(name="datetimeindex_factorize")
def datetimeindex_factorize(datetimeindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(datetimeindex)
    return _instance.factorize()

@mcp.tool(name="datetimeindex_fillna")
def datetimeindex_fillna(datetimeindex: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(datetimeindex)
    return _instance.fillna()

@mcp.tool(name="datetimeindex_floor")
def datetimeindex_floor(datetimeindex: str) -> Any:
    """Perform floor operation on the data to the specified `freq`."""
    _instance = _get_object(datetimeindex)
    return _instance.floor()

@mcp.tool(name="datetimeindex_format")
def datetimeindex_format(datetimeindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(datetimeindex)
    return _instance.format()

@mcp.tool(name="datetimeindex_get_indexer")
def datetimeindex_get_indexer(datetimeindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(datetimeindex)
    return _instance.get_indexer()

@mcp.tool(name="datetimeindex_get_indexer_for")
def datetimeindex_get_indexer_for(datetimeindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(datetimeindex)
    return _instance.get_indexer_for()

@mcp.tool(name="datetimeindex_get_indexer_non_unique")
def datetimeindex_get_indexer_non_unique(datetimeindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(datetimeindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="datetimeindex_get_level_values")
def datetimeindex_get_level_values(datetimeindex: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(datetimeindex)
    return _instance.get_level_values()

@mcp.tool(name="datetimeindex_get_loc")
def datetimeindex_get_loc(datetimeindex: str) -> Any:
    """Get integer location for requested label"""
    _instance = _get_object(datetimeindex)
    return _instance.get_loc()

@mcp.tool(name="datetimeindex_get_slice_bound")
def datetimeindex_get_slice_bound(datetimeindex: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(datetimeindex)
    return _instance.get_slice_bound()

@mcp.tool(name="datetimeindex_groupby")
def datetimeindex_groupby(datetimeindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(datetimeindex)
    return _instance.groupby()

@mcp.tool(name="datetimeindex_holds_integer")
def datetimeindex_holds_integer(datetimeindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(datetimeindex)
    return _instance.holds_integer()

@mcp.tool(name="datetimeindex_identical")
def datetimeindex_identical(datetimeindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(datetimeindex)
    return _instance.identical()

@mcp.tool(name="datetimeindex_indexer_at_time")
def datetimeindex_indexer_at_time(datetimeindex: str) -> Any:
    """Return index locations of values at particular time of day."""
    _instance = _get_object(datetimeindex)
    return _instance.indexer_at_time()

@mcp.tool(name="datetimeindex_indexer_between_time")
def datetimeindex_indexer_between_time(datetimeindex: str) -> Any:
    """Return index locations of values between particular times of day."""
    _instance = _get_object(datetimeindex)
    return _instance.indexer_between_time()

@mcp.tool(name="datetimeindex_infer_objects")
def datetimeindex_infer_objects(datetimeindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(datetimeindex)
    return _instance.infer_objects()

@mcp.tool(name="datetimeindex_insert")
def datetimeindex_insert(datetimeindex: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(datetimeindex)
    return _instance.insert()

@mcp.tool(name="datetimeindex_intersection")
def datetimeindex_intersection(datetimeindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(datetimeindex)
    return _instance.intersection()

@mcp.tool(name="datetimeindex_is_")
def datetimeindex_is_(datetimeindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(datetimeindex)
    return _instance.is_()

@mcp.tool(name="datetimeindex_is_boolean")
def datetimeindex_is_boolean(datetimeindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(datetimeindex)
    return _instance.is_boolean()

@mcp.tool(name="datetimeindex_is_categorical")
def datetimeindex_is_categorical(datetimeindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(datetimeindex)
    return _instance.is_categorical()

@mcp.tool(name="datetimeindex_is_floating")
def datetimeindex_is_floating(datetimeindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(datetimeindex)
    return _instance.is_floating()

@mcp.tool(name="datetimeindex_is_integer")
def datetimeindex_is_integer(datetimeindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(datetimeindex)
    return _instance.is_integer()

@mcp.tool(name="datetimeindex_is_interval")
def datetimeindex_is_interval(datetimeindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(datetimeindex)
    return _instance.is_interval()

@mcp.tool(name="datetimeindex_is_numeric")
def datetimeindex_is_numeric(datetimeindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(datetimeindex)
    return _instance.is_numeric()

@mcp.tool(name="datetimeindex_is_object")
def datetimeindex_is_object(datetimeindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(datetimeindex)
    return _instance.is_object()

@mcp.tool(name="datetimeindex_isin")
def datetimeindex_isin(datetimeindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(datetimeindex)
    return _instance.isin()

@mcp.tool(name="datetimeindex_isna")
def datetimeindex_isna(datetimeindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(datetimeindex)
    return _instance.isna()

@mcp.tool(name="datetimeindex_isnull")
def datetimeindex_isnull(datetimeindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(datetimeindex)
    return _instance.isnull()

@mcp.tool(name="datetimeindex_isocalendar")
def datetimeindex_isocalendar(datetimeindex: str) -> Any:
    """Calculate year, week, and day according to the ISO 8601 standard."""
    _instance = _get_object(datetimeindex)
    return _instance.isocalendar()

@mcp.tool(name="datetimeindex_item")
def datetimeindex_item(datetimeindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(datetimeindex)
    return _instance.item()

@mcp.tool(name="datetimeindex_join")
def datetimeindex_join(datetimeindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(datetimeindex)
    return _instance.join()

@mcp.tool(name="datetimeindex_map")
def datetimeindex_map(datetimeindex: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(datetimeindex)
    return _instance.map()

@mcp.tool(name="datetimeindex_max")
def datetimeindex_max(datetimeindex: str) -> Any:
    """Return the maximum value of the Index."""
    _instance = _get_object(datetimeindex)
    return _instance.max()

@mcp.tool(name="datetimeindex_mean")
def datetimeindex_mean(datetimeindex: str) -> Any:
    """Return the mean value of the Array."""
    _instance = _get_object(datetimeindex)
    return _instance.mean()

@mcp.tool(name="datetimeindex_memory_usage")
def datetimeindex_memory_usage(datetimeindex: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(datetimeindex)
    return _instance.memory_usage()

@mcp.tool(name="datetimeindex_min")
def datetimeindex_min(datetimeindex: str) -> Any:
    """Return the minimum value of the Index."""
    _instance = _get_object(datetimeindex)
    return _instance.min()

@mcp.tool(name="datetimeindex_month_name")
def datetimeindex_month_name(datetimeindex: str) -> Any:
    """Return the month names with specified locale."""
    _instance = _get_object(datetimeindex)
    return _instance.month_name()

@mcp.tool(name="datetimeindex_normalize")
def datetimeindex_normalize(datetimeindex: str) -> Any:
    """Convert times to midnight."""
    _instance = _get_object(datetimeindex)
    return _instance.normalize()

@mcp.tool(name="datetimeindex_notna")
def datetimeindex_notna(datetimeindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(datetimeindex)
    return _instance.notna()

@mcp.tool(name="datetimeindex_notnull")
def datetimeindex_notnull(datetimeindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(datetimeindex)
    return _instance.notnull()

@mcp.tool(name="datetimeindex_nunique")
def datetimeindex_nunique(datetimeindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(datetimeindex)
    return _instance.nunique()

@mcp.tool(name="datetimeindex_putmask")
def datetimeindex_putmask(datetimeindex: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(datetimeindex)
    return _instance.putmask()

@mcp.tool(name="datetimeindex_ravel")
def datetimeindex_ravel(datetimeindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(datetimeindex)
    return _instance.ravel()

@mcp.tool(name="datetimeindex_reindex")
def datetimeindex_reindex(datetimeindex: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(datetimeindex)
    return _instance.reindex()

@mcp.tool(name="datetimeindex_rename")
def datetimeindex_rename(datetimeindex: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(datetimeindex)
    return _instance.rename()

@mcp.tool(name="datetimeindex_repeat")
def datetimeindex_repeat(datetimeindex: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(datetimeindex)
    return _instance.repeat()

@mcp.tool(name="datetimeindex_round")
def datetimeindex_round(datetimeindex: str) -> Any:
    """Perform round operation on the data to the specified `freq`."""
    _instance = _get_object(datetimeindex)
    return _instance.round()

@mcp.tool(name="datetimeindex_searchsorted")
def datetimeindex_searchsorted(datetimeindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(datetimeindex)
    return _instance.searchsorted()

@mcp.tool(name="datetimeindex_set_names")
def datetimeindex_set_names(datetimeindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(datetimeindex)
    return _instance.set_names()

@mcp.tool(name="datetimeindex_shift")
def datetimeindex_shift(datetimeindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(datetimeindex)
    return _instance.shift()

@mcp.tool(name="datetimeindex_slice_indexer")
def datetimeindex_slice_indexer(datetimeindex: str) -> Any:
    """Return indexer for specified label slice."""
    _instance = _get_object(datetimeindex)
    return _instance.slice_indexer()

@mcp.tool(name="datetimeindex_slice_locs")
def datetimeindex_slice_locs(datetimeindex: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(datetimeindex)
    return _instance.slice_locs()

@mcp.tool(name="datetimeindex_snap")
def datetimeindex_snap(datetimeindex: str) -> Any:
    """Snap time stamps to nearest occurring frequency."""
    _instance = _get_object(datetimeindex)
    return _instance.snap()

@mcp.tool(name="datetimeindex_sort")
def datetimeindex_sort(datetimeindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(datetimeindex)
    return _instance.sort()

@mcp.tool(name="datetimeindex_sort_values")
def datetimeindex_sort_values(datetimeindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(datetimeindex)
    return _instance.sort_values()

@mcp.tool(name="datetimeindex_sortlevel")
def datetimeindex_sortlevel(datetimeindex: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(datetimeindex)
    return _instance.sortlevel()

@mcp.tool(name="datetimeindex_std")
def datetimeindex_std(datetimeindex: str) -> Any:
    """Return sample standard deviation over requested axis."""
    _instance = _get_object(datetimeindex)
    return _instance.std()

@mcp.tool(name="datetimeindex_strftime")
def datetimeindex_strftime(datetimeindex: str) -> Any:
    """Convert to Index using specified date_format."""
    _instance = _get_object(datetimeindex)
    return _instance.strftime()

@mcp.tool(name="datetimeindex_symmetric_difference")
def datetimeindex_symmetric_difference(datetimeindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(datetimeindex)
    return _instance.symmetric_difference()

@mcp.tool(name="datetimeindex_take")
def datetimeindex_take(datetimeindex: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(datetimeindex)
    return _instance.take()

@mcp.tool(name="datetimeindex_to_flat_index")
def datetimeindex_to_flat_index(datetimeindex: str) -> Any:
    """Identity method."""
    _instance = _get_object(datetimeindex)
    return _instance.to_flat_index()

@mcp.tool(name="datetimeindex_to_frame")
def datetimeindex_to_frame(datetimeindex: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(datetimeindex)
    return _instance.to_frame()

@mcp.tool(name="datetimeindex_to_julian_date")
def datetimeindex_to_julian_date(datetimeindex: str) -> Any:
    """Convert Datetime Array to float64 ndarray of Julian Dates."""
    _instance = _get_object(datetimeindex)
    return _instance.to_julian_date()

@mcp.tool(name="datetimeindex_to_list")
def datetimeindex_to_list(datetimeindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(datetimeindex)
    return _instance.to_list()

@mcp.tool(name="datetimeindex_to_numpy")
def datetimeindex_to_numpy(datetimeindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(datetimeindex)
    return _instance.to_numpy()

@mcp.tool(name="datetimeindex_to_period")
def datetimeindex_to_period(datetimeindex: str) -> Any:
    """Cast to PeriodArray/PeriodIndex at a particular frequency."""
    _instance = _get_object(datetimeindex)
    return _instance.to_period()

@mcp.tool(name="datetimeindex_to_pydatetime")
def datetimeindex_to_pydatetime(datetimeindex: str) -> Any:
    """Return an ndarray of ``datetime.datetime`` objects."""
    _instance = _get_object(datetimeindex)
    return _instance.to_pydatetime()

@mcp.tool(name="datetimeindex_to_series")
def datetimeindex_to_series(datetimeindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(datetimeindex)
    return _instance.to_series()

@mcp.tool(name="datetimeindex_tolist")
def datetimeindex_tolist(datetimeindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(datetimeindex)
    return _instance.tolist()

@mcp.tool(name="datetimeindex_transpose")
def datetimeindex_transpose(datetimeindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(datetimeindex)
    return _instance.transpose()

@mcp.tool(name="datetimeindex_tz_convert")
def datetimeindex_tz_convert(datetimeindex: str) -> Any:
    """Convert tz-aware Datetime Array/Index from one time zone to another."""
    _instance = _get_object(datetimeindex)
    return _instance.tz_convert()

@mcp.tool(name="datetimeindex_tz_localize")
def datetimeindex_tz_localize(datetimeindex: str) -> Any:
    """Localize tz-naive Datetime Array/Index to tz-aware Datetime Array/Index."""
    _instance = _get_object(datetimeindex)
    return _instance.tz_localize()

@mcp.tool(name="datetimeindex_union")
def datetimeindex_union(datetimeindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(datetimeindex)
    return _instance.union()

@mcp.tool(name="datetimeindex_unique")
def datetimeindex_unique(datetimeindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(datetimeindex)
    return _instance.unique()

@mcp.tool(name="datetimeindex_value_counts")
def datetimeindex_value_counts(datetimeindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(datetimeindex)
    return _instance.value_counts()

@mcp.tool(name="datetimeindex_view")
def datetimeindex_view(datetimeindex: str) -> Any:
    """Tool: datetimeindex_view"""
    _instance = _get_object(datetimeindex)
    return _instance.view()

@mcp.tool(name="datetimeindex_where")
def datetimeindex_where(datetimeindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(datetimeindex)
    return _instance.where()

@mcp.tool(name="datetimetzdtype_construct_array_type")
def datetimetzdtype_construct_array_type(datetimetzdtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(datetimetzdtype)
    return _instance.construct_array_type()

@mcp.tool(name="datetimetzdtype_construct_from_string")
def datetimetzdtype_construct_from_string(datetimetzdtype: str) -> Any:
    """Construct a DatetimeTZDtype from a string."""
    _instance = _get_object(datetimetzdtype)
    return _instance.construct_from_string()

@mcp.tool(name="datetimetzdtype_empty")
def datetimetzdtype_empty(datetimetzdtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(datetimetzdtype)
    return _instance.empty()

@mcp.tool(name="datetimetzdtype_is_dtype")
def datetimetzdtype_is_dtype(datetimetzdtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(datetimetzdtype)
    return _instance.is_dtype()

@mcp.tool(name="datetimetzdtype_reset_cache")
def datetimetzdtype_reset_cache(datetimetzdtype: str) -> Any:
    """clear the cache"""
    _instance = _get_object(datetimetzdtype)
    return _instance.reset_cache()

@mcp.tool(name="excelfile_close")
def excelfile_close(excelfile: str) -> Any:
    """close io if necessary"""
    _instance = _get_object(excelfile)
    return _instance.close()

@mcp.tool(name="excelfile_parse")
def excelfile_parse(excelfile: str) -> Any:
    """Parse specified sheet(s) into a DataFrame."""
    _instance = _get_object(excelfile)
    return _instance.parse()

@mcp.tool(name="excelwriter_check_extension")
def excelwriter_check_extension(excelwriter: str) -> Any:
    """checks that path's extension against the Writer's supported"""
    _instance = _get_object(excelwriter)
    return _instance.check_extension()

@mcp.tool(name="excelwriter_close")
def excelwriter_close(excelwriter: str) -> Any:
    """synonym for save, to make it more file-like"""
    _instance = _get_object(excelwriter)
    return _instance.close()

@mcp.tool(name="float32dtype_construct_array_type")
def float32dtype_construct_array_type(float32dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(float32dtype)
    return _instance.construct_array_type()

@mcp.tool(name="float32dtype_construct_from_string")
def float32dtype_construct_from_string(float32dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(float32dtype)
    return _instance.construct_from_string()

@mcp.tool(name="float32dtype_empty")
def float32dtype_empty(float32dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(float32dtype)
    return _instance.empty()

@mcp.tool(name="float32dtype_from_numpy_dtype")
def float32dtype_from_numpy_dtype(float32dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(float32dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="float32dtype_is_dtype")
def float32dtype_is_dtype(float32dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(float32dtype)
    return _instance.is_dtype()

@mcp.tool(name="float64dtype_construct_array_type")
def float64dtype_construct_array_type(float64dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(float64dtype)
    return _instance.construct_array_type()

@mcp.tool(name="float64dtype_construct_from_string")
def float64dtype_construct_from_string(float64dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(float64dtype)
    return _instance.construct_from_string()

@mcp.tool(name="float64dtype_empty")
def float64dtype_empty(float64dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(float64dtype)
    return _instance.empty()

@mcp.tool(name="float64dtype_from_numpy_dtype")
def float64dtype_from_numpy_dtype(float64dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(float64dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="float64dtype_is_dtype")
def float64dtype_is_dtype(float64dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(float64dtype)
    return _instance.is_dtype()

@mcp.tool(name="hdfstore_append")
def hdfstore_append(hdfstore: str) -> Any:
    """Append to Table in file."""
    _instance = _get_object(hdfstore)
    return _instance.append()

@mcp.tool(name="hdfstore_append_to_multiple")
def hdfstore_append_to_multiple(hdfstore: str) -> Any:
    """Append to multiple tables"""
    _instance = _get_object(hdfstore)
    return _instance.append_to_multiple()

@mcp.tool(name="hdfstore_close")
def hdfstore_close(hdfstore: str) -> Any:
    """Close the PyTables file handle"""
    _instance = _get_object(hdfstore)
    return _instance.close()

@mcp.tool(name="hdfstore_copy")
def hdfstore_copy(hdfstore: str) -> Any:
    """Copy the existing store to a new file, updating in place."""
    _instance = _get_object(hdfstore)
    return _instance.copy()

@mcp.tool(name="hdfstore_create_table_index")
def hdfstore_create_table_index(hdfstore: str) -> Any:
    """Create a pytables index on the table."""
    _instance = _get_object(hdfstore)
    return _instance.create_table_index()

@mcp.tool(name="hdfstore_flush")
def hdfstore_flush(hdfstore: str) -> Any:
    """Force all buffered modifications to be written to disk."""
    _instance = _get_object(hdfstore)
    return _instance.flush()

@mcp.tool(name="hdfstore_get")
def hdfstore_get(hdfstore: str) -> Any:
    """Retrieve pandas object stored in file."""
    _instance = _get_object(hdfstore)
    return _instance.get()

@mcp.tool(name="hdfstore_get_node")
def hdfstore_get_node(hdfstore: str) -> Any:
    """return the node with the key or None if it does not exist"""
    _instance = _get_object(hdfstore)
    return _instance.get_node()

@mcp.tool(name="hdfstore_get_storer")
def hdfstore_get_storer(hdfstore: str) -> Any:
    """return the storer object for a key, raise if not in the file"""
    _instance = _get_object(hdfstore)
    return _instance.get_storer()

@mcp.tool(name="hdfstore_groups")
def hdfstore_groups(hdfstore: str) -> Any:
    """Return a list of all the top-level nodes."""
    _instance = _get_object(hdfstore)
    return _instance.groups()

@mcp.tool(name="hdfstore_info")
def hdfstore_info(hdfstore: str) -> Any:
    """Print detailed information on the store."""
    _instance = _get_object(hdfstore)
    return _instance.info()

@mcp.tool(name="hdfstore_items")
def hdfstore_items(hdfstore: str) -> Any:
    """iterate on key->group"""
    _instance = _get_object(hdfstore)
    return _instance.items()

@mcp.tool(name="hdfstore_keys")
def hdfstore_keys(hdfstore: str) -> Any:
    """Return a list of keys corresponding to objects stored in HDFStore."""
    _instance = _get_object(hdfstore)
    return _instance.keys()

@mcp.tool(name="hdfstore_open")
def hdfstore_open(hdfstore: str) -> Any:
    """Open the file in the specified mode"""
    _instance = _get_object(hdfstore)
    return _instance.open()

@mcp.tool(name="hdfstore_put")
def hdfstore_put(hdfstore: str) -> Any:
    """Store object in HDFStore."""
    _instance = _get_object(hdfstore)
    return _instance.put()

@mcp.tool(name="hdfstore_remove")
def hdfstore_remove(hdfstore: str) -> Any:
    """Remove pandas object partially by specifying the where condition"""
    _instance = _get_object(hdfstore)
    return _instance.remove()

@mcp.tool(name="hdfstore_select")
def hdfstore_select(hdfstore: str) -> Any:
    """Retrieve pandas object stored in file, optionally based on where criteria."""
    _instance = _get_object(hdfstore)
    return _instance.select()

@mcp.tool(name="hdfstore_select_as_coordinates")
def hdfstore_select_as_coordinates(hdfstore: str) -> Any:
    """return the selection as an Index"""
    _instance = _get_object(hdfstore)
    return _instance.select_as_coordinates()

@mcp.tool(name="hdfstore_select_as_multiple")
def hdfstore_select_as_multiple(hdfstore: str) -> Any:
    """Retrieve pandas objects from multiple tables."""
    _instance = _get_object(hdfstore)
    return _instance.select_as_multiple()

@mcp.tool(name="hdfstore_select_column")
def hdfstore_select_column(hdfstore: str) -> Any:
    """return a single column from the table. This is generally only useful to"""
    _instance = _get_object(hdfstore)
    return _instance.select_column()

@mcp.tool(name="hdfstore_walk")
def hdfstore_walk(hdfstore: str) -> Any:
    """Walk the pytables group hierarchy for pandas objects."""
    _instance = _get_object(hdfstore)
    return _instance.walk()

@mcp.tool(name="index_all")
def index_all(index: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(index)
    return _instance.all()

@mcp.tool(name="index_any")
def index_any(index: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(index)
    return _instance.any()

@mcp.tool(name="index_append")
def index_append(index: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(index)
    return _instance.append()

@mcp.tool(name="index_argmax")
def index_argmax(index: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(index)
    return _instance.argmax()

@mcp.tool(name="index_argmin")
def index_argmin(index: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(index)
    return _instance.argmin()

@mcp.tool(name="index_argsort")
def index_argsort(index: str) -> Any:
    """Return the integer indices that would sort the index."""
    _instance = _get_object(index)
    return _instance.argsort()

@mcp.tool(name="index_asof")
def index_asof(index: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(index)
    return _instance.asof()

@mcp.tool(name="index_asof_locs")
def index_asof_locs(index: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(index)
    return _instance.asof_locs()

@mcp.tool(name="index_astype")
def index_astype(index: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(index)
    return _instance.astype()

@mcp.tool(name="index_copy")
def index_copy(index: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(index)
    return _instance.copy()

@mcp.tool(name="index_delete")
def index_delete(index: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(index)
    return _instance.delete()

@mcp.tool(name="index_diff")
def index_diff(index: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(index)
    return _instance.diff()

@mcp.tool(name="index_difference")
def index_difference(index: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(index)
    return _instance.difference()

@mcp.tool(name="index_drop")
def index_drop(index: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(index)
    return _instance.drop()

@mcp.tool(name="index_drop_duplicates")
def index_drop_duplicates(index: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(index)
    return _instance.drop_duplicates()

@mcp.tool(name="index_droplevel")
def index_droplevel(index: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(index)
    return _instance.droplevel()

@mcp.tool(name="index_dropna")
def index_dropna(index: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(index)
    return _instance.dropna()

@mcp.tool(name="index_duplicated")
def index_duplicated(index: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(index)
    return _instance.duplicated()

@mcp.tool(name="index_equals")
def index_equals(index: str) -> Any:
    """Determine if two Index object are equal."""
    _instance = _get_object(index)
    return _instance.equals()

@mcp.tool(name="index_factorize")
def index_factorize(index: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(index)
    return _instance.factorize()

@mcp.tool(name="index_fillna")
def index_fillna(index: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(index)
    return _instance.fillna()

@mcp.tool(name="index_format")
def index_format(index: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(index)
    return _instance.format()

@mcp.tool(name="index_get_indexer")
def index_get_indexer(index: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(index)
    return _instance.get_indexer()

@mcp.tool(name="index_get_indexer_for")
def index_get_indexer_for(index: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(index)
    return _instance.get_indexer_for()

@mcp.tool(name="index_get_indexer_non_unique")
def index_get_indexer_non_unique(index: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(index)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="index_get_level_values")
def index_get_level_values(index: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(index)
    return _instance.get_level_values()

@mcp.tool(name="index_get_loc")
def index_get_loc(index: str) -> Any:
    """Get integer location, slice or boolean mask for requested label."""
    _instance = _get_object(index)
    return _instance.get_loc()

@mcp.tool(name="index_get_slice_bound")
def index_get_slice_bound(index: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(index)
    return _instance.get_slice_bound()

@mcp.tool(name="index_groupby")
def index_groupby(index: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(index)
    return _instance.groupby()

@mcp.tool(name="index_holds_integer")
def index_holds_integer(index: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(index)
    return _instance.holds_integer()

@mcp.tool(name="index_identical")
def index_identical(index: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(index)
    return _instance.identical()

@mcp.tool(name="index_infer_objects")
def index_infer_objects(index: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(index)
    return _instance.infer_objects()

@mcp.tool(name="index_insert")
def index_insert(index: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(index)
    return _instance.insert()

@mcp.tool(name="index_intersection")
def index_intersection(index: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(index)
    return _instance.intersection()

@mcp.tool(name="index_is_")
def index_is_(index: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(index)
    return _instance.is_()

@mcp.tool(name="index_is_boolean")
def index_is_boolean(index: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(index)
    return _instance.is_boolean()

@mcp.tool(name="index_is_categorical")
def index_is_categorical(index: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(index)
    return _instance.is_categorical()

@mcp.tool(name="index_is_floating")
def index_is_floating(index: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(index)
    return _instance.is_floating()

@mcp.tool(name="index_is_integer")
def index_is_integer(index: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(index)
    return _instance.is_integer()

@mcp.tool(name="index_is_interval")
def index_is_interval(index: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(index)
    return _instance.is_interval()

@mcp.tool(name="index_is_numeric")
def index_is_numeric(index: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(index)
    return _instance.is_numeric()

@mcp.tool(name="index_is_object")
def index_is_object(index: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(index)
    return _instance.is_object()

@mcp.tool(name="index_isin")
def index_isin(index: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(index)
    return _instance.isin()

@mcp.tool(name="index_isna")
def index_isna(index: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(index)
    return _instance.isna()

@mcp.tool(name="index_isnull")
def index_isnull(index: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(index)
    return _instance.isnull()

@mcp.tool(name="index_item")
def index_item(index: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(index)
    return _instance.item()

@mcp.tool(name="index_join")
def index_join(index: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(index)
    return _instance.join()

@mcp.tool(name="index_map")
def index_map(index: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(index)
    return _instance.map()

@mcp.tool(name="index_max")
def index_max(index: str) -> Any:
    """Return the maximum value of the Index."""
    _instance = _get_object(index)
    return _instance.max()

@mcp.tool(name="index_memory_usage")
def index_memory_usage(index: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(index)
    return _instance.memory_usage()

@mcp.tool(name="index_min")
def index_min(index: str) -> Any:
    """Return the minimum value of the Index."""
    _instance = _get_object(index)
    return _instance.min()

@mcp.tool(name="index_notna")
def index_notna(index: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(index)
    return _instance.notna()

@mcp.tool(name="index_notnull")
def index_notnull(index: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(index)
    return _instance.notnull()

@mcp.tool(name="index_nunique")
def index_nunique(index: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(index)
    return _instance.nunique()

@mcp.tool(name="index_putmask")
def index_putmask(index: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(index)
    return _instance.putmask()

@mcp.tool(name="index_ravel")
def index_ravel(index: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(index)
    return _instance.ravel()

@mcp.tool(name="index_reindex")
def index_reindex(index: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(index)
    return _instance.reindex()

@mcp.tool(name="index_rename")
def index_rename(index: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(index)
    return _instance.rename()

@mcp.tool(name="index_repeat")
def index_repeat(index: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(index)
    return _instance.repeat()

@mcp.tool(name="index_round")
def index_round(index: str) -> Any:
    """Round each value in the Index to the given number of decimals."""
    _instance = _get_object(index)
    return _instance.round()

@mcp.tool(name="index_searchsorted")
def index_searchsorted(index: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(index)
    return _instance.searchsorted()

@mcp.tool(name="index_set_names")
def index_set_names(index: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(index)
    return _instance.set_names()

@mcp.tool(name="index_shift")
def index_shift(index: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(index)
    return _instance.shift()

@mcp.tool(name="index_slice_indexer")
def index_slice_indexer(index: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(index)
    return _instance.slice_indexer()

@mcp.tool(name="index_slice_locs")
def index_slice_locs(index: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(index)
    return _instance.slice_locs()

@mcp.tool(name="index_sort")
def index_sort(index: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(index)
    return _instance.sort()

@mcp.tool(name="index_sort_values")
def index_sort_values(index: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(index)
    return _instance.sort_values()

@mcp.tool(name="index_sortlevel")
def index_sortlevel(index: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(index)
    return _instance.sortlevel()

@mcp.tool(name="index_symmetric_difference")
def index_symmetric_difference(index: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(index)
    return _instance.symmetric_difference()

@mcp.tool(name="index_take")
def index_take(index: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(index)
    return _instance.take()

@mcp.tool(name="index_to_flat_index")
def index_to_flat_index(index: str) -> Any:
    """Identity method."""
    _instance = _get_object(index)
    return _instance.to_flat_index()

@mcp.tool(name="index_to_frame")
def index_to_frame(index: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(index)
    return _instance.to_frame()

@mcp.tool(name="index_to_list")
def index_to_list(index: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(index)
    return _instance.to_list()

@mcp.tool(name="index_to_numpy")
def index_to_numpy(index: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(index)
    return _instance.to_numpy()

@mcp.tool(name="index_to_series")
def index_to_series(index: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(index)
    return _instance.to_series()

@mcp.tool(name="index_tolist")
def index_tolist(index: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(index)
    return _instance.tolist()

@mcp.tool(name="index_transpose")
def index_transpose(index: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(index)
    return _instance.transpose()

@mcp.tool(name="index_union")
def index_union(index: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(index)
    return _instance.union()

@mcp.tool(name="index_unique")
def index_unique(index: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(index)
    return _instance.unique()

@mcp.tool(name="index_value_counts")
def index_value_counts(index: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(index)
    return _instance.value_counts()

@mcp.tool(name="index_view")
def index_view(index: str) -> Any:
    """Tool: index_view"""
    _instance = _get_object(index)
    return _instance.view()

@mcp.tool(name="index_where")
def index_where(index: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(index)
    return _instance.where()

@mcp.tool(name="int16dtype_construct_array_type")
def int16dtype_construct_array_type(int16dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(int16dtype)
    return _instance.construct_array_type()

@mcp.tool(name="int16dtype_construct_from_string")
def int16dtype_construct_from_string(int16dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(int16dtype)
    return _instance.construct_from_string()

@mcp.tool(name="int16dtype_empty")
def int16dtype_empty(int16dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(int16dtype)
    return _instance.empty()

@mcp.tool(name="int16dtype_from_numpy_dtype")
def int16dtype_from_numpy_dtype(int16dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(int16dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="int16dtype_is_dtype")
def int16dtype_is_dtype(int16dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(int16dtype)
    return _instance.is_dtype()

@mcp.tool(name="int32dtype_construct_array_type")
def int32dtype_construct_array_type(int32dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(int32dtype)
    return _instance.construct_array_type()

@mcp.tool(name="int32dtype_construct_from_string")
def int32dtype_construct_from_string(int32dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(int32dtype)
    return _instance.construct_from_string()

@mcp.tool(name="int32dtype_empty")
def int32dtype_empty(int32dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(int32dtype)
    return _instance.empty()

@mcp.tool(name="int32dtype_from_numpy_dtype")
def int32dtype_from_numpy_dtype(int32dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(int32dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="int32dtype_is_dtype")
def int32dtype_is_dtype(int32dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(int32dtype)
    return _instance.is_dtype()

@mcp.tool(name="int64dtype_construct_array_type")
def int64dtype_construct_array_type(int64dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(int64dtype)
    return _instance.construct_array_type()

@mcp.tool(name="int64dtype_construct_from_string")
def int64dtype_construct_from_string(int64dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(int64dtype)
    return _instance.construct_from_string()

@mcp.tool(name="int64dtype_empty")
def int64dtype_empty(int64dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(int64dtype)
    return _instance.empty()

@mcp.tool(name="int64dtype_from_numpy_dtype")
def int64dtype_from_numpy_dtype(int64dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(int64dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="int64dtype_is_dtype")
def int64dtype_is_dtype(int64dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(int64dtype)
    return _instance.is_dtype()

@mcp.tool(name="int8dtype_construct_array_type")
def int8dtype_construct_array_type(int8dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(int8dtype)
    return _instance.construct_array_type()

@mcp.tool(name="int8dtype_construct_from_string")
def int8dtype_construct_from_string(int8dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(int8dtype)
    return _instance.construct_from_string()

@mcp.tool(name="int8dtype_empty")
def int8dtype_empty(int8dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(int8dtype)
    return _instance.empty()

@mcp.tool(name="int8dtype_from_numpy_dtype")
def int8dtype_from_numpy_dtype(int8dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(int8dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="int8dtype_is_dtype")
def int8dtype_is_dtype(int8dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(int8dtype)
    return _instance.is_dtype()

@mcp.tool(name="interval_overlaps")
def interval_overlaps(interval: str) -> Any:
    """Check whether two Interval objects overlap."""
    _instance = _get_object(interval)
    return _instance.overlaps()

@mcp.tool(name="intervaldtype_construct_array_type")
def intervaldtype_construct_array_type(intervaldtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(intervaldtype)
    return _instance.construct_array_type()

@mcp.tool(name="intervaldtype_construct_from_string")
def intervaldtype_construct_from_string(intervaldtype: str) -> Any:
    """attempt to construct this type from a string, raise a TypeError"""
    _instance = _get_object(intervaldtype)
    return _instance.construct_from_string()

@mcp.tool(name="intervaldtype_empty")
def intervaldtype_empty(intervaldtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(intervaldtype)
    return _instance.empty()

@mcp.tool(name="intervaldtype_is_dtype")
def intervaldtype_is_dtype(intervaldtype: str) -> Any:
    """Return a boolean if we if the passed type is an actual dtype that we"""
    _instance = _get_object(intervaldtype)
    return _instance.is_dtype()

@mcp.tool(name="intervaldtype_reset_cache")
def intervaldtype_reset_cache(intervaldtype: str) -> Any:
    """clear the cache"""
    _instance = _get_object(intervaldtype)
    return _instance.reset_cache()

@mcp.tool(name="intervalindex_all")
def intervalindex_all(intervalindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(intervalindex)
    return _instance.all()

@mcp.tool(name="intervalindex_any")
def intervalindex_any(intervalindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(intervalindex)
    return _instance.any()

@mcp.tool(name="intervalindex_append")
def intervalindex_append(intervalindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(intervalindex)
    return _instance.append()

@mcp.tool(name="intervalindex_argmax")
def intervalindex_argmax(intervalindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(intervalindex)
    return _instance.argmax()

@mcp.tool(name="intervalindex_argmin")
def intervalindex_argmin(intervalindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(intervalindex)
    return _instance.argmin()

@mcp.tool(name="intervalindex_argsort")
def intervalindex_argsort(intervalindex: str) -> Any:
    """Return the integer indices that would sort the index."""
    _instance = _get_object(intervalindex)
    return _instance.argsort()

@mcp.tool(name="intervalindex_asof")
def intervalindex_asof(intervalindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(intervalindex)
    return _instance.asof()

@mcp.tool(name="intervalindex_asof_locs")
def intervalindex_asof_locs(intervalindex: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(intervalindex)
    return _instance.asof_locs()

@mcp.tool(name="intervalindex_astype")
def intervalindex_astype(intervalindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(intervalindex)
    return _instance.astype()

@mcp.tool(name="intervalindex_contains")
def intervalindex_contains(intervalindex: str) -> Any:
    """Check elementwise if the Intervals contain the value."""
    _instance = _get_object(intervalindex)
    return _instance.contains()

@mcp.tool(name="intervalindex_copy")
def intervalindex_copy(intervalindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(intervalindex)
    return _instance.copy()

@mcp.tool(name="intervalindex_delete")
def intervalindex_delete(intervalindex: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(intervalindex)
    return _instance.delete()

@mcp.tool(name="intervalindex_diff")
def intervalindex_diff(intervalindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(intervalindex)
    return _instance.diff()

@mcp.tool(name="intervalindex_difference")
def intervalindex_difference(intervalindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(intervalindex)
    return _instance.difference()

@mcp.tool(name="intervalindex_drop")
def intervalindex_drop(intervalindex: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(intervalindex)
    return _instance.drop()

@mcp.tool(name="intervalindex_drop_duplicates")
def intervalindex_drop_duplicates(intervalindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(intervalindex)
    return _instance.drop_duplicates()

@mcp.tool(name="intervalindex_droplevel")
def intervalindex_droplevel(intervalindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(intervalindex)
    return _instance.droplevel()

@mcp.tool(name="intervalindex_dropna")
def intervalindex_dropna(intervalindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(intervalindex)
    return _instance.dropna()

@mcp.tool(name="intervalindex_duplicated")
def intervalindex_duplicated(intervalindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(intervalindex)
    return _instance.duplicated()

@mcp.tool(name="intervalindex_equals")
def intervalindex_equals(intervalindex: str) -> Any:
    """Determine if two Index object are equal."""
    _instance = _get_object(intervalindex)
    return _instance.equals()

@mcp.tool(name="intervalindex_factorize")
def intervalindex_factorize(intervalindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(intervalindex)
    return _instance.factorize()

@mcp.tool(name="intervalindex_fillna")
def intervalindex_fillna(intervalindex: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(intervalindex)
    return _instance.fillna()

@mcp.tool(name="intervalindex_format")
def intervalindex_format(intervalindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(intervalindex)
    return _instance.format()

@mcp.tool(name="intervalindex_from_arrays")
def intervalindex_from_arrays(intervalindex: str) -> Any:
    """Construct from two arrays defining the left and right bounds."""
    _instance = _get_object(intervalindex)
    return _instance.from_arrays()

@mcp.tool(name="intervalindex_from_breaks")
def intervalindex_from_breaks(intervalindex: str) -> Any:
    """Construct an IntervalIndex from an array of splits."""
    _instance = _get_object(intervalindex)
    return _instance.from_breaks()

@mcp.tool(name="intervalindex_from_tuples")
def intervalindex_from_tuples(intervalindex: str) -> Any:
    """Construct an IntervalIndex from an array-like of tuples."""
    _instance = _get_object(intervalindex)
    return _instance.from_tuples()

@mcp.tool(name="intervalindex_get_indexer")
def intervalindex_get_indexer(intervalindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(intervalindex)
    return _instance.get_indexer()

@mcp.tool(name="intervalindex_get_indexer_for")
def intervalindex_get_indexer_for(intervalindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(intervalindex)
    return _instance.get_indexer_for()

@mcp.tool(name="intervalindex_get_indexer_non_unique")
def intervalindex_get_indexer_non_unique(intervalindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(intervalindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="intervalindex_get_level_values")
def intervalindex_get_level_values(intervalindex: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(intervalindex)
    return _instance.get_level_values()

@mcp.tool(name="intervalindex_get_loc")
def intervalindex_get_loc(intervalindex: str) -> Any:
    """Get integer location, slice or boolean mask for requested label."""
    _instance = _get_object(intervalindex)
    return _instance.get_loc()

@mcp.tool(name="intervalindex_get_slice_bound")
def intervalindex_get_slice_bound(intervalindex: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(intervalindex)
    return _instance.get_slice_bound()

@mcp.tool(name="intervalindex_groupby")
def intervalindex_groupby(intervalindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(intervalindex)
    return _instance.groupby()

@mcp.tool(name="intervalindex_holds_integer")
def intervalindex_holds_integer(intervalindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(intervalindex)
    return _instance.holds_integer()

@mcp.tool(name="intervalindex_identical")
def intervalindex_identical(intervalindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(intervalindex)
    return _instance.identical()

@mcp.tool(name="intervalindex_infer_objects")
def intervalindex_infer_objects(intervalindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(intervalindex)
    return _instance.infer_objects()

@mcp.tool(name="intervalindex_insert")
def intervalindex_insert(intervalindex: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(intervalindex)
    return _instance.insert()

@mcp.tool(name="intervalindex_intersection")
def intervalindex_intersection(intervalindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(intervalindex)
    return _instance.intersection()

@mcp.tool(name="intervalindex_is_")
def intervalindex_is_(intervalindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(intervalindex)
    return _instance.is_()

@mcp.tool(name="intervalindex_is_boolean")
def intervalindex_is_boolean(intervalindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(intervalindex)
    return _instance.is_boolean()

@mcp.tool(name="intervalindex_is_categorical")
def intervalindex_is_categorical(intervalindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(intervalindex)
    return _instance.is_categorical()

@mcp.tool(name="intervalindex_is_floating")
def intervalindex_is_floating(intervalindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(intervalindex)
    return _instance.is_floating()

@mcp.tool(name="intervalindex_is_integer")
def intervalindex_is_integer(intervalindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(intervalindex)
    return _instance.is_integer()

@mcp.tool(name="intervalindex_is_interval")
def intervalindex_is_interval(intervalindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(intervalindex)
    return _instance.is_interval()

@mcp.tool(name="intervalindex_is_numeric")
def intervalindex_is_numeric(intervalindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(intervalindex)
    return _instance.is_numeric()

@mcp.tool(name="intervalindex_is_object")
def intervalindex_is_object(intervalindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(intervalindex)
    return _instance.is_object()

@mcp.tool(name="intervalindex_isin")
def intervalindex_isin(intervalindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(intervalindex)
    return _instance.isin()

@mcp.tool(name="intervalindex_isna")
def intervalindex_isna(intervalindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(intervalindex)
    return _instance.isna()

@mcp.tool(name="intervalindex_isnull")
def intervalindex_isnull(intervalindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(intervalindex)
    return _instance.isnull()

@mcp.tool(name="intervalindex_item")
def intervalindex_item(intervalindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(intervalindex)
    return _instance.item()

@mcp.tool(name="intervalindex_join")
def intervalindex_join(intervalindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(intervalindex)
    return _instance.join()

@mcp.tool(name="intervalindex_map")
def intervalindex_map(intervalindex: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(intervalindex)
    return _instance.map()

@mcp.tool(name="intervalindex_max")
def intervalindex_max(intervalindex: str) -> Any:
    """Return the maximum value of the Index."""
    _instance = _get_object(intervalindex)
    return _instance.max()

@mcp.tool(name="intervalindex_memory_usage")
def intervalindex_memory_usage(intervalindex: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(intervalindex)
    return _instance.memory_usage()

@mcp.tool(name="intervalindex_min")
def intervalindex_min(intervalindex: str) -> Any:
    """Return the minimum value of the Index."""
    _instance = _get_object(intervalindex)
    return _instance.min()

@mcp.tool(name="intervalindex_notna")
def intervalindex_notna(intervalindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(intervalindex)
    return _instance.notna()

@mcp.tool(name="intervalindex_notnull")
def intervalindex_notnull(intervalindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(intervalindex)
    return _instance.notnull()

@mcp.tool(name="intervalindex_nunique")
def intervalindex_nunique(intervalindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(intervalindex)
    return _instance.nunique()

@mcp.tool(name="intervalindex_overlaps")
def intervalindex_overlaps(intervalindex: str) -> Any:
    """Check elementwise if an Interval overlaps the values in the IntervalArray."""
    _instance = _get_object(intervalindex)
    return _instance.overlaps()

@mcp.tool(name="intervalindex_putmask")
def intervalindex_putmask(intervalindex: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(intervalindex)
    return _instance.putmask()

@mcp.tool(name="intervalindex_ravel")
def intervalindex_ravel(intervalindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(intervalindex)
    return _instance.ravel()

@mcp.tool(name="intervalindex_reindex")
def intervalindex_reindex(intervalindex: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(intervalindex)
    return _instance.reindex()

@mcp.tool(name="intervalindex_rename")
def intervalindex_rename(intervalindex: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(intervalindex)
    return _instance.rename()

@mcp.tool(name="intervalindex_repeat")
def intervalindex_repeat(intervalindex: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(intervalindex)
    return _instance.repeat()

@mcp.tool(name="intervalindex_round")
def intervalindex_round(intervalindex: str) -> Any:
    """Round each value in the Index to the given number of decimals."""
    _instance = _get_object(intervalindex)
    return _instance.round()

@mcp.tool(name="intervalindex_searchsorted")
def intervalindex_searchsorted(intervalindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(intervalindex)
    return _instance.searchsorted()

@mcp.tool(name="intervalindex_set_closed")
def intervalindex_set_closed(intervalindex: str) -> Any:
    """Return an identical IntervalArray closed on the specified side."""
    _instance = _get_object(intervalindex)
    return _instance.set_closed()

@mcp.tool(name="intervalindex_set_names")
def intervalindex_set_names(intervalindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(intervalindex)
    return _instance.set_names()

@mcp.tool(name="intervalindex_shift")
def intervalindex_shift(intervalindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(intervalindex)
    return _instance.shift()

@mcp.tool(name="intervalindex_slice_indexer")
def intervalindex_slice_indexer(intervalindex: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(intervalindex)
    return _instance.slice_indexer()

@mcp.tool(name="intervalindex_slice_locs")
def intervalindex_slice_locs(intervalindex: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(intervalindex)
    return _instance.slice_locs()

@mcp.tool(name="intervalindex_sort")
def intervalindex_sort(intervalindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(intervalindex)
    return _instance.sort()

@mcp.tool(name="intervalindex_sort_values")
def intervalindex_sort_values(intervalindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(intervalindex)
    return _instance.sort_values()

@mcp.tool(name="intervalindex_sortlevel")
def intervalindex_sortlevel(intervalindex: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(intervalindex)
    return _instance.sortlevel()

@mcp.tool(name="intervalindex_symmetric_difference")
def intervalindex_symmetric_difference(intervalindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(intervalindex)
    return _instance.symmetric_difference()

@mcp.tool(name="intervalindex_take")
def intervalindex_take(intervalindex: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(intervalindex)
    return _instance.take()

@mcp.tool(name="intervalindex_to_flat_index")
def intervalindex_to_flat_index(intervalindex: str) -> Any:
    """Identity method."""
    _instance = _get_object(intervalindex)
    return _instance.to_flat_index()

@mcp.tool(name="intervalindex_to_frame")
def intervalindex_to_frame(intervalindex: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(intervalindex)
    return _instance.to_frame()

@mcp.tool(name="intervalindex_to_list")
def intervalindex_to_list(intervalindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(intervalindex)
    return _instance.to_list()

@mcp.tool(name="intervalindex_to_numpy")
def intervalindex_to_numpy(intervalindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(intervalindex)
    return _instance.to_numpy()

@mcp.tool(name="intervalindex_to_series")
def intervalindex_to_series(intervalindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(intervalindex)
    return _instance.to_series()

@mcp.tool(name="intervalindex_to_tuples")
def intervalindex_to_tuples(intervalindex: str) -> Any:
    """Return an ndarray (if self is IntervalArray) or Index (if self is IntervalIndex) of tuples of the form (left, right)."""
    _instance = _get_object(intervalindex)
    return _instance.to_tuples()

@mcp.tool(name="intervalindex_tolist")
def intervalindex_tolist(intervalindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(intervalindex)
    return _instance.tolist()

@mcp.tool(name="intervalindex_transpose")
def intervalindex_transpose(intervalindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(intervalindex)
    return _instance.transpose()

@mcp.tool(name="intervalindex_union")
def intervalindex_union(intervalindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(intervalindex)
    return _instance.union()

@mcp.tool(name="intervalindex_unique")
def intervalindex_unique(intervalindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(intervalindex)
    return _instance.unique()

@mcp.tool(name="intervalindex_value_counts")
def intervalindex_value_counts(intervalindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(intervalindex)
    return _instance.value_counts()

@mcp.tool(name="intervalindex_view")
def intervalindex_view(intervalindex: str) -> Any:
    """Tool: intervalindex_view"""
    _instance = _get_object(intervalindex)
    return _instance.view()

@mcp.tool(name="intervalindex_where")
def intervalindex_where(intervalindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(intervalindex)
    return _instance.where()

@mcp.tool(name="multiindex_all")
def multiindex_all(multiindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(multiindex)
    return _instance.all()

@mcp.tool(name="multiindex_any")
def multiindex_any(multiindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(multiindex)
    return _instance.any()

@mcp.tool(name="multiindex_append")
def multiindex_append(multiindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(multiindex)
    return _instance.append()

@mcp.tool(name="multiindex_argmax")
def multiindex_argmax(multiindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(multiindex)
    return _instance.argmax()

@mcp.tool(name="multiindex_argmin")
def multiindex_argmin(multiindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(multiindex)
    return _instance.argmin()

@mcp.tool(name="multiindex_argsort")
def multiindex_argsort(multiindex: str) -> Any:
    """Return the integer indices that would sort the index."""
    _instance = _get_object(multiindex)
    return _instance.argsort()

@mcp.tool(name="multiindex_asof")
def multiindex_asof(multiindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(multiindex)
    return _instance.asof()

@mcp.tool(name="multiindex_asof_locs")
def multiindex_asof_locs(multiindex: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(multiindex)
    return _instance.asof_locs()

@mcp.tool(name="multiindex_astype")
def multiindex_astype(multiindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(multiindex)
    return _instance.astype()

@mcp.tool(name="multiindex_copy")
def multiindex_copy(multiindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(multiindex)
    return _instance.copy()

@mcp.tool(name="multiindex_delete")
def multiindex_delete(multiindex: str) -> Any:
    """Make new index with passed location deleted"""
    _instance = _get_object(multiindex)
    return _instance.delete()

@mcp.tool(name="multiindex_diff")
def multiindex_diff(multiindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(multiindex)
    return _instance.diff()

@mcp.tool(name="multiindex_difference")
def multiindex_difference(multiindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(multiindex)
    return _instance.difference()

@mcp.tool(name="multiindex_drop")
def multiindex_drop(multiindex: str) -> Any:
    """Make a new :class:`pandas.MultiIndex` with the passed list of codes deleted."""
    _instance = _get_object(multiindex)
    return _instance.drop()

@mcp.tool(name="multiindex_drop_duplicates")
def multiindex_drop_duplicates(multiindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(multiindex)
    return _instance.drop_duplicates()

@mcp.tool(name="multiindex_droplevel")
def multiindex_droplevel(multiindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(multiindex)
    return _instance.droplevel()

@mcp.tool(name="multiindex_dropna")
def multiindex_dropna(multiindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(multiindex)
    return _instance.dropna()

@mcp.tool(name="multiindex_duplicated")
def multiindex_duplicated(multiindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(multiindex)
    return _instance.duplicated()

@mcp.tool(name="multiindex_equal_levels")
def multiindex_equal_levels(multiindex: str) -> Any:
    """Return True if the levels of both MultiIndex objects are the same"""
    _instance = _get_object(multiindex)
    return _instance.equal_levels()

@mcp.tool(name="multiindex_equals")
def multiindex_equals(multiindex: str) -> Any:
    """Determines if two MultiIndex objects have the same labeling information"""
    _instance = _get_object(multiindex)
    return _instance.equals()

@mcp.tool(name="multiindex_factorize")
def multiindex_factorize(multiindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(multiindex)
    return _instance.factorize()

@mcp.tool(name="multiindex_fillna")
def multiindex_fillna(multiindex: str) -> Any:
    """fillna is not implemented for MultiIndex"""
    _instance = _get_object(multiindex)
    return _instance.fillna()

@mcp.tool(name="multiindex_format")
def multiindex_format(multiindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(multiindex)
    return _instance.format()

@mcp.tool(name="multiindex_from_arrays")
def multiindex_from_arrays(multiindex: str) -> Any:
    """Convert arrays to MultiIndex."""
    _instance = _get_object(multiindex)
    return _instance.from_arrays()

@mcp.tool(name="multiindex_from_frame")
def multiindex_from_frame(multiindex: str) -> Any:
    """Make a MultiIndex from a DataFrame."""
    _instance = _get_object(multiindex)
    return _instance.from_frame()

@mcp.tool(name="multiindex_from_product")
def multiindex_from_product(multiindex: str) -> Any:
    """Make a MultiIndex from the cartesian product of multiple iterables."""
    _instance = _get_object(multiindex)
    return _instance.from_product()

@mcp.tool(name="multiindex_from_tuples")
def multiindex_from_tuples(multiindex: str) -> Any:
    """Convert list of tuples to MultiIndex."""
    _instance = _get_object(multiindex)
    return _instance.from_tuples()

@mcp.tool(name="multiindex_get_indexer")
def multiindex_get_indexer(multiindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(multiindex)
    return _instance.get_indexer()

@mcp.tool(name="multiindex_get_indexer_for")
def multiindex_get_indexer_for(multiindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(multiindex)
    return _instance.get_indexer_for()

@mcp.tool(name="multiindex_get_indexer_non_unique")
def multiindex_get_indexer_non_unique(multiindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(multiindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="multiindex_get_level_values")
def multiindex_get_level_values(multiindex: str) -> Any:
    """Return vector of label values for requested level."""
    _instance = _get_object(multiindex)
    return _instance.get_level_values()

@mcp.tool(name="multiindex_get_loc")
def multiindex_get_loc(multiindex: str) -> Any:
    """Get location for a label or a tuple of labels."""
    _instance = _get_object(multiindex)
    return _instance.get_loc()

@mcp.tool(name="multiindex_get_loc_level")
def multiindex_get_loc_level(multiindex: str) -> Any:
    """Get location and sliced index for requested label(s)/level(s)."""
    _instance = _get_object(multiindex)
    return _instance.get_loc_level()

@mcp.tool(name="multiindex_get_locs")
def multiindex_get_locs(multiindex: str) -> Any:
    """Get location for a sequence of labels."""
    _instance = _get_object(multiindex)
    return _instance.get_locs()

@mcp.tool(name="multiindex_get_slice_bound")
def multiindex_get_slice_bound(multiindex: str) -> Any:
    """For an ordered MultiIndex, compute slice bound"""
    _instance = _get_object(multiindex)
    return _instance.get_slice_bound()

@mcp.tool(name="multiindex_groupby")
def multiindex_groupby(multiindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(multiindex)
    return _instance.groupby()

@mcp.tool(name="multiindex_holds_integer")
def multiindex_holds_integer(multiindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(multiindex)
    return _instance.holds_integer()

@mcp.tool(name="multiindex_identical")
def multiindex_identical(multiindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(multiindex)
    return _instance.identical()

@mcp.tool(name="multiindex_infer_objects")
def multiindex_infer_objects(multiindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(multiindex)
    return _instance.infer_objects()

@mcp.tool(name="multiindex_insert")
def multiindex_insert(multiindex: str) -> Any:
    """Make new MultiIndex inserting new item at location"""
    _instance = _get_object(multiindex)
    return _instance.insert()

@mcp.tool(name="multiindex_intersection")
def multiindex_intersection(multiindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(multiindex)
    return _instance.intersection()

@mcp.tool(name="multiindex_is_")
def multiindex_is_(multiindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(multiindex)
    return _instance.is_()

@mcp.tool(name="multiindex_is_boolean")
def multiindex_is_boolean(multiindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(multiindex)
    return _instance.is_boolean()

@mcp.tool(name="multiindex_is_categorical")
def multiindex_is_categorical(multiindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(multiindex)
    return _instance.is_categorical()

@mcp.tool(name="multiindex_is_floating")
def multiindex_is_floating(multiindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(multiindex)
    return _instance.is_floating()

@mcp.tool(name="multiindex_is_integer")
def multiindex_is_integer(multiindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(multiindex)
    return _instance.is_integer()

@mcp.tool(name="multiindex_is_interval")
def multiindex_is_interval(multiindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(multiindex)
    return _instance.is_interval()

@mcp.tool(name="multiindex_is_numeric")
def multiindex_is_numeric(multiindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(multiindex)
    return _instance.is_numeric()

@mcp.tool(name="multiindex_is_object")
def multiindex_is_object(multiindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(multiindex)
    return _instance.is_object()

@mcp.tool(name="multiindex_isin")
def multiindex_isin(multiindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(multiindex)
    return _instance.isin()

@mcp.tool(name="multiindex_isna")
def multiindex_isna(multiindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(multiindex)
    return _instance.isna()

@mcp.tool(name="multiindex_isnull")
def multiindex_isnull(multiindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(multiindex)
    return _instance.isnull()

@mcp.tool(name="multiindex_item")
def multiindex_item(multiindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(multiindex)
    return _instance.item()

@mcp.tool(name="multiindex_join")
def multiindex_join(multiindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(multiindex)
    return _instance.join()

@mcp.tool(name="multiindex_map")
def multiindex_map(multiindex: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(multiindex)
    return _instance.map()

@mcp.tool(name="multiindex_max")
def multiindex_max(multiindex: str) -> Any:
    """Return the maximum value of the Index."""
    _instance = _get_object(multiindex)
    return _instance.max()

@mcp.tool(name="multiindex_memory_usage")
def multiindex_memory_usage(multiindex: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(multiindex)
    return _instance.memory_usage()

@mcp.tool(name="multiindex_min")
def multiindex_min(multiindex: str) -> Any:
    """Return the minimum value of the Index."""
    _instance = _get_object(multiindex)
    return _instance.min()

@mcp.tool(name="multiindex_notna")
def multiindex_notna(multiindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(multiindex)
    return _instance.notna()

@mcp.tool(name="multiindex_notnull")
def multiindex_notnull(multiindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(multiindex)
    return _instance.notnull()

@mcp.tool(name="multiindex_nunique")
def multiindex_nunique(multiindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(multiindex)
    return _instance.nunique()

@mcp.tool(name="multiindex_putmask")
def multiindex_putmask(multiindex: str) -> Any:
    """Return a new MultiIndex of the values set with the mask."""
    _instance = _get_object(multiindex)
    return _instance.putmask()

@mcp.tool(name="multiindex_ravel")
def multiindex_ravel(multiindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(multiindex)
    return _instance.ravel()

@mcp.tool(name="multiindex_reindex")
def multiindex_reindex(multiindex: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(multiindex)
    return _instance.reindex()

@mcp.tool(name="multiindex_remove_unused_levels")
def multiindex_remove_unused_levels(multiindex: str) -> Any:
    """Create new MultiIndex from current that removes unused levels."""
    _instance = _get_object(multiindex)
    return _instance.remove_unused_levels()

@mcp.tool(name="multiindex_rename")
def multiindex_rename(multiindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(multiindex)
    return _instance.rename()

@mcp.tool(name="multiindex_reorder_levels")
def multiindex_reorder_levels(multiindex: str) -> Any:
    """Rearrange levels using input order. May not drop or duplicate levels."""
    _instance = _get_object(multiindex)
    return _instance.reorder_levels()

@mcp.tool(name="multiindex_repeat")
def multiindex_repeat(multiindex: str) -> Any:
    """Repeat elements of a MultiIndex."""
    _instance = _get_object(multiindex)
    return _instance.repeat()

@mcp.tool(name="multiindex_round")
def multiindex_round(multiindex: str) -> Any:
    """Round each value in the Index to the given number of decimals."""
    _instance = _get_object(multiindex)
    return _instance.round()

@mcp.tool(name="multiindex_searchsorted")
def multiindex_searchsorted(multiindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(multiindex)
    return _instance.searchsorted()

@mcp.tool(name="multiindex_set_codes")
def multiindex_set_codes(multiindex: str) -> Any:
    """Set new codes on MultiIndex. Defaults to returning new index."""
    _instance = _get_object(multiindex)
    return _instance.set_codes()

@mcp.tool(name="multiindex_set_levels")
def multiindex_set_levels(multiindex: str) -> Any:
    """Set new levels on MultiIndex. Defaults to returning new index."""
    _instance = _get_object(multiindex)
    return _instance.set_levels()

@mcp.tool(name="multiindex_set_names")
def multiindex_set_names(multiindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(multiindex)
    return _instance.set_names()

@mcp.tool(name="multiindex_shift")
def multiindex_shift(multiindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(multiindex)
    return _instance.shift()

@mcp.tool(name="multiindex_slice_indexer")
def multiindex_slice_indexer(multiindex: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(multiindex)
    return _instance.slice_indexer()

@mcp.tool(name="multiindex_slice_locs")
def multiindex_slice_locs(multiindex: str) -> Any:
    """For an ordered MultiIndex, compute the slice locations for input"""
    _instance = _get_object(multiindex)
    return _instance.slice_locs()

@mcp.tool(name="multiindex_sort")
def multiindex_sort(multiindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(multiindex)
    return _instance.sort()

@mcp.tool(name="multiindex_sort_values")
def multiindex_sort_values(multiindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(multiindex)
    return _instance.sort_values()

@mcp.tool(name="multiindex_sortlevel")
def multiindex_sortlevel(multiindex: str) -> Any:
    """Sort MultiIndex at the requested level."""
    _instance = _get_object(multiindex)
    return _instance.sortlevel()

@mcp.tool(name="multiindex_swaplevel")
def multiindex_swaplevel(multiindex: str) -> Any:
    """Swap level i with level j."""
    _instance = _get_object(multiindex)
    return _instance.swaplevel()

@mcp.tool(name="multiindex_symmetric_difference")
def multiindex_symmetric_difference(multiindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(multiindex)
    return _instance.symmetric_difference()

@mcp.tool(name="multiindex_take")
def multiindex_take(multiindex: str) -> Any:
    """Return a new MultiIndex of the values selected by the indices."""
    _instance = _get_object(multiindex)
    return _instance.take()

@mcp.tool(name="multiindex_to_flat_index")
def multiindex_to_flat_index(multiindex: str) -> Any:
    """Convert a MultiIndex to an Index of Tuples containing the level values."""
    _instance = _get_object(multiindex)
    return _instance.to_flat_index()

@mcp.tool(name="multiindex_to_frame")
def multiindex_to_frame(multiindex: str) -> Any:
    """Create a DataFrame with the levels of the MultiIndex as columns."""
    _instance = _get_object(multiindex)
    return _instance.to_frame()

@mcp.tool(name="multiindex_to_list")
def multiindex_to_list(multiindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(multiindex)
    return _instance.to_list()

@mcp.tool(name="multiindex_to_numpy")
def multiindex_to_numpy(multiindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(multiindex)
    return _instance.to_numpy()

@mcp.tool(name="multiindex_to_series")
def multiindex_to_series(multiindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(multiindex)
    return _instance.to_series()

@mcp.tool(name="multiindex_tolist")
def multiindex_tolist(multiindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(multiindex)
    return _instance.tolist()

@mcp.tool(name="multiindex_transpose")
def multiindex_transpose(multiindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(multiindex)
    return _instance.transpose()

@mcp.tool(name="multiindex_truncate")
def multiindex_truncate(multiindex: str) -> Any:
    """Slice index between two labels / tuples, return new MultiIndex."""
    _instance = _get_object(multiindex)
    return _instance.truncate()

@mcp.tool(name="multiindex_union")
def multiindex_union(multiindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(multiindex)
    return _instance.union()

@mcp.tool(name="multiindex_unique")
def multiindex_unique(multiindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(multiindex)
    return _instance.unique()

@mcp.tool(name="multiindex_value_counts")
def multiindex_value_counts(multiindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(multiindex)
    return _instance.value_counts()

@mcp.tool(name="multiindex_view")
def multiindex_view(multiindex: str) -> Any:
    """this is defined as a copy with the same identity"""
    _instance = _get_object(multiindex)
    return _instance.view()

@mcp.tool(name="multiindex_where")
def multiindex_where(multiindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(multiindex)
    return _instance.where()

@mcp.tool(name="namedagg_count")
def namedagg_count(namedagg: str, value: Any) -> Any:
    """Return number of occurrences of value."""
    _instance = _get_object(namedagg)
    return _instance.count(value=value)

@mcp.tool(name="namedagg_index")
def namedagg_index(namedagg: str, value: Any, start: Any = 0, stop: Any = None) -> Any:
    """Return first index of value."""
    _instance = _get_object(namedagg)
    return _instance.index(value=value, start=start, stop=stop)

@mcp.tool(name="period_asfreq")
def period_asfreq(period: str) -> Any:
    """Convert Period to desired frequency, at the start or end of the interval."""
    _instance = _get_object(period)
    return _instance.asfreq()

@mcp.tool(name="period_now")
def period_now(period: str) -> Any:
    """Return the period of now's date."""
    _instance = _get_object(period)
    return _instance.now()

@mcp.tool(name="period_strftime")
def period_strftime(period: str) -> Any:
    """Returns a formatted string representation of the :class:`Period`."""
    _instance = _get_object(period)
    return _instance.strftime()

@mcp.tool(name="period_to_timestamp")
def period_to_timestamp(period: str) -> Any:
    """Return the Timestamp representation of the Period."""
    _instance = _get_object(period)
    return _instance.to_timestamp()

@mcp.tool(name="perioddtype_construct_array_type")
def perioddtype_construct_array_type(perioddtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(perioddtype)
    return _instance.construct_array_type()

@mcp.tool(name="perioddtype_construct_from_string")
def perioddtype_construct_from_string(perioddtype: str) -> Any:
    """Strict construction from a string, raise a TypeError if not"""
    _instance = _get_object(perioddtype)
    return _instance.construct_from_string()

@mcp.tool(name="perioddtype_empty")
def perioddtype_empty(perioddtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(perioddtype)
    return _instance.empty()

@mcp.tool(name="perioddtype_is_dtype")
def perioddtype_is_dtype(perioddtype: str) -> Any:
    """Return a boolean if we if the passed type is an actual dtype that we"""
    _instance = _get_object(perioddtype)
    return _instance.is_dtype()

@mcp.tool(name="perioddtype_reset_cache")
def perioddtype_reset_cache(perioddtype: str) -> Any:
    """clear the cache"""
    _instance = _get_object(perioddtype)
    return _instance.reset_cache()

@mcp.tool(name="periodindex_all")
def periodindex_all(periodindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(periodindex)
    return _instance.all()

@mcp.tool(name="periodindex_any")
def periodindex_any(periodindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(periodindex)
    return _instance.any()

@mcp.tool(name="periodindex_append")
def periodindex_append(periodindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(periodindex)
    return _instance.append()

@mcp.tool(name="periodindex_argmax")
def periodindex_argmax(periodindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(periodindex)
    return _instance.argmax()

@mcp.tool(name="periodindex_argmin")
def periodindex_argmin(periodindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(periodindex)
    return _instance.argmin()

@mcp.tool(name="periodindex_argsort")
def periodindex_argsort(periodindex: str) -> Any:
    """Return the integer indices that would sort the index."""
    _instance = _get_object(periodindex)
    return _instance.argsort()

@mcp.tool(name="periodindex_asfreq")
def periodindex_asfreq(periodindex: str) -> Any:
    """Convert the PeriodArray to the specified frequency `freq`."""
    _instance = _get_object(periodindex)
    return _instance.asfreq()

@mcp.tool(name="periodindex_asof")
def periodindex_asof(periodindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(periodindex)
    return _instance.asof()

@mcp.tool(name="periodindex_asof_locs")
def periodindex_asof_locs(periodindex: str) -> Any:
    """where : array of timestamps"""
    _instance = _get_object(periodindex)
    return _instance.asof_locs()

@mcp.tool(name="periodindex_astype")
def periodindex_astype(periodindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(periodindex)
    return _instance.astype()

@mcp.tool(name="periodindex_copy")
def periodindex_copy(periodindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(periodindex)
    return _instance.copy()

@mcp.tool(name="periodindex_delete")
def periodindex_delete(periodindex: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(periodindex)
    return _instance.delete()

@mcp.tool(name="periodindex_diff")
def periodindex_diff(periodindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(periodindex)
    return _instance.diff()

@mcp.tool(name="periodindex_difference")
def periodindex_difference(periodindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(periodindex)
    return _instance.difference()

@mcp.tool(name="periodindex_drop")
def periodindex_drop(periodindex: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(periodindex)
    return _instance.drop()

@mcp.tool(name="periodindex_drop_duplicates")
def periodindex_drop_duplicates(periodindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(periodindex)
    return _instance.drop_duplicates()

@mcp.tool(name="periodindex_droplevel")
def periodindex_droplevel(periodindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(periodindex)
    return _instance.droplevel()

@mcp.tool(name="periodindex_dropna")
def periodindex_dropna(periodindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(periodindex)
    return _instance.dropna()

@mcp.tool(name="periodindex_duplicated")
def periodindex_duplicated(periodindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(periodindex)
    return _instance.duplicated()

@mcp.tool(name="periodindex_equals")
def periodindex_equals(periodindex: str) -> Any:
    """Determines if two Index objects contain the same elements."""
    _instance = _get_object(periodindex)
    return _instance.equals()

@mcp.tool(name="periodindex_factorize")
def periodindex_factorize(periodindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(periodindex)
    return _instance.factorize()

@mcp.tool(name="periodindex_fillna")
def periodindex_fillna(periodindex: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(periodindex)
    return _instance.fillna()

@mcp.tool(name="periodindex_format")
def periodindex_format(periodindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(periodindex)
    return _instance.format()

@mcp.tool(name="periodindex_from_fields")
def periodindex_from_fields(periodindex: str) -> Any:
    """Tool: periodindex_from_fields"""
    _instance = _get_object(periodindex)
    return _instance.from_fields()

@mcp.tool(name="periodindex_from_ordinals")
def periodindex_from_ordinals(periodindex: str) -> Any:
    """Tool: periodindex_from_ordinals"""
    _instance = _get_object(periodindex)
    return _instance.from_ordinals()

@mcp.tool(name="periodindex_get_indexer")
def periodindex_get_indexer(periodindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(periodindex)
    return _instance.get_indexer()

@mcp.tool(name="periodindex_get_indexer_for")
def periodindex_get_indexer_for(periodindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(periodindex)
    return _instance.get_indexer_for()

@mcp.tool(name="periodindex_get_indexer_non_unique")
def periodindex_get_indexer_non_unique(periodindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(periodindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="periodindex_get_level_values")
def periodindex_get_level_values(periodindex: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(periodindex)
    return _instance.get_level_values()

@mcp.tool(name="periodindex_get_loc")
def periodindex_get_loc(periodindex: str) -> Any:
    """Get integer location for requested label."""
    _instance = _get_object(periodindex)
    return _instance.get_loc()

@mcp.tool(name="periodindex_get_slice_bound")
def periodindex_get_slice_bound(periodindex: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(periodindex)
    return _instance.get_slice_bound()

@mcp.tool(name="periodindex_groupby")
def periodindex_groupby(periodindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(periodindex)
    return _instance.groupby()

@mcp.tool(name="periodindex_holds_integer")
def periodindex_holds_integer(periodindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(periodindex)
    return _instance.holds_integer()

@mcp.tool(name="periodindex_identical")
def periodindex_identical(periodindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(periodindex)
    return _instance.identical()

@mcp.tool(name="periodindex_infer_objects")
def periodindex_infer_objects(periodindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(periodindex)
    return _instance.infer_objects()

@mcp.tool(name="periodindex_insert")
def periodindex_insert(periodindex: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(periodindex)
    return _instance.insert()

@mcp.tool(name="periodindex_intersection")
def periodindex_intersection(periodindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(periodindex)
    return _instance.intersection()

@mcp.tool(name="periodindex_is_")
def periodindex_is_(periodindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(periodindex)
    return _instance.is_()

@mcp.tool(name="periodindex_is_boolean")
def periodindex_is_boolean(periodindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(periodindex)
    return _instance.is_boolean()

@mcp.tool(name="periodindex_is_categorical")
def periodindex_is_categorical(periodindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(periodindex)
    return _instance.is_categorical()

@mcp.tool(name="periodindex_is_floating")
def periodindex_is_floating(periodindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(periodindex)
    return _instance.is_floating()

@mcp.tool(name="periodindex_is_integer")
def periodindex_is_integer(periodindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(periodindex)
    return _instance.is_integer()

@mcp.tool(name="periodindex_is_interval")
def periodindex_is_interval(periodindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(periodindex)
    return _instance.is_interval()

@mcp.tool(name="periodindex_is_numeric")
def periodindex_is_numeric(periodindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(periodindex)
    return _instance.is_numeric()

@mcp.tool(name="periodindex_is_object")
def periodindex_is_object(periodindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(periodindex)
    return _instance.is_object()

@mcp.tool(name="periodindex_isin")
def periodindex_isin(periodindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(periodindex)
    return _instance.isin()

@mcp.tool(name="periodindex_isna")
def periodindex_isna(periodindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(periodindex)
    return _instance.isna()

@mcp.tool(name="periodindex_isnull")
def periodindex_isnull(periodindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(periodindex)
    return _instance.isnull()

@mcp.tool(name="periodindex_item")
def periodindex_item(periodindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(periodindex)
    return _instance.item()

@mcp.tool(name="periodindex_join")
def periodindex_join(periodindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(periodindex)
    return _instance.join()

@mcp.tool(name="periodindex_map")
def periodindex_map(periodindex: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(periodindex)
    return _instance.map()

@mcp.tool(name="periodindex_max")
def periodindex_max(periodindex: str) -> Any:
    """Return the maximum value of the Index."""
    _instance = _get_object(periodindex)
    return _instance.max()

@mcp.tool(name="periodindex_mean")
def periodindex_mean(periodindex: str) -> Any:
    """Return the mean value of the Array."""
    _instance = _get_object(periodindex)
    return _instance.mean()

@mcp.tool(name="periodindex_memory_usage")
def periodindex_memory_usage(periodindex: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(periodindex)
    return _instance.memory_usage()

@mcp.tool(name="periodindex_min")
def periodindex_min(periodindex: str) -> Any:
    """Return the minimum value of the Index."""
    _instance = _get_object(periodindex)
    return _instance.min()

@mcp.tool(name="periodindex_notna")
def periodindex_notna(periodindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(periodindex)
    return _instance.notna()

@mcp.tool(name="periodindex_notnull")
def periodindex_notnull(periodindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(periodindex)
    return _instance.notnull()

@mcp.tool(name="periodindex_nunique")
def periodindex_nunique(periodindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(periodindex)
    return _instance.nunique()

@mcp.tool(name="periodindex_putmask")
def periodindex_putmask(periodindex: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(periodindex)
    return _instance.putmask()

@mcp.tool(name="periodindex_ravel")
def periodindex_ravel(periodindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(periodindex)
    return _instance.ravel()

@mcp.tool(name="periodindex_reindex")
def periodindex_reindex(periodindex: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(periodindex)
    return _instance.reindex()

@mcp.tool(name="periodindex_rename")
def periodindex_rename(periodindex: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(periodindex)
    return _instance.rename()

@mcp.tool(name="periodindex_repeat")
def periodindex_repeat(periodindex: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(periodindex)
    return _instance.repeat()

@mcp.tool(name="periodindex_round")
def periodindex_round(periodindex: str) -> Any:
    """Round each value in the Index to the given number of decimals."""
    _instance = _get_object(periodindex)
    return _instance.round()

@mcp.tool(name="periodindex_searchsorted")
def periodindex_searchsorted(periodindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(periodindex)
    return _instance.searchsorted()

@mcp.tool(name="periodindex_set_names")
def periodindex_set_names(periodindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(periodindex)
    return _instance.set_names()

@mcp.tool(name="periodindex_shift")
def periodindex_shift(periodindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(periodindex)
    return _instance.shift()

@mcp.tool(name="periodindex_slice_indexer")
def periodindex_slice_indexer(periodindex: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(periodindex)
    return _instance.slice_indexer()

@mcp.tool(name="periodindex_slice_locs")
def periodindex_slice_locs(periodindex: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(periodindex)
    return _instance.slice_locs()

@mcp.tool(name="periodindex_sort")
def periodindex_sort(periodindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(periodindex)
    return _instance.sort()

@mcp.tool(name="periodindex_sort_values")
def periodindex_sort_values(periodindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(periodindex)
    return _instance.sort_values()

@mcp.tool(name="periodindex_sortlevel")
def periodindex_sortlevel(periodindex: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(periodindex)
    return _instance.sortlevel()

@mcp.tool(name="periodindex_strftime")
def periodindex_strftime(periodindex: str) -> Any:
    """Convert to Index using specified date_format."""
    _instance = _get_object(periodindex)
    return _instance.strftime()

@mcp.tool(name="periodindex_symmetric_difference")
def periodindex_symmetric_difference(periodindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(periodindex)
    return _instance.symmetric_difference()

@mcp.tool(name="periodindex_take")
def periodindex_take(periodindex: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(periodindex)
    return _instance.take()

@mcp.tool(name="periodindex_to_flat_index")
def periodindex_to_flat_index(periodindex: str) -> Any:
    """Identity method."""
    _instance = _get_object(periodindex)
    return _instance.to_flat_index()

@mcp.tool(name="periodindex_to_frame")
def periodindex_to_frame(periodindex: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(periodindex)
    return _instance.to_frame()

@mcp.tool(name="periodindex_to_list")
def periodindex_to_list(periodindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(periodindex)
    return _instance.to_list()

@mcp.tool(name="periodindex_to_numpy")
def periodindex_to_numpy(periodindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(periodindex)
    return _instance.to_numpy()

@mcp.tool(name="periodindex_to_series")
def periodindex_to_series(periodindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(periodindex)
    return _instance.to_series()

@mcp.tool(name="periodindex_to_timestamp")
def periodindex_to_timestamp(periodindex: str) -> Any:
    """Cast to DatetimeArray/Index."""
    _instance = _get_object(periodindex)
    return _instance.to_timestamp()

@mcp.tool(name="periodindex_tolist")
def periodindex_tolist(periodindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(periodindex)
    return _instance.tolist()

@mcp.tool(name="periodindex_transpose")
def periodindex_transpose(periodindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(periodindex)
    return _instance.transpose()

@mcp.tool(name="periodindex_union")
def periodindex_union(periodindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(periodindex)
    return _instance.union()

@mcp.tool(name="periodindex_unique")
def periodindex_unique(periodindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(periodindex)
    return _instance.unique()

@mcp.tool(name="periodindex_value_counts")
def periodindex_value_counts(periodindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(periodindex)
    return _instance.value_counts()

@mcp.tool(name="periodindex_view")
def periodindex_view(periodindex: str) -> Any:
    """Tool: periodindex_view"""
    _instance = _get_object(periodindex)
    return _instance.view()

@mcp.tool(name="periodindex_where")
def periodindex_where(periodindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(periodindex)
    return _instance.where()

@mcp.tool(name="rangeindex_all")
def rangeindex_all(rangeindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(rangeindex)
    return _instance.all()

@mcp.tool(name="rangeindex_any")
def rangeindex_any(rangeindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(rangeindex)
    return _instance.any()

@mcp.tool(name="rangeindex_append")
def rangeindex_append(rangeindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(rangeindex)
    return _instance.append()

@mcp.tool(name="rangeindex_argmax")
def rangeindex_argmax(rangeindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(rangeindex)
    return _instance.argmax()

@mcp.tool(name="rangeindex_argmin")
def rangeindex_argmin(rangeindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(rangeindex)
    return _instance.argmin()

@mcp.tool(name="rangeindex_argsort")
def rangeindex_argsort(rangeindex: str) -> Any:
    """Returns the indices that would sort the index and its"""
    _instance = _get_object(rangeindex)
    return _instance.argsort()

@mcp.tool(name="rangeindex_asof")
def rangeindex_asof(rangeindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(rangeindex)
    return _instance.asof()

@mcp.tool(name="rangeindex_asof_locs")
def rangeindex_asof_locs(rangeindex: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(rangeindex)
    return _instance.asof_locs()

@mcp.tool(name="rangeindex_astype")
def rangeindex_astype(rangeindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(rangeindex)
    return _instance.astype()

@mcp.tool(name="rangeindex_copy")
def rangeindex_copy(rangeindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(rangeindex)
    return _instance.copy()

@mcp.tool(name="rangeindex_delete")
def rangeindex_delete(rangeindex: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(rangeindex)
    return _instance.delete()

@mcp.tool(name="rangeindex_diff")
def rangeindex_diff(rangeindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(rangeindex)
    return _instance.diff()

@mcp.tool(name="rangeindex_difference")
def rangeindex_difference(rangeindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(rangeindex)
    return _instance.difference()

@mcp.tool(name="rangeindex_drop")
def rangeindex_drop(rangeindex: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(rangeindex)
    return _instance.drop()

@mcp.tool(name="rangeindex_drop_duplicates")
def rangeindex_drop_duplicates(rangeindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(rangeindex)
    return _instance.drop_duplicates()

@mcp.tool(name="rangeindex_droplevel")
def rangeindex_droplevel(rangeindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(rangeindex)
    return _instance.droplevel()

@mcp.tool(name="rangeindex_dropna")
def rangeindex_dropna(rangeindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(rangeindex)
    return _instance.dropna()

@mcp.tool(name="rangeindex_duplicated")
def rangeindex_duplicated(rangeindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(rangeindex)
    return _instance.duplicated()

@mcp.tool(name="rangeindex_equals")
def rangeindex_equals(rangeindex: str) -> Any:
    """Determines if two Index objects contain the same elements."""
    _instance = _get_object(rangeindex)
    return _instance.equals()

@mcp.tool(name="rangeindex_factorize")
def rangeindex_factorize(rangeindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(rangeindex)
    return _instance.factorize()

@mcp.tool(name="rangeindex_fillna")
def rangeindex_fillna(rangeindex: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(rangeindex)
    return _instance.fillna()

@mcp.tool(name="rangeindex_format")
def rangeindex_format(rangeindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(rangeindex)
    return _instance.format()

@mcp.tool(name="rangeindex_from_range")
def rangeindex_from_range(rangeindex: str) -> Any:
    """Create :class:`pandas.RangeIndex` from a ``range`` object."""
    _instance = _get_object(rangeindex)
    return _instance.from_range()

@mcp.tool(name="rangeindex_get_indexer")
def rangeindex_get_indexer(rangeindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(rangeindex)
    return _instance.get_indexer()

@mcp.tool(name="rangeindex_get_indexer_for")
def rangeindex_get_indexer_for(rangeindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(rangeindex)
    return _instance.get_indexer_for()

@mcp.tool(name="rangeindex_get_indexer_non_unique")
def rangeindex_get_indexer_non_unique(rangeindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(rangeindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="rangeindex_get_level_values")
def rangeindex_get_level_values(rangeindex: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(rangeindex)
    return _instance.get_level_values()

@mcp.tool(name="rangeindex_get_loc")
def rangeindex_get_loc(rangeindex: str) -> Any:
    """Get integer location, slice or boolean mask for requested label."""
    _instance = _get_object(rangeindex)
    return _instance.get_loc()

@mcp.tool(name="rangeindex_get_slice_bound")
def rangeindex_get_slice_bound(rangeindex: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(rangeindex)
    return _instance.get_slice_bound()

@mcp.tool(name="rangeindex_groupby")
def rangeindex_groupby(rangeindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(rangeindex)
    return _instance.groupby()

@mcp.tool(name="rangeindex_holds_integer")
def rangeindex_holds_integer(rangeindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(rangeindex)
    return _instance.holds_integer()

@mcp.tool(name="rangeindex_identical")
def rangeindex_identical(rangeindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(rangeindex)
    return _instance.identical()

@mcp.tool(name="rangeindex_infer_objects")
def rangeindex_infer_objects(rangeindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(rangeindex)
    return _instance.infer_objects()

@mcp.tool(name="rangeindex_insert")
def rangeindex_insert(rangeindex: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(rangeindex)
    return _instance.insert()

@mcp.tool(name="rangeindex_intersection")
def rangeindex_intersection(rangeindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(rangeindex)
    return _instance.intersection()

@mcp.tool(name="rangeindex_is_")
def rangeindex_is_(rangeindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(rangeindex)
    return _instance.is_()

@mcp.tool(name="rangeindex_is_boolean")
def rangeindex_is_boolean(rangeindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(rangeindex)
    return _instance.is_boolean()

@mcp.tool(name="rangeindex_is_categorical")
def rangeindex_is_categorical(rangeindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(rangeindex)
    return _instance.is_categorical()

@mcp.tool(name="rangeindex_is_floating")
def rangeindex_is_floating(rangeindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(rangeindex)
    return _instance.is_floating()

@mcp.tool(name="rangeindex_is_integer")
def rangeindex_is_integer(rangeindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(rangeindex)
    return _instance.is_integer()

@mcp.tool(name="rangeindex_is_interval")
def rangeindex_is_interval(rangeindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(rangeindex)
    return _instance.is_interval()

@mcp.tool(name="rangeindex_is_numeric")
def rangeindex_is_numeric(rangeindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(rangeindex)
    return _instance.is_numeric()

@mcp.tool(name="rangeindex_is_object")
def rangeindex_is_object(rangeindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(rangeindex)
    return _instance.is_object()

@mcp.tool(name="rangeindex_isin")
def rangeindex_isin(rangeindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(rangeindex)
    return _instance.isin()

@mcp.tool(name="rangeindex_isna")
def rangeindex_isna(rangeindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(rangeindex)
    return _instance.isna()

@mcp.tool(name="rangeindex_isnull")
def rangeindex_isnull(rangeindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(rangeindex)
    return _instance.isnull()

@mcp.tool(name="rangeindex_item")
def rangeindex_item(rangeindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(rangeindex)
    return _instance.item()

@mcp.tool(name="rangeindex_join")
def rangeindex_join(rangeindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(rangeindex)
    return _instance.join()

@mcp.tool(name="rangeindex_map")
def rangeindex_map(rangeindex: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(rangeindex)
    return _instance.map()

@mcp.tool(name="rangeindex_max")
def rangeindex_max(rangeindex: str) -> Any:
    """The maximum value of the RangeIndex"""
    _instance = _get_object(rangeindex)
    return _instance.max()

@mcp.tool(name="rangeindex_memory_usage")
def rangeindex_memory_usage(rangeindex: str) -> Any:
    """Memory usage of my values"""
    _instance = _get_object(rangeindex)
    return _instance.memory_usage()

@mcp.tool(name="rangeindex_min")
def rangeindex_min(rangeindex: str) -> Any:
    """The minimum value of the RangeIndex"""
    _instance = _get_object(rangeindex)
    return _instance.min()

@mcp.tool(name="rangeindex_notna")
def rangeindex_notna(rangeindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(rangeindex)
    return _instance.notna()

@mcp.tool(name="rangeindex_notnull")
def rangeindex_notnull(rangeindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(rangeindex)
    return _instance.notnull()

@mcp.tool(name="rangeindex_nunique")
def rangeindex_nunique(rangeindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(rangeindex)
    return _instance.nunique()

@mcp.tool(name="rangeindex_putmask")
def rangeindex_putmask(rangeindex: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(rangeindex)
    return _instance.putmask()

@mcp.tool(name="rangeindex_ravel")
def rangeindex_ravel(rangeindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(rangeindex)
    return _instance.ravel()

@mcp.tool(name="rangeindex_reindex")
def rangeindex_reindex(rangeindex: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(rangeindex)
    return _instance.reindex()

@mcp.tool(name="rangeindex_rename")
def rangeindex_rename(rangeindex: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(rangeindex)
    return _instance.rename()

@mcp.tool(name="rangeindex_repeat")
def rangeindex_repeat(rangeindex: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(rangeindex)
    return _instance.repeat()

@mcp.tool(name="rangeindex_round")
def rangeindex_round(rangeindex: str) -> Any:
    """Round each value in the Index to the given number of decimals."""
    _instance = _get_object(rangeindex)
    return _instance.round()

@mcp.tool(name="rangeindex_searchsorted")
def rangeindex_searchsorted(rangeindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(rangeindex)
    return _instance.searchsorted()

@mcp.tool(name="rangeindex_set_names")
def rangeindex_set_names(rangeindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(rangeindex)
    return _instance.set_names()

@mcp.tool(name="rangeindex_shift")
def rangeindex_shift(rangeindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(rangeindex)
    return _instance.shift()

@mcp.tool(name="rangeindex_slice_indexer")
def rangeindex_slice_indexer(rangeindex: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(rangeindex)
    return _instance.slice_indexer()

@mcp.tool(name="rangeindex_slice_locs")
def rangeindex_slice_locs(rangeindex: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(rangeindex)
    return _instance.slice_locs()

@mcp.tool(name="rangeindex_sort")
def rangeindex_sort(rangeindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(rangeindex)
    return _instance.sort()

@mcp.tool(name="rangeindex_sort_values")
def rangeindex_sort_values(rangeindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(rangeindex)
    return _instance.sort_values()

@mcp.tool(name="rangeindex_sortlevel")
def rangeindex_sortlevel(rangeindex: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(rangeindex)
    return _instance.sortlevel()

@mcp.tool(name="rangeindex_symmetric_difference")
def rangeindex_symmetric_difference(rangeindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(rangeindex)
    return _instance.symmetric_difference()

@mcp.tool(name="rangeindex_take")
def rangeindex_take(rangeindex: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(rangeindex)
    return _instance.take()

@mcp.tool(name="rangeindex_to_flat_index")
def rangeindex_to_flat_index(rangeindex: str) -> Any:
    """Identity method."""
    _instance = _get_object(rangeindex)
    return _instance.to_flat_index()

@mcp.tool(name="rangeindex_to_frame")
def rangeindex_to_frame(rangeindex: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(rangeindex)
    return _instance.to_frame()

@mcp.tool(name="rangeindex_to_list")
def rangeindex_to_list(rangeindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(rangeindex)
    return _instance.to_list()

@mcp.tool(name="rangeindex_to_numpy")
def rangeindex_to_numpy(rangeindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(rangeindex)
    return _instance.to_numpy()

@mcp.tool(name="rangeindex_to_series")
def rangeindex_to_series(rangeindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(rangeindex)
    return _instance.to_series()

@mcp.tool(name="rangeindex_tolist")
def rangeindex_tolist(rangeindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(rangeindex)
    return _instance.tolist()

@mcp.tool(name="rangeindex_transpose")
def rangeindex_transpose(rangeindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(rangeindex)
    return _instance.transpose()

@mcp.tool(name="rangeindex_union")
def rangeindex_union(rangeindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(rangeindex)
    return _instance.union()

@mcp.tool(name="rangeindex_unique")
def rangeindex_unique(rangeindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(rangeindex)
    return _instance.unique()

@mcp.tool(name="rangeindex_value_counts")
def rangeindex_value_counts(rangeindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(rangeindex)
    return _instance.value_counts()

@mcp.tool(name="rangeindex_view")
def rangeindex_view(rangeindex: str) -> Any:
    """Tool: rangeindex_view"""
    _instance = _get_object(rangeindex)
    return _instance.view()

@mcp.tool(name="rangeindex_where")
def rangeindex_where(rangeindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(rangeindex)
    return _instance.where()

@mcp.tool(name="series_abs")
def series_abs(series: str) -> Any:
    """Return a Series/DataFrame with absolute numeric value of each element."""
    _instance = _get_object(series)
    return _instance.abs()

@mcp.tool(name="series_add")
def series_add(series: str) -> Any:
    """Return Addition of series and other, element-wise (binary operator `add`)."""
    _instance = _get_object(series)
    return _instance.add()

@mcp.tool(name="series_add_prefix")
def series_add_prefix(series: str) -> Any:
    """Prefix labels with string `prefix`."""
    _instance = _get_object(series)
    return _instance.add_prefix()

@mcp.tool(name="series_add_suffix")
def series_add_suffix(series: str) -> Any:
    """Suffix labels with string `suffix`."""
    _instance = _get_object(series)
    return _instance.add_suffix()

@mcp.tool(name="series_agg")
def series_agg(series: str) -> Any:
    """Aggregate using one or more operations over the specified axis."""
    _instance = _get_object(series)
    return _instance.agg()

@mcp.tool(name="series_aggregate")
def series_aggregate(series: str) -> Any:
    """Aggregate using one or more operations over the specified axis."""
    _instance = _get_object(series)
    return _instance.aggregate()

@mcp.tool(name="series_align")
def series_align(series: str) -> Any:
    """Align two objects on their axes with the specified join method."""
    _instance = _get_object(series)
    return _instance.align()

@mcp.tool(name="series_all")
def series_all(series: str) -> Any:
    """Return whether all elements are True, potentially over an axis."""
    _instance = _get_object(series)
    return _instance.all()

@mcp.tool(name="series_any")
def series_any(series: str) -> Any:
    """Return whether any element is True, potentially over an axis."""
    _instance = _get_object(series)
    return _instance.any()

@mcp.tool(name="series_apply")
def series_apply(series: str) -> Any:
    """Invoke function on values of Series."""
    _instance = _get_object(series)
    return _instance.apply()

@mcp.tool(name="series_argmax")
def series_argmax(series: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(series)
    return _instance.argmax()

@mcp.tool(name="series_argmin")
def series_argmin(series: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(series)
    return _instance.argmin()

@mcp.tool(name="series_argsort")
def series_argsort(series: str) -> Any:
    """Return the integer indices that would sort the Series values."""
    _instance = _get_object(series)
    return _instance.argsort()

@mcp.tool(name="series_asfreq")
def series_asfreq(series: str) -> Any:
    """Convert time series to specified frequency."""
    _instance = _get_object(series)
    return _instance.asfreq()

@mcp.tool(name="series_asof")
def series_asof(series: str) -> Any:
    """Return the last row(s) without any NaNs before `where`."""
    _instance = _get_object(series)
    return _instance.asof()

@mcp.tool(name="series_astype")
def series_astype(series: str) -> Any:
    """Cast a pandas object to a specified dtype ``dtype``."""
    _instance = _get_object(series)
    return _instance.astype()

@mcp.tool(name="series_at_time")
def series_at_time(series: str) -> Any:
    """Select values at particular time of day (e.g., 9:30AM)."""
    _instance = _get_object(series)
    return _instance.at_time()

@mcp.tool(name="series_autocorr")
def series_autocorr(series: str) -> Any:
    """Compute the lag-N autocorrelation."""
    _instance = _get_object(series)
    return _instance.autocorr()

@mcp.tool(name="series_backfill")
def series_backfill(series: str) -> Any:
    """Fill NA/NaN values by using the next valid observation to fill the gap."""
    _instance = _get_object(series)
    return _instance.backfill()

@mcp.tool(name="series_between")
def series_between(series: str) -> Any:
    """Return boolean Series equivalent to left <= series <= right."""
    _instance = _get_object(series)
    return _instance.between()

@mcp.tool(name="series_between_time")
def series_between_time(series: str) -> Any:
    """Select values between particular times of the day (e.g., 9:00-9:30 AM)."""
    _instance = _get_object(series)
    return _instance.between_time()

@mcp.tool(name="series_bfill")
def series_bfill(series: str) -> Any:
    """Fill NA/NaN values by using the next valid observation to fill the gap."""
    _instance = _get_object(series)
    return _instance.bfill()

@mcp.tool(name="series_bool")
def series_bool(series: str) -> Any:
    """Return the bool of a single element Series or DataFrame."""
    _instance = _get_object(series)
    return _instance.bool()

@mcp.tool(name="series_case_when")
def series_case_when(series: str) -> Any:
    """Replace values where the conditions are True."""
    _instance = _get_object(series)
    return _instance.case_when()

@mcp.tool(name="series_clip")
def series_clip(series: str) -> Any:
    """Trim values at input threshold(s)."""
    _instance = _get_object(series)
    return _instance.clip()

@mcp.tool(name="series_combine")
def series_combine(series: str) -> Any:
    """Combine the Series with a Series or scalar according to `func`."""
    _instance = _get_object(series)
    return _instance.combine()

@mcp.tool(name="series_combine_first")
def series_combine_first(series: str) -> Any:
    """Update null elements with value in the same location in 'other'."""
    _instance = _get_object(series)
    return _instance.combine_first()

@mcp.tool(name="series_compare")
def series_compare(series: str) -> Any:
    """Compare to another Series and show the differences."""
    _instance = _get_object(series)
    return _instance.compare()

@mcp.tool(name="series_convert_dtypes")
def series_convert_dtypes(series: str) -> Any:
    """Convert columns to the best possible dtypes using dtypes supporting ``pd.NA``."""
    _instance = _get_object(series)
    return _instance.convert_dtypes()

@mcp.tool(name="series_copy")
def series_copy(series: str) -> Any:
    """Make a copy of this object's indices and data."""
    _instance = _get_object(series)
    return _instance.copy()

@mcp.tool(name="series_corr")
def series_corr(series: str) -> Any:
    """Compute correlation with `other` Series, excluding missing values."""
    _instance = _get_object(series)
    return _instance.corr()

@mcp.tool(name="series_count")
def series_count(series: str) -> Any:
    """Return number of non-NA/null observations in the Series."""
    _instance = _get_object(series)
    return _instance.count()

@mcp.tool(name="series_cov")
def series_cov(series: str) -> Any:
    """Compute covariance with Series, excluding missing values."""
    _instance = _get_object(series)
    return _instance.cov()

@mcp.tool(name="series_cummax")
def series_cummax(series: str) -> Any:
    """Return cumulative maximum over a DataFrame or Series axis."""
    _instance = _get_object(series)
    return _instance.cummax()

@mcp.tool(name="series_cummin")
def series_cummin(series: str) -> Any:
    """Return cumulative minimum over a DataFrame or Series axis."""
    _instance = _get_object(series)
    return _instance.cummin()

@mcp.tool(name="series_cumprod")
def series_cumprod(series: str) -> Any:
    """Return cumulative product over a DataFrame or Series axis."""
    _instance = _get_object(series)
    return _instance.cumprod()

@mcp.tool(name="series_cumsum")
def series_cumsum(series: str) -> Any:
    """Return cumulative sum over a DataFrame or Series axis."""
    _instance = _get_object(series)
    return _instance.cumsum()

@mcp.tool(name="series_describe")
def series_describe(series: str) -> Any:
    """Generate descriptive statistics."""
    _instance = _get_object(series)
    return _instance.describe()

@mcp.tool(name="series_diff")
def series_diff(series: str) -> Any:
    """First discrete difference of element."""
    _instance = _get_object(series)
    return _instance.diff()

@mcp.tool(name="series_div")
def series_div(series: str) -> Any:
    """Return Floating division of series and other, element-wise (binary operator `truediv`)."""
    _instance = _get_object(series)
    return _instance.div()

@mcp.tool(name="series_divide")
def series_divide(series: str) -> Any:
    """Return Floating division of series and other, element-wise (binary operator `truediv`)."""
    _instance = _get_object(series)
    return _instance.divide()

@mcp.tool(name="series_divmod")
def series_divmod(series: str) -> Any:
    """Return Integer division and modulo of series and other, element-wise (binary operator `divmod`)."""
    _instance = _get_object(series)
    return _instance.divmod()

@mcp.tool(name="series_dot")
def series_dot(series: str) -> Any:
    """Compute the dot product between the Series and the columns of other."""
    _instance = _get_object(series)
    return _instance.dot()

@mcp.tool(name="series_drop")
def series_drop(series: str) -> Any:
    """Return Series with specified index labels removed."""
    _instance = _get_object(series)
    return _instance.drop()

@mcp.tool(name="series_drop_duplicates")
def series_drop_duplicates(series: str) -> Any:
    """Return Series with duplicate values removed."""
    _instance = _get_object(series)
    return _instance.drop_duplicates()

@mcp.tool(name="series_droplevel")
def series_droplevel(series: str) -> Any:
    """Return Series/DataFrame with requested index / column level(s) removed."""
    _instance = _get_object(series)
    return _instance.droplevel()

@mcp.tool(name="series_dropna")
def series_dropna(series: str) -> Any:
    """Return a new Series with missing values removed."""
    _instance = _get_object(series)
    return _instance.dropna()

@mcp.tool(name="series_duplicated")
def series_duplicated(series: str) -> Any:
    """Indicate duplicate Series values."""
    _instance = _get_object(series)
    return _instance.duplicated()

@mcp.tool(name="series_eq")
def series_eq(series: str) -> Any:
    """Return Equal to of series and other, element-wise (binary operator `eq`)."""
    _instance = _get_object(series)
    return _instance.eq()

@mcp.tool(name="series_equals")
def series_equals(series: str) -> Any:
    """Test whether two objects contain the same elements."""
    _instance = _get_object(series)
    return _instance.equals()

@mcp.tool(name="series_ewm")
def series_ewm(series: str) -> Any:
    """Provide exponentially weighted (EW) calculations."""
    _instance = _get_object(series)
    return _instance.ewm()

@mcp.tool(name="series_expanding")
def series_expanding(series: str) -> Any:
    """Provide expanding window calculations."""
    _instance = _get_object(series)
    return _instance.expanding()

@mcp.tool(name="series_explode")
def series_explode(series: str) -> Any:
    """Transform each element of a list-like to a row."""
    _instance = _get_object(series)
    return _instance.explode()

@mcp.tool(name="series_factorize")
def series_factorize(series: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(series)
    return _instance.factorize()

@mcp.tool(name="series_ffill")
def series_ffill(series: str) -> Any:
    """Fill NA/NaN values by propagating the last valid observation to next valid."""
    _instance = _get_object(series)
    return _instance.ffill()

@mcp.tool(name="series_fillna")
def series_fillna(series: str) -> Any:
    """Fill NA/NaN values using the specified method."""
    _instance = _get_object(series)
    return _instance.fillna()

@mcp.tool(name="series_filter")
def series_filter(series: str) -> Any:
    """Subset the dataframe rows or columns according to the specified index labels."""
    _instance = _get_object(series)
    return _instance.filter()

@mcp.tool(name="series_first")
def series_first(series: str) -> Any:
    """Select initial periods of time series data based on a date offset."""
    _instance = _get_object(series)
    return _instance.first()

@mcp.tool(name="series_first_valid_index")
def series_first_valid_index(series: str) -> Any:
    """Return index for first non-NA value or None, if no non-NA value is found."""
    _instance = _get_object(series)
    return _instance.first_valid_index()

@mcp.tool(name="series_floordiv")
def series_floordiv(series: str) -> Any:
    """Return Integer division of series and other, element-wise (binary operator `floordiv`)."""
    _instance = _get_object(series)
    return _instance.floordiv()

@mcp.tool(name="series_ge")
def series_ge(series: str) -> Any:
    """Return Greater than or equal to of series and other, element-wise (binary operator `ge`)."""
    _instance = _get_object(series)
    return _instance.ge()

@mcp.tool(name="series_get")
def series_get(series: str) -> Any:
    """Get item from object for given key (ex: DataFrame column)."""
    _instance = _get_object(series)
    return _instance.get()

@mcp.tool(name="series_groupby")
def series_groupby(series: str) -> Any:
    """Group Series using a mapper or by a Series of columns."""
    _instance = _get_object(series)
    return _instance.groupby()

@mcp.tool(name="series_gt")
def series_gt(series: str) -> Any:
    """Return Greater than of series and other, element-wise (binary operator `gt`)."""
    _instance = _get_object(series)
    return _instance.gt()

@mcp.tool(name="series_head")
def series_head(series: str) -> Any:
    """Return the first `n` rows."""
    _instance = _get_object(series)
    return _instance.head()

@mcp.tool(name="series_hist")
def series_hist(series: str) -> Any:
    """Draw histogram of the input series using matplotlib."""
    _instance = _get_object(series)
    return _instance.hist()

@mcp.tool(name="series_idxmax")
def series_idxmax(series: str) -> Any:
    """Return the row label of the maximum value."""
    _instance = _get_object(series)
    return _instance.idxmax()

@mcp.tool(name="series_idxmin")
def series_idxmin(series: str) -> Any:
    """Return the row label of the minimum value."""
    _instance = _get_object(series)
    return _instance.idxmin()

@mcp.tool(name="series_infer_objects")
def series_infer_objects(series: str) -> Any:
    """Attempt to infer better dtypes for object columns."""
    _instance = _get_object(series)
    return _instance.infer_objects()

@mcp.tool(name="series_info")
def series_info(series: str) -> Any:
    """Print a concise summary of a Series."""
    _instance = _get_object(series)
    return _instance.info()

@mcp.tool(name="series_interpolate")
def series_interpolate(series: str) -> Any:
    """Fill NaN values using an interpolation method."""
    _instance = _get_object(series)
    return _instance.interpolate()

@mcp.tool(name="series_isin")
def series_isin(series: str) -> Any:
    """Whether elements in Series are contained in `values`."""
    _instance = _get_object(series)
    return _instance.isin()

@mcp.tool(name="series_isna")
def series_isna(series: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(series)
    return _instance.isna()

@mcp.tool(name="series_isnull")
def series_isnull(series: str) -> Any:
    """Series.isnull is an alias for Series.isna."""
    _instance = _get_object(series)
    return _instance.isnull()

@mcp.tool(name="series_item")
def series_item(series: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(series)
    return _instance.item()

@mcp.tool(name="series_items")
def series_items(series: str) -> Any:
    """Lazily iterate over (index, value) tuples."""
    _instance = _get_object(series)
    return _instance.items()

@mcp.tool(name="series_keys")
def series_keys(series: str) -> Any:
    """Return alias for index."""
    _instance = _get_object(series)
    return _instance.keys()

@mcp.tool(name="series_kurt")
def series_kurt(series: str) -> Any:
    """Return unbiased kurtosis over requested axis."""
    _instance = _get_object(series)
    return _instance.kurt()

@mcp.tool(name="series_kurtosis")
def series_kurtosis(series: str) -> Any:
    """Return unbiased kurtosis over requested axis."""
    _instance = _get_object(series)
    return _instance.kurtosis()

@mcp.tool(name="series_last")
def series_last(series: str) -> Any:
    """Select final periods of time series data based on a date offset."""
    _instance = _get_object(series)
    return _instance.last()

@mcp.tool(name="series_last_valid_index")
def series_last_valid_index(series: str) -> Any:
    """Return index for last non-NA value or None, if no non-NA value is found."""
    _instance = _get_object(series)
    return _instance.last_valid_index()

@mcp.tool(name="series_le")
def series_le(series: str) -> Any:
    """Return Less than or equal to of series and other, element-wise (binary operator `le`)."""
    _instance = _get_object(series)
    return _instance.le()

@mcp.tool(name="series_lt")
def series_lt(series: str) -> Any:
    """Return Less than of series and other, element-wise (binary operator `lt`)."""
    _instance = _get_object(series)
    return _instance.lt()

@mcp.tool(name="series_map")
def series_map(series: str) -> Any:
    """Map values of Series according to an input mapping or function."""
    _instance = _get_object(series)
    return _instance.map()

@mcp.tool(name="series_mask")
def series_mask(series: str) -> Any:
    """Replace values where the condition is True."""
    _instance = _get_object(series)
    return _instance.mask()

@mcp.tool(name="series_max")
def series_max(series: str) -> Any:
    """Return the maximum of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.max()

@mcp.tool(name="series_mean")
def series_mean(series: str) -> Any:
    """Return the mean of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.mean()

@mcp.tool(name="series_median")
def series_median(series: str) -> Any:
    """Return the median of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.median()

@mcp.tool(name="series_memory_usage")
def series_memory_usage(series: str) -> Any:
    """Return the memory usage of the Series."""
    _instance = _get_object(series)
    return _instance.memory_usage()

@mcp.tool(name="series_min")
def series_min(series: str) -> Any:
    """Return the minimum of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.min()

@mcp.tool(name="series_mod")
def series_mod(series: str) -> Any:
    """Return Modulo of series and other, element-wise (binary operator `mod`)."""
    _instance = _get_object(series)
    return _instance.mod()

@mcp.tool(name="series_mode")
def series_mode(series: str) -> Any:
    """Return the mode(s) of the Series."""
    _instance = _get_object(series)
    return _instance.mode()

@mcp.tool(name="series_mul")
def series_mul(series: str) -> Any:
    """Return Multiplication of series and other, element-wise (binary operator `mul`)."""
    _instance = _get_object(series)
    return _instance.mul()

@mcp.tool(name="series_multiply")
def series_multiply(series: str) -> Any:
    """Return Multiplication of series and other, element-wise (binary operator `mul`)."""
    _instance = _get_object(series)
    return _instance.multiply()

@mcp.tool(name="series_ne")
def series_ne(series: str) -> Any:
    """Return Not equal to of series and other, element-wise (binary operator `ne`)."""
    _instance = _get_object(series)
    return _instance.ne()

@mcp.tool(name="series_nlargest")
def series_nlargest(series: str) -> Any:
    """Return the largest `n` elements."""
    _instance = _get_object(series)
    return _instance.nlargest()

@mcp.tool(name="series_notna")
def series_notna(series: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(series)
    return _instance.notna()

@mcp.tool(name="series_notnull")
def series_notnull(series: str) -> Any:
    """Series.notnull is an alias for Series.notna."""
    _instance = _get_object(series)
    return _instance.notnull()

@mcp.tool(name="series_nsmallest")
def series_nsmallest(series: str) -> Any:
    """Return the smallest `n` elements."""
    _instance = _get_object(series)
    return _instance.nsmallest()

@mcp.tool(name="series_nunique")
def series_nunique(series: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(series)
    return _instance.nunique()

@mcp.tool(name="series_pad")
def series_pad(series: str) -> Any:
    """Fill NA/NaN values by propagating the last valid observation to next valid."""
    _instance = _get_object(series)
    return _instance.pad()

@mcp.tool(name="series_pct_change")
def series_pct_change(series: str) -> Any:
    """Fractional change between the current and a prior element."""
    _instance = _get_object(series)
    return _instance.pct_change()

@mcp.tool(name="series_pipe")
def series_pipe(series: str) -> Any:
    """Apply chainable functions that expect Series or DataFrames."""
    _instance = _get_object(series)
    return _instance.pipe()

@mcp.tool(name="series_pop")
def series_pop(series: str) -> Any:
    """Return item and drops from series. Raise KeyError if not found."""
    _instance = _get_object(series)
    return _instance.pop()

@mcp.tool(name="series_pow")
def series_pow(series: str) -> Any:
    """Return Exponential power of series and other, element-wise (binary operator `pow`)."""
    _instance = _get_object(series)
    return _instance.pow()

@mcp.tool(name="series_prod")
def series_prod(series: str) -> Any:
    """Return the product of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.prod()

@mcp.tool(name="series_product")
def series_product(series: str) -> Any:
    """Return the product of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.product()

@mcp.tool(name="series_quantile")
def series_quantile(series: str) -> Any:
    """Return value at the given quantile."""
    _instance = _get_object(series)
    return _instance.quantile()

@mcp.tool(name="series_radd")
def series_radd(series: str) -> Any:
    """Return Addition of series and other, element-wise (binary operator `radd`)."""
    _instance = _get_object(series)
    return _instance.radd()

@mcp.tool(name="series_rank")
def series_rank(series: str) -> Any:
    """Compute numerical data ranks (1 through n) along axis."""
    _instance = _get_object(series)
    return _instance.rank()

@mcp.tool(name="series_ravel")
def series_ravel(series: str) -> Any:
    """Return the flattened underlying data as an ndarray or ExtensionArray."""
    _instance = _get_object(series)
    return _instance.ravel()

@mcp.tool(name="series_rdiv")
def series_rdiv(series: str) -> Any:
    """Return Floating division of series and other, element-wise (binary operator `rtruediv`)."""
    _instance = _get_object(series)
    return _instance.rdiv()

@mcp.tool(name="series_rdivmod")
def series_rdivmod(series: str) -> Any:
    """Return Integer division and modulo of series and other, element-wise (binary operator `rdivmod`)."""
    _instance = _get_object(series)
    return _instance.rdivmod()

@mcp.tool(name="series_reindex")
def series_reindex(series: str) -> Any:
    """Conform Series to new index with optional filling logic."""
    _instance = _get_object(series)
    return _instance.reindex()

@mcp.tool(name="series_reindex_like")
def series_reindex_like(series: str) -> Any:
    """Return an object with matching indices as other object."""
    _instance = _get_object(series)
    return _instance.reindex_like()

@mcp.tool(name="series_rename")
def series_rename(series: str) -> Any:
    """Alter Series index labels or name."""
    _instance = _get_object(series)
    return _instance.rename()

@mcp.tool(name="series_rename_axis")
def series_rename_axis(series: str) -> Any:
    """Set the name of the axis for the index or columns."""
    _instance = _get_object(series)
    return _instance.rename_axis()

@mcp.tool(name="series_reorder_levels")
def series_reorder_levels(series: str) -> Any:
    """Rearrange index levels using input order."""
    _instance = _get_object(series)
    return _instance.reorder_levels()

@mcp.tool(name="series_repeat")
def series_repeat(series: str) -> Any:
    """Repeat elements of a Series."""
    _instance = _get_object(series)
    return _instance.repeat()

@mcp.tool(name="series_replace")
def series_replace(series: str) -> Any:
    """Replace values given in `to_replace` with `value`."""
    _instance = _get_object(series)
    return _instance.replace()

@mcp.tool(name="series_resample")
def series_resample(series: str) -> Any:
    """Resample time-series data."""
    _instance = _get_object(series)
    return _instance.resample()

@mcp.tool(name="series_reset_index")
def series_reset_index(series: str) -> Any:
    """Generate a new DataFrame or Series with the index reset."""
    _instance = _get_object(series)
    return _instance.reset_index()

@mcp.tool(name="series_rfloordiv")
def series_rfloordiv(series: str) -> Any:
    """Return Integer division of series and other, element-wise (binary operator `rfloordiv`)."""
    _instance = _get_object(series)
    return _instance.rfloordiv()

@mcp.tool(name="series_rmod")
def series_rmod(series: str) -> Any:
    """Return Modulo of series and other, element-wise (binary operator `rmod`)."""
    _instance = _get_object(series)
    return _instance.rmod()

@mcp.tool(name="series_rmul")
def series_rmul(series: str) -> Any:
    """Return Multiplication of series and other, element-wise (binary operator `rmul`)."""
    _instance = _get_object(series)
    return _instance.rmul()

@mcp.tool(name="series_rolling")
def series_rolling(series: str) -> Any:
    """Provide rolling window calculations."""
    _instance = _get_object(series)
    return _instance.rolling()

@mcp.tool(name="series_round")
def series_round(series: str) -> Any:
    """Round each value in a Series to the given number of decimals."""
    _instance = _get_object(series)
    return _instance.round()

@mcp.tool(name="series_rpow")
def series_rpow(series: str) -> Any:
    """Return Exponential power of series and other, element-wise (binary operator `rpow`)."""
    _instance = _get_object(series)
    return _instance.rpow()

@mcp.tool(name="series_rsub")
def series_rsub(series: str) -> Any:
    """Return Subtraction of series and other, element-wise (binary operator `rsub`)."""
    _instance = _get_object(series)
    return _instance.rsub()

@mcp.tool(name="series_rtruediv")
def series_rtruediv(series: str) -> Any:
    """Return Floating division of series and other, element-wise (binary operator `rtruediv`)."""
    _instance = _get_object(series)
    return _instance.rtruediv()

@mcp.tool(name="series_sample")
def series_sample(series: str) -> Any:
    """Return a random sample of items from an axis of object."""
    _instance = _get_object(series)
    return _instance.sample()

@mcp.tool(name="series_searchsorted")
def series_searchsorted(series: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(series)
    return _instance.searchsorted()

@mcp.tool(name="series_sem")
def series_sem(series: str) -> Any:
    """Return unbiased standard error of the mean over requested axis."""
    _instance = _get_object(series)
    return _instance.sem()

@mcp.tool(name="series_set_axis")
def series_set_axis(series: str) -> Any:
    """Assign desired index to given axis."""
    _instance = _get_object(series)
    return _instance.set_axis()

@mcp.tool(name="series_set_flags")
def series_set_flags(series: str) -> Any:
    """Return a new object with updated flags."""
    _instance = _get_object(series)
    return _instance.set_flags()

@mcp.tool(name="series_shift")
def series_shift(series: str) -> Any:
    """Shift index by desired number of periods with an optional time `freq`."""
    _instance = _get_object(series)
    return _instance.shift()

@mcp.tool(name="series_skew")
def series_skew(series: str) -> Any:
    """Return unbiased skew over requested axis."""
    _instance = _get_object(series)
    return _instance.skew()

@mcp.tool(name="series_sort_index")
def series_sort_index(series: str) -> Any:
    """Sort Series by index labels."""
    _instance = _get_object(series)
    return _instance.sort_index()

@mcp.tool(name="series_sort_values")
def series_sort_values(series: str) -> Any:
    """Sort by the values."""
    _instance = _get_object(series)
    return _instance.sort_values()

@mcp.tool(name="series_squeeze")
def series_squeeze(series: str) -> Any:
    """Squeeze 1 dimensional axis objects into scalars."""
    _instance = _get_object(series)
    return _instance.squeeze()

@mcp.tool(name="series_std")
def series_std(series: str) -> Any:
    """Return sample standard deviation over requested axis."""
    _instance = _get_object(series)
    return _instance.std()

@mcp.tool(name="series_sub")
def series_sub(series: str) -> Any:
    """Return Subtraction of series and other, element-wise (binary operator `sub`)."""
    _instance = _get_object(series)
    return _instance.sub()

@mcp.tool(name="series_subtract")
def series_subtract(series: str) -> Any:
    """Return Subtraction of series and other, element-wise (binary operator `sub`)."""
    _instance = _get_object(series)
    return _instance.subtract()

@mcp.tool(name="series_sum")
def series_sum(series: str) -> Any:
    """Return the sum of the values over the requested axis."""
    _instance = _get_object(series)
    return _instance.sum()

@mcp.tool(name="series_swapaxes")
def series_swapaxes(series: str) -> Any:
    """Interchange axes and swap values axes appropriately."""
    _instance = _get_object(series)
    return _instance.swapaxes()

@mcp.tool(name="series_swaplevel")
def series_swaplevel(series: str) -> Any:
    """Swap levels i and j in a :class:`MultiIndex`."""
    _instance = _get_object(series)
    return _instance.swaplevel()

@mcp.tool(name="series_tail")
def series_tail(series: str) -> Any:
    """Return the last `n` rows."""
    _instance = _get_object(series)
    return _instance.tail()

@mcp.tool(name="series_take")
def series_take(series: str) -> Any:
    """Return the elements in the given *positional* indices along an axis."""
    _instance = _get_object(series)
    return _instance.take()

@mcp.tool(name="series_to_clipboard")
def series_to_clipboard(series: str) -> Any:
    """Copy object to the system clipboard."""
    _instance = _get_object(series)
    return _instance.to_clipboard()

@mcp.tool(name="series_to_csv")
def series_to_csv(series: str) -> Any:
    """Write object to a comma-separated values (csv) file."""
    _instance = _get_object(series)
    return _instance.to_csv()

@mcp.tool(name="series_to_dict")
def series_to_dict(series: str) -> Any:
    """Convert Series to {label -> value} dict or dict-like object."""
    _instance = _get_object(series)
    return _instance.to_dict()

@mcp.tool(name="series_to_excel")
def series_to_excel(series: str) -> Any:
    """Write object to an Excel sheet."""
    _instance = _get_object(series)
    return _instance.to_excel()

@mcp.tool(name="series_to_frame")
def series_to_frame(series: str) -> Any:
    """Convert Series to DataFrame."""
    _instance = _get_object(series)
    return _instance.to_frame()

@mcp.tool(name="series_to_hdf")
def series_to_hdf(series: str) -> Any:
    """Write the contained data to an HDF5 file using HDFStore."""
    _instance = _get_object(series)
    return _instance.to_hdf()

@mcp.tool(name="series_to_json")
def series_to_json(series: str) -> Any:
    """Convert the object to a JSON string."""
    _instance = _get_object(series)
    return _instance.to_json()

@mcp.tool(name="series_to_latex")
def series_to_latex(series: str) -> Any:
    """Render object to a LaTeX tabular, longtable, or nested table."""
    _instance = _get_object(series)
    return _instance.to_latex()

@mcp.tool(name="series_to_list")
def series_to_list(series: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(series)
    return _instance.to_list()

@mcp.tool(name="series_to_markdown")
def series_to_markdown(series: str) -> Any:
    """Print Series in Markdown-friendly format."""
    _instance = _get_object(series)
    return _instance.to_markdown()

@mcp.tool(name="series_to_numpy")
def series_to_numpy(series: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(series)
    return _instance.to_numpy()

@mcp.tool(name="series_to_period")
def series_to_period(series: str) -> Any:
    """Convert Series from DatetimeIndex to PeriodIndex."""
    _instance = _get_object(series)
    return _instance.to_period()

@mcp.tool(name="series_to_pickle")
def series_to_pickle(series: str) -> Any:
    """Pickle (serialize) object to file."""
    _instance = _get_object(series)
    return _instance.to_pickle()

@mcp.tool(name="series_to_sql")
def series_to_sql(series: str) -> Any:
    """Write records stored in a DataFrame to a SQL database."""
    _instance = _get_object(series)
    return _instance.to_sql()

@mcp.tool(name="series_to_string")
def series_to_string(series: str) -> Any:
    """Render a string representation of the Series."""
    _instance = _get_object(series)
    return _instance.to_string()

@mcp.tool(name="series_to_timestamp")
def series_to_timestamp(series: str) -> Any:
    """Cast to DatetimeIndex of Timestamps, at *beginning* of period."""
    _instance = _get_object(series)
    return _instance.to_timestamp()

@mcp.tool(name="series_to_xarray")
def series_to_xarray(series: str) -> Any:
    """Return an xarray object from the pandas object."""
    _instance = _get_object(series)
    return _instance.to_xarray()

@mcp.tool(name="series_tolist")
def series_tolist(series: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(series)
    return _instance.tolist()

@mcp.tool(name="series_transform")
def series_transform(series: str) -> Any:
    """Call ``func`` on self producing a Series with the same axis shape as self."""
    _instance = _get_object(series)
    return _instance.transform()

@mcp.tool(name="series_transpose")
def series_transpose(series: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(series)
    return _instance.transpose()

@mcp.tool(name="series_truediv")
def series_truediv(series: str) -> Any:
    """Return Floating division of series and other, element-wise (binary operator `truediv`)."""
    _instance = _get_object(series)
    return _instance.truediv()

@mcp.tool(name="series_truncate")
def series_truncate(series: str) -> Any:
    """Truncate a Series or DataFrame before and after some index value."""
    _instance = _get_object(series)
    return _instance.truncate()

@mcp.tool(name="series_tz_convert")
def series_tz_convert(series: str) -> Any:
    """Convert tz-aware axis to target time zone."""
    _instance = _get_object(series)
    return _instance.tz_convert()

@mcp.tool(name="series_tz_localize")
def series_tz_localize(series: str) -> Any:
    """Localize tz-naive index of a Series or DataFrame to target time zone."""
    _instance = _get_object(series)
    return _instance.tz_localize()

@mcp.tool(name="series_unique")
def series_unique(series: str) -> Any:
    """Return unique values of Series object."""
    _instance = _get_object(series)
    return _instance.unique()

@mcp.tool(name="series_unstack")
def series_unstack(series: str) -> Any:
    """Unstack, also known as pivot, Series with MultiIndex to produce DataFrame."""
    _instance = _get_object(series)
    return _instance.unstack()

@mcp.tool(name="series_update")
def series_update(series: str) -> Any:
    """Modify Series in place using values from passed Series."""
    _instance = _get_object(series)
    return _instance.update()

@mcp.tool(name="series_value_counts")
def series_value_counts(series: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(series)
    return _instance.value_counts()

@mcp.tool(name="series_var")
def series_var(series: str) -> Any:
    """Return unbiased variance over requested axis."""
    _instance = _get_object(series)
    return _instance.var()

@mcp.tool(name="series_view")
def series_view(series: str) -> Any:
    """Create a new view of the Series."""
    _instance = _get_object(series)
    return _instance.view()

@mcp.tool(name="series_where")
def series_where(series: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(series)
    return _instance.where()

@mcp.tool(name="series_xs")
def series_xs(series: str) -> Any:
    """Return cross-section from the Series/DataFrame."""
    _instance = _get_object(series)
    return _instance.xs()

@mcp.tool(name="sparsedtype_construct_array_type")
def sparsedtype_construct_array_type(sparsedtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(sparsedtype)
    return _instance.construct_array_type()

@mcp.tool(name="sparsedtype_construct_from_string")
def sparsedtype_construct_from_string(sparsedtype: str) -> Any:
    """Construct a SparseDtype from a string form."""
    _instance = _get_object(sparsedtype)
    return _instance.construct_from_string()

@mcp.tool(name="sparsedtype_empty")
def sparsedtype_empty(sparsedtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(sparsedtype)
    return _instance.empty()

@mcp.tool(name="sparsedtype_is_dtype")
def sparsedtype_is_dtype(sparsedtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(sparsedtype)
    return _instance.is_dtype()

@mcp.tool(name="sparsedtype_update_dtype")
def sparsedtype_update_dtype(sparsedtype: str) -> Any:
    """Convert the SparseDtype to a new dtype."""
    _instance = _get_object(sparsedtype)
    return _instance.update_dtype()

@mcp.tool(name="stringdtype_construct_array_type")
def stringdtype_construct_array_type(stringdtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(stringdtype)
    return _instance.construct_array_type()

@mcp.tool(name="stringdtype_construct_from_string")
def stringdtype_construct_from_string(stringdtype: str) -> Any:
    """Construct a StringDtype from a string."""
    _instance = _get_object(stringdtype)
    return _instance.construct_from_string()

@mcp.tool(name="stringdtype_empty")
def stringdtype_empty(stringdtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(stringdtype)
    return _instance.empty()

@mcp.tool(name="stringdtype_is_dtype")
def stringdtype_is_dtype(stringdtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(stringdtype)
    return _instance.is_dtype()

@mcp.tool(name="timedelta_as_unit")
def timedelta_as_unit(timedelta: str) -> Any:
    """Convert the underlying int64 representation to the given unit."""
    _instance = _get_object(timedelta)
    return _instance.as_unit()

@mcp.tool(name="timedelta_ceil")
def timedelta_ceil(timedelta: str) -> Any:
    """Return a new Timedelta ceiled to this resolution."""
    _instance = _get_object(timedelta)
    return _instance.ceil()

@mcp.tool(name="timedelta_floor")
def timedelta_floor(timedelta: str) -> Any:
    """Return a new Timedelta floored to this resolution."""
    _instance = _get_object(timedelta)
    return _instance.floor()

@mcp.tool(name="timedelta_isoformat")
def timedelta_isoformat(timedelta: str) -> Any:
    """Format the Timedelta as ISO 8601 Duration."""
    _instance = _get_object(timedelta)
    return _instance.isoformat()

@mcp.tool(name="timedelta_round")
def timedelta_round(timedelta: str) -> Any:
    """Round the Timedelta to the specified resolution."""
    _instance = _get_object(timedelta)
    return _instance.round()

@mcp.tool(name="timedelta_to_numpy")
def timedelta_to_numpy(timedelta: str) -> Any:
    """Convert the Timedelta to a NumPy timedelta64."""
    _instance = _get_object(timedelta)
    return _instance.to_numpy()

@mcp.tool(name="timedelta_to_pytimedelta")
def timedelta_to_pytimedelta(timedelta: str) -> Any:
    """Convert a pandas Timedelta object into a python ``datetime.timedelta`` object."""
    _instance = _get_object(timedelta)
    return _instance.to_pytimedelta()

@mcp.tool(name="timedelta_to_timedelta64")
def timedelta_to_timedelta64(timedelta: str) -> Any:
    """Return a numpy.timedelta64 object with 'ns' precision."""
    _instance = _get_object(timedelta)
    return _instance.to_timedelta64()

@mcp.tool(name="timedelta_total_seconds")
def timedelta_total_seconds(timedelta: str) -> Any:
    """Total seconds in the duration."""
    _instance = _get_object(timedelta)
    return _instance.total_seconds()

@mcp.tool(name="timedelta_view")
def timedelta_view(timedelta: str) -> Any:
    """Array view compatibility."""
    _instance = _get_object(timedelta)
    return _instance.view()

@mcp.tool(name="timedeltaindex_all")
def timedeltaindex_all(timedeltaindex: str) -> Any:
    """Return whether all elements are Truthy."""
    _instance = _get_object(timedeltaindex)
    return _instance.all()

@mcp.tool(name="timedeltaindex_any")
def timedeltaindex_any(timedeltaindex: str) -> Any:
    """Return whether any element is Truthy."""
    _instance = _get_object(timedeltaindex)
    return _instance.any()

@mcp.tool(name="timedeltaindex_append")
def timedeltaindex_append(timedeltaindex: str) -> Any:
    """Append a collection of Index options together."""
    _instance = _get_object(timedeltaindex)
    return _instance.append()

@mcp.tool(name="timedeltaindex_argmax")
def timedeltaindex_argmax(timedeltaindex: str) -> Any:
    """Return int position of the largest value in the Series."""
    _instance = _get_object(timedeltaindex)
    return _instance.argmax()

@mcp.tool(name="timedeltaindex_argmin")
def timedeltaindex_argmin(timedeltaindex: str) -> Any:
    """Return int position of the smallest value in the Series."""
    _instance = _get_object(timedeltaindex)
    return _instance.argmin()

@mcp.tool(name="timedeltaindex_argsort")
def timedeltaindex_argsort(timedeltaindex: str) -> Any:
    """Return the integer indices that would sort the index."""
    _instance = _get_object(timedeltaindex)
    return _instance.argsort()

@mcp.tool(name="timedeltaindex_as_unit")
def timedeltaindex_as_unit(timedeltaindex: str) -> Any:
    """Convert to a dtype with the given unit resolution."""
    _instance = _get_object(timedeltaindex)
    return _instance.as_unit()

@mcp.tool(name="timedeltaindex_asof")
def timedeltaindex_asof(timedeltaindex: str) -> Any:
    """Return the label from the index, or, if not present, the previous one."""
    _instance = _get_object(timedeltaindex)
    return _instance.asof()

@mcp.tool(name="timedeltaindex_asof_locs")
def timedeltaindex_asof_locs(timedeltaindex: str) -> Any:
    """Return the locations (indices) of labels in the index."""
    _instance = _get_object(timedeltaindex)
    return _instance.asof_locs()

@mcp.tool(name="timedeltaindex_astype")
def timedeltaindex_astype(timedeltaindex: str) -> Any:
    """Create an Index with values cast to dtypes."""
    _instance = _get_object(timedeltaindex)
    return _instance.astype()

@mcp.tool(name="timedeltaindex_ceil")
def timedeltaindex_ceil(timedeltaindex: str) -> Any:
    """Perform ceil operation on the data to the specified `freq`."""
    _instance = _get_object(timedeltaindex)
    return _instance.ceil()

@mcp.tool(name="timedeltaindex_copy")
def timedeltaindex_copy(timedeltaindex: str) -> Any:
    """Make a copy of this object."""
    _instance = _get_object(timedeltaindex)
    return _instance.copy()

@mcp.tool(name="timedeltaindex_delete")
def timedeltaindex_delete(timedeltaindex: str) -> Any:
    """Make new Index with passed location(-s) deleted."""
    _instance = _get_object(timedeltaindex)
    return _instance.delete()

@mcp.tool(name="timedeltaindex_diff")
def timedeltaindex_diff(timedeltaindex: str) -> Any:
    """Computes the difference between consecutive values in the Index object."""
    _instance = _get_object(timedeltaindex)
    return _instance.diff()

@mcp.tool(name="timedeltaindex_difference")
def timedeltaindex_difference(timedeltaindex: str) -> Any:
    """Return a new Index with elements of index not in `other`."""
    _instance = _get_object(timedeltaindex)
    return _instance.difference()

@mcp.tool(name="timedeltaindex_drop")
def timedeltaindex_drop(timedeltaindex: str) -> Any:
    """Make new Index with passed list of labels deleted."""
    _instance = _get_object(timedeltaindex)
    return _instance.drop()

@mcp.tool(name="timedeltaindex_drop_duplicates")
def timedeltaindex_drop_duplicates(timedeltaindex: str) -> Any:
    """Return Index with duplicate values removed."""
    _instance = _get_object(timedeltaindex)
    return _instance.drop_duplicates()

@mcp.tool(name="timedeltaindex_droplevel")
def timedeltaindex_droplevel(timedeltaindex: str) -> Any:
    """Return index with requested level(s) removed."""
    _instance = _get_object(timedeltaindex)
    return _instance.droplevel()

@mcp.tool(name="timedeltaindex_dropna")
def timedeltaindex_dropna(timedeltaindex: str) -> Any:
    """Return Index without NA/NaN values."""
    _instance = _get_object(timedeltaindex)
    return _instance.dropna()

@mcp.tool(name="timedeltaindex_duplicated")
def timedeltaindex_duplicated(timedeltaindex: str) -> Any:
    """Indicate duplicate index values."""
    _instance = _get_object(timedeltaindex)
    return _instance.duplicated()

@mcp.tool(name="timedeltaindex_equals")
def timedeltaindex_equals(timedeltaindex: str) -> Any:
    """Determines if two Index objects contain the same elements."""
    _instance = _get_object(timedeltaindex)
    return _instance.equals()

@mcp.tool(name="timedeltaindex_factorize")
def timedeltaindex_factorize(timedeltaindex: str) -> Any:
    """Encode the object as an enumerated type or categorical variable."""
    _instance = _get_object(timedeltaindex)
    return _instance.factorize()

@mcp.tool(name="timedeltaindex_fillna")
def timedeltaindex_fillna(timedeltaindex: str) -> Any:
    """Fill NA/NaN values with the specified value."""
    _instance = _get_object(timedeltaindex)
    return _instance.fillna()

@mcp.tool(name="timedeltaindex_floor")
def timedeltaindex_floor(timedeltaindex: str) -> Any:
    """Perform floor operation on the data to the specified `freq`."""
    _instance = _get_object(timedeltaindex)
    return _instance.floor()

@mcp.tool(name="timedeltaindex_format")
def timedeltaindex_format(timedeltaindex: str) -> Any:
    """Render a string representation of the Index."""
    _instance = _get_object(timedeltaindex)
    return _instance.format()

@mcp.tool(name="timedeltaindex_get_indexer")
def timedeltaindex_get_indexer(timedeltaindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(timedeltaindex)
    return _instance.get_indexer()

@mcp.tool(name="timedeltaindex_get_indexer_for")
def timedeltaindex_get_indexer_for(timedeltaindex: str) -> Any:
    """Guaranteed return of an indexer even when non-unique."""
    _instance = _get_object(timedeltaindex)
    return _instance.get_indexer_for()

@mcp.tool(name="timedeltaindex_get_indexer_non_unique")
def timedeltaindex_get_indexer_non_unique(timedeltaindex: str) -> Any:
    """Compute indexer and mask for new index given the current index."""
    _instance = _get_object(timedeltaindex)
    return _instance.get_indexer_non_unique()

@mcp.tool(name="timedeltaindex_get_level_values")
def timedeltaindex_get_level_values(timedeltaindex: str) -> Any:
    """Return an Index of values for requested level."""
    _instance = _get_object(timedeltaindex)
    return _instance.get_level_values()

@mcp.tool(name="timedeltaindex_get_loc")
def timedeltaindex_get_loc(timedeltaindex: str) -> Any:
    """Get integer location for requested label"""
    _instance = _get_object(timedeltaindex)
    return _instance.get_loc()

@mcp.tool(name="timedeltaindex_get_slice_bound")
def timedeltaindex_get_slice_bound(timedeltaindex: str) -> Any:
    """Calculate slice bound that corresponds to given label."""
    _instance = _get_object(timedeltaindex)
    return _instance.get_slice_bound()

@mcp.tool(name="timedeltaindex_groupby")
def timedeltaindex_groupby(timedeltaindex: str) -> Any:
    """Group the index labels by a given array of values."""
    _instance = _get_object(timedeltaindex)
    return _instance.groupby()

@mcp.tool(name="timedeltaindex_holds_integer")
def timedeltaindex_holds_integer(timedeltaindex: str) -> Any:
    """Whether the type is an integer type."""
    _instance = _get_object(timedeltaindex)
    return _instance.holds_integer()

@mcp.tool(name="timedeltaindex_identical")
def timedeltaindex_identical(timedeltaindex: str) -> Any:
    """Similar to equals, but checks that object attributes and types are also equal."""
    _instance = _get_object(timedeltaindex)
    return _instance.identical()

@mcp.tool(name="timedeltaindex_infer_objects")
def timedeltaindex_infer_objects(timedeltaindex: str) -> Any:
    """If we have an object dtype, try to infer a non-object dtype."""
    _instance = _get_object(timedeltaindex)
    return _instance.infer_objects()

@mcp.tool(name="timedeltaindex_insert")
def timedeltaindex_insert(timedeltaindex: str) -> Any:
    """Make new Index inserting new item at location."""
    _instance = _get_object(timedeltaindex)
    return _instance.insert()

@mcp.tool(name="timedeltaindex_intersection")
def timedeltaindex_intersection(timedeltaindex: str) -> Any:
    """Form the intersection of two Index objects."""
    _instance = _get_object(timedeltaindex)
    return _instance.intersection()

@mcp.tool(name="timedeltaindex_is_")
def timedeltaindex_is_(timedeltaindex: str) -> Any:
    """More flexible, faster check like ``is`` but that works through views."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_()

@mcp.tool(name="timedeltaindex_is_boolean")
def timedeltaindex_is_boolean(timedeltaindex: str) -> Any:
    """Check if the Index only consists of booleans."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_boolean()

@mcp.tool(name="timedeltaindex_is_categorical")
def timedeltaindex_is_categorical(timedeltaindex: str) -> Any:
    """Check if the Index holds categorical data."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_categorical()

@mcp.tool(name="timedeltaindex_is_floating")
def timedeltaindex_is_floating(timedeltaindex: str) -> Any:
    """Check if the Index is a floating type."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_floating()

@mcp.tool(name="timedeltaindex_is_integer")
def timedeltaindex_is_integer(timedeltaindex: str) -> Any:
    """Check if the Index only consists of integers."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_integer()

@mcp.tool(name="timedeltaindex_is_interval")
def timedeltaindex_is_interval(timedeltaindex: str) -> Any:
    """Check if the Index holds Interval objects."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_interval()

@mcp.tool(name="timedeltaindex_is_numeric")
def timedeltaindex_is_numeric(timedeltaindex: str) -> Any:
    """Check if the Index only consists of numeric data."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_numeric()

@mcp.tool(name="timedeltaindex_is_object")
def timedeltaindex_is_object(timedeltaindex: str) -> Any:
    """Check if the Index is of the object dtype."""
    _instance = _get_object(timedeltaindex)
    return _instance.is_object()

@mcp.tool(name="timedeltaindex_isin")
def timedeltaindex_isin(timedeltaindex: str) -> Any:
    """Return a boolean array where the index values are in `values`."""
    _instance = _get_object(timedeltaindex)
    return _instance.isin()

@mcp.tool(name="timedeltaindex_isna")
def timedeltaindex_isna(timedeltaindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(timedeltaindex)
    return _instance.isna()

@mcp.tool(name="timedeltaindex_isnull")
def timedeltaindex_isnull(timedeltaindex: str) -> Any:
    """Detect missing values."""
    _instance = _get_object(timedeltaindex)
    return _instance.isnull()

@mcp.tool(name="timedeltaindex_item")
def timedeltaindex_item(timedeltaindex: str) -> Any:
    """Return the first element of the underlying data as a Python scalar."""
    _instance = _get_object(timedeltaindex)
    return _instance.item()

@mcp.tool(name="timedeltaindex_join")
def timedeltaindex_join(timedeltaindex: str) -> Any:
    """Compute join_index and indexers to conform data structures to the new index."""
    _instance = _get_object(timedeltaindex)
    return _instance.join()

@mcp.tool(name="timedeltaindex_map")
def timedeltaindex_map(timedeltaindex: str) -> Any:
    """Map values using an input mapping or function."""
    _instance = _get_object(timedeltaindex)
    return _instance.map()

@mcp.tool(name="timedeltaindex_max")
def timedeltaindex_max(timedeltaindex: str) -> Any:
    """Return the maximum value of the Index."""
    _instance = _get_object(timedeltaindex)
    return _instance.max()

@mcp.tool(name="timedeltaindex_mean")
def timedeltaindex_mean(timedeltaindex: str) -> Any:
    """Return the mean value of the Array."""
    _instance = _get_object(timedeltaindex)
    return _instance.mean()

@mcp.tool(name="timedeltaindex_median")
def timedeltaindex_median(timedeltaindex: str) -> Any:
    """Tool: timedeltaindex_median"""
    _instance = _get_object(timedeltaindex)
    return _instance.median()

@mcp.tool(name="timedeltaindex_memory_usage")
def timedeltaindex_memory_usage(timedeltaindex: str) -> Any:
    """Memory usage of the values."""
    _instance = _get_object(timedeltaindex)
    return _instance.memory_usage()

@mcp.tool(name="timedeltaindex_min")
def timedeltaindex_min(timedeltaindex: str) -> Any:
    """Return the minimum value of the Index."""
    _instance = _get_object(timedeltaindex)
    return _instance.min()

@mcp.tool(name="timedeltaindex_notna")
def timedeltaindex_notna(timedeltaindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(timedeltaindex)
    return _instance.notna()

@mcp.tool(name="timedeltaindex_notnull")
def timedeltaindex_notnull(timedeltaindex: str) -> Any:
    """Detect existing (non-missing) values."""
    _instance = _get_object(timedeltaindex)
    return _instance.notnull()

@mcp.tool(name="timedeltaindex_nunique")
def timedeltaindex_nunique(timedeltaindex: str) -> Any:
    """Return number of unique elements in the object."""
    _instance = _get_object(timedeltaindex)
    return _instance.nunique()

@mcp.tool(name="timedeltaindex_putmask")
def timedeltaindex_putmask(timedeltaindex: str) -> Any:
    """Return a new Index of the values set with the mask."""
    _instance = _get_object(timedeltaindex)
    return _instance.putmask()

@mcp.tool(name="timedeltaindex_ravel")
def timedeltaindex_ravel(timedeltaindex: str) -> Any:
    """Return a view on self."""
    _instance = _get_object(timedeltaindex)
    return _instance.ravel()

@mcp.tool(name="timedeltaindex_reindex")
def timedeltaindex_reindex(timedeltaindex: str) -> Any:
    """Create index with target's values."""
    _instance = _get_object(timedeltaindex)
    return _instance.reindex()

@mcp.tool(name="timedeltaindex_rename")
def timedeltaindex_rename(timedeltaindex: str) -> Any:
    """Alter Index or MultiIndex name."""
    _instance = _get_object(timedeltaindex)
    return _instance.rename()

@mcp.tool(name="timedeltaindex_repeat")
def timedeltaindex_repeat(timedeltaindex: str) -> Any:
    """Repeat elements of a Index."""
    _instance = _get_object(timedeltaindex)
    return _instance.repeat()

@mcp.tool(name="timedeltaindex_round")
def timedeltaindex_round(timedeltaindex: str) -> Any:
    """Perform round operation on the data to the specified `freq`."""
    _instance = _get_object(timedeltaindex)
    return _instance.round()

@mcp.tool(name="timedeltaindex_searchsorted")
def timedeltaindex_searchsorted(timedeltaindex: str) -> Any:
    """Find indices where elements should be inserted to maintain order."""
    _instance = _get_object(timedeltaindex)
    return _instance.searchsorted()

@mcp.tool(name="timedeltaindex_set_names")
def timedeltaindex_set_names(timedeltaindex: str) -> Any:
    """Set Index or MultiIndex name."""
    _instance = _get_object(timedeltaindex)
    return _instance.set_names()

@mcp.tool(name="timedeltaindex_shift")
def timedeltaindex_shift(timedeltaindex: str) -> Any:
    """Shift index by desired number of time frequency increments."""
    _instance = _get_object(timedeltaindex)
    return _instance.shift()

@mcp.tool(name="timedeltaindex_slice_indexer")
def timedeltaindex_slice_indexer(timedeltaindex: str) -> Any:
    """Compute the slice indexer for input labels and step."""
    _instance = _get_object(timedeltaindex)
    return _instance.slice_indexer()

@mcp.tool(name="timedeltaindex_slice_locs")
def timedeltaindex_slice_locs(timedeltaindex: str) -> Any:
    """Compute slice locations for input labels."""
    _instance = _get_object(timedeltaindex)
    return _instance.slice_locs()

@mcp.tool(name="timedeltaindex_sort")
def timedeltaindex_sort(timedeltaindex: str) -> Any:
    """Use sort_values instead."""
    _instance = _get_object(timedeltaindex)
    return _instance.sort()

@mcp.tool(name="timedeltaindex_sort_values")
def timedeltaindex_sort_values(timedeltaindex: str) -> Any:
    """Return a sorted copy of the index."""
    _instance = _get_object(timedeltaindex)
    return _instance.sort_values()

@mcp.tool(name="timedeltaindex_sortlevel")
def timedeltaindex_sortlevel(timedeltaindex: str) -> Any:
    """For internal compatibility with the Index API."""
    _instance = _get_object(timedeltaindex)
    return _instance.sortlevel()

@mcp.tool(name="timedeltaindex_std")
def timedeltaindex_std(timedeltaindex: str) -> Any:
    """Tool: timedeltaindex_std"""
    _instance = _get_object(timedeltaindex)
    return _instance.std()

@mcp.tool(name="timedeltaindex_sum")
def timedeltaindex_sum(timedeltaindex: str) -> Any:
    """Tool: timedeltaindex_sum"""
    _instance = _get_object(timedeltaindex)
    return _instance.sum()

@mcp.tool(name="timedeltaindex_symmetric_difference")
def timedeltaindex_symmetric_difference(timedeltaindex: str) -> Any:
    """Compute the symmetric difference of two Index objects."""
    _instance = _get_object(timedeltaindex)
    return _instance.symmetric_difference()

@mcp.tool(name="timedeltaindex_take")
def timedeltaindex_take(timedeltaindex: str) -> Any:
    """Return a new Index of the values selected by the indices."""
    _instance = _get_object(timedeltaindex)
    return _instance.take()

@mcp.tool(name="timedeltaindex_to_flat_index")
def timedeltaindex_to_flat_index(timedeltaindex: str) -> Any:
    """Identity method."""
    _instance = _get_object(timedeltaindex)
    return _instance.to_flat_index()

@mcp.tool(name="timedeltaindex_to_frame")
def timedeltaindex_to_frame(timedeltaindex: str) -> Any:
    """Create a DataFrame with a column containing the Index."""
    _instance = _get_object(timedeltaindex)
    return _instance.to_frame()

@mcp.tool(name="timedeltaindex_to_list")
def timedeltaindex_to_list(timedeltaindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(timedeltaindex)
    return _instance.to_list()

@mcp.tool(name="timedeltaindex_to_numpy")
def timedeltaindex_to_numpy(timedeltaindex: str) -> Any:
    """A NumPy ndarray representing the values in this Series or Index."""
    _instance = _get_object(timedeltaindex)
    return _instance.to_numpy()

@mcp.tool(name="timedeltaindex_to_pytimedelta")
def timedeltaindex_to_pytimedelta(timedeltaindex: str) -> Any:
    """Return an ndarray of datetime.timedelta objects."""
    _instance = _get_object(timedeltaindex)
    return _instance.to_pytimedelta()

@mcp.tool(name="timedeltaindex_to_series")
def timedeltaindex_to_series(timedeltaindex: str) -> Any:
    """Create a Series with both index and values equal to the index keys."""
    _instance = _get_object(timedeltaindex)
    return _instance.to_series()

@mcp.tool(name="timedeltaindex_tolist")
def timedeltaindex_tolist(timedeltaindex: str) -> Any:
    """Return a list of the values."""
    _instance = _get_object(timedeltaindex)
    return _instance.tolist()

@mcp.tool(name="timedeltaindex_total_seconds")
def timedeltaindex_total_seconds(timedeltaindex: str) -> Any:
    """Return total duration of each element expressed in seconds."""
    _instance = _get_object(timedeltaindex)
    return _instance.total_seconds()

@mcp.tool(name="timedeltaindex_transpose")
def timedeltaindex_transpose(timedeltaindex: str) -> Any:
    """Return the transpose, which is by definition self."""
    _instance = _get_object(timedeltaindex)
    return _instance.transpose()

@mcp.tool(name="timedeltaindex_union")
def timedeltaindex_union(timedeltaindex: str) -> Any:
    """Form the union of two Index objects."""
    _instance = _get_object(timedeltaindex)
    return _instance.union()

@mcp.tool(name="timedeltaindex_unique")
def timedeltaindex_unique(timedeltaindex: str) -> Any:
    """Return unique values in the index."""
    _instance = _get_object(timedeltaindex)
    return _instance.unique()

@mcp.tool(name="timedeltaindex_value_counts")
def timedeltaindex_value_counts(timedeltaindex: str) -> Any:
    """Return a Series containing counts of unique values."""
    _instance = _get_object(timedeltaindex)
    return _instance.value_counts()

@mcp.tool(name="timedeltaindex_view")
def timedeltaindex_view(timedeltaindex: str) -> Any:
    """Tool: timedeltaindex_view"""
    _instance = _get_object(timedeltaindex)
    return _instance.view()

@mcp.tool(name="timedeltaindex_where")
def timedeltaindex_where(timedeltaindex: str) -> Any:
    """Replace values where the condition is False."""
    _instance = _get_object(timedeltaindex)
    return _instance.where()

@mcp.tool(name="timestamp_as_unit")
def timestamp_as_unit(timestamp: str) -> Any:
    """Convert the underlying int64 representaton to the given unit."""
    _instance = _get_object(timestamp)
    return _instance.as_unit()

@mcp.tool(name="timestamp_astimezone")
def timestamp_astimezone(timestamp: str) -> Any:
    """Convert timezone-aware Timestamp to another time zone."""
    _instance = _get_object(timestamp)
    return _instance.astimezone()

@mcp.tool(name="timestamp_ceil")
def timestamp_ceil(timestamp: str) -> Any:
    """Return a new Timestamp ceiled to this resolution."""
    _instance = _get_object(timestamp)
    return _instance.ceil()

@mcp.tool(name="timestamp_combine")
def timestamp_combine(timestamp: str) -> Any:
    """Timestamp.combine(date, time)"""
    _instance = _get_object(timestamp)
    return _instance.combine()

@mcp.tool(name="timestamp_ctime")
def timestamp_ctime(timestamp: str) -> Any:
    """Return ctime() style string."""
    _instance = _get_object(timestamp)
    return _instance.ctime()

@mcp.tool(name="timestamp_date")
def timestamp_date(timestamp: str) -> Any:
    """Return date object with same year, month and day."""
    _instance = _get_object(timestamp)
    return _instance.date()

@mcp.tool(name="timestamp_day_name")
def timestamp_day_name(timestamp: str) -> Any:
    """Return the day name of the Timestamp with specified locale."""
    _instance = _get_object(timestamp)
    return _instance.day_name()

@mcp.tool(name="timestamp_dst")
def timestamp_dst(timestamp: str) -> Any:
    """Return the daylight saving time (DST) adjustment."""
    _instance = _get_object(timestamp)
    return _instance.dst()

@mcp.tool(name="timestamp_floor")
def timestamp_floor(timestamp: str) -> Any:
    """Return a new Timestamp floored to this resolution."""
    _instance = _get_object(timestamp)
    return _instance.floor()

@mcp.tool(name="timestamp_fromisocalendar")
def timestamp_fromisocalendar(timestamp: str) -> Any:
    """int, int, int -> Construct a date from the ISO year, week number and weekday."""
    _instance = _get_object(timestamp)
    return _instance.fromisocalendar()

@mcp.tool(name="timestamp_fromisoformat")
def timestamp_fromisoformat(timestamp: str) -> Any:
    """string -> datetime from a string in most ISO 8601 formats"""
    _instance = _get_object(timestamp)
    return _instance.fromisoformat()

@mcp.tool(name="timestamp_fromordinal")
def timestamp_fromordinal(timestamp: str) -> Any:
    """Construct a timestamp from a a proleptic Gregorian ordinal."""
    _instance = _get_object(timestamp)
    return _instance.fromordinal()

@mcp.tool(name="timestamp_fromtimestamp")
def timestamp_fromtimestamp(timestamp: str) -> Any:
    """Timestamp.fromtimestamp(ts)"""
    _instance = _get_object(timestamp)
    return _instance.fromtimestamp()

@mcp.tool(name="timestamp_isocalendar")
def timestamp_isocalendar(timestamp: str) -> Any:
    """Return a named tuple containing ISO year, week number, and weekday."""
    _instance = _get_object(timestamp)
    return _instance.isocalendar()

@mcp.tool(name="timestamp_isoformat")
def timestamp_isoformat(timestamp: str) -> Any:
    """Return the time formatted according to ISO 8601."""
    _instance = _get_object(timestamp)
    return _instance.isoformat()

@mcp.tool(name="timestamp_isoweekday")
def timestamp_isoweekday(timestamp: str) -> Any:
    """Return the day of the week represented by the date."""
    _instance = _get_object(timestamp)
    return _instance.isoweekday()

@mcp.tool(name="timestamp_month_name")
def timestamp_month_name(timestamp: str) -> Any:
    """Return the month name of the Timestamp with specified locale."""
    _instance = _get_object(timestamp)
    return _instance.month_name()

@mcp.tool(name="timestamp_normalize")
def timestamp_normalize(timestamp: str) -> Any:
    """Normalize Timestamp to midnight, preserving tz information."""
    _instance = _get_object(timestamp)
    return _instance.normalize()

@mcp.tool(name="timestamp_now")
def timestamp_now(timestamp: str) -> Any:
    """Return new Timestamp object representing current time local to tz."""
    _instance = _get_object(timestamp)
    return _instance.now()

@mcp.tool(name="timestamp_replace")
def timestamp_replace(timestamp: str) -> Any:
    """Implements datetime.replace, handles nanoseconds."""
    _instance = _get_object(timestamp)
    return _instance.replace()

@mcp.tool(name="timestamp_round")
def timestamp_round(timestamp: str) -> Any:
    """Round the Timestamp to the specified resolution."""
    _instance = _get_object(timestamp)
    return _instance.round()

@mcp.tool(name="timestamp_strftime")
def timestamp_strftime(timestamp: str) -> Any:
    """Return a formatted string of the Timestamp."""
    _instance = _get_object(timestamp)
    return _instance.strftime()

@mcp.tool(name="timestamp_strptime")
def timestamp_strptime(timestamp: str) -> Any:
    """Timestamp.strptime(string, format)"""
    _instance = _get_object(timestamp)
    return _instance.strptime()

@mcp.tool(name="timestamp_time")
def timestamp_time(timestamp: str) -> Any:
    """Return time object with same time but with tzinfo=None."""
    _instance = _get_object(timestamp)
    return _instance.time()

@mcp.tool(name="timestamp_timestamp")
def timestamp_timestamp(timestamp: str) -> Any:
    """Return POSIX timestamp as float."""
    _instance = _get_object(timestamp)
    return _instance.timestamp()

@mcp.tool(name="timestamp_timetuple")
def timestamp_timetuple(timestamp: str) -> Any:
    """Return time tuple, compatible with time.localtime()."""
    _instance = _get_object(timestamp)
    return _instance.timetuple()

@mcp.tool(name="timestamp_timetz")
def timestamp_timetz(timestamp: str) -> Any:
    """Return time object with same time and tzinfo."""
    _instance = _get_object(timestamp)
    return _instance.timetz()

@mcp.tool(name="timestamp_to_datetime64")
def timestamp_to_datetime64(timestamp: str) -> Any:
    """Return a numpy.datetime64 object with same precision."""
    _instance = _get_object(timestamp)
    return _instance.to_datetime64()

@mcp.tool(name="timestamp_to_julian_date")
def timestamp_to_julian_date(timestamp: str) -> Any:
    """Convert TimeStamp to a Julian Date."""
    _instance = _get_object(timestamp)
    return _instance.to_julian_date()

@mcp.tool(name="timestamp_to_numpy")
def timestamp_to_numpy(timestamp: str) -> Any:
    """Convert the Timestamp to a NumPy datetime64."""
    _instance = _get_object(timestamp)
    return _instance.to_numpy()

@mcp.tool(name="timestamp_to_period")
def timestamp_to_period(timestamp: str) -> Any:
    """Return an period of which this timestamp is an observation."""
    _instance = _get_object(timestamp)
    return _instance.to_period()

@mcp.tool(name="timestamp_to_pydatetime")
def timestamp_to_pydatetime(timestamp: str) -> Any:
    """Convert a Timestamp object to a native Python datetime object."""
    _instance = _get_object(timestamp)
    return _instance.to_pydatetime()

@mcp.tool(name="timestamp_today")
def timestamp_today(timestamp: str) -> Any:
    """Return the current time in the local timezone."""
    _instance = _get_object(timestamp)
    return _instance.today()

@mcp.tool(name="timestamp_toordinal")
def timestamp_toordinal(timestamp: str) -> Any:
    """Return proleptic Gregorian ordinal. January 1 of year 1 is day 1."""
    _instance = _get_object(timestamp)
    return _instance.toordinal()

@mcp.tool(name="timestamp_tz_convert")
def timestamp_tz_convert(timestamp: str) -> Any:
    """Convert timezone-aware Timestamp to another time zone."""
    _instance = _get_object(timestamp)
    return _instance.tz_convert()

@mcp.tool(name="timestamp_tz_localize")
def timestamp_tz_localize(timestamp: str) -> Any:
    """Localize the Timestamp to a timezone."""
    _instance = _get_object(timestamp)
    return _instance.tz_localize()

@mcp.tool(name="timestamp_tzname")
def timestamp_tzname(timestamp: str) -> Any:
    """Return time zone name."""
    _instance = _get_object(timestamp)
    return _instance.tzname()

@mcp.tool(name="timestamp_utcfromtimestamp")
def timestamp_utcfromtimestamp(timestamp: str) -> Any:
    """Timestamp.utcfromtimestamp(ts)"""
    _instance = _get_object(timestamp)
    return _instance.utcfromtimestamp()

@mcp.tool(name="timestamp_utcnow")
def timestamp_utcnow(timestamp: str) -> Any:
    """Timestamp.utcnow()"""
    _instance = _get_object(timestamp)
    return _instance.utcnow()

@mcp.tool(name="timestamp_utcoffset")
def timestamp_utcoffset(timestamp: str) -> Any:
    """Return utc offset."""
    _instance = _get_object(timestamp)
    return _instance.utcoffset()

@mcp.tool(name="timestamp_utctimetuple")
def timestamp_utctimetuple(timestamp: str) -> Any:
    """Return UTC time tuple, compatible with time.localtime()."""
    _instance = _get_object(timestamp)
    return _instance.utctimetuple()

@mcp.tool(name="timestamp_weekday")
def timestamp_weekday(timestamp: str) -> Any:
    """Return the day of the week represented by the date."""
    _instance = _get_object(timestamp)
    return _instance.weekday()

@mcp.tool(name="uint16dtype_construct_array_type")
def uint16dtype_construct_array_type(uint16dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(uint16dtype)
    return _instance.construct_array_type()

@mcp.tool(name="uint16dtype_construct_from_string")
def uint16dtype_construct_from_string(uint16dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(uint16dtype)
    return _instance.construct_from_string()

@mcp.tool(name="uint16dtype_empty")
def uint16dtype_empty(uint16dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(uint16dtype)
    return _instance.empty()

@mcp.tool(name="uint16dtype_from_numpy_dtype")
def uint16dtype_from_numpy_dtype(uint16dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(uint16dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="uint16dtype_is_dtype")
def uint16dtype_is_dtype(uint16dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(uint16dtype)
    return _instance.is_dtype()

@mcp.tool(name="uint32dtype_construct_array_type")
def uint32dtype_construct_array_type(uint32dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(uint32dtype)
    return _instance.construct_array_type()

@mcp.tool(name="uint32dtype_construct_from_string")
def uint32dtype_construct_from_string(uint32dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(uint32dtype)
    return _instance.construct_from_string()

@mcp.tool(name="uint32dtype_empty")
def uint32dtype_empty(uint32dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(uint32dtype)
    return _instance.empty()

@mcp.tool(name="uint32dtype_from_numpy_dtype")
def uint32dtype_from_numpy_dtype(uint32dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(uint32dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="uint32dtype_is_dtype")
def uint32dtype_is_dtype(uint32dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(uint32dtype)
    return _instance.is_dtype()

@mcp.tool(name="uint64dtype_construct_array_type")
def uint64dtype_construct_array_type(uint64dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(uint64dtype)
    return _instance.construct_array_type()

@mcp.tool(name="uint64dtype_construct_from_string")
def uint64dtype_construct_from_string(uint64dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(uint64dtype)
    return _instance.construct_from_string()

@mcp.tool(name="uint64dtype_empty")
def uint64dtype_empty(uint64dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(uint64dtype)
    return _instance.empty()

@mcp.tool(name="uint64dtype_from_numpy_dtype")
def uint64dtype_from_numpy_dtype(uint64dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(uint64dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="uint64dtype_is_dtype")
def uint64dtype_is_dtype(uint64dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(uint64dtype)
    return _instance.is_dtype()

@mcp.tool(name="uint8dtype_construct_array_type")
def uint8dtype_construct_array_type(uint8dtype: str) -> Any:
    """Return the array type associated with this dtype."""
    _instance = _get_object(uint8dtype)
    return _instance.construct_array_type()

@mcp.tool(name="uint8dtype_construct_from_string")
def uint8dtype_construct_from_string(uint8dtype: str) -> Any:
    """Construct this type from a string."""
    _instance = _get_object(uint8dtype)
    return _instance.construct_from_string()

@mcp.tool(name="uint8dtype_empty")
def uint8dtype_empty(uint8dtype: str) -> Any:
    """Construct an ExtensionArray of this dtype with the given shape."""
    _instance = _get_object(uint8dtype)
    return _instance.empty()

@mcp.tool(name="uint8dtype_from_numpy_dtype")
def uint8dtype_from_numpy_dtype(uint8dtype: str) -> Any:
    """Construct the MaskedDtype corresponding to the given numpy dtype."""
    _instance = _get_object(uint8dtype)
    return _instance.from_numpy_dtype()

@mcp.tool(name="uint8dtype_is_dtype")
def uint8dtype_is_dtype(uint8dtype: str) -> Any:
    """Check if we match 'dtype'."""
    _instance = _get_object(uint8dtype)
    return _instance.is_dtype()


if __name__ == "__main__":
    mcp.run()