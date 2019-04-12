import subprocess
import z3
import ivy.ivy_lexer

import sys, os.path
INPUT = sys.argv[1]
BASE_NAME = os.path.basename(INPUT)

print 'Processing...', INPUT

with open(INPUT) as f:
    source = f.read().split('\n')

conjecture_line_numbers = []
all_lines = []

lines = enumerate(source)

in_a_conjecture = False
try:
    while True:
        i, line = lines.next()
        line = line.lstrip()
        if in_a_conjecture:
            BAD_WORDS = 'conjecture init individual object relation action'.split(' ')
            if any([line.startswith(word) for word in BAD_WORDS]) or '}' in line:
#           if line.startswith('conjecture') or line.startswith('init') or ('}' in line):
                in_a_conjecture = False
            else:
                all_lines[conjecture_line_numbers[-1]] += ' ' + line.split('#')[0]
                all_lines.append('#')
        if not in_a_conjecture:
            all_lines.append(line)
            if line.startswith('conjecture'):
                in_a_conjecture = True
                conjecture_line_numbers.append(i)
except StopIteration:
    pass









print 'The (zero-indexed) conjecture line numbers are:', conjecture_line_numbers

def query(Pk, conjectures, axioms):
    print 'Query:', Pk, conjectures, axioms
    filename = 'test-' + str(Pk) + '-' + BASE_NAME
    with open(filename, 'w') as f:
        for i, line in enumerate(all_lines):
            if i not in conjecture_line_numbers: # normal line of ivy
                f.write(line + '\n')
            elif i == Pk: # always include Pk as a conjecture
                f.write(line + '\n')
            elif i in axioms:
                f.write(line.replace('conjecture', 'axiom') + '\n')
            elif i in conjectures:
                f.write(line + '\n')
            else: #elif i not in axioms and i not in conjectures:
                f.write('#' + line + '\n')
    try:
        out = subprocess.check_output(['ivy_check', 'complete=fo', filename])
        return True
    except subprocess.CalledProcessError as e:
        err_lines = e.output.split('\n')
        err_lines = [l for l in err_lines if 'FAIL' in l]
        err_lines = [int(l.split(' line ')[1].split(':')[0]) - 1 for l in err_lines]
        if err_lines == []:
            print repr(e.output), ':('
        if Pk in err_lines:
            return False
        return True


def complement(seed):
    return set(conjecture_line_numbers) - set(seed)

def shrink(Pk, seed):
    current = set(seed)
    for Pi in seed:
        current.remove(Pi)
        #print 'Trying to shrink...', current
        if not query(Pk, current, set()):
            current.add(Pi)
    return current

def grow(Pk, seed):
    current = set(seed)
    for Pi in complement(seed):
        current.add(Pi)
        #print 'Trying to grow...', current
        if query(Pk, current, set()):
            current.remove(Pi)
    return current


def marco(Pk):
    print 'Starting to think about...', Pk
    solver = z3.Solver()
    P = []
    for line_number in conjecture_line_numbers:
        P.append(z3.Bool('P_' + str(line_number)))
    out = []
    while True:
        if solver.check() == z3.sat:
            m = solver.model()
            #seed = [conjecture_line_numbers[i] for i, Pi in enumerate(P) if m.eval(Pi, model_completion=True)]
            seed = [conjecture_line_numbers[i] for i, Pi in enumerate(P) if not z3.is_false(m[Pi])]
            #print 'Got seed:', seed
            if query(Pk, set(seed), set()):
                seed = shrink(Pk, seed)
                #print 'Shrank to:', seed, 'which works'
                out.append(seed)
                block = z3.Or([z3.Not(P[i]) for i, line_number in enumerate(conjecture_line_numbers) if line_number in seed])
                #print 'Blocking:', block
                solver.add(block)
            else:
                seed = grow(Pk, seed)
                #print 'Grew to:', seed, 'which does not work'
                block = z3.Or([P[i] for i, line_number in enumerate(conjecture_line_numbers) if line_number not in seed])
                #print 'Blocking:', block
                solver.add(block)
        else:
            #print out
            break
    print 'Fully analyzed...', Pk
    return out

import multiprocessing
p = multiprocessing.Pool(16)
mu = p.map(marco, conjecture_line_numbers)

entries = zip(conjecture_line_numbers, mu)

def fancy_line_number(n):
    return '[' + str(n + 1) + '] ' + all_lines[n].replace('conjecture ', '')[:10] + '...';





graph = ''

graph += 'digraph G {' + '\n'
graph += '  graph[label="%s"];' % (INPUT) + '\n'
for source, targets in entries:
    graph += '  %s[shape=box, label="%s"];' % (source, fancy_line_number(source)) + '\n'
    if len(targets) > 0 and len(targets[0]) > 0:
        graph += '  %s -> %s;' % (source, ', '.join(map(str, targets[0]))) + '\n'
    if len(targets) > 1 and len(targets[1]) > 0:
        graph += '  %s -> %s[style=dotted];' % (source, ', '.join(map(str, targets[1]))) + '\n'
graph += '}' + '\n'




repr_filename = BASE_NAME.replace('.ivy', '.out')
print 'Writing graph repr to %s...' % (repr_filename)
with open(repr_filename, 'w') as f:
    f.write(repr(entries))

graph_filename = BASE_NAME.replace('.ivy', '.dot')
print 'Writing graph viz to %s...' % (graph_filename)
with open(graph_filename, 'w') as f:
    f.write(graph)
