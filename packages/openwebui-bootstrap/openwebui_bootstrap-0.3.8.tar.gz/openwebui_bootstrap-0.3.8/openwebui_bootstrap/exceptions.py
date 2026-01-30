"""Custom exceptions for Open WebUI Bootstrap."""


class OpenWebUIBootstrapError(Exception):
    """Base exception for Open WebUI Bootstrap errors."""


class DatabaseError(OpenWebUIBootstrapError):
    """Base exception for database-related errors."""


class DatabaseConnectionError(DatabaseError):
    """Exception for database connection failures."""


class DatabaseOperationError(DatabaseError):
    """Exception for database operation failures."""


class DatabaseTransactionError(DatabaseError):
    """Exception for database transaction failures."""


class ConfigurationError(OpenWebUIBootstrapError):
    """Base exception for configuration-related errors."""


class ConfigurationValidationError(ConfigurationError):
    """Exception for configuration validation failures."""


class ConfigurationFileError(ConfigurationError):
    """Exception for configuration file reading/parsing failures."""


class ResetError(OpenWebUIBootstrapError):
    """Exception for database reset operation failures."""


class UpsertError(OpenWebUIBootstrapError):
    """Exception for upsert operation failures."""


class DryRunError(OpenWebUIBootstrapError):
    """Exception for dry run operation failures."""


class DatabaseValidationError(DatabaseError):
    """Exception for database validation failures."""


class DatabaseCorruptionError(DatabaseError):
    """Exception for database corruption detection."""


class DatabaseReplacementError(DatabaseError):
    """Exception for database replacement operation failures."""
