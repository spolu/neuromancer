import os

from data.corpus import Corpus

from utils import Config

FILTER = [",", ".", "\"", "!", "...", "'", "--", "/", "\\", "(", ")", ":"]


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
        if done == 2:
            break

    done = 0
    for path in test_files:
        print("Processing: path={}".format(path))
        with open(path, 'r') as f:
            for l in f:
                test_set.append(process_line(l))
        done += 1
        if done == 2:
            break

    return Corpus(config, train_set, test_set)
