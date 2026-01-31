import datetime
from json import JSONEncoder
from typing import Any


class DateTimeEncoder(JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

        return super().default(o)
