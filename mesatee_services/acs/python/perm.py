from acs_py_enclave import ffi
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
            return None
        if match_pos:
            string = string[match_pos:]
        if self.__items.startswith(string, pos):
            return Stream(self.__items, pos + len(string))
        return None

    def accept_matcher(self, matcher):
        pos = self.__pos
        l = len(self.__items)
        while pos < l and self.__items[pos] in self.WHITESPACES:
            pos += 1

        res = matcher(self.__items, pos)
        if res is None:
            return None
        obj, npos = res
        return obj, Stream(self.__items, npos)

    def end(self):
        return self.__pos == len(self.__items)

    def __repr__(self):
        line_start = max(0, self.__items.rfind('\n', 0, self.__pos))
        line_end = self.__items.find('\n', self.__pos)
        if line_end == -1:
            line_end = self.__pos

        parts = []

        if line_end - line_start > 80:
            line_start = max(line_start, self.__pos - 40)
            line_end = min(line_start + 80, len(self.__items))
            
        return ''.join([
            self.__items[line_start:line_end],
            '\n',
            ' ' * (self.__pos - line_start),
            '^',
            ' ' * (line_end - self.__pos - 1),
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

    def __iter__(self):
        yield self.success
        yield self.payload
        yield self.stream

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
        if not n_state or not n_state.stream.end():
            print n_state.stream
            raise ParsingError(n_state.stream)
        return n_state

    def fail(self, stream):
        return State(stream, None, False)

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
            return self.fail(stream)
        n_stream = stream.accept_strlit(self.__string)
        if n_stream is None:
            return self.fail(stream)
        else:
            return State(n_stream, self.__string)

class CustomMatcher(Parser):
    def __init__(self, matcher):
        super(CustomMatcher, self).__init__()
        self.__matcher = matcher

    def __call__(self, stream):
        res = stream.accept_matcher(self.__matcher)
        if res is None:
            return self.fail(stream)
        else:
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
            return State(stream, None, False)
        p1 = n_state.payload
        n_state = self.__second(n_state.stream)
        if not n_state:
            return State(stream, None, False)
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
        return self.fail(stream)

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

ALPHA_LOWER = 'abcdefghijklmnopqrstuvwxyz'
DIGIT = '0123456789'

Alpha = one_of(map(StrLiteral, ALPHA_LOWER))
Digit = one_of(map(StrLiteral, DIGIT))

Equal, Comma, Dot = [StrLiteral(c).ignore() for c in ['=', ',', '.']]
Underscore = StrLiteral('_')
NewLine = (~ StrLiteral('\n')).ignore()

Chars = (~ one_of([Alpha, Underscore,  Digit])) ** join

Identifier = one_of([Alpha, Underscore]) + (~ one_of([Alpha, Underscore,  Digit])) ** join
Identifier = (Identifier ** flatten) ** join

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
RoleDefHeader    = StrLiteral('[role_definition]') + NewLine
PolicyDefHeader  = StrLiteral('[policy_definition]') + NewLine
PolicyEftHeader  = StrLiteral('[policy_effect]') + NewLine
MatchersHeader   = StrLiteral('[matchers]') + NewLine

RequestDefSec = RequestDefHeader.ignore() + ~Definition
RoleDefSec = RoleDefHeader.ignore() + ~Definition
PolicyDefSec = PolicyDefHeader.ignore() + ~Definition
PolicyEftSec = PolicyEftHeader.ignore() + PolicyEft
MatchersSec = MatchersHeader.ignore() + ~Matcher

ModelDef = (RequestDefSec + PolicyDefSec + RoleDefSec + PolicyEftSec + MatchersSec) ** flatten

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
            'multiple definition(s) of term(s)',
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

class Term(object):
    def __init__(self, attrs, vals):
        assert len(attrs) == len(vals)
        self.__named_attrs = attrs
        for attr, val in zip(attrs, vals):
            setattr(self, attr, val)

    def __repr__(self):
        parts = ['\nTerm {\n']
        for attr in self.__named_attrs:
            parts.append('  ')
            parts.append(attr)
            parts.append(': ')
            parts.append(repr(getattr(self, attr)))
            parts.append('\n')
        parts.append('}\n')
        return ''.join(parts)

class Model(object):
    def __init__(self, raw_model, terms = []):
        request_def, policy_def, role_def, effect, matchers = raw_model
        self.request_template = { r[0]:r[1] for r in request_def }
        self.policy_template = { p[0]:p[1] for p in policy_def }
        self.role_template = { r[0]:r[1] for r in role_def }
        self.effect = effect
        self.matchers = { m[0]:m[1] for m in matchers }

        def_sections = zip(
            ['request_definition', '[policy_definition]', '[role_definition]'],
            [self.request_template, self.policy_template, self.role_template],
        )

        n_sec = len(def_sections)
        for i in range(n_sec):
            for j in range(i + 1, n_sec):
                overlap = set(def_sections[i][1].keys()) & set(def_sections[j][1].keys())
                if overlap:
                    raise InvalidModelDefinition.redundant_def(
                        overalp, def_sections[i][0], def_sections[j][0]
                    )

        missing_matchers = set(self.request_template.keys()) - set(self.matchers.keys())
        if missing_matchers:
            raise InvalidModelDefinition.missing_matchers(missing_matchers)

        unknown_requests = set(self.matchers.keys()) - set(self.request_template.keys())
        if unknown_requests:
            raise InvalidModelDefinition.unknown_requests(unknown_requests)

        self.term_to_template = {}
        self.term_to_template.update(self.policy_template)
        self.term_to_template.update(self.role_template)

        self.knowledge_base = {term_name:set() for term_name in self.term_to_template.keys()}

        self.add_terms(terms)

    def add_terms(self, terms):
        for t in terms:
            tpl = self.term_to_template[t[0]]
            self.knowledge_base[t[0]].add(Term(tpl, t[1:]))

    def add_terms_from_csv_text(self, csv):
        self.add_terms([
            [p.strip() for p in line.split(',')] for line in csv.splitlines() if line
        ])
            
    def get_matcher_proxy(self, request_type, env):
        def matcher_proxy():
            for k, v in env.items():
                locals()[k] = v
            return eval(self.matchers[request_type])
        return matcher_proxy

    def enforce(self, request):
        request_type, request_content = request
        tpl = self.request_template[request_type]
        request_term = Term(tpl, request_content)

        has_allow = False
        
        def decisions(remaining_term_keys, env):
            if not remaining_term_keys:
                yield self.get_matcher_proxy(request_type, env)()
            else:
                next_key = remaining_term_keys[0]
                remaining_term_keys = remaining_term_keys[1:]
                term_candidates = self.knowledge_base[next_key]
                for term in term_candidates:
                    env[next_key] = term
                    for d in decisions(remaining_term_keys, env):
                        yield d

        for decision in decisions(self.knowledge_base.keys(), {request_type: request_term}):
            if decision is True:
                return True
        return False

def build_model(conf, csv):
    raw_model = parse_model(conf)
    model = Model(raw_model)
    model.add_terms_from_csv_text(csv)
    return model

global_perm_model = None

@ffi.def_extern()
def mesapy_setup_model():
    conf = """
# request definition
[request_definition]
r = sub, obj, act
r2 = sub, obj

[policy_definition]
p = sub, obj, act

[role_definition]
g = sub, grp

[policy_effect]
allow-and-deny

[matchers]
r = (r.sub == p.sub and r.obj == p.obj and r.act == p.act) or (g.sub == r.sub and g.grp == 'admin')
r2 = r2.sub == r2.obj.Owner
"""
    csv = """
p, alice, file1, read
p, bob, file1, read
p, alice, file2, write
p, bob, file1, write

g, charlie, admin
"""
    global global_perm_model
    global_perm_model = build_model(conf, csv)

@ffi.def_extern()
def mesapy_run_tests():
    model = global_perm_model
    assert model.enforce(['r', ['alice', 'file1', 'read']]) == True
    assert model.enforce(['r', ['alice', 'file1', 'write']]) == False
    assert model.enforce(['r', ['alice', 'file2', 'read']]) == False
    assert model.enforce(['r', ['alice', 'file2', 'write']]) == True

    assert model.enforce(['r', ['bob', 'file1', 'read']]) == True
    assert model.enforce(['r', ['bob', 'file1', 'write']]) == True
    assert model.enforce(['r', ['bob', 'file2', 'read']]) == False
    assert model.enforce(['r', ['bob', 'file2', 'write']]) == False

    assert model.enforce(['r', ['charlie', 'file1', 'read']]) == True
    assert model.enforce(['r', ['charlie', 'file1', 'write']]) == True
    assert model.enforce(['r', ['charlie', 'file2', 'read']]) == True
    assert model.enforce(['r', ['charlie', 'file2', 'write']]) == True

    class ABACObj(object):
        def __init__(self, name, owner):
            self.Name = name
            self.Owner = owner
            
    alicedata = ABACObj('alicedata', 'alice')

    assert model.enforce(['r2', ['charlie', alicedata]]) == False
    assert model.enforce(['r2', ['alice', alicedata]]) == True

    print 'all access control checks correct!'

