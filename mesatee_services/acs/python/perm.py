###############################################################################
# Parser Combinators
###############################################################################
class Pair(tuple):
    def __new__(cls, a, b):
        return super(Pair, cls).__new__(cls, [a, b])

class Either(object):
    def __init__(self, left, right):
        self.__left = left
        self.__right = right

    def left(self):
        if not self.is_left():
            raise ValueError('wrong extractor for either')
        return self.__left

    def right(self):
        if not self.is_right():
            raise ValueError('wrong extractor for either')
        return self.__right

    def is_right(self):
        return False

    def is_left(self):
        return False

    def get(self):
        if self.is_right():
            return self.right()
        if self.is_left():
            return self.left()
        raise ValueError('incomplete Either object')

    def __str__(self):
        if self.is_left():
            return 'Left(' + str(self.left()) + ')'
        else:
            return 'Right(' + str(self.right()) + ')'

    def __repr__(self):
        if self.is_left():
            return 'Left(' + repr(self.left()) + ')'
        else:
            return 'Right(' + repr(self.right()) + ')'

class Left(Either):
    def __init__(self, payload):
        super(Left, self).__init__(payload, None)

    def is_left(self):
        return True

class Right(Either):
    def __init__(self, payload):
        super(Right, self).__init__(None, payload)

    def is_right(self):
        return True

class Stream(object):
    WHITESPACES = [' ', '\t', '\r']
    def __init__(self, items, pos = 0):
        self.__items = items
        self.__pos = pos

    def accept_strlit(self, string):
        # Typically parsers want to skip white spaces except line breaks
        # In the future this should be configurable
        pos = self.__pos
        l = len(self.__items)
        while pos < l and self.__items[pos] in self.WHITESPACES:
            pos += 1

        match_pos = 0
        l = len(string)        
        while match_pos < l and string[match_pos] in self.WHITESPACES:
            match_pos += 1
        if pos < match_pos:
            raise ParsingError(self, 'expecting "{}"'.format(string))
        if match_pos:
            string = string[match_pos:]
        if self.__items.startswith(string, pos):
            return Stream(self.__items, pos + len(string))
        raise ParsingError(self, 'expecting "{}"'.format(string))

    def accept_matcher(self, matcher):
        pos = self.__pos
        l = len(self.__items)
        while pos < l and self.__items[pos] in self.WHITESPACES:
            pos += 1

        res = matcher(self.__items, pos)
        if res is None:
            raise ParsingError(self, 'matcher for {} failed'.format(matcher.__doc__))
        obj, npos = res
        return obj, Stream(self.__items, npos)

    def end(self):
        return self.__pos == len(self.__items)

    def pos(self):
        return self.__pos

    def __repr__(self):
        line_start = self.__items.rfind('\n', 0, self.__pos) + 1
        line_end = self.__items.find('\n', self.__pos)
        if line_end == -1:
            line_end = self.__pos

        if line_end - line_start > 80:
            line_start = max(line_start, self.__pos - 40)
            line_end = min(line_start + 80, len(self.__items))

        return ''.join([
            self.__items[line_start:line_end],
            '\n',
            ' ' * (self.__pos - line_start),
            '^',
            ' ' * (line_end - self.__pos),
            '\nerror at character ',
            str(self.__pos),
        ])

class State(object):
    def __init__(self, stream, payload = None, success = True):
        self.stream = stream
        self.payload = payload
        self.success = success

    def __bool__(self):
        return self.success

    def __nonzero__(self):
        return self.__bool__()

    def fmap(self, f):
        if self:
            return State(self.stream, f(self.payload))
        return self

class ParsingError(Exception):
    def __init__(self, stream, msg = ''):
        super(ParsingError, self).__init__(msg)
        self.stream = stream

    def __repr__(self):
        return repr(self.stream)

