# SPDX-FileCopyrightText: 2025 Jannik Schmitt <jannik.schmitt@deepsight.de>
#
# SPDX-License-Identifier: Apache-2.0
"""
Lists of regular expressions used to identify whether a token matches a given
pattern.
"""

import re

from limes.analyzers.models import AffixType

# Suffixes were lifted from InProD2 guidelines.
ADJECTIVE_SUFFIXES: list[re.Pattern] = [
    re.compile(r"(\w+)dicht"),
    re.compile(r"(\w+)komponentig"),
    re.compile(r"(\w+)geheftet"),
    re.compile(r"(\w+)variabel"),
    re.compile(r"(\w+)bestückt"),
    re.compile(r"(\w+)dicht"),
    re.compile(r"(\w+)echt"),
    re.compile(r"(\w+)breit"),
    re.compile(r"(\w+)vernetzt"),
    re.compile(r"(\w+)abweisend"),
    re.compile(r"(\w+)bar"),
    re.compile(r"(\w+)haltig"),
    re.compile(r"(\w+)beständig"),
    re.compile(r"(\w+)fest"),
    re.compile(r"(\w+)resistent"),
    re.compile(r"(\w+)abhängig"),
]

NEGATION_AFFIXES: dict[AffixType, list[re.Pattern]] = {
    "prefix": [
        re.compile(r"(?P<affix>un)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>in)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>ir)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>il)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>dis)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>des)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>non)(?P<stem>\w+)"),
        re.compile(r"(?P<affix>a)(?P<stem>\w+)"),
    ],
    "suffix": [
        re.compile(r"(?P<stem>\w+)(?P<affix>frei)(heit)?"),
        re.compile(r"(?P<stem>\w+)(?P<affix>los)(igkeit)?"),
    ],
}

NOUN_PROPERTY_SUFFIXES: list[re.Pattern] = [
    re.compile(r"(\w+)heit"),
    re.compile(r"(\w+)ität"),
    re.compile(r"(\w+)keit"),
]
