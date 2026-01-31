from enum import IntEnum


class BaseEnum(IntEnum):

    @classmethod
    def get(cls, name: str) -> int | None:
        try:
            return cls[name].value
        except KeyError:
            return None

    @classmethod
    def name_from_value(cls, value: int) -> str | None:
        member = cls._value2member_map_.get(value)
        return member.name if member else None


