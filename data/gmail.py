from data.corpus import Corpus

from utils import Config


def load_gmail_data(
        config: Config,
        path: str,
) -> Corpus:
    messages = []
    with open(path, 'r') as f:
        message = ''
        lines = []
        for l in f:
            line = l[:-1]

            if line == '<START>':
                lines = []
                message = ''
            elif line == '<END>':
                for ll in lines:
                    if len(message) > 0 and message[:-1] != ' ' \
                            and len(ll) > 0 and ll[0] != ' ':
                        message += ' '
                    message += ll
                messages.append(message)
            else:
                lines.append(l)

        print("Parsed gmail.data: messages_count={}".format(len(messages)))

        test_set = messages[0:64]
        train_set = messages[64:]

    return Corpus(config, train_set, test_set)
