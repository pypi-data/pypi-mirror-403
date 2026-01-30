from sqlalchemy.types import ARRAY, BLOB, VARCHAR, DateTime, Float, Integer, String, TypeDecorator

from relationalai_gnns.common.dataset_model import ColumnDType

# Classes used to map sqlalchemy types to our own ColumnDtypes
# Used only when we visualize a dataset


class CustomDateTime(TypeDecorator):
    """Helper class to map a DateTime SQLAlchemy dtype to a ColumnDType datetime_t."""

    impl = DateTime

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.datetime_t.value


class CustomInteger(TypeDecorator):
    """Helper class to map a Integer SQLAlchemy dtype to a ColumnDType integer_t."""

    impl = Integer

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.integer_t.value


class CustomFloat(TypeDecorator):
    """Helper class to map a Float SQLAlchemy dtype to a ColumnDType float_t."""

    impl = Float

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.float_t.value


class CustomVARCHAR(TypeDecorator):
    """Helper class to map a Integer VARCHAR dtype to a ColumnDType category_t."""

    impl = VARCHAR

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.category_t.value


class CustomString(TypeDecorator):
    """Helper class to map a Integer String dtype to a ColumnDType text_t."""

    impl = String

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.text_t.value


class CustomARRAY(TypeDecorator):
    """Helper class to map a ARRAY String dtype to a ColumnDType multi_category_t."""

    impl = ARRAY

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.multi_category_t.value


class CustomBLOB(TypeDecorator):
    """Helper class to map a BLOB String dtype to a ColumnDType embedding_t."""

    impl = BLOB

    def get_col_spec(self, **kw):
        """Rename column."""
        return ColumnDType.embedding_t.value
