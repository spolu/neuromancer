import os

from data.corpus import Corpus

from utils import Config

FILTER = [
    ',', '.', '"', '!', '...', '\'', '--', '/', '\\', '(', ')', ':', '\x00',
    ' ', '.', '-', '$', "'", 'ʼ', '?', ',', ';', '£', 'é', '€', 'X', '_', '+',
    '�', '&', ']', '[', '%', '>', '#', 'è', '@', 'ö', '½', '*', 'á', 'í', 'ø',
    '|', 'ë', 'Á', 'ü', '•', 'î', 'ç', '¶', '·', '¥', '^', 'É', 'ó', '²', '†',
    'â', '»', '~', '′', 'ï', 'ú', 'ñ', '¼', '=', 'Â', '‑', 'ã', 'à', '¿', '®',
    '‚', 'Ã', '°', '\x95', '<', '¢', 'ä', 'Ü', '●', '´', 'ô', '‟', '©', 'ё',
    'ê', 'ì', '\uf028', '§', '}', '{', 'Í', 'å', '‐', 'ş', 'ù', '¾', '¤', 'ˈ',
    '\x9d', 'ŵ', '¬', 'ﬁ', 'Ö', '¨', 'æ', '\x92', 'ò', '\x9e', '\x9a', '\x83',
    '×', '™', 'ą', 'ż', 'ś', 'Ó', '−', '³', 'Î', 'º', 'ł',
]


def process_line(
        line: str,
) -> str:
    final = ""
    tokens = line[:-1].split(" ")
    for i in reversed(range(len(tokens))):
        if tokens[i] not in FILTER:
            if len(final) > 0 and tokens[i][0] != "'":
                final += " "
            final += tokens[i]

    return final


def load_1bwords_data(
        config: Config,
        train_dir: str,
        test_dir: str,
) -> Corpus:
    train_set = []
    test_set = []

    assert os.path.isdir(train_dir)
    assert os.path.isdir(test_dir)

    train_files = [
        os.path.join(train_dir, f)
        for f in os.listdir(train_dir)
        if os.path.isfile(os.path.join(train_dir, f))
    ]
    test_files = [
        os.path.join(test_dir, f)
        for f in os.listdir(test_dir)
        if os.path.isfile(os.path.join(test_dir, f))
    ]

    done = 0
    for path in train_files:
        print("Processing: path={}".format(path))
        with open(path, 'r') as f:
            for l in f:
                train_set.append(process_line(l))
        done += 1
        if done == 10:
            break

    done = 0
    for path in test_files:
        print("Processing: path={}".format(path))
        with open(path, 'r') as f:
            for l in f:
                test_set.append(process_line(l))
        done += 1
        if done == 1:
            break

    return Corpus(config, train_set, test_set)