class Parser(object):
    def __init__(self):
        pass

    def __call__(self, stream):
        raise NotImplementedError("pure abstract parser cannot be called")

    def parse_from(self, stream):
        n_state = self(stream)
        if not n_state:
            print n_state.stream, n_state.payload
            raise ParsingError(n_state.stream, n_state.payload)
        elif not n_state.stream.end():
            print n_state.stream, 'trailing unparsable input'
            print n_state.stream.pos()
            raise ParsingError(n_state.stream, 'trailing unparsable input')
        return n_state

    def fail(self, exception):
        return State(exception.stream, str(exception), False)

    def ignore(self):
        return Ignore(self)

    def __or__(self, p):
        return Or(self, p)

    def __add__(self, p):
        if isinstance(self, Ignore) and isinstance(p, Ignore):
            return Ignore(Concat(self, p))
        else:
            return Concat(self, p)

    def __invert__(self):
        return Rep(self)

    def __pow__(self, f):
        return Apply(self, f)

class Epsilon(Parser):
    def __init__(self):
        super(Epsilon, self).__init__()

    def __call__(self, stream):
        return State(stream)

class StrLiteral(Parser):
    def __init__(self, string):
        super(StrLiteral, self).__init__()
        self.__string = string

    def __call__(self, stream):
        if stream.end():
            return self.fail(ParsingError(
                stream, 'insufficient input, expecting {}'.format(self.__string))
            )
        try:
            n_stream = stream.accept_strlit(self.__string)
        except ParsingError as e:
            return self.fail(e)

        return State(n_stream, self.__string)

class CustomMatcher(Parser):
    def __init__(self, matcher):
        super(CustomMatcher, self).__init__()
        self.__matcher = matcher

    def __call__(self, stream):
        try:
            res = stream.accept_matcher(self.__matcher)
        except ParsingError as e:
            return self.fail(e)

        obj, n_stream = res
        return State(n_stream, obj)

class Concat(Parser):
    def __init__(self, c1, c2):
        super(Concat, self).__init__()
        assert not isinstance(self, Ignore) or not isinstance(p, Ignore)
        self.__first = c1
        self.__second = c2

    def __call__(self, stream):
        n_state = self.__first(stream)
        if not n_state:
            return n_state
        p1 = n_state.payload
        n_state = self.__second(n_state.stream)
        if not n_state:
            return n_state
        p2 = n_state.payload

        if isinstance(self.__first, Ignore):
            return State(n_state.stream, p2)
        if isinstance(self.__second, Ignore):
            return State(n_state.stream, p1)
        # The construction of Concat ensures that at least
        # one of this children is not Ignore
        return State(n_state.stream, Pair(p1, p2))

class Or(Parser):
    def __init__(self, c1, c2):
        super(Or, self).__init__()
        self.__if = c1
        self.__else = c2

    def __call__(self, stream):
        n_state = self.__if(stream)
        if n_state:
            return n_state.fmap(lambda x: Left(x))
        n_state = self.__else(stream)
        if n_state:
            return n_state.fmap(lambda x: Right(x))
        return n_state

class Rep(Parser):
    def __init__(self, c):
        super(Rep, self).__init__()
        self.__loop = c

    def __call__(self, stream):
        payload = []

        n_state = self.__loop(stream)
        if n_state:
            payload.append(n_state.payload)
            stream = n_state.stream
            n_state = self(stream)
            if n_state:
                payload = payload + n_state.payload
                stream = n_state.stream
        return State(stream, payload)

class Apply(Parser):
    def __init__(self, base, f):
        super(Apply, self).__init__()
        self.__base = base
        self.__trans = f

    def __call__(self, stream):
        return self.__base(stream).fmap(self.__trans)

class Ignore(Parser):
    def __init__(self, base):
        super(Ignore, self).__init__()
        self.__base = base

    def __call__(self, stream):
        return self.__base(stream)

###############################################################################
# Grammars for PERM model configuration 
###############################################################################
from operator import or_, add

def extract(nested_or):
    while isinstance(nested_or, Either):
        nested_or = nested_or.left() if nested_or.is_left() else nested_or.right()
    return nested_or

def flatten(nested_concat):
    res = []

    def pre_order(pair, res):
        if isinstance(pair, Pair):
            pre_order(pair[0], res)
            pre_order(pair[1], res)
        else:
            res.append(pair)

    pre_order(nested_concat, res)
    return res

def one_of(parsers):
    nested = reduce(or_, parsers)
    return nested ** extract

def join(sl):
    return ''.join(sl)

