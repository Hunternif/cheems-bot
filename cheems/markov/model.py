import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# these characters indicate end of a sentence
ENDS = '.?!'

ModelData = dict[str, dict[str, int]]


@dataclass
class Model:
    from_time: datetime
    to_time: datetime
    updated_time: datetime
    server_id: int
    target_id: int
    description: str
    # E.g. { first_word: {next_word: 1}}
    # next_word includes punctuation attached to the preceding world, e.g. 'hello' - ',my'
    data: ModelData = field(default_factory=dict)

    @classmethod
    def parse_data(cls, text: str) -> ModelData:
        data: ModelData = {}
        for line in text.strip().splitlines():
            (first_word, next_word, count) = line.strip().split(' ')
            data.setdefault(first_word, {})
            next_words = data[first_word]
            next_words.setdefault(next_word, 0)
            next_words[next_word] += int(count)
        return data

    @classmethod
    def _serialize_data(cls, data: ModelData) -> str:
        lines: list[str] = []
        for first_word, next_words in data.items():
            for next_word, count in next_words.items():
                lines.append(f'{first_word} {next_word} {count}')
        return '\n'.join(sorted(lines))

    def serialize_data(self) -> str:
        return self._serialize_data(self.data)

    def append_word_pair(self, w1: str, w2: str, count: int = 1):
        """Update data with this new word pair"""
        self.data.setdefault(w1, {})
        next_words = self.data[w1]
        next_words.setdefault(w2, 0)
        next_words[w2] += count
