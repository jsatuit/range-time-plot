#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.elan.tclparser import Word, TclCommand, TclParser


def test_tclcommand():
    cmd = TclCommand("eval", "callblock", "beata", "[argv]")
    cmd2 = eval(repr(cmd))

    assert cmd.words == cmd2.words
    assert cmd == cmd2

    assert str(cmd) == "eval callblock beata [argv]"


def test_parser():
    p = TclParser()

    # Empty command
    assert p("") == [TclCommand()]

    # Single-line script
    assert p(""" puts "Hello, World" """) == \
        [TclCommand(Word('puts'), Word('Hello, World'))]

    # Multiline script
    s = """
        puts "Hello, World" 
        """
    res = [
        TclCommand(),
        TclCommand(Word('puts'), Word('Hello, World')),
        TclCommand(),
    ]
    assert p(s) == res
    
    assert p("gotoblock ${SCAN_PAT} $EXPSTART $EXPNAME $HEIGHT") == \
        [TclCommand(Word('gotoblock'), Word('${SCAN_PAT}'), Word('$EXPSTART'), 
                    Word('$EXPNAME'), Word('$HEIGHT'))]
def test_bracket_finding():
    p = TclParser()
    
    p.find_brackets('["a"]&&["b"]') == ['["a"]', '&&', '["b"]']