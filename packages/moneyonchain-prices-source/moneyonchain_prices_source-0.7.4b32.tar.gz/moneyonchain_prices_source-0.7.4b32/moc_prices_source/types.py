from json import dumps as base_json_dumps
from json import loads as json_loads
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from datetime import timedelta



class Serializable():
    
    serializable_class = str
    _frozen = True
    
    @property
    def as_serializable(self):
        return self.serializable_class(self)
    
    @as_serializable.setter
    def as_serializable(self, value):
        if self._frozen:
            self._attribute_error()
        if not(isinstance(value, self.serializable_class)):
            raise ValueError(f"value must be {self.serializable_class.__name__}")
        self._set_new_value(value)

    @staticmethod
    def _attribute_error():
        raise AttributeError("can't set attribute")

    def _set_new_value(self, value):
        self._attribute_error()    


class SerializableDecimal(Decimal, Serializable):
    serializable_class = float


class FancyTimedelta(timedelta, Serializable):
    
    serializable_class = float
    
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], timedelta):
            td = args[0]
            return super().__new__(
                cls,
                days=td.days,
                seconds=td.seconds,
                microseconds=td.microseconds
            )
        return super().__new__(cls, *args, **kwargs)

   
    def __float__(self):
        return float(self.days * 24 * 3600
                     + self.seconds
                     + (self.microseconds/1000000))

    def __int__(self):
        return int(float(self))

    def __str__(self):
        total_us = abs(self.days * 86400_000_000
                       + self.seconds * 1_000_000
                       + self.microseconds)
        sign = "-" if self.total_seconds() < 0 else ""
        days, rem_us = divmod(total_us, 86400_000_000)
        hours, rem_us = divmod(rem_us, 3600_000_000)
        minutes, rem_us = divmod(rem_us, 60_000_000)
        seconds, us = divmod(rem_us, 1_000_000)
        sec = seconds + us / 1_000_000
        if days:
            return f"{sign}{days}d {hours:02}h {minutes:02}m {sec:05.2f}s"
        if hours:
            return f"{sign}{hours:02}h {minutes:02}m {sec:05.2f}s"
        if minutes:
            return f"{sign}{minutes:02}m {sec:05.2f}s"
        out = str(f"{sign}{sec:5.2f}s").strip()
        if out == "0.00s" and sec:
            out = "<10ms"
        elif out == "-0.00s" and sec:
            out = ">-10ms"
        elif not sec:
            out = "none"
        elif int(sec)==0:
            out = str(f"{sign}{int(sec*1000)}ms").strip()

        return out


class FancyDecimal(SerializableDecimal):

    def __new__(cls, value):
        return super().__new__(cls, value)

    def __str__(self) -> str:
        value = Decimal(self)
        out = f"{value:,.6f}"
        if out=="0.000000":
            out = f"{value}"
            if 'E-' in out:
                out = out.split('E-')
                out[1] = ''.join(["⁰¹²³⁴⁵⁶⁷⁸⁹"[int(i)] for i in out[1]])
                out = f"{float(out[0]):.3f} × 10⁻{out[1]}"
        return out        


class PercentageDecimal(SerializableDecimal):

    UP_SYMBOL = "▲"
    DOWN_SYMBOL = "▼"
    ZERO_SYMBOL = "~"

    def __new__(cls, value):
        return super().__new__(cls, value)

    def __str__(self) -> str:
        
        percent_value = (self * Decimal("100")).quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP,
        )

        if percent_value > 0:
            symbol = self.UP_SYMBOL
            value = percent_value
        elif percent_value < 0:
            symbol = self.DOWN_SYMBOL
            value = abs(percent_value)
        else:
            symbol = self.ZERO_SYMBOL
            value = percent_value

        return f"{symbol} {value:.2f}%"


class Bool(Serializable):

    serializable_class = bool
    TRUE_TEXT = "true"
    FALSE_TEXT = "false"
    _true_str_options = ['1', 't', 'true', 'y', 'yes', 'ok']
    _false_str_options = ['0', 'f', 'false', 'n', 'no', 'cancel']

    @classmethod
    def from_string(cls, value: str, frozen: bool = False):
        value = str(value).strip().lower()
        if value in cls._true_str_options:
            return cls(True, frozen=frozen)
        elif value in cls._false_str_options:
            return cls(False, frozen=frozen)
        else:
            raise ValueError(f"Cannot convert '{value}' to {cls.__name__}")

    def __init__(self, value: bool, frozen: bool = False):
        self._value = bool(value)
        self._frozen = bool(frozen)

    def __bool__(self):
        return self._value

    def __repr__(self):
        return self.TRUE_TEXT if self._value else self.FALSE_TEXT
    
    def __int__(self):
        return 1 if self._value else 0
    
    def __float__(self):
        return 1.0 if self._value else 0.0
    
    def _set_new_value(self, value):
        self._value = bool(value)


class YesNo(Bool):

    TRUE_TEXT = "Yes"
    FALSE_TEXT = "No"
    _true_str_options = ['1', 'y', 'yes']
    _false_str_options = ['0', 'n', 'no']


Yes = YesNo(True, frozen = True)


No = YesNo(False, frozen = True)


def json_dumps(obj: Any,
               indent = 4,
               sort_keys = True) -> str:

    def clean_keys(obj):
        """keys must be str, int, float, bool or None"""
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                if isinstance(key, (str, int, float, bool)) or key is None:
                    safe_key = key
                else:
                    safe_key = str(key)
                new_dict[safe_key] = clean_keys(value)
            return new_dict
        elif isinstance(obj, list):
            return [clean_keys(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(clean_keys(item) for item in obj)
        elif isinstance(obj, set):
            return [clean_keys(item) for item in obj]  # JSON has no sets
        else:
            return obj

    def default(value):
        if isinstance(value, Serializable):
            value: Serializable
            return value.as_serializable
        elif isinstance(value, timedelta):
            value: timedelta
            return value.seconds + value.microseconds/1000000        
        elif isinstance(value, Decimal):
            value: Decimal
            return float(value)
        return str(value)

    obj = clean_keys(obj)

    return base_json_dumps(obj,
                           default = default,
                           indent = indent,
                           sort_keys = sort_keys)


def normalize_obj(obj: Any) -> Any:
    return json_loads(json_dumps(obj))