def rep_with_sep(to_rep, sep):
    if not isinstance(sep, Ignore):
        sep = sep.ignore()
    r = to_rep + ~(sep + to_rep)
    r = r ** (lambda x: [x[0]] + x[1])
    return r

ALPHA = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
DIGIT = set('0123456789')
ALPHA_DIGIT = ALPHA | DIGIT

Alpha = one_of(map(StrLiteral, ALPHA))
Digit = one_of(map(StrLiteral, DIGIT))

Equal, Comma, Dot = [StrLiteral(c).ignore() for c in ['=', ',', '.']]
Underscore = StrLiteral('_')
NewLine = (~ StrLiteral('\n')).ignore()

def identifier_matcher(text, pos):
    """identifier"""
    end = len(text)
    start = pos
    if pos >= end:
        return None
    first = text[pos]
    if first != '_' and first not in ALPHA:
        return None
    pos += 1
    while pos < end:
        char = text[pos]
        if char == '_' or char in ALPHA_DIGIT:
            pos += 1
        else:
            break
    return text[start:pos], pos

Identifier = CustomMatcher(identifier_matcher)

IdTuple = rep_with_sep(Identifier, Comma)

Definition = Identifier + Equal + IdTuple + NewLine

Relation = Identifier + Equal + IdTuple + NewLine
Relation = Relation ** (lambda x: (x[0], 1 + len(x[1][1])))

POLICY_EFFECT_ALLOW_OVERRIDE = 'allow-override'
POLICY_EFFECT_DENY_OVERRIDE  = 'deny-override'
POLICY_EFFECT_ALLOW_AND_DENY = 'allow-and-deny'

POLICY_EFFECTS = [
    POLICY_EFFECT_ALLOW_OVERRIDE,
    POLICY_EFFECT_DENY_OVERRIDE,
    POLICY_EFFECT_ALLOW_AND_DENY
]

PolicyEft = one_of(map(StrLiteral, POLICY_EFFECTS)) + NewLine

def pyparser_matcher(text, pos):
    """syntactically correct python code"""
    line_end = text.find('\n', pos)
    if line_end == -1:
        return None
    try:
        c = compile(text[pos:line_end], '__abac_model__.py', 'eval')
    except SyntaxError:
        return None
    return c, line_end

PyExpr = CustomMatcher(pyparser_matcher)
Matcher = Identifier + Equal + PyExpr + NewLine

RequestDefHeader = StrLiteral('[request_definition]') + NewLine
TermDefHeader    = StrLiteral('[term_definition]') + NewLine
PolicyDefHeader  = StrLiteral('[policy_definition]') + NewLine
PolicyEftHeader  = StrLiteral('[policy_effect]') + NewLine
MatchersHeader   = StrLiteral('[matchers]') + NewLine

RequestDefSec = RequestDefHeader.ignore() + ~Definition
TermDefSec = TermDefHeader.ignore() + ~Definition
PolicyDefSec = PolicyDefHeader.ignore() + ~Definition
PolicyEftSec = PolicyEftHeader.ignore() + PolicyEft
MatchersSec = MatchersHeader.ignore() + ~Matcher

ModelDef = (RequestDefSec + PolicyDefSec + TermDefSec + PolicyEftSec + MatchersSec) ** flatten

def preprocess(conf):
    # process escaped line breaks
    conf = conf.replace('\\\n', '')
    # remove comments    
    conf = '\n'.join(line.partition('#')[0] for line in conf.splitlines())
    # remove redundant new lines
    conf = conf.strip()

    return conf + '\n'

def parse_model(text):
    text = preprocess(text)
    raw_model = ModelDef.parse_from(Stream(text)).payload
    return raw_model

class InvalidModelDefinition(Exception):
    def __init__(self, msg = ''):
        super(InvalidModelDefinition, self).__init__(msg)        

    @staticmethod
    def redundant_def(redefined_vars, g1, g2):
        msg_parts = [
            'multiple definition(s) of identifiers(s)',
            ', '.join(redfined_vars),
            'found in sections',
            g1, g2
        ]
        return InvalidModelDefinition(''.join(msg_parts))

    @staticmethod
    def missing_matchers(missing_matchers):
        msg = 'missing matcher(s) for request type(s): {}'
        return InvalidModelDefinition(msg.format(', '.join(missing_matchers)))

    @staticmethod
    def unknown_requests(unknown_requests):
        msg = 'matcher(s) defined for unknown request type(s): {}'
        return InvalidModelDefinition(msg.format(', '.join(unknown_requests)))

