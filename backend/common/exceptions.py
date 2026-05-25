from rest_framework import status
from rest_framework.exceptions import APIException


class LockedRecordError(APIException):
    """Raised when attempting to modify an audit-locked record."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'This record is audit-locked and cannot be modified.'
    default_code = 'locked_record'


class ValidationPipelineError(APIException):
    """Raised when a validation pipeline step fails."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation pipeline error.'
    default_code = 'validation_pipeline_error'


class DuplicateRecordError(APIException):
    """Raised when a duplicate record is detected."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A duplicate record already exists.'
    default_code = 'duplicate_record'
