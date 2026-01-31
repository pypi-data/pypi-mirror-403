class pH:
    def __init__(self, value):
        if not value < 14 and not value > 0:
            raise ValueError(f"Invalid pH (got {value})")
        self._value = value

    @property
    def value(self):
        return self._value


class NetCharge:
    def __init__(self):
        self._value = 0.0

    def add(self, value: float):
        self._value += value

    @property
    def value(self):
        return self._value