class Policy(object):
    def __init__(self, attrs, vals):
        assert len(attrs) == len(vals)
        self.__named_attrs = attrs
        for attr, val in zip(attrs, vals):
            setattr(self, attr, val)

    def __repr__(self):
        parts = ['Policy {\n']
        for attr in self.__named_attrs:
            parts.append('  ')
            parts.append(attr)
            parts.append(': ')
            parts.append(repr(getattr(self, attr)))
            parts.append('\n')
        parts.append('}\n')
        return ''.join(parts)

class Term(object):
    WILDCARD = object()
    def __init__(self, arity):
        self.__arity = arity
        self.__facts = []

    def add_facts(self, facts):
        for fact in facts:
            self.add_fact(fact)

    def add_fact(self, fact):
        assert len(fact) == self.__arity
        if not isinstance(fact, tuple):
            fact = tuple(fact)
        self.__facts.append(fact)

    def __call__(self, *args):
        assert len(args) == self.__arity
        # When all arguments are concrete, calling a term just returns boolean results
        # indicating whether the called tuple is part of the known facts
        if not any(arg is Term.WILDCARD for arg in args):
            return any(all(a == b for a, b in zip(fact, args)) for fact in self.__facts)
        # If arguments contain one or more wildcards, calling a term is more like a
        # query. The call returns a generator that iterates all facts that match with
        # the pattern described by the arguments
        def gen():
            for fact in self.__facts:
                rns = []
                matched = True
                for a, b in zip(fact, args):
                    if b is Term.WILDCARD:
                        rns.append(a)
                    else:
                        if a != b:
                            matched = False
                            break
                if matched:
                    yield rns
        return gen()

class Model(object):
    def __init__(self, raw_model):
        request_def, policy_def, term_def, effect, matchers = raw_model
        self.__request_template = { r[0]:r[1] for r in request_def }
        self.__policy_template = { p[0]:p[1] for p in policy_def }
        self.__term_template = { t[0]:t[1] for t in term_def }
        self.__effect = effect
        self.__matchers = { m[0]:m[1] for m in matchers }

        def_sections = zip(
            ['request_definition', '[policy_definition]', '[term_definition]'],
            [self.__request_template, self.__policy_template, self.__term_template],
        )

        n_sec = len(def_sections)
        for i in range(n_sec):
            for j in range(i + 1, n_sec):
                overlap = set(def_sections[i][1].keys()) & set(def_sections[j][1].keys())
                if overlap:
                    raise InvalidModelDefinition.redundant_def(
                        overalp, def_sections[i][0], def_sections[j][0]
                    )

        missing_matchers = set(self.__request_template.keys()) - set(self.__matchers.keys())
        if missing_matchers:
            raise InvalidModelDefinition.missing_matchers(missing_matchers)

        unknown_requests = set(self.__matchers.keys()) - set(self.__request_template.keys())
        if unknown_requests:
            raise InvalidModelDefinition.unknown_requests(unknown_requests)

        self.__policy_knowledge_base = {
            policy_name:set() for policy_name in self.__policy_template.keys()
        }
        self.__term_knowledge_base = {
            term_name:Term(len(term_tpl)) for term_name, term_tpl in self.__term_template.items()
        }

    def add_policies(self, policies):
        for p in policies:
            tpl = self.__policy_template[p[0]]
            self.__policy_knowledge_base[p[0]].add(Policy(tpl, p[1:]))

    def add_policies_from_csv_text(self, csv):
        self.add_policies([
            [p.strip() for p in line.split(',')] for line in csv.splitlines() if line
        ])

    def add_term_items(self, term_items):
        for ti in term_items:
            term = self.__term_knowledge_base[ti[0]]
            term.add_fact(ti[1:])

    def add_term_items_from_csv_text(self, csv):
        self.add_term_items([
            [p.strip() for p in line.split(',')] for line in csv.splitlines() if line
        ])

    def get_matcher_proxy(self, request_type, env):
        def matcher_proxy():
            return eval(self.__matchers[request_type], env)
        return matcher_proxy

    def enforce(self, request_type, request_content):
        tpl = self.__request_template[request_type]
        request_policy = Policy(tpl, request_content)

        has_allow = False
        
        def decisions(remaining_policy_keys, env):
            if not remaining_policy_keys:
                yield self.get_matcher_proxy(request_type, env)()
            else:
                next_key = remaining_policy_keys[0]
                remaining_policy_keys = remaining_policy_keys[1:]
                policy_candidates = self.__policy_knowledge_base[next_key]
                for policy in policy_candidates:
                    env[next_key] = policy
                    for d in decisions(remaining_policy_keys, env):
                        yield d

        enforcer_env = {
            request_type: request_policy,
            'true': True, 'false': False, 'null': None,
            '_': Term.WILDCARD
        }
        enforcer_env.update(self.__term_knowledge_base)

        for decision in decisions(self.__policy_knowledge_base.keys(), enforcer_env):
            if decision is True:
                return True
        return False

