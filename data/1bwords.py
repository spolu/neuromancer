from data.corpus import Corpus

from utils import Config


def load_1bwords_data(
        config: Config,
        train_dir: str,
        test_dir: str,
) -> Corpus:
