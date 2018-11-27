import argparse
import os.path
import random
import signal
import sys
import torch

from data.gmail import load_gmail_data

from algorithms import FixedSequenceLSTM

from utils import Config, str2bool


def run(args):
    cfg = Config(args.config_path)

    if args.cuda is not None:
        cfg.override('cuda', args.cuda)

    torch.manual_seed(cfg.get('seed'))
    random.seed(cfg.get('seed'))

    if cfg.get('cuda'):
        torch.cuda.manual_seed(cfg.get('seed'))

    corpus = load_gmail_data(cfg, 'gmail.data')

    if cfg.get('algorithm') == 'fixed_sequence_lstm':
        algorithm = FixedSequenceLSTM(
            cfg, corpus, args.save_dir, args.load_dir,
        )
    assert algorithm is not None

    while True:
        algorithm.batch_train()


# "clean" exit
def signal_handler(signal, frame):
        sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    os.environ['OMP_NUM_THREADS'] = '1'

    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        'config_path', type=str, help="path to the config file",
    )
    parser.add_argument(
        '--save_dir', type=str, help="directory to save policies to",
    )
    parser.add_argument(
        '--load_dir', type=str, help="path to saved policies directory",
    )

    parser.add_argument('--cuda', type=str2bool, help="config override")

    args = parser.parse_args()

    run(args)
