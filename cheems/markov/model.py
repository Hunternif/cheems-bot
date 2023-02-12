import logging
from dataclasses import dataclass, field
from datetime import datetime

from cheems.config import config
from cheems.targets import Target

logger = logging.getLogger(__name__)

ModelData = dict[str, dict[str, int]]


@dataclass
class Model:
    """
    The data structure holding the word sequences for Markov chains.
    This class is responsible for storing and serializing the data.
    """
    from_time: datetime
    to_time: datetime
    updated_time: datetime
    target: Target
    description: str
    # E.g. { first_word: {next_word: 1}}
    # next_word includes punctuation attached to the preceding world, e.g. 'hello' - ',my'
    data: ModelData = field(default_factory=dict)

    @property
    def server_id(self) -> int:
        return self.target.server_id

    @classmethod
    def parse_data(cls, text: str) -> ModelData:
        data: ModelData = {}
        max_weight = config.get('markov_model_max_weight', 9999)
        for line in text.strip().splitlines():
            (first_word, next_word, count) = line.strip().split(' ')
            weight = min(int(count), max_weight)  # limit word count
            data.setdefault(first_word, {})
            next_words = data[first_word]
            next_words.setdefault(next_word, 0)
            next_words[next_word] += weight
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

    @classmethod
    def _append_word_pair(cls, data: ModelData, w1: str, w2: str, count: int = 1):
        """Update data with this new word pair"""
        w1 = w1.lower()
        w2 = w2.lower()
        data.setdefault(w1, {})
        next_words = data[w1]
        next_words.setdefault(w2, 0)
        next_words[w2] += count

    def append_word_pair(self, w1: str, w2: str, count: int = 1):
        """Update this Model's data with this new word pair"""
        self._append_word_pair(self.data, w1, w2, count)
