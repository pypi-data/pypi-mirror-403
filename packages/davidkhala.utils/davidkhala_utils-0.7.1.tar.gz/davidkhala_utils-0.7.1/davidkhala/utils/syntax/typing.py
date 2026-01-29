from dataclasses import dataclass
from enum import Enum


class NameEnum(Enum):
    @staticmethod
    def _generate_next_value_(name, *args):
        return name


@dataclass
class DataClass:
    ...
