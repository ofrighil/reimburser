class FieldError(Exception):
    """Raised when the file does not have the required fields"""
    pass

class FileFormatError(Exception):
    """Raised when the file is not the appropriate format"""
    pass
