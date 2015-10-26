import sys
from argparse import *
from pygraphviz import *
from __builtin__ import frozenset, set, dict, sorted
from _functools import reduce

class NFA: 
	def __init__(self, delta, q0, F):
		self.delta = delta
		self.q0 = q0
		self.F = set(F)
	def alphabet(self):
		sigma = reduce(lambda a,b:set(a) | set(b), [x.keys() for x in self.delta.values()])
		return sigma
	def getStateBySimbol(self, state, simbols):
		states = set([state])
		for simbol in simbols: 
			newStates = set([])
			for state in states: 
				try: 
					newStates = newStates | set(self.delta[state][simbol])
				except KeyError: pass
			states = newStates
		return states
	def states(self):
		d = set([self.q0]) | set(self.delta.keys()) | reduce(lambda a,b:a | b, reduce(lambda a,b:a + b, [x.values() for x in self.delta.values()]))
		return d

class DFA:	
	def __init__(self, delta, q0, F):
		self.delta = delta	
		self.q0 = q0
		self.F = F
	def alphabet(self):
		sigma = reduce(lambda a,b:set(a) | set(b), [x.keys() for x in self.delta.values()])
		return sigma
	def states(self):
		d = set([self.q0]) | set(self.delta.keys()) | reduce(lambda a,b:a | b, reduce(lambda a,b:a + b, [x.values() for x in self.delta.values()]))
		return d

class NFAParserFromFile:
    def __init__(self, file):
        fileRead = open(file, 'r')
        self.delta = dict()
        definitions = fileRead.read().replace(' ', '').replace('\n', '').replace('\t', '').split('.')
        del definitions[-1]
        for definition in definitions:
            if (definition.split(':')[0][0] == 'T'):
                transitionsString = definition.replace(':=','=').split('T:')[1].replace('},','*').replace('}','*').split('*')
                for transition in transitionsString:
                    if (transition != ''):
                        transition = transition.split('={')
                        state = transition[0][0]
                        simbol = transition[0][2]
                        targets = set(transition[1].split(','))
                        deltaAux = dict([(simbol,targets)])
                        if self.delta.has_key(state):
                            self.delta[state][simbol] = targets
                        else:
                            self.delta[state] = deltaAux
            elif (definition.split(':')[0][0] == 'I'):
                self.q0 = definition.split(':')[1].split(',')[0]
            elif (definition.split(':')[0][0] == 'F'):
                self.F = definition.split(':')[1].split(',')
        fileRead.close()

def NFAtoDFA(N):
	q0 = frozenset(N.q0)
	Q = set([q0])
	unprocessedQ = Q.copy()
	delta = {}
	F = []
	Sigma = N.alphabet()
	
	while len(unprocessedQ) > 0:
		qSet = unprocessedQ.pop()
		delta[qSet] = {}
		for a in Sigma: 
		    nextStates = reduce(lambda x,y: x | y, [N.getStateBySimbol(q,a) for q in qSet])
		    nextStates = frozenset(nextStates)
		    if (nextStates is not frozenset([])):
		        delta[qSet][a] = nextStates
		    if not nextStates in Q: 
		        if (nextStates is not frozenset([])):
		            Q.add(nextStates)
		            unprocessedQ.add(nextStates)
	for qSet in Q: 
		if len(qSet & N.F) > 0: 
			F.append(qSet)
	M = DFA(delta, q0, F)
	return M

def saveAsDot(automata, name, display):
    file = open(name,'w+')
    intialState = ''
    for i in automata.q0:
        intialState = intialState + i
    data = "digraph \"" + display + "\" {\n\t_nil [style=\"invis\"];\n\t_nil -> " + intialState + " [label=\"\"];\n"
    finalStates = ''
    for final in automata.F:
        for s in final:
            finalStates = finalStates + s
        data = data + "\t" + finalStates + " [peripheries=2];\n"
    transitions = ""
    for state in sorted(automata.delta.keys()):
        nameState = ''
        for s in state:
            nameState = nameState + s
        targetSimbols = sorted(automata.delta[state].keys())
        targets = automata.delta[state]
        for t in targets:
            transitions = transitions + '\t' + nameState + ' -> '
            targetName = ''
            for a in targets[t]:
                targetName = targetName + a
            transitions = transitions + targetName + ' [label=' + t + '];\n'
    data = data + transitions + '}'
    file.write(data)

