# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE.txt and WARRANTY.txt for details.

import typing

from buildingid.command_line.dict_datum import DictDatum
from buildingid.command_line.dict_pipe import DictEncoder


class BaseGeometryDictEncoder(DictEncoder[DictDatum]):
    def __init__(self, fieldname_code: str, code_length: int) -> None:
        super().__init__()

        self.fieldname_code = fieldname_code

        self.code_length = code_length

    def encode(self, datum: DictDatum) -> dict[str, typing.Any]:
        code = datum.encode(codeLength=self.code_length)

        row = {}

        row[self.fieldname_code] = code

        return row

    @property
    def fieldnames(self) -> list[str]:
        return [
            self.fieldname_code,
        ]


class ErrorDictEncoder(DictEncoder[BaseException]):
    def __init__(self, fieldname_code: str) -> None:
        super().__init__()

        self.fieldname_code = fieldname_code

    def encode(self, exception: BaseException) -> dict[str, typing.Any]:
        row = {}

        row[f"{self.fieldname_code}_Error_Name"] = type(exception).__name__
        row[f"{self.fieldname_code}_Error_Message"] = str(exception)

        return row

    @property
    def fieldnames(self) -> list[str]:
        return [
            f"{self.fieldname_code}_Error_Name",
            f"{self.fieldname_code}_Error_Message",
        ]
