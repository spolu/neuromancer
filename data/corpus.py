import json
import os
import torch
import typing

from torch.utils.data import Dataset

from utils import Config

END = 0


class CorpusDictionary():
    def __init__(
            self,
            config: Config,
    ) -> None:
        self.sequence_length_max = config.get('sequence_length_max')

        self.device = torch.device(
            'cuda:0' if config.get('cuda') else 'cpu'
        )

        self._char_to_ix = {
            '\0': END,
        }
        self._ix_to_char = {
            END: '\0',
        }
        self._charset_size = 1

    def munge(
            self,
            sentence: str,
    ) -> None:
        for c in sentence:
            if c not in self._char_to_ix:
                self._char_to_ix[c] = self._charset_size
                self._ix_to_char[self._charset_size] = c
                self._charset_size += 1

    def charset_size(
            self,
    ) -> int:
        return self._charset_size

    def char_to_ix(
            self,
            c,
    ) -> int:
        return self._char_to_ix[c]

    def input_target(
            self,
            message: str,
    ):
        input_tensor = torch.zeros(
            self.sequence_length_max,
            self._charset_size,
        ).to(self.device)
        target_tensor = torch.zeros(
            self.sequence_length_max, dtype=torch.int64,
        ).to(self.device)

        for j in range(self.sequence_length_max):
            if j < len(message)-1:
                input_tensor[j][
                    self.char_to_ix(message[j])
                ] = 1.0
                target_tensor[j] = \
                    self.char_to_ix(message[j+1])
            if j == len(message)-1:
                input_tensor[j][
                    self.char_to_ix(message[j])
                ] = 1.0
                target_tensor[j] = END
            if j > len(message)-1:
                input_tensor[j][END] = 1.0
                target_tensor[j] = END

        return (
            input_tensor.to(self.device),
            target_tensor.to(self.device),
        )

    def __iter__(
            self,
    ):
        yield 'char_to_ix', self._char_to_ix
        yield 'ix_to_char', self._ix_to_char
        yield 'charset_size', self._charset_size

    @staticmethod
    def from_dict(
            spec,
            config: Config,
    ):
        d = CorpusDictionary(config)

        d._char_to_ix = spec['char_to_ix']
        d._ix_to_char = {}
        for k in spec['ix_to_char']:
            d._ix_to_char[int(k)] = spec['ix_to_char'][k]
        d._charset_size = spec['charset_size']

        return d

    @staticmethod
    def from_file(
            path: str,
            config: Config,
    ):
        assert path is not None and os.path.isfile(path)

        with open(path) as f:
            return CorpusDictionary.from_dict(json.load(f), config)


class CorpusDataset(Dataset):
    def __init__(
            self,
            dict: CorpusDictionary,
            messages,
    ) -> None:
        self._messages = messages
        self._dict = dict

    def __len__(
            self,
    ) -> int:
        return len(self._messages)

    def __getitem__(
            self,
            index: int,
    ):
        return self._dict.input_target(self._messages[index])


class Corpus():
    def __init__(
            self,
            config,
            train_corpus: typing.List[str],
            test_corpus: typing.List[str],
    ) -> None:
        self._dict = CorpusDictionary(config)

        for i in range(len(train_corpus)):
            self._dict.munge(train_corpus[i])
        for i in range(len(test_corpus)):
            self._dict.munge(test_corpus[i])

        self._train_set = CorpusDataset(self._dict, train_corpus)
        self._test_set = CorpusDataset(self._dict, test_corpus)

        print("Created corpus: corpus_size={} charset_size={}".format(
            self._train_set.__len__() + self._test_set.__len__(),
            self._dict.charset_size(),
        ))

    def train_set(
            self,
    ) -> CorpusDataset:
        return self._train_set

    def test_set(
            self,
    ) -> CorpusDataset:
        return self._test_set

    def dict(
            self,
    ) -> CorpusDictionary:
        return self._dict
