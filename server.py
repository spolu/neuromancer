import argparse
import eventlet
import eventlet.wsgi

from data.corpus import CorpusDictionary

from algorithms import FixedSequenceLSTM

from flask import Flask
from flask import jsonify
from flask import request

from utils import Config

_app = Flask(__name__)
_algorithm = None
_cfg = None


@_app.route('/predict', methods=['GET'])
def predict():
    prefix = request.args.get('prefix')
    prefix = prefix[-_cfg.get('sequence_length_max')-32:]

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
    parser.add_argument(
        'config_path', type=str, help="path to the config file"
    )
    parser.add_argument(
        '--load_dir', type=str, help="path to saved policies directory"
    )

    args = parser.parse_args()

    _cfg = Config(args.config_path)
    _cfg.override('cuda', False)

    if _cfg.get('algorithm') == 'fixed_sequence_lstm':
        _algorithm = FixedSequenceLSTM(_cfg, None, args.load_dir)
    assert _algorithm is not None

    d = CorpusDictionary.from_file(args.load_dir + "/dictionary.out", _cfg)

    _algorithm.initialize(d)

    run_server()