def saveAsDFA(dfa, name):
    file = open(name, 'w+')

    states = "E: "
    hasError = False
    for state in sorted(dfa.delta.keys()):
        nameState = ''
        if len(dfa.delta.get(state)) != len(dfa.alphabet()):
            hasError = True
        for s in state:
            nameState = nameState + s
        states = states + "\t" + nameState + ','
    
    if hasError:
        states = states + '\tError,'
    states = states.rsplit(',',1)[0]
    states = states + '.'
    
    simbols = "A: "
    for simbol in sorted(dfa.alphabet()):
        simbols = simbols + "\t" + simbol + ','
    simbols = simbols.rsplit(',',1)[0]
    simbols = simbols + '.'       

    transitions = "T:\n"
    for state in sorted(dfa.delta.keys()):
        for simbol in sorted(dfa.alphabet()):
            transitions = transitions + '\t'
            nameState = ''
            for s in state:
                nameState = nameState + s
            transitions = transitions + nameState + '[' + simbol + ']\t := \t{'
            targetSimbols = sorted(dfa.delta[state].keys())
            targets = dfa.delta[state]
            for t in targetSimbols:
                if simbol == t:
                    for s in targets[t]:
                        transitions = transitions + s
                    transitions = transitions + '},\n'
                else:
                    if len(targetSimbols) < 2:
                        transitions = transitions + 'Error},\n'
    transitions = transitions.rsplit(',',1)[0]
    transitions = transitions + '.'

    stateInitial = "I:\t"
    nameState = ''
    for state in dfa.q0:
        for s in state:
            nameState = nameState + s
    stateInitial = stateInitial + nameState + '.'

    stateFinal = "F:\t"
    nameState = ''
    for state in dfa.F:
        for s in state:
            nameState = nameState + s
    stateFinal = stateFinal + nameState + '.'

    result = states
    result = result + '\n' + simbols
    result = result + '\n' + transitions
    result = result + '\n' + stateInitial
    result = result + '\n' + stateFinal

    file.write(result)

""" Format Optional Arguments For Command-Line (In Portuguese)
    Usar: redutor <Opções> [AFN de entrada] [AFD de saída]
    Opções:
        -n [Arquivo DOT] AFN Original em formato DOT ou AFN
        -d [Arquivo DOT ou AFD] AFD Gerado em formato DOT ou AFD
"""
parser = ArgumentParser('Transform NFA Automata to DFA Automata.')
parser.add_argument('-n', metavar='FilenamePath', dest='filenameOriginDot', default = False, help='Option for save NFA as .DOT files.')
parser.add_argument('-d', metavar='FilenamePath', dest='filenameDestinyDot', default = False, help='Option for save DFA processed as .DOT file.')
parser.add_argument('origin', nargs='+', help='File path for .AFN file. *Its obrigatory')
parser.add_argument('destiny', nargs='+', help='File path for .AFD file. *Its obrigatory')

args = parser.parse_args()

nfaParsed = NFAParserFromFile(args.origin[0])
NFA = NFA(nfaParsed.delta,nfaParsed.q0,nfaParsed.F)
DFA = NFAtoDFA(NFA)
saveAsDFA(DFA, args.destiny[0])

if (args.filenameOriginDot):
    saveAsDot(NFA, args.filenameOriginDot,"AFN")
if (args.filenameDestinyDot):
    saveAsDot(DFA, args.filenameDestinyDot,"AFD")
    file = "" + args.filenameDestinyDot + ""
    builded = AGraph(file)
    builded.layout()
    builded.draw('out/AFDGerado.pdf')