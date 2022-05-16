import random

from cheems.markov.model import Model, END

punctuation = r'.,;:!?'


def _pick_first_word(model: Model) -> str:
    """Pick a random word that doesn't immediately end the chain."""
    # try multiple times until we run through the length of data.
    # if all words immediately end the phrase, pick any one
    data = model.data
    if len(data) == 0:
        return END
    for x in range(len(data)):
        first, row = random.choice(list(data.items()))
        if row.next_word != END:
            return first
    return random.choice(list(data.keys()))


def _pick_next_word(model: Model, first_word: str) -> str:
    """
    :param first_word: can include punctuation, which will be stripped.
    :return: Word including space and punctuation, e.g. ' word' or ', word'.
    """
    # drop punctuation from first_word:
    first_word = first_word.strip()
    if first_word == END:
        return END
    if first_word[0] in punctuation:
        first_word = first_word[1:].strip()
    if len(first_word) == 0:
        return END

    rows = model.data.getall(first_word, [])
    if len(rows) == 0:
        return END

    words: list[str] = []
    weights: list[int] = []
    for r in rows:
        words.append(r.next_word)
        weights.append(r.count)
    next_word = random.choices(words, weights)[0]

    if next_word == END:
        return END
    # format punctuation correctly:
    elif next_word[0] in punctuation:
        return next_word[0] + ' ' + next_word[1:]
    else:
        return ' ' + next_word


def markov_chain(model: Model, start: str = '', limit: int = 50) -> str:
    """
    Runs the given model as a Markov Chain.

    :param model: contains possible word sequences.
    :param start: start of the sentence.
    If empty, the start will be picked randomly from the model.
    :param limit: maximum number of words.
    :return:
    """
    result = start.strip()

    # pick the first word to begin the chain
    first_word = start.strip().split(' ')[-1]
    if len(first_word) <= 0:
        first_word = _pick_first_word(model)
        if first_word == END:
            return ''
        else:
            result = first_word

    # start the chain
    last_word = first_word
    count = 1
    while count < limit:
        next_word = _pick_next_word(model, last_word)
        if next_word.strip() == END:
            break
        result += next_word
        count += 1
        last_word = next_word
    return result
