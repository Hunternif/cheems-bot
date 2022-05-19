import logging
import typing
from dataclasses import dataclass
from datetime import datetime

from multidict import MultiDict

logger = logging.getLogger(__name__)

# these characters indicate end of a sentence
ENDS = '.?!'

# 'next_word' will include punctuation attached to the preceding world, e.g. 'hello' - ',my'
Row = typing.NamedTuple('Row', [
    ('next_word', str),
    ('count', int)
])


@dataclass
class Model:
    from_time: datetime
    to_time: datetime
    updated_time: datetime
    server_id: int
    target_id: int
    description: str
    data: MultiDict[Row] = MultiDict()

    @classmethod
    def parse_data(cls, text: str) -> MultiDict[Row]:
        data: MultiDict[Row] = MultiDict()
        for line in text.strip().splitlines():
            (first_word, next_word, count) = line.strip().split(' ')
            data.add(first_word, Row(next_word, int(count)))
        return data

    @classmethod
    def serialize_data(cls, data: MultiDict[Row]) -> str:
        lines = []
        for first_word, row in data.items():
            next_word = row.next_word
            count = row.count
            lines.append(f'{first_word} {next_word} {count}')
        return '\n'.join(lines)
