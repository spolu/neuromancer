import sys
import torch
import collections

import torch.nn as nn
import torch.optim as optim

from data.corpus import Corpus, CorpusDictionary

from utils import Meter, Config

from torch.utils.data import DataLoader


class LSTMPolicy(nn.Module):
    def __init__(
            self,
            config: Config,
            charset_size: int,
    ):
        super(LSTMPolicy, self).__init__()

        self.hidden_size = config.get('hidden_size')
        self.layer_count = config.get('layer_count')
        self.charset_size = charset_size

        self.device = torch.device(
            'cuda:0' if config.get('cuda') else 'cpu'
        )
        self.config = config

        self.lstm = nn.LSTM(
            self.charset_size, self.hidden_size, num_layers=self.layer_count,
            bias=True
        )
        self.fc1 = nn.Linear(self.hidden_size, self.charset_size)

        self.softmax = nn.LogSoftmax(dim=2)
        self.tanh = nn.Tanh()

        for name, param in self.lstm.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0.0)
            elif 'weight' in name:
                nn.init.xavier_normal_(param)

        nn.init.xavier_normal_(self.fc1.weight.data)
        self.fc1.bias.data.fill_(0)

    def forward(self, inputs, hidden=None):
        out, (h_n, c_n) = self.lstm(inputs, hidden)

        x = self.tanh(out)
        x = self.softmax(self.fc1(x))

        return x, (h_n, c_n)


Beam = collections.namedtuple(
    'Beam',
    ('current '
     'hidden '
     'probability '
     'prediction '
     'final '),
)


