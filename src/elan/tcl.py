#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains tcl parsing functions. These are badly documented here to speed up developing time. 

TclScope is the main class that executes functions.  

Notes:
There are problems with the implementation of lists. At current, tcl lists are saved as python lists, but that sometimes gives errors. Since the most important parts of library work as expected, the implementation might stay like this. 
"""
import re
import logging

from math import sin, cos, sqrt, hypot

from src.elan.tclparser import TclCommand, TclParser, TclError

module_logger = logging.getLogger(__name__)

def extend(liste, string):
    """
    Return element of the list that starts with this string.
    """
    # Completion of command (or whatever else)
    # Tcl loves to do this, but python hasnt implemented it...
    possibles = [item for item in liste if item.startswith(string)]
    if len(possibles) == 1:
        return possibles[0]
    elif len(possibles) > 1:
        raise RuntimeError("Found multiple extensions", possibles)
    else:
        raise KeyError(string)

class TclScope:
    def __init__(self, master = None, **var):
        module_logger.info(f"Creating Tcl scope with variables {var.keys()}")
        self._var = var
        if master is not None:
            for proc_name, proc in master.py_get_procs().items():
                # print("loaded proc", proc_name)
                setattr(self, proc_name, proc)
        self._procs = {}  # procs that are defined in this scope
        self.__parser = TclParser()
        self.__return_value = None
        self._cmdlog = []
        self._log = []
        self._master = master
        self._subscopes = []

    def __execute(self, cmd: TclCommand, filename=""):
        if len(cmd.words) == 0:
            # The empty function -> Do nothing
            return None
        # Interpolate words / perform substitutions
        words = []
        for i_word, word in enumerate(cmd.words):
            try:
                if word.env == "{}":
                    wordsub = word.word
                elif word.env == "[]":
                    wordsub = self(word.word)
                else:
                    wordsub = self.subst(word.word)
            except KeyError as e:
                msg = f"Variable {e!s} is not known in Tcl scope!"
                raise TclError(msg, cmd, i_word)
            except UnicodeDecodeError as e:
                s = e.object[e.start:e.end]
                msg = f"Could not handle escape sequence {s}"
                raise TclError(msg, cmd, i_word)
            except TclError as e:
                # e.cmd = cmd
                e.msg = f"{TclError.cmd2str(cmd, i_word)}"+\
                    f"Error when substituting '{word.word}':\n"+\
                    f"{TclError.cmd2str(e.cmd, e.i_word)} {e.msg}"
                
                raise e

            words.append(wordsub)

        # Treat keywords in python
        keyword_dict = {"if": "iftest", 
                        "return": "returnval",
                        "global": "global_var",
                        "for": "forloop",
        }
        if words[0] in keyword_dict.keys():
            words[0] = keyword_dict[words[0]]
        
        # Check that function exists
        if not hasattr(self, words[0]):
            msg = f"Function '{words[0]}' is not known in Tcl scope!"
            raise TclError(msg, cmd, 0)
        
        self._log.append({"words": words})
        
        func = getattr(self, words[0])
        if len(words) == 1:
            # Function calling without argument
            result = func()
        else:
            try:
                result = func(words[1:])
            except StopIteration as e:
                # print(f"stopped executing command {words[0]}")
                raise e
            except TclError as e:
                raise e
            except Exception as e:
                msg = f"{type(e).__name__}: {e.args}"
                raise TclError(msg, cmd)
        self._log[-1]["result"] = result
        return result

    def __substitute_variables(self, string: str, 
                               into_quotes: bool = False) -> str:
        s_out = ""

        r"""Pattern: 
        () – Patterngroup: Starts with first character in parentheses, ends 
            with last char.
        \\?– A backslash if it is there. This is in order to catch \$ because \$ means 
            use "$" and not variable substitute.
        \$+– A series (+) of one or more dollarsigns
        [^\$\\\s]* – A series (*) of characters [] that are not (^) dollar $,
            backslash \\ or whitespace \s
        """
        # print(string)
        # If not with brace
        pattern = r'\\?\$+(?!{)[^\$,.\+\-\=/\*<>"\s{}()\\]*'
        # If with braces
        pattern2 = r'\\?\$+{[^}]+}'
        def replace(x):
            s = x[0]
            # Dont match the first $-s or ecaped dollars \$
            # This implementation has consequence that "$\$bla" will be typed as
            # "$$bla" (with backslach substitution, else "$\$bla").
            # This seems also to be what Tcl does...
            if "$" in s.split(r"\$")[-1]:
                ld = s.rfind(r"$")
                var_string = f"{self._var[s[ld+1:]]}"
                if into_quotes:
                    var_string = f"'{var_string}'"
                return s[0:ld] + var_string
            else:
                return s
            
        def replace2(x):
            s = x[0]
            # Match from after first { to last }
            varname = re.findall(r"{[\s\S]+}", s)[0][1:-1]
            # print(varname)
            var = self._var[varname]
            if isinstance(var, list):
                var = ' '.join(var)
            var_string = f"{var}"
            if into_quotes:
                var_string = f"'{var_string}'"
            return var_string
        s_wo_brace = re.sub(pattern, replace, string)
        s_out = re.sub(pattern2, replace2, s_wo_brace)
        return s_out

    def __substitute_backslashes(self, string: str, which: str = "") -> str:
        # Which == "" means substitute all possible backslash characters
        # Backspace substitutions that are not implemented
        bs_not = 'xouU'
        # Backspace substitutions in Python
        bs_py = "nabfrtv"

        s_out = ""
        b = 0
        r"""pattern:
        \\ – A backslash
        [\w\W] – Either a whitespace or a non-whitespace char (that is any char)
        """
        for s in re.split(r"(\\[\w\W])", string):
            b += len(s)
            # Switch all possible second-characters
            if s.startswith("\\") and (which == "" or s[1] in which):
                if s[1] in bs_py:
                    s = s.encode().decode("unicode_escape")
                elif s[1] in bs_not:
                    # Ignore \x \o \u \U
                    raise NotImplementedError(f"Escape sequence {s}")
                else:
                    s = s[1]
            # The others are are for digit formatting. That is not needed here.
            s_out += s
        return s_out
    
    def __substitute_commands(self, string: str, into_quotes: bool = False) -> str:
        s_out = ""
        for s in self.__parser.find_brackets(string):
            if len(s) > 0 and s[0] == "[" and s[-1] == "]":
                s = self(s[1:-1])
                if into_quotes:
                    s = "'" + s + "'"
                
            s_out += s
        return s_out

    def __substitute(self, string: str, backslashes: bool = True,
                     variables: str = True, commands: str = True,
                     into_quotes: bool = False) -> str:
        if commands:
            string = self.__substitute_commands(string, into_quotes)
        if variables:
            string = self.__substitute_variables(string, into_quotes)
        if backslashes:
            string = self.__substitute_backslashes(string)
        return string
    
    def substitute_expr(self, string: str) -> str:
        # Go through all that is in quotes. If that is a number, convert it 
        # such that python can read it as a number instead of a string
        s_out = ""
        # print(string)
        s_int = re.sub(r"['\"]\d+[!\.]?['\"]", 
                       lambda x: str(int(x[0][1:-1])),  string)
        s_float = re.sub(r"['\"]\d+[!\.]\d*?['\"]", 
                         lambda x: str(float(x[0][1:-1])),  s_int)
        s_bool = re.sub(r"['\"](True|False)['\"]",lambda x: x[0][1:-1], s_float)
        s_math1 = s_bool.replace("||", " or ")
        s_math2 = s_math1.replace("&&", " and ")
        # s_math1 = re.sub(r"(\|\|)|(\&\&)", lambda x: x[0][0], s_bool)
        # double in tcl is float in python
        s_math3 = s_math2.replace("double", "float")
        s_out = s_math3
        # print(s_out)
        return s_out
    def __call__(self, s, filename=""):
        if self._master is None:
            filename = "console"
        cmds = self.__parser(s, filename)
        # print(cmds)
        for cmd in cmds:
            self._cmdlog.append(cmd)
            try:
                ret = self.__execute(cmd, filename)
            except StopIteration as e:
                # print(f"stopped executing script {filename}")
                ret = e.value
                if filename.lower().startswith("proc") or\
                    filename.lower() == ["console"]:
                        break
                else:
                    raise e
        
        # Note that this is the return of the last command which may or may not 
        # be last command in the executed script.
        return ret
    
    def py_getlog(self):
        return self._log
            
    def py_getcallings(self, callings: list, recursive: bool = True) -> list:
        """
        Return the log for executing these commands
        
        :param callings: List of commands to include in the log
        :type callings: list
        :param bool recursive: Include subscopes (statements in called functions)
        :return: list of the words in the calling of the commands in callings
        :rtype: list

        """
        log = []
        for entry in self._log:
            if entry["words"][0] in callings:
                log.append(entry["words"])
            if "scope" in entry and recursive:
                log.extend(entry["scope"].py_getcallings(callings))
        return log
    
    def py_get_procs(self):
        # print("py_get_procs")
        return self._procs
        
    def append(self, args):
        if len(args) == 0:
            raise ValueError("You must at least have the name of the list")
        varname = args[0]
        print(varname)
        # Create list if not existing
        if varname not in self._var:
            self._var[varname] = []
        var = self._var[varname]

        # If variable is not a list, then make it to a list
        if isinstance(var, str):  # that is not a list...
            self._var[varname] = [var]
            var = self._var[varname]
            
        for arg in args[1:]:
            var.append(arg)
        return
        
    def eval(self, args, name =""):
        # if len(args) > 1:
        #     raise NotImplementedError("Only evaluate one command at once!")
        # return self(args[0])
        return self(' '.join(args), name)
    
    def expr(self, args):
        # Arrays are not implemented

        expression = ''.join(args)
        sub = self.__substitute(expression, into_quotes=True)
        sub = self.substitute_expr(sub)
        
        # print(sub)
        # We are using python default interpreter, which is dangerous.
        # Therefore lambdas, double underscores, newlines and semicolons are 
        # completely forbidden in the evaluation
        # TODO: Do the list positive, only call int, float, sin, cos etc., and 
        # strings...
        forbidden = ["lambda", "__", "\n", ";", "exec"]
        for exp in forbidden:
            if exp in sub:
                msg = "Tried to evaluate expression with forbidden word: "
                raise NotImplementedError(msg+exp)
        # Mostly, python should be able to run all expressions correctly...
        
        if len(sub) > 0:
            try:
                res = eval(sub)
            except TypeError as e:
                print(repr(e.args[0]))
                e.args = [repr(e.args[0]) + " in expression" + sub]
                raise e
        else:
            res = "False"
        # print(res)
        return str(res)
        
    
    def exec(self, args):
        print("Nice try...")
    
    def forloop(self, args):
        start, test, nekst, body = args
        
        max_iter = 1000
        
        self.eval([start])
        for i in range(max_iter):
            if not self.expr(test) == "True":
                break
            self.eval([body])
            self.eval([nekst])
        
    def incr(self, args):
        varname = args[0]
        if len(args) > 1:
            increment = int(args[1])
        else:
            increment = 1        
        
        self._var[varname] = str(int(self._var[varname]) + increment)
        
    def global_var(self, args):
        print(f"Set or query {args} to global variables. Not implemented because",
              " implementation propably uses global variables anyway...")
        
    def iftest(self, args):
        # print(args)
        conditions = []
        expressions = []
        for arg in args:
            if arg in ["then", "elseif"]:
                continue
            elif len(conditions) > len(expressions):
                expressions.append(arg)
            else:
                conditions.append(arg)
        
        if len(conditions) != len(expressions):
            msg = f"There is a unequal number of conditions, {len(conditions)}"+\
                f", and expressions, {len(expressions)}!"
            raise ValueError(msg)
        
        # print(conditions, expressions)
        
        # Perform the test
        for i, cond in enumerate(conditions):
            if cond != "else":
                ret = self.expr([cond])
            else:
                ret = "True"
            # print(f"Condition '{cond}' evaulated to {ret!r}")
            if ret in ["True", "1", "yes", "true"]:
                self.eval([expressions[i]], f"if {cond[i]}")
                break
    def lindex(self, args):
        liste = args[0]
        index = int(args[1])
        return liste[index]
    
    def list(self, args):
        # Is already a list in this implementation.......
        return args
    
    def llength(self, args):
        return str(len(args))
    
    def proc(self, args):
        if len(args) > 3:
            raise ValueError("Too many arguments for function proc!")
        elif len(args) < 2:
            raise ValueError("Too few arguments for function proc!")
        # print(args)
        name = args[0]
        body = args[-1]
        if len(args) == 3:
            # raise NotImplementedError()
            argwords = self.__parser.get_words(args[1])
            funcargs = []
            defargs = []
            for word in argwords:
                if word.env == "{}":
                    ret = self.__parser.get_words(word.word)
                    if len(ret) == 2:
                        argname = ret[0].word
                        val = ret[1].word
                    else:
                        msg = "Can only have one argument name and one"+\
                            " default value!"
                        raise ValueError(msg)
                    funcargs.append(argname)
                    defargs.append(val)
                elif word.env in [" ",""]:
                    if len(defargs) > 0 and word.word != "args":
                        # Tcl has no problem with this, but Python has
                        msg = "non-default argument follows default argument"
                        raise ValueError(msg)
                    funcargs.append(word.word)
                else:
                    msg = f"Please dont use {word.env!r} in the argument list!"
                    raise NotImplementedError(msg)
                
            # print(funcargs, defargs)
        else:
            funcargs = []
            defargs = []
            
        def execute_function(funcargs, defargs, callargs):
            # print(funcargs, defargs, callargs)
            scope = type(self)(master=self, **self._var)
            self._log[-1]["scope"] = scope
            self._subscopes.append(scope)
            required_args = len(funcargs) - len(defargs)
            if funcargs[-1] == "args":
                required_args -= 1
                if len(callargs) > len(funcargs) - 1:
                    # print(callargs[len(funcargs)-1:])
                    scope.set(['args', ' '.join(callargs[len(funcargs)-1:])])
                    # print(scope._var["args"])
                else:
                    scope.set(['args', ''])
            for i, arg in enumerate(funcargs):
                if arg == "args" and i == len(funcargs) - 1:
                    break
                elif i < len(callargs):
                    scope.set([arg, callargs[i]])
                elif i >= required_args:
                    j = i - required_args
                    scope.set([arg, defargs[j]])
                elif i == len(funcargs)-1:
                    raise NotImplementedError(funcargs[-1])
                else:
                    msg = "Must specify at least "+\
                        f"{len(funcargs) - len(defargs)} arguments!"+\
                        f" {funcargs[i]}"
                    raise ValueError(msg)
            scope(body, f"proc {name}")
            return scope.__return_value
        func = lambda x ="": execute_function(funcargs, defargs, x)
        
        setattr(self, name, func)
        self._procs[name] = func
        
        
            
    def puts(self, args):
        # Channelid not supported
        if len(args) > 3:
            raise TypeError("Too many arguments to puts!")

        if args[0] == "-nonewline":
            end = ""
        else:
            end = "\n"
        print(args[-1], end=end)
        
    def returnval(self, args):
        self.__return_value = args[-1]
        raise StopIteration(args[-1])
        
    def set(self, args):
        if len(args) > 2:
            raise TypeError("Too many arguments to set!")
        elif len(args) == 0:
            raise TypeError("Function set requires at least one argument!")
        if len(args) == 2:
            name, val = args
        else:
            name = args[0]
            val = ""

        self._var[name] = val
        return val
    
    def source(self, args):
        #The arg should be a path to the source file.
        print(f"Not executing source file {args[0]}")
    
    def split(self, args):
        # print(args)
        # Note: Tcl uses every character in the string as a separator, 
        # python uses the whole string as one single separator.
        stringg = args[0]
        split_chars = args[1]
        for char in split_chars:
            stringg = stringg.replace(char, split_chars[0])
        res = stringg.split(split_chars[0])
        # This generates a python list which may (not) work correctly with tcl
        return res
        

    def string(self, args):
        if args[0] == "tolower":
            return args[1].lower()
    def subst(self, *args):
        return self.__substitute(args[-1])
