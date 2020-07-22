#!/usr/bin/env python3

import argparse
from collections import defaultdict
from matplotlib import pyplot as plt
from pathlib import Path

if __name__ == "__main__":
    proc_options=['clause-size-hist']
    parser = argparse.ArgumentParser(description="Find Strongly Connected Components")
    parser.add_argument('input_file', help='Invariant as CNF where first line is the property')
    parser.add_argument('--proc', metavar="<PROC_TYPE>", choices=proc_options, default='clause-size-hist',
                        help='The type of processing to do: <{}>'.format('|'.join(proc_options)))
    args = parser.parse_args()

    proc = args.proc
    input_file = Path(args.input_file)

    with input_file.open('r') as f:
        lines = f.read().split("\n")

    assert lines
    idx = 0
    # first remove leading comments
    for i, line in enumerate(lines):
        if line[0] != 'c':
            idx = i
            break

    lines = lines[idx:]

    if proc == 'clause-size-hist':
        hist_sizes = defaultdict(int)
        for line in lines:
            lit_list = line.split()
            # lit list is zero terminated, don't count last one
            hist_sizes[len(lit_list) - 1] += 1

        length, freq = zip(*sorted(hist_sizes.items()))
        length = list(map(int, length))
        freq = list(map(int, freq))
        x_pos = list(range(len(length)))
        plt.bar(x_pos, freq, align='center')
        plt.xticks(x_pos, length)
        plt.xlabel('Size of Clause')
        plt.ylabel('Number of Clauses of this size')
        plt.title('Occurrences of Clause sizes')
        plt.show()
    else:
        raise RuntimeError("Unknown proc option {}".format(proc))
