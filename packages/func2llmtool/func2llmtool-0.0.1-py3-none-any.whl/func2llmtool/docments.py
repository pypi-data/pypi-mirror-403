# Extracted code from https://github.com/AnswerDotAI/fastcore.docments (License: Apache-2.0)

import re, sys, types, pprint, functools, textwrap, copy
from io import BytesIO
from ast import parse, FunctionDef, AsyncFunctionDef, AnnAssign
from tokenize import tokenize, COMMENT
from textwrap import dedent
from inspect import signature, Parameter, getsource, isfunction, ismethod, isclass, getdoc
from inspect import _empty as empty
from dataclasses import is_dataclass
from typing import Union
from warnings import warn
from collections import namedtuple
from collections.abc import Mapping

NoneType = type(None)
_allowed_types = (type(lambda:0), type(len), type(str.join), types.ModuleType, type(type.__call__), type(''.__str__))
_clean_re = re.compile(r'^\s*#(.*)\s*$')

class AttrDict(dict):
    "`dict` subclass that also provides access to keys as attrs"
    def __getattr__(self,k):
        if k in self: return self[k]
        raise AttributeError(k)
    def __setattr__(self, k, v): (self.__setitem__,super().__setattr__)[k[0]=='_'](k,v)
    def __dir__(self): return super().__dir__() + list(self.keys())
    def _repr_markdown_(self): return f'```python\n{pprint.pformat(self, indent=2)}\n```'
    def copy(self): return AttrDict(**self)

def eval_type(t, glb, loc):
    "`eval` a type or collection of types, if needed, for annotations in py3.10+"
    if isinstance(t,str):
        if '|' in t: return Union[eval_type(tuple(t.split('|')), glb, loc)]
        return eval(t, glb, loc)
    if isinstance(t,(tuple,list)): return type(t)([eval_type(c, glb, loc) for c in t])
    return t

def _eval_type(t, glb, loc):
    res = eval_type(t, glb, loc)
    return NoneType if res is None else res

def get_annotations_ex(obj, *, globals=None, locals=None):
    "Backport of py3.10 `get_annotations` that returns globals/locals"
    if isinstance(obj, type):
        obj_dict = getattr(obj, '__dict__', None)
        if obj_dict and hasattr(obj_dict, 'get'):
            ann = obj_dict.get('__annotations__', None)
            if isinstance(ann, types.GetSetDescriptorType): ann = None
        else: ann = None
        obj_globals = None
        module_name = getattr(obj, '__module__', None)
        if module_name:
            module = sys.modules.get(module_name, None)
            if module: obj_globals = getattr(module, '__dict__', None)
        obj_locals = dict(vars(obj))
        unwrap = obj
    elif isinstance(obj, types.ModuleType):
        ann = getattr(obj, '__annotations__', None)
        obj_globals = getattr(obj, '__dict__')
        obj_locals,unwrap = None,None
    elif callable(obj):
        ann = getattr(obj, '__annotations__', None)
        obj_globals = getattr(obj, '__globals__', None)
        obj_locals,unwrap = None,obj
    else: raise TypeError(f"{obj!r} is not a module, class, or callable.")
    if ann is None: ann = {}
    if not isinstance(ann, dict): raise ValueError(f"{obj!r}.__annotations__ is neither a dict nor None")
    if not ann: ann = {}
    if unwrap is not None:
        while True:
            if hasattr(unwrap, '__wrapped__'):
                unwrap = unwrap.__wrapped__
                continue
            if isinstance(unwrap, functools.partial):
                unwrap = unwrap.func
                continue
            break
        if hasattr(unwrap, "__globals__"): obj_globals = unwrap.__globals__
    if globals is None: globals = obj_globals
    if locals is None: locals = obj_locals
    return dict(ann), globals, locals

def type_hints(f):
    "Like `typing.get_type_hints` but returns `{}` if not allowed type"
    if not isinstance(f, _allowed_types): return {}
    ann,glb,loc = get_annotations_ex(f)
    return {k:_eval_type(v,glb,loc) for k,v in ann.items()}

