import base64
import re

with open('gmail.raw', 'r') as fin:
    with open('gmail.data', 'w+') as fout:
        selected = []
        done = False
        msg_count = 0
        char_count = 0

        for l in fin:
            l = l[:-1]

            if l == '<START>':
                selected = []
                done = False
            elif l == '<END>':
                if len(selected) > 0:
                    fout.write('<START>\n')
                    for l in selected:
                        fout.write(l + '\n')
                    fout.write('<END>\n')
                print("Dumping message: msg_count={} char_count={}".format(
                    msg_count,
                    char_count,
                ))
                msg_count += 1
            else:
                if re.match('^ *(On )?\w+,? \w+ [0-9]+,? [0-9]{4},?( (at )?[0-9]{1,2}:[0-9]{2}(:[0-9]+)?)? .*$', l):
                    done = True
                if re.match('^ *(On )[0-9]+,? \w+,? [0-9]{4},?( (at )?[0-9]{1,2}:[0-9]{2}(:[0-9]+)?)? .*$', l):
                    done = True
                if re.match('^ *(On )?[0-9]+-[0-9]+-[0-9]+,?( (at )?[0-9]{1,2}:[0-9]{2}(:[0-9]+)?)? .*$', l):
                    done = True
                if re.match('^ *(On )?[0-9]+/[0-9]+/[0-9]+,?( (at )?[0-9]{1,2}:[0-9]{2}(:[0-9]+)?)? .*$', l):
                    done = True
                if re.match('^-{2,}', l):
                    done = True

                if not done:
                    if re.match('^\>+', l):
                        continue
                    selected.append(l)
                    char_count += len(l)

