#  Copyright (C) 2025 ASTRON (Netherlands Institute for Radio Astronomy)
#  SPDX-License-Identifier: Apache-2.0

"""Special string that ignores casing in comparison"""


class CaseInsensitiveString(str):
    """Special string that ignores casing in comparison"""

    def __eq__(self, other):
        if isinstance(other, str):
            return self.casefold() == other.casefold()

        return self.casefold() == other

    def __hash__(self):
        return hash(self.__str__())

    def __contains__(self, key):
        if isinstance(key, str):
            return key.casefold() in str(self)
        return key in str(self)

    def __str__(self) -> str:
        return self.casefold().__str__()

    def __repr__(self) -> str:
        return self.casefold().__repr__()

    def find(self, sub: str, start = None, end = None):
        return self.casefold().find(sub.casefold(), start, end)
