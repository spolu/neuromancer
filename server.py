import time
import argparse
import eventlet
import eventlet.wsgi
import os

from flask import Flask
from flask import jsonify
from eventlet.green import threading

from utils import Config, str2bool, load_data
from algorithms import FixedSequenceLSTM

_app = Flask(__name__)
_algorithm = None

@_app.route('/predict/<prefix>', methods=['GET'])
def predict(prefix):
    return jsonify({
        'prediction': _algorithm.infer(prefix, 32),
    })

def run_server():
    global _app
    print("Starting server: port=9093")
    address = ('0.0.0.0', 9093)
    try:
        eventlet.wsgi.server(eventlet.listen(address), _app)
    except KeyboardInterrupt:
        print("Stopping server")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('config_path', type=str, help="path to the config file")
    parser.add_argument('--load_dir', type=str, help="path to saved policies directory")

    args = parser.parse_args()

    cfg = Config(args.config_path)
    cfg.override('cuda', False)

    if cfg.get('algorithm') == 'fixed_sequence_lstm':
        _algorithm = FixedSequenceLSTM(cfg, None, args.load_dir)
    assert _algorithm is not None
    _algorithm.initialize(load_data('gmail.data'))

    run_server()
