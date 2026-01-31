from typing import List, Optional, Union

from pydantic.v1 import BaseModel

from fiddler.constants.model import DataType


class Column(BaseModel):
    """Represents a single column in a model schema with its metadata and constraints.

    A Column defines the structure and properties of a data column that will be used
    in a Fiddler model. It includes information about the column's data type, value
    ranges, categorical values, binning configuration, and other metadata necessary
    for proper data validation and monitoring.

    This class is used within ModelSchema to define the complete structure of data
    that a model expects to receive.

    Examples:
        Creating a numeric column:

        column = Column(
            name="age",
            data_type=DataType.INTEGER,
            min=0,
            max=120
        )

        Creating a categorical column:

        column = Column(
            name="category",
            data_type=DataType.CATEGORY,
            categories=["A", "B", "C"]
        )

        Creating a vector column:

        column = Column(
            name="embedding",
            data_type=DataType.VECTOR,
            n_dimensions=128
        )
    """

    name: str
    """Column name provided by the customer"""

    data_type: DataType
    """Data type of the column"""

    min: Optional[Union[int, float]] = None
    """Min value of integer/float column"""

    max: Optional[Union[int, float]] = None
    """Max value of integer/float column"""

    categories: Optional[List] = None
    """List of unique values of a categorical column"""

    bins: Optional[List[Union[int, float]]] = None
    """Bins of integer/float column"""

    replace_with_nulls: Optional[List] = None
    """Replace the list of given values to NULL if found in the events data"""

    n_dimensions: Optional[int] = None
    """Number of dimensions of a vector column"""

    class Config:
        smart_union = True


class ModelSchema(BaseModel):
    """Defines the complete schema structure for a model's input data.

    ModelSchema contains the specification of all columns that a model expects
    to receive, including their data types, constraints, and metadata. This schema
    is used by Fiddler for data validation, monitoring, and analysis purposes.

    The schema acts as a contract between your model and Fiddler, ensuring that
    incoming data conforms to expected formats and enabling proper drift detection,
    data quality monitoring, and other features.

    Attributes:
        schema_version: Version of the schema format (currently 1)
        columns: List of Column objects defining each field in the model input

    Examples:
        Creating a model schema:

        schema = ModelSchema(
            columns=[
                Column(name="age", data_type=DataType.INTEGER, min=0, max=120),
                Column(name="income", data_type=DataType.FLOAT, min=0),
                Column(name="category", data_type=DataType.CATEGORY,
                       categories=["A", "B", "C"])
            ]
        )

        Accessing columns by name:

        age_column = schema["age"]
        print(age_column.data_type)

        Adding a new column:

        new_column = Column(name="score", data_type=DataType.FLOAT)
        schema["score"] = new_column

        Removing a column:

        del schema["age"]
    """

    schema_version: int = 1
    """Schema version"""

    columns: List[Column]
    """List of columns"""

    def _col_index_from_name(self, name: str) -> int:
        """Look up the index of the column by name"""
        for i, col in enumerate(self.columns):
            if col.name == name:
                return i
        raise KeyError(name)

    def __getitem__(self, item: str) -> Column:
        """Get column by name"""
        return self.columns[self._col_index_from_name(item)]

    def __setitem__(self, key: str, value: Column) -> None:
        """Set column by name"""
        try:
            index = self._col_index_from_name(key)
            self.columns[index] = value
        except KeyError:
            self.columns.append(value)

    def __delitem__(self, key: str) -> None:
        """Delete column by name"""
        self.columns.pop(self._col_index_from_name(key))
