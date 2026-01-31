# SPDX-FileCopyrightText: 2025 Jannik Schmitt <jannik.schmitt@deepsight.de>
#
# SPDX-License-Identifier: Apache-2.0
"""Module for additional models."""

from typing import Literal

from pydantic import BaseModel

AffixType = Literal["prefix", "suffix"]


class Stem(BaseModel):
    """Information about a word stem."""

    string: str
    freq: int


class DecomposedNegationCompound(BaseModel):
    """A negation compound that was split into its parts."""

    stem: Stem
    affix: str
    type: AffixType
