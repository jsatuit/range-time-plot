#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains tcl parsing functions. These are badly documented here to speed up developing time. 

The class TclParser parses a tcl script/line into TclCommand objects. These are used/executed by TclScope.  
"""
import re


class Word:
    def __init__(self, word, line=0, filename="", start: int = 0,
                 env: str = ''):
        self.word = word
        self.line = line
        self.filename = filename
        self.start = start
        self.env = env

    def __str__(self):
        if self.env in ["{}", "[]"]:
            return self.env[0]+self.word+self.env[-1]
        else:
            return self.word
    def __repr__(self):
        return f"Word('{self.word}', env='{self.env}')"

    def __eq__(self, other):
        if isinstance(other, Word):
            return self.word == other.word
        else:
            msg = f"Must compare a Word with another Word, not a {type(other)}"
            raise NotImplementedError(msg)

    def endswith(self, *args):
        return self.word.endswith(args)


class TclCommand:

    def __init__(self, *words: list[Word | str], line: int = 0,
                 filename: str = "Console", char1: int = 0, char2: int = 0):
        self.words = words
        self.line = line
        self.filename = filename
        self.char1 = char1
        self.char2 = char2

    def __str__(self):
        words_str = [str(word) for word in self.words]
        return f"{' '.join(words_str)}"

    def __repr__(self):
        words_str = ["'"+str(word)+"'" for word in self.words]
        return f"TclCommand({', '.join(words_str)})"

    def __eq__(self, other):
        return self.words == other.words


class TclError(Exception):
    def __init__(self, msg: str, cmd: TclCommand, i_word: int | None = None):
        self.msg = msg
        self.cmd = cmd
        self.i_word = i_word
        

        errmsg = self.cmd2str(self.cmd, self.i_word) + msg

        super().__init__(errmsg)
    @staticmethod
    def cmd2str(cmd, i_word):
        if cmd.filename.lower() == "console":
            s = cmd.filename
        else:
            s = cmd.filename
        if cmd.line > 0:
            s += f", line {cmd.line}"

        if i_word is None:
            if cmd.char1 > 0:
                if cmd.char2 > cmd.char1:
                    s += f", chars {cmd.char1}–{cmd.char2}: "
                else:
                    s += f", char {cmd.char1}: "
        else:
            # Word causing the error
            word = cmd.words[i_word]
            char1 = word.start
            # Not correct, but fast to implement
            char2 = word.start + len(word.word)
            s += f", chars {char1}–{char2}: "
        return s
        


class TclParser:
    def __init__(self):
        self.reset()

    def reset(self):
        self.words = []
        self.commands = []

        self.env = ""
        self.env_level = 0
        self.in_comment = False

    def __call__(self, script: str, name: str = "", filename: str = "Console",
                 startline: int = 1):
        self.reset()
        self.filename = filename
        self.name = name
        self.startline = startline
        self.line = 1
        self.wordstart = 0
        self.curchar = 1
        self.curchar_next = 1

        if isinstance(script, str):
            if not script.endswith("\n"):
                script += "\n"

        # tokens = re.split('([ \n\t\\#;{}\[\]"$])', script)
        tokens = re.split(r'([ \n\t"#\|&{}\[\]])', script)

        for token in tokens:
            self.curchar = self.curchar_next
            self.curchar_next += len(token)

            if token == "\n":
                self.line += 1
                self.curchar_next = 1
                if len(self.words) > 0 and self.words[-1].endswith('\\'):
                    # Line continuation \\\n
                    if isinstance(self.words[-1], Word):
                        self.words[-1].word = self.words[-1].word[0:-1] + " "
                    else:
                        self.words[-1] = self.words[-1][0:-1] + " "
                    continue

            if self.env:
                self.handle_env(token)
            elif self.in_comment:
                if token == "\n":
                    self.in_comment = False
            elif token in " \t":
                pass
            elif token in ";\n":
                self.command_ends()
            elif token == "#":
                if len(self.words) > 0:
                    self.raise_error("Cannot start a comment here!")
                self.in_comment = True
            else:
                self.start_env(token)

        return self.commands

    def handle_env(self, token):

        # Tokens that end the different environments
        end_tokens = {
            '""': ['"'],
            " ": " \t\n;",
            "{}": ["}"],
            "[]": ["]"],
        }
        in_backslash = self.words[-1].endswith('\\')
        incr_level = ((self.env == "{}" and token == "{") or
                      (self.env == "[]" and token == "[")) and not in_backslash
        decr_level = ((self.env == "{}" and token == "}") or
                      (self.env == "[]" and token == "]")) and not in_backslash and self.env_level > 1
        end_env = token in end_tokens[self.env] and \
            (self.env == " " or not in_backslash) and not decr_level
        change_env = token == "[" and self.env == " " and not in_backslash
        end_command = self.env == " " and token in [":", "\n"]
        # print(repr(token), in_backslash, incr_level, decr_level, end_env, end_command)

        if incr_level:
            self.env_level += 1
            self.words[-1] += token
        elif decr_level:
            self.env_level -= 1
            self.words[-1] += token
        elif end_env:
            self.words[-1] = Word(self.words[-1], line = self.line,
                                  start=self.wordstart, env=self.env)
            self.wordstart = 0
            self.env_level = 0
            if self.env == " " and token == "[":
                self.start_env(token)
            else:
                self.env = ""
        elif change_env:
            self.handle_env(" ")
            self.start_env(token)
        else:
            self.words[-1] += token

        if end_command:
            self.command_ends()

    def raise_error(self, msg):
        cmd = TclCommand("", line=self.line, filename=self.filename,
                         char1=self.curchar)

        raise TclError(msg, cmd)

    def start_env(self, token):
        if token == '"':
            self.words.append('')
            self.env = '""'

        elif token == "{":
            self.env_level = 1
            self.words.append('')
            self.env = "{}"
        elif token == "[":
            self.env_level = 1
            self.words.append('')
            self.env = '[]'
        else:
            self.words.append(token)
            self.env = " "

        if not self.wordstart:
            self.wordstart = self.curchar

    def command_ends(self):
        # Comments are not commands
        if len(self.words) == 0:
            # The empty command. Is valid in Tcl??????
            self.commands.append(TclCommand())
        else:
            # A normal command
            char1 = self.words[0].start
            char2 = self.words[-1].start + len(self.words[-1].word) + \
                len(self.words[-1].env)
            self.commands.append(TclCommand(*self.words,
                                            line=self.words[0].line,
                                            char1=char1, char2=char2))
        self.cmdchar1 = 1
        self.words = []

    def get_words(self, script):
        words = []
        commands = self(script)
        for cmd in commands:
            for word in cmd.words:
                words.append(word)
        return words

    def find_brackets(self, script):
        brackets = []
        pos = []
        
        commands = self(script)
        for cmd in commands:
            for word in cmd.words:
                if word.env == "[]":
                    brackets.append(str(word))
                    pos.append(word.start)
                    
        strings = []
        if len(brackets) > 0:
            for i in range(len(brackets)):
                if i == 0:
                    strings.append(script[0:pos[i]-1])
                else:
                    strings.append(script[pos[i-1]+len(brackets[i])-1:pos[i]-1])
                strings.append(brackets[i])
            strings.append(script[pos[-1]+len(brackets[i])-1:])
        else:
            strings.append(script)
        return strings
                
