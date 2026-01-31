# Copyright (c) 2019, Battelle Memorial Institute
# All rights reserved.
#
# See LICENSE.txt and WARRANTY.txt for details.

import re

from openlocationcode import openlocationcode

SEPARATOR_ = "-"
FORMAT_STRING_ = "%s-%.0f-%.0f-%.0f-%.0f"

# fmt: off
RE_PATTERN_ = re.compile(
    r"".join(
        [
            r"^",
            r"(",
                r"[", re.escape(openlocationcode.CODE_ALPHABET_[0:9]), r"][", re.escape(openlocationcode.CODE_ALPHABET_[0:18]), r"]",
                r"(?:",
                    re.escape(openlocationcode.PADDING_CHARACTER_), r"{6}",
                    re.escape(openlocationcode.SEPARATOR_),
                    r"(?:",
                        re.escape(openlocationcode.PADDING_CHARACTER_), r"{2,}",
                    r")?",
                    r"|",
                    r"[", re.escape(openlocationcode.CODE_ALPHABET_), r"]{2}",
                    r"(?:",
                        re.escape(openlocationcode.PADDING_CHARACTER_), r"{4}",
                        re.escape(openlocationcode.SEPARATOR_),
                        r"(?:",
                            re.escape(openlocationcode.PADDING_CHARACTER_), r"{2,}",
                        r")?",
                        r"|",
                        r"[", re.escape(openlocationcode.CODE_ALPHABET_), r"]{2}",
                        r"(?:",
                            re.escape(openlocationcode.PADDING_CHARACTER_), r"{2}", re.escape(openlocationcode.SEPARATOR_),
                            r"(?:",
                                re.escape(openlocationcode.PADDING_CHARACTER_), r"{2,}",
                            r")?",
                            r"|",
                            r"[", re.escape(openlocationcode.CODE_ALPHABET_), r"]{2}",
                            re.escape(openlocationcode.SEPARATOR_),
                            r"(?:",
                                re.escape(openlocationcode.PADDING_CHARACTER_), r"{2,}",
                                r"|",
                                r"[", re.escape(openlocationcode.CODE_ALPHABET_), r"]{2,}",
                                re.escape(openlocationcode.PADDING_CHARACTER_), r"*",
                            r")?",
                        r")",
                    r")",
                r")",
            r")",
            re.escape(SEPARATOR_),
            r"(0|[1-9][0-9]*)",
            re.escape(SEPARATOR_),
            r"(0|[1-9][0-9]*)",
            re.escape(SEPARATOR_),
            r"(0|[1-9][0-9]*)",
            re.escape(SEPARATOR_),
            r"(0|[1-9][0-9]*)",
            r"$",
        ],
    ),
    flags=re.IGNORECASE,
)
# fmt: on

RE_GROUP_OPENLOCATIONCODE_ = 1
RE_GROUP_NORTH_ = 2
RE_GROUP_EAST_ = 3
RE_GROUP_SOUTH_ = 4
RE_GROUP_WEST_ = 5