global_perm_model = None
if __name__ != '__main__':
    from acs_py_enclave import ffi

    @ffi.def_extern()
    def mesapy_setup_model(conf):
        global global_perm_model
        global_perm_model = Model(parse_model(ffi.string(conf)))
else:
    test_model = """
# request definition
[request_definition]
r = sub, obj, act
r2 = sub, obj
r3 = task, participants

[policy_definition]
p = sub, obj, act

[term_definition]
g = sub, grp
c = task, usr

[policy_effect]
allow-and-deny

[matchers]
r = (r.sub == p.sub and r.obj == p.obj and r.act == p.act) or (g(r.sub, 'admin') and not g(r.sub, 'blklist'))
r2 = r2.sub == r2.obj.Owner
r3 = all(usr in r3.participants for usr, in c(r3.task, _))
"""
    policy_csv = """
p, alice, file1, read
p, bob, file1, read
p, alice, file2, write
p, bob, file1, write
"""
    term_csv = """
g, charlie, admin
g, david, admin
g, david, blklist

c, task1, usr1
c, task1, usr2
c, task1, usr3
"""
    raw_model = parse_model(test_model)
    model = Model(raw_model)
    model.add_policies_from_csv_text(policy_csv)
    model.add_term_items_from_csv_text(term_csv)

    assert model.enforce('r', ['alice', 'file1', 'read']) == True
    assert model.enforce('r', ['alice', 'file1', 'write']) == False
    assert model.enforce('r', ['alice', 'file2', 'read']) == False
    assert model.enforce('r', ['alice', 'file2', 'write']) == True
  
    assert model.enforce('r', ['bob', 'file1', 'read']) == True
    assert model.enforce('r', ['bob', 'file1', 'write']) == True
    assert model.enforce('r', ['bob', 'file2', 'read']) == False
    assert model.enforce('r', ['bob', 'file2', 'write']) == False
  
    assert model.enforce('r', ['charlie', 'file1', 'read']) == True
    assert model.enforce('r', ['charlie', 'file1', 'write']) == True
    assert model.enforce('r', ['charlie', 'file2', 'read']) == True
    assert model.enforce('r', ['charlie', 'file2', 'write']) == True
  
    assert model.enforce('r', ['david', 'file1', 'read']) == False
    assert model.enforce('r', ['david', 'file1', 'write']) == False
    assert model.enforce('r', ['david', 'file2', 'read']) == False
    assert model.enforce('r', ['david', 'file2', 'write']) == False
  
    class ABACObj(object):
        def __init__(self, name, owner):
            self.Name = name
            self.Owner = owner
            
    r2obj = ABACObj('alicedata', 'alice')
  
    assert model.enforce('r2', ['charlie', r2obj]) == False
    assert model.enforce('r2', ['alice', r2obj]) == True
  
    assert model.enforce('r3', ['task1', ['usr1', 'usr2', 'usr3']]) == True
    assert model.enforce('r3', ['task1', ['usr1', 'usr3']]) == False
    assert model.enforce('r3', ['task1', ['usr1', 'usr2']]) == False
    assert model.enforce('r3', ['task1', ['usr1']]) == False
    assert model.enforce('r3', ['task1', []]) == False
    
    print 'all access control checks correct!'
