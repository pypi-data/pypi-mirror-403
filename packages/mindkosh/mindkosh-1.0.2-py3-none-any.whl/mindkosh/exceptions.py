# Copyright (C) 2023 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

class MkException(Exception):
    def __init__(self, message, **kwargs):            
        super().__init__(message)
            
        self.message = message

    def __str__(self):
        return self.message


class AuthorizationError(MkException):
    """ unauthorized """
    pass

class InternalServerError(MkException):
    pass

class NetworkError(MkException):
    pass

class InvalidLabelError(MkException):
    """duplicate label name,
        invalid color hex,
        invalid label height,width,length
    """
    pass

class InvalidTagError(MkException):
    pass

class DataSetError(MkException):
    pass

class DatasetFileError(MkException):
    """sequence/tags/related_files error"""
    pass

class SubscriptionError(MkException):
    pass