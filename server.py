import argparse
import eventlet
import eventlet.wsgi

from data.corpus import CorpusDictionary

from algorithms import FixedSequenceLSTM

from flask import Flask
from flask import jsonify
from flask import request

from utils import Config, str2bool

_app = Flask(__name__)
_algorithm = None
_cfg = None


@_app.route('/predict', methods=['GET'])
def predict():
    prefix = request.args.get('prefix')
    prefix = prefix[-_cfg.get('sequence_length_max')-32:]

    print("PREFIX: {}".format(prefix))

    prediction, score = _algorithm.infer(prefix)

    return jsonify({
        'prediction': prediction,
        'score': score,
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
    parser.add_argument(
        '--cuda', type=str2bool, help="config override"
    )

    args = parser.parse_args()

    _cfg = Config(args.config_path)

    if args.cuda is not None:
        _cfg.override('cuda', args.cuda)

    if _cfg.get('algorithm') == 'fixed_sequence_lstm':
        _algorithm = FixedSequenceLSTM(_cfg, None, args.load_dir)
    assert _algorithm is not None

    d = CorpusDictionary.from_file(args.load_dir + "/dictionary.out", _cfg)

    _algorithm.initialize(d)

    run_server()
