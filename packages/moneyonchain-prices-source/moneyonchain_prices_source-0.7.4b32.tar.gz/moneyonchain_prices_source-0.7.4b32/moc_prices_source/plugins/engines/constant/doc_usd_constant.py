from ...pairs.special import DOC_USD
from ...base import Base, Engines, Decimal
import datetime



@Engines.register_decorator()
class Engine(Base):

    _description = "Dummy"
    _coinpair = DOC_USD
    _uri = None

    def __call__(self, start_time=None):
        if start_time is None:
            start_time = datetime.datetime.now()
        self._clean_output_values()
        self._price = Decimal('1')
        self._volume = Decimal('0')
        self._timestamp = self._now()
        self._last_change_timestamp = self._timestamp
        self._time = datetime.datetime.now() - start_time
        self._age = None
        self._error = None
        return True
