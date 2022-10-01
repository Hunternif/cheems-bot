import random
import re

from cheems.markov.model import Model, ModelData
from cheems.util import pairwise

# these characters indicate end of a sentence
ENDS = '.?!'
omitted_ends = '.'  # characters that are too boring and should be trimmed
punctuation = '.,;:!?'
punctuation_except_ENDS = ',;:'
bad_punctuation = '`~^*(){}[]=+•“”"…—«»'  # keeping $/ for discord commands and <@#&> for mentions.
re_ENDS = re.escape(ENDS)
re_command = re.compile(r'[.?!$/]\w+')
re_punctuation = re.escape(punctuation)
re_punctuation_except_END = re.escape(punctuation_except_ENDS)
re_bad_punctuation = re.escape(bad_punctuation)
url_pattern = re.compile(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#\-()!]*[\w@?^=%&/~+#-])')


def strip_punctuation(text: str) -> str:
    """Strips punctuation from both ends, except command characters at the start."""
    if re_command.match(text) is not None:
        return text  # don't strip command
    text = re.sub(rf'^[{re_punctuation}]+', '', text).strip()
    text = re.sub(rf'[{re_punctuation}]+$', '', text).strip()
    return text


def canonical_form(word: str) -> str:
    """
    Returns the canonical form of the word: lowercase, no whitespace, no punctuation.
    This form is used as key in the data dictionary.
    """
    word = word.lower().strip()
    if word in ENDS:
        return word
    word = strip_punctuation(word)
    if len(word) == 0:
        return ENDS[0]
    return word


def get_last_word(sentence: str) -> str:
    """
    Finds the last word that is not punctuation
    """
    words = _break_into_words(sentence)
    for w in reversed(words):
        canonical = canonical_form(w)
        if canonical in ENDS:
            continue
        if len(canonical) > 0:
            return canonical
    return ''


def _break_into_words(sentence: str) -> list[str]:
    """
    Extracts a sequence of words from the sentence.
    Punctuation is stripped or formatted for the model.
    """
    # Remove code:
    sentence = re.sub(r'```.*```', '', sentence, flags=re.DOTALL)
    sentence = sentence.strip()
    # Remove urls:
    sentence = url_pattern.sub('', sentence)
    # Line breaks are considered spaces:
    sentence = sentence.replace('\n', ' ')
    # Clean whitespaces:
    sentence = re.sub(r'[ᅟ\s]+', ' ', sentence)
    # Remove bad punctuation:
    sentence = re.sub(rf'[{re_bad_punctuation}]+', ' ', sentence)
    # Remove other bad characters such as zero-width whitespace:
    sentence = sentence.replace('\u200b', '')
    # Convert long strings of punctuation into a short one, e.g. ...->. ?!->?
    sentence = re.sub(rf'([{re_punctuation}]+)', lambda m: m.group(0)[0], sentence)
    # Ensure every end character is a separate word, except in discord mentions like <@!123>:
    sentence = re.sub(
        rf'(\S)([{re_ENDS}]) ',
        lambda m: f'{m.group(1)} {m.group(2)} ',
        sentence
    )
    # Allow using commands as words, e.g. '.roll'
    # sentence = re.sub(
    #     rf' ([{re_ENDS}])(\S)',
    #     lambda m: f' {m.group(1)} {m.group(2)}',
    #     sentence
    # )

    # Ensure punctuation sticks to the NEXT word, e.g. 'hello ,world'
    sentence = re.sub(
        rf'\s?([{re_punctuation_except_END}]+)\s',
        lambda m: f' {m.group(1)}',
        sentence
    )
    words = [w for w in sentence.split(' ') if len(w) > 0]
    return words


def train_model_on_sentence(data: ModelData, sentence: str):
    """
    Updates the model with word sequences from the given sentence.
    """
    train_models_on_sentence([data], sentence)


def train_models_on_sentence(models_data: list[ModelData], sentence: str):
    """
    Updates the given models with word sequences from the given sentence.
    """
    words = _break_into_words(sentence)
    if len(words) == 0:
        return
    # ensure there is an END character at the end:
    if words[-1] not in ENDS:
        words.append(ENDS[0])
    for w1, w2 in pairwise(words):
        w1 = canonical_form(w1)
        if w1 in ENDS:
            continue
        for data in models_data:
            # noinspection PyProtectedMember
            Model._append_word_pair(data, w1, w2)


def _pick_first_word(data: ModelData) -> str:
    """
    Pick a random word that doesn't immediately end the chain.
    """
    # try multiple times until we run through the length of data.
    # if all words immediately end the phrase, pick any one
    if len(data) == 0:
        return ENDS[0]
    for x in range(len(data)):
        first, next_words = random.choice(list(data.items()))
        for y in next_words.keys():
            if y not in ENDS:
                return first
    return random.choice(list(data.keys()))


def _pick_next_word(data: ModelData, first_word: str) -> str:
    """
    :param first_word: can include punctuation, which will be stripped.
    :return: Word including space and punctuation, e.g. ' word' or ', word'.
    """
    # drop punctuation from first_word:
    first_word = canonical_form(first_word)

    next_words = data[first_word] if first_word in data else []
    if len(next_words) == 0:
        return ENDS[0]

    words: list[str] = []
    weights: list[int] = []
    for next_word, count in next_words.items():
        words.append(next_word)
        weights.append(count)
    next_word = random.choices(words, weights)[0]

    if next_word in ENDS:
        return next_word
    # format punctuation like so: ', '
    elif next_word[0] in punctuation:
        return next_word[0] + ' ' + next_word[1:]
    else:
        return ' ' + next_word


def markov_chain(data: ModelData, start: str = '', limit: int = 50) -> str:
    """
    Runs the given model as a Markov Chain.

    :param data: contains possible word sequences.
    :param start: start of the sentence.
    If empty, the start will be picked randomly from the model.
    :param limit: maximum number of words.
    :return:
    """
    result = strip_punctuation(start)

    # pick the first word to begin the chain
    first_word = start.strip().split(' ')[-1]
    if len(first_word) <= 0:
        first_word = _pick_first_word(data)
        if first_word in ENDS:
            return ''
        else:
            result = first_word

    # start the chain
    last_word = first_word
    count = 1
    while count < limit:
        next_word = _pick_next_word(data, last_word)
        if next_word in omitted_ends:
            break  # '.' is too boring, so skip it
        result += next_word
        count += 1
        last_word = next_word
        if last_word in ENDS:
            break
    return result