class FixedSequenceLSTM:
    def __init__(
            self,
            config: Config,
            save_dir: str = None,
            load_dir: str = None,
    ):
        self.learning_rate = config.get('learning_rate')
        self.hidden_size = config.get('hidden_size')
        self.sequence_length_max = config.get('sequence_length_max')
        self.grad_norm_max = config.get('grad_norm_max')
        self.beam_size = config.get('beam_size')

        self.config = config
        self.train_loader = None
        self.test_loader = None
        self.save_dir = save_dir
        self.load_dir = load_dir

        self.device = torch.device('cuda:0' if config.get('cuda') else 'cpu')

        self.best_test_loss = 999999.99

    def initialize(
            self,
            d: CorpusDictionary,
    ) -> None:
        self.dict = d

        self.policy = LSTMPolicy(
            self.config, d.charset_size(),
        ).to(self.device)

        self.optimizer = optim.Adam(
            self.policy.parameters(),
            self.learning_rate,
        )

        self.loss = nn.NLLLoss()

        if self.load_dir:
            if self.config.get('cuda'):
                self.policy.load_state_dict(
                    torch.load(self.load_dir + "/policy.pt"),
                )
                self.optimizer.load_state_dict(
                    torch.load(self.load_dir + "/optimizer.pt"),
                )
            else:
                self.policy.load_state_dict(
                    torch.load(
                        self.load_dir + "/policy.pt", map_location='cpu',
                    ),
                )
                self.optimizer.load_state_dict(
                    torch.load(
                        self.load_dir + "/optimizer.pt", map_location='cpu',
                    ),
                )

    def initialize_training(
            self,
            corpus: Corpus,
    ) -> None:
        self.corpus = corpus
        self.initialize(self.corpus.dict())

    def batch_train(
            self,
    ):
        self.policy.train()

        loss_meter_total = Meter()
        loss_meter_inter = Meter()

        if self.train_loader is None:
            self.train_loader = DataLoader(
                self.corpus.train_set(),
                batch_size=8, shuffle=True,
            )

        for i, (sequence, target) in enumerate(self.train_loader):
            predictions, _ = self.policy(sequence.transpose(0, 1))

            loss = self.loss(
                predictions.view(-1, predictions.size(2)),
                target.transpose(0, 1).contiguous().view(-1),
            )

            loss_meter_total.update(loss.item())
            loss_meter_inter.update(loss.item())

            self.optimizer.zero_grad()
            loss.backward()

            if self.grad_norm_max > 0.0:
                nn.utils.clip_grad_norm_(
                    self.policy.parameters(), self.grad_norm_max,
                )

            self.optimizer.step()

            if i % 500 == 0:
                print(
                    ("STEP {} avg/min/max L {:.6f} {:.6f} {:.6f}").
                    format(
                        i,
                        loss_meter_inter.avg,
                        loss_meter_inter.min,
                        loss_meter_inter.max,
                    )
                )
                sys.stdout.flush()
                loss_meter_inter = Meter()

            if (i+1) % 10000 == 0:
                test_loss = self.batch_test()
                self.policy.train()
                if test_loss < self.best_test_loss:
                    self.best_test_loss = test_loss
                    if self.save_dir:
                        print(
                            "Saving policy and optimizer: save_dir={}".
                            format(self.save_dir)
                        )
                        torch.save(
                            self.policy.state_dict(),
                            self.save_dir + "/policy.pt",
                        )
                        torch.save(
                            self.optimizer.state_dict(),
                            self.save_dir + "/optimizer.pt",
                        )

        print(
            ("EPISODE avg/min/max L {:.6f} {:.6f} {:.6f}").
            format(
                loss_meter_total.avg,
                loss_meter_total.min,
                loss_meter_total.max,
            )
        )
        sys.stdout.flush()

        return loss_meter_total

    def batch_test(self):
        self.policy.eval()
        loss_meter = Meter()

        if self.test_loader is None:
            self.test_loader = DataLoader(
                self.corpus.test_set(),
                batch_size=2, shuffle=True,
            )

        for i, (sequence, target) in enumerate(self.test_loader):
            predictions, _ = self.policy(sequence.transpose(0, 1))

            loss = self.loss(
                predictions.view(-1, predictions.size(2)),
                target.transpose(0, 1).contiguous().view(-1),
            )

            loss_meter.update(loss.item())

        print(
            ("TEST avg/min/max L {:.6f} {:.6f} {:.6f}").
            format(
                loss_meter.avg,
                loss_meter.min,
                loss_meter.max,
            )
        )
        sys.stdout.flush()

        return loss_meter.avg

    def infer(self, m, stop=' '):
        self.policy.eval()

        beams = []
        finished = False

        with torch.no_grad():
            h = None
            if len(m) > 1:
                (sequence, _) = self.dict.input_target(m[:-1])
                sequence = sequence[:len(m)-1]
                _, h = self.policy(sequence.unsqueeze(1))
            (c, _) = self.dict.input_target(m[-1:])
            c = c[0]

            import pdb; pdb.set_trace()

            # TODO(stan): fix c, sequence is not the right legnth anymore

            beams = [Beam(c, h, 1.0, '', False)]

            while not finished:
                candidates = []
                for i in range(len(beams)):
                    if beams[i].final:
                        candidates += [beams[i]]
                        continue

                    output, h = self.policy(
                        beams[i].current.unsqueeze(1), beams[i].hidden,
                    )
                    topv, topi = output.topk(self.beam_size)

                    for j in range(self.beam_size):
                        ix = topi[0][0][j].item()
                        letter = self.ix_to_char[ix]

                        if letter == ' ' or ix == 0:
                            if len(beams[i].prediction) > 0:
                                candidates += [
                                    Beam(
                                        beams[i].current,
                                        beams[i].hidden,
                                        beams[i].probability,
                                        beams[i].prediction,
                                        True,
                                    )
                                ]
                        else:
                            (c, _) = self.input_target_for_message(letter)
                            candidates += [
                                Beam(
                                    c,
                                    h,
                                    beams[i].probability *
                                    torch.exp(topv)[0][0][j].item(),
                                    beams[i].prediction + letter,
                                    False,
                                )
                            ]

                beams = sorted(
                    candidates,
                    key=lambda x: x.probability,
                    reverse=True,
                )[:self.beam_size]

                finished = True
                for b in beams:
                    if b.final is not True:
                        finished = False

            beams = sorted(
                beams,
                key=lambda x: (x.probability + 0.1 * len(x.prediction)),
                reverse=True,
            )

            for b in beams:
                print("{} {:.4f}".format(
                    b.prediction, b.probability + 0.05 * len(b.prediction),
                ))

            return beams[0].prediction

            # for i in range(length):
            #     output, hiddens = self.policy(current.unsqueeze(1), hiddens)
            #     topv, topi = output.topk(1)
            #     ix = topi[0][0][0].item()
            #     if ix == 0:
            #         break

            #     letter = self.ix_to_char[ix]
            #     prediction += letter

            #     (current, _) = self.input_target_for_message(letter)