def signature_ex(obj, eval_str:bool=False):
    "Backport of `inspect.signature(..., eval_str=True` to <py310"
    def _eval_param(ann, k, v):
        if k not in ann: return v
        return Parameter(v.name, v.kind, annotation=ann[k], default=v.default)
    if not eval_str: return signature(obj)
    sig = signature(obj)
    if sig is None: return None
    ann = type_hints(obj)
    params = [_eval_param(ann,k,v) for k,v in sig.parameters.items()]
    return signature.__class__(params, return_annotation=sig.return_annotation)

def isdataclass(s):
    "Check if `s` is a dataclass but not a dataclass' instance"
    return is_dataclass(s) and isclass(s)

def get_dataclass_source(s):
    "Get source code for dataclass `s`"
    return getsource(s) if not getattr(s, "__module__") == '__main__' else ""

def get_source(s):
    "Get source code for string, function object or dataclass `s`"
    if isinstance(s,str): return s
    return getsource(s) if isfunction(s) or ismethod(s) else get_dataclass_source(s) if isdataclass(s) else None

def _parses(s):
    "Parse Python code in string, function object or dataclass `s`"
    return parse(dedent(get_source(s) or ''))

def _tokens(s):
    "Tokenize Python code in string or function object `s`"
    s = get_source(s)
    if not s: return []
    return tokenize(BytesIO(s.encode('utf-8')).readline)

def _clean_comment(s):
    res = _clean_re.findall(s)
    return res[0] if res else None

def _get_comment(line, arg, comments, parms):
    if line in comments: return comments[line].strip()
    line -= 1
    res = []
    while line and line in comments and line not in parms:
        res.append(comments[line])
        line -= 1
    return dedent('\n'.join(reversed(res))) if res else None

def _param_locs(s, returns=True, args_kwargs=False):
    "`dict` of parameter line numbers to names"
    body = _parses(s).body
    if len(body)==1:
        defn = body[0]
        if isinstance(defn, (FunctionDef, AsyncFunctionDef)):
            res = {arg.lineno:arg.arg for arg in defn.args.args}
            if defn.args.vararg: res[defn.args.vararg.lineno] = defn.args.vararg.arg
            res.update({arg.lineno:arg.arg for arg in defn.args.kwonlyargs})
            if defn.args.kwarg and args_kwargs: res[defn.args.kwarg.lineno] = defn.args.kwarg.arg
            if returns and defn.returns: res[defn.returns.lineno] = 'return'
            return res
        elif isdataclass(s):
            res = {arg.lineno:arg.target.id for arg in defn.body if isinstance(arg, AnnAssign)}
            return res
    return None

def _get_full(p, docs, eval_str=False):
    anno = p.annotation
    if anno==empty:
        if p.default!=empty: anno = type(p.default)
        elif p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD): anno = p.kind
        elif eval_str: anno = None
    return AttrDict(docment=docs.get(p.name), anno=anno, default=p.default)

def docstring(sym):
    "Get docstring for `sym` for functions ad classes"
    if isinstance(sym, str): return sym
    res = getdoc(sym)
    if not res and isclass(sym): res = getdoc(sym.__init__)
    return res or ""

def _merge_doc(dm, npdoc):
    if not npdoc: return dm
    if not isinstance(dm, dict): return dm or '\n'.join(npdoc.desc)
    if not dm.docment: dm.docment = '\n'.join(npdoc.desc)
    return dm

def _merge_docs(dms, npdocs):
    npparams = npdocs['Parameters']
    params = {nm:_merge_doc(dm,npparams.get(nm,None)) for nm,dm in dms.items()}
    if 'return' in dms: params['return'] = _merge_doc(dms['return'], npdocs['Returns'])
    return params

SECTIONS = 'Summary Extended Yields Receives Other Raises Warns Warnings See Also Notes References Examples Attributes Methods'.split()
PARAM_SECTIONS = {"Parameters", "Other Parameters", "Attributes", "Methods", "Raises", "Warns", "Yields", "Receives"}
NPParameter = namedtuple('Parameter', ['name', 'type', 'desc'])

def strip_blank_lines(l):
    "Remove leading and trailing blank lines from a list of lines"
    while l and not l[0].strip(): del l[0]
    while l and not l[-1].strip(): del l[-1]
    return l

