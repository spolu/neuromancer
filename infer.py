import sys
import random
import argparse
import signal
import os.path

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from utils import Config, str2bool, load_data
from algorithms import FixedSequenceLSTM

def run(args):
    cfg = Config(args.config_path)

    cfg.override('cuda', False)

    if cfg.get('algorithm') == 'fixed_sequence_lstm':
        algorithm = FixedSequenceLSTM(cfg, None, args.load_dir)
    assert algorithm is not None

    algorithm.initialize(load_data('gmail.data'))

    sys.stdout.write('>')
    sys.stdout.flush()
    for m in sys.stdin:
        print(algorithm.infer(m[:-1], 32))
        sys.stdout.write('>')
        sys.stdout.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('config_path', type=str, help="path to the config file")

    parser.add_argument('--load_dir', type=str, help="path to saved policies directory")

    args = parser.parse_args()

    run(args)
