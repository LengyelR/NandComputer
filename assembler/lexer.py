import re


class Lexer:
    def __init__(self, path):
        self.lines = []
        with open(path, 'r') as f:
            for line in f.readlines():
                removed_comment = line.split('#')[0]
                removed_whitespace = removed_comment.strip()
                if removed_whitespace:
                    self.lines.append(removed_whitespace)

    def tokenize(self):
        res = []
        labels = []

        pc = 0
        for line in self.lines:
            if line.endswith(':'):
                label = line[:-1]
                labels.append((label, pc))
                continue

            instruction = line[:3]
            arguments = re.sub('\\s+', '', line[4:]).split(',')
            res.append((instruction, arguments))

            skip = instruction == 'STR' and arguments[0] == 'A'
            if skip or '$' not in line:
                pc += 1
            else:
                pc += 2

        return res, labels


if __name__ == '__main__':
    import os

    lexer = Lexer(os.path.join('..', 'examples', 'add100.asm'))
    ts, ls = lexer.tokenize()
    for t in ts:
        print(t)
    for l in ls:
        print(l)