def dedent_lines(lines, split=True):
    "Deindent a list of lines maximally"
    res = textwrap.dedent("\n".join(lines))
    if split: res = res.split("\n")
    return res

class Reader:
    "A line-based string reader."
    def __init__(self, data):
        if isinstance(data, list): self._str = data
        else: self._str = data.split('\n')
        self.reset()
    def __getitem__(self, n): return self._str[n]
    def reset(self): self._l = 0
    def read(self):
        if not self.eof():
            out = self[self._l]
            self._l += 1
            return out
        else: return ''
    def seek_next_non_empty_line(self):
        for l in self[self._l:]:
            if l.strip(): break
            else: self._l += 1
    def eof(self): return self._l >= len(self._str)
    def read_to_condition(self, condition_func):
        start = self._l
        for line in self[start:]:
            if condition_func(line): return self[start:self._l]
            self._l += 1
            if self.eof(): return self[start:self._l+1]
        return []
    def read_to_next_empty_line(self):
        self.seek_next_non_empty_line()
        def is_empty(line): return not line.strip()
        return self.read_to_condition(is_empty)
    def read_to_next_unindented_line(self):
        def is_unindented(line): return (line.strip() and (len(line.lstrip()) == len(line)))
        return self.read_to_condition(is_unindented)
    def peek(self, n=0):
        if self._l + n < len(self._str): return self[self._l + n]
        else: return ''
    def is_empty(self): return not ''.join(self._str).strip()

