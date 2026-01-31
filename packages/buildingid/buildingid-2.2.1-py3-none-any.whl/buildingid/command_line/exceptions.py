# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE.txt and WARRANTY.txt for details.


class CustomError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__()

        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class FieldNotFoundError(CustomError):
    def __init__(self, fieldname: str) -> None:
        msg = f"field {fieldname!r} is not defined"

        super().__init__(msg)

        self.fieldname = fieldname


class FieldNotUniqueError(CustomError):
    def __init__(self, fieldname: str) -> None:
        msg = f"field {fieldname!r} has already been taken"

        super().__init__(msg)

        self.fieldname = fieldname