class NumpyDocString(Mapping):
    "Parses a numpydoc string to an abstract representation"
    sections = {o:[] for o in SECTIONS}
    sections['Summary'] = ['']
    sections['Parameters'] = []
    sections['Returns'] = []
    param_sections: set[str] = set(PARAM_SECTIONS)

    def __init__(self, docstring, config=None, supported_sections=SECTIONS, supports_params=PARAM_SECTIONS):
        if supports_params is None: supports_params = set(PARAM_SECTIONS)
        else:
            missing = set(supports_params) - set(self.param_sections)
            for sec in missing: self.param_sections.add(sec)
        if supported_sections is None: supported_sections = set(SECTIONS)
        else:
            missing = set(supported_sections) - set(self.sections.keys())
            for sec in missing: self.sections[sec] = []
        docstring = textwrap.dedent(docstring).split('\n')
        self._doc = Reader(docstring)
        self._parsed_data = copy.deepcopy(self.sections)
        self._parse()
        self['Parameters'] = {o.name:o for o in self['Parameters']}
        if self['Returns']: self['Returns'] = self['Returns'][0]
        for sec in supports_params:
            if sec in self._parsed_data: self._parsed_data[sec] = self._normalize_param_section(self._parsed_data[sec])
        for section in SECTIONS: self[section] = dedent_lines(self[section], split=False)
    def __iter__(self): return iter(self._parsed_data)
    def __len__(self): return len(self._parsed_data)
    def __getitem__(self, key): return self._parsed_data[key]
    def __setitem__(self, key, val):
        if key not in self._parsed_data: self._error_location(f"Unknown section {key}", error=False)
        else: self._parsed_data[key] = val
    def _is_at_section(self):
        self._doc.seek_next_non_empty_line()
        if self._doc.eof(): return False
        l1 = self._doc.peek().strip()
        l2 = self._doc.peek(1).strip()
        if len(l2) >= 3 and (set(l2) in ({'-'}, {'='})) and len(l2) != len(l1):
            snip = '\n'.join(self._doc._str[:2])+'...'
            self._error_location("potentially wrong underline length... \n%s \n%s in \n%s" % (l1, l2, snip), error=False)
        return l2.startswith('-'*len(l1)) or l2.startswith('='*len(l1))
    def _strip(self, doc):
        i,j = 0,0
        for i, line in enumerate(doc):
            if line.strip(): break
        for j, line in enumerate(doc[::-1]):
            if line.strip(): break
        return doc[i:len(doc)-j]
    def _read_to_next_section(self):
        section = self._doc.read_to_next_empty_line()
        while not self._is_at_section() and not self._doc.eof():
            if not self._doc.peek(-1).strip(): section += ['']
            section += self._doc.read_to_next_empty_line()
        return section
    def _read_sections(self):
        while not self._doc.eof():
            data = self._read_to_next_section()
            name = data[0].strip()
            if name.startswith('..'): yield name, data[1:]
            elif len(data) < 2: yield StopIteration
            else: yield name, self._strip(data[2:])
    def _parse_param_list(self, content, single_element_is_type=False):
        content = dedent_lines(content)
        r = Reader(content)
        params = []
        while not r.eof():
            header = r.read().strip()
            if ' :' in header:
                arg_name, arg_type = header.split(' :', maxsplit=1)
                arg_name, arg_type = arg_name.strip(), arg_type.strip()
            else:
                if single_element_is_type: arg_name, arg_type = '', header
                else: arg_name, arg_type = header, ''
            desc = r.read_to_next_unindented_line()
            desc = dedent_lines(desc)
            desc = strip_blank_lines(desc)
            params.append(NPParameter(arg_name, arg_type, desc))
        return params
    def _normalize_param_section(self, val):
        if not isinstance(val, list) or not val: return val
        if not isinstance(val[0], NPParameter): return val
        return {p.name: p for p in val}
    def _parse_summary(self):
        if self._is_at_section(): return
        while True:
            summary = self._doc.read_to_next_empty_line()
            summary_str = " ".join([s.strip() for s in summary]).strip()
            compiled = re.compile(r'^([\w., ]+=)?\s*[\w\.]+\(.*\)$')
            if compiled.match(summary_str) and not self._is_at_section(): continue
            break
        if summary is not None: self['Summary'] = summary
        if not self._is_at_section(): self['Extended'] = self._read_to_next_section()
    def _parse(self):
        self._doc.reset()
        self._parse_summary()
        sections = list(self._read_sections())
        section_names = {section for section, content in sections}
        has_returns = 'Returns' in section_names
        has_yields = 'Yields' in section_names
        if has_returns and has_yields: raise ValueError('Docstring contains both a Returns and Yields section.')
        if not has_yields and 'Receives' in section_names: raise ValueError('Docstring contains a Receives section but not Yields.')
        for (section, content) in sections:
            if not section.startswith('..'):
                section = (s.capitalize() for s in section.split(' '))
                section = ' '.join(section)
                if self.get(section): self._error_location("The section %s appears twice in  %s" % (section, '\n'.join(self._doc._str)))
            if section in ('Parameters', 'Other Parameters', 'Attributes', 'Methods'): self[section] = self._parse_param_list(content)
            elif section in ('Returns', 'Yields', 'Raises', 'Warns', 'Receives'): self[section] = self._parse_param_list(content, single_element_is_type=True)
            else: self[section] = content
    @property
    def _obj(self):
        if hasattr(self, '_cls'): return self._cls
        elif hasattr(self, '_f'): return self._f
        return None
    def _error_location(self, msg, error=True):
        if error: raise ValueError(msg)
        else: warn(msg)

def parse_docstring(sym):
    "Parse a numpy-style docstring in `sym`"
    return AttrDict(**NumpyDocString(docstring(sym)))

def docments(s, full=False, eval_str=False, returns=True, args_kwargs=False):
    "Get docments for `s`"
    if isclass(s) and not is_dataclass(s): s = s.__init__
    try: sig = signature_ex(s, eval_str=eval_str)
    except ValueError: return AttrDict()
    nps = parse_docstring(s)
    docs = {}
    while s:
        p = _param_locs(s, returns=returns, args_kwargs=args_kwargs) or {}
        c = {o.start[0]:_clean_comment(o.string) for o in _tokens(s) if o.type==COMMENT}
        for k,v in p.items():
            if v not in docs: docs[v] = _get_comment(k, v, c, p)
        s = getattr(s, '__delwrap__', None)
    res = {k:_get_full(v, docs, eval_str=eval_str) if full else docs.get(k) for k,v in sig.parameters.items()}
    if returns:
        if full: res['return'] = AttrDict(docment=docs.get('return'), anno=sig.return_annotation, default=empty)
        else: res['return'] = docs.get('return')
    return AttrDict(_merge_docs(res, nps))
