#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

from src.elan.tcl import TclError, TclScope


def stdouttest(shell, capsys, string, printed, add_newline=True):
    if add_newline:
        printed += "\n"
    shell(string)
    assert capsys.readouterr().out == printed


def longstr2strlist(s):
    return '"'+s.replace("\n", '",\n"')+'"'


def remove_leading_whitespaces(s):
    import re
    return re.sub("\n *", "\n", s)


def test_tutorial1(capsys):
    # https://wiki.tcl-lang.org/page/Tcl+Tutorial+Lesson+1
    sh = TclScope()

    stdouttest(sh, capsys, "puts Hello,", "Hello,")
    stdouttest(sh, capsys, "puts World.", "World.")

    stdouttest(sh, capsys, """
               puts Hello,
               puts World""", """Hello,\nWorld""")
    stdouttest(sh, capsys, """
               puts -nonewline Hello,
               puts World
               """, "Hello,World")

    stdouttest(sh, capsys, 'puts "Hello, World"', "Hello, World")

    # And now the final example
    script = """
    puts "Hello, World - In quotes"    ;# Note: comment after a command.
    # This is a comment at beginning of a line
    puts {Hello, World - In Braces}
    
    puts "This is line 1"; puts "this is line 2"
    
    puts "Hello, World; - With  a semicolon inside the quotes"
    
    # Words don't need to be quoted unless they contain white space:
    puts HelloWorld
    """
    printout = '\n'.join([
        "Hello, World - In quotes",
        "Hello, World - In Braces",
        "This is line 1",
        "this is line 2",
        "Hello, World; - With  a semicolon inside the quotes",
        "HelloWorld",
    ])
    stdouttest(sh, capsys, script, printout)

    with pytest.raises(TclError):
        sh("puts {Bad comment syntax example}   # *Error* - no semicolon!")


def test_tutorial2(capsys):
    sh = TclScope()

    script = """
    set X "This is a string"

    set Y 1.24
    
    puts $X
    puts $Y
    
    puts "..............................."
    
    set label "The value in Y is: "
    puts "$label $Y"
    """
    printout = '\n'.join([
        "This is a string",
        "1.24",
        "...............................",
        "The value in Y is:  1.24",
    ])
    stdouttest(sh, capsys, script, printout)


def test_tutorial3(capsys):
    sh = TclScope()

    script = remove_leading_whitespaces(r"""
    set Z Albany
    set Z_LABEL "The capital of New York is: "
    
    puts "$Z_LABEL $Z"   ;# Prints the value of Z
    puts "$Z_LABEL \$Z"  ;# Prints literal $Z instead of the value of Z
    
    puts "\nBen Franklin is on the \$100.00 bill"
    
    set a 100.00
    puts "Washington is not on the $a bill"    ;# Not what you want
    puts "Lincoln is not on the $$a bill"      ;# This is OK
    puts "Hamilton is not on the \$a bill"     ;# Not what you want either
    puts "Ben Franklin is on the \$$a bill"    ;# But, this is OK
    
    puts "\n................. examples of escape strings"
    puts "Tab\tTab\tTab"
    puts "This string prints out \non two lines"
    puts "This string comes out\
    on a single line"
    """)

    printout = '\n'.join([
        "The capital of New York is:  Albany",
        "The capital of New York is:  $Z",
        "",
        "Ben Franklin is on the $100.00 bill",
        "Washington is not on the 100.00 bill",
        "Lincoln is not on the $100.00 bill",
        "Hamilton is not on the $a bill",
        "Ben Franklin is on the $100.00 bill",
        "",
        "................. examples of escape strings",
        "Tab\tTab\tTab",
        "This string prints out ",
        "on two lines",
        "This string comes out on a single line",
    ])
    stdouttest(sh, capsys, script, printout)


def test_tutorial4(capsys):
    sh = TclScope()

    script = remove_leading_whitespaces(r"""
    set Z Albany
    set Z_LABEL "The capital of New York is: "
    
    puts "\n.............. examples of differences between  \" and \{"
    puts "$Z_LABEL $Z"
    puts {$Z_LABEL $Z}
    
    puts "\n....... examples of differences in nesting \{ and \" "
    puts "$Z_LABEL {$Z}"
    puts {Who said, "What this country needs is a good $0.05 cigar!"?}
    
    puts "\n.............. examples of escape strings"
    puts {Note: no substitutions done within braces \n \r \x0a \f \v}
    puts {But:
    The escaped newline at the end of a\
    string is replaced by a space}
    """)

    printout = remove_leading_whitespaces(r"""
    .............. examples of differences between  " and {
    The capital of New York is:  Albany
    $Z_LABEL $Z
    
    ....... examples of differences in nesting { and " 
    The capital of New York is:  {Albany}
    Who said, "What this country needs is a good $0.05 cigar!"?
    
    .............. examples of escape strings
    Note: no substitutions done within braces \n \r \x0a \f \v
    But:
    The escaped newline at the end of a string is replaced by a space""")

    stdouttest(sh, capsys, script, printout)

def test_tutorial5(capsys):
    sh = TclScope()

    script = remove_leading_whitespaces(r"""
    set x abc
    puts "A simple substitution: $x\n"
    
    set y [set x "def"]
    puts "Remember that set returns the new value of the variable:"
    puts ">>>>X: $x Y: $y\n"
    
    set z {[set x "String within quotes within braces"]}
    puts "Note curly braces: $z\n"
    
    set a "[set x {String within braces within quotes}]"
    puts "See how the set is executed: $a"
    puts "\$x is: $x\n"
    
    set b "\[set y {This is a string within braces within quotes}]"
    # Note the \ escapes the bracket, and must be doubled to be a
    # literal character in double quotes
    puts "Note the \\ escapes the bracket:\n>\$b is: $b"
    puts "\$y is: $y"
    """)

    printout = remove_leading_whitespaces(r"""A simple substitution: abc

    Remember that set returns the new value of the variable:
    >>>>X: def Y: def
    
    Note curly braces: [set x "String within quotes within braces"]
    
    See how the set is executed: String within braces within quotes
    $x is: String within braces within quotes
    
    Note the \ escapes the bracket:
    >$b is: [set y {This is a string within braces within quotes}]
    $y is: def""")

    stdouttest(sh, capsys, script, printout)
    
def test_tutorial6a(capsys):
    sh = TclScope()

    script = remove_leading_whitespaces(r"""
    set X 100
    set Y 256
    set Z [expr {$Y + $X}]
    set Z_LABEL "$Y plus $X is "
    
    puts "$Z_LABEL $Z"
    puts "The square root of $Y is [expr { sqrt($Y) }]\n"
    
    puts "Because of the precedence rules \"5 + -3 * 4\"   is:"
    puts ">  [expr {-3 * 4 + 5}]"
    puts "Because of the parentheses      \"(5 + -3) * 4\" is:"
    puts ">  [expr {(5 + -3) * 4}]"
    """)
    printout = remove_leading_whitespaces(r"""256 plus 100 is  356
    The square root of 256 is 16.0
    
    Because of the precedence rules "5 + -3 * 4"   is:
    >  -7
    Because of the parentheses      "(5 + -3) * 4" is:
    >  8""")
    stdouttest(sh, capsys, script, printout)
def test_tutorial6b(capsys):
    sh = TclScope()   
    script = remove_leading_whitespaces(r"""
    set A 3
    set B 4
    puts "The hypotenuse of a triangle: [expr {hypot($A,$B)}]"
    
    #
    # The trigonometric functions work with radians ...
    #
    set pi6 [expr {3.1415926/6.0}]
    puts "Sine and cosine of pi/6: [expr {sin($pi6)}] [expr {cos($pi6)}]"
    """)
    printout = remove_leading_whitespaces(\
    r"""The hypotenuse of a triangle: 5.0
    Sine and cosine of pi/6: 0.49999999226497965 0.8660254082502546""")
    stdouttest(sh, capsys, script, printout)
# def test_tutorial6c(capsys):
    # sh = TclScope()    
    # Dont implement arrays (yet)
    # script = remove_leading_whitespaces(r"""
    # #
    # # Working with arrays
    # #
    # set a(1) 10
    # set a(2) 7
    # set a(3) 17
    # set b    2
    # puts "Sum: [expr {$a(1)+$a($b)}]"
    # puts ">  [expr {(5 + -3) * 4}]"
    # """)
    # printout = remove_leading_whitespaces(r"""Sum: 17""")
    # stdouttest(sh, capsys, script, printout)
def test_tutorial6d(capsys):
    sh = TclScope()   
    script = remove_leading_whitespaces(r"""
    puts "1/2 is [expr {1./2}]"
    puts "1/3 is [expr {1./3}]"

    set a [expr {1.0/3.0}]
    puts "3*(1/3) is [expr {3.0*$a}]"

    set b [expr {10.0/3.0}]
    puts "3*(10/3) is [expr {3.0*$b}]"

    set c [expr {10.0/3.0}]
    set d [expr {2.0/3.0}]
    puts "(10.0/3.0) / (2.0/3.0) is [expr {$c/$d}]"

    set e [expr {1.0/10.0}]
    puts "1.2 / 0.1 is [expr {1.2/$e}]"
    """)
    printout = remove_leading_whitespaces(\
    r"""1/2 is 0.5
    1/3 is 0.3333333333333333
    3*(1/3) is 1.0
    3*(10/3) is 10.0
    (10.0/3.0) / (2.0/3.0) is 5.000000000000001
    1.2 / 0.1 is 11.999999999999998""")
    stdouttest(sh, capsys, script, printout)
    
def test_tutorial7(capsys):
    sh = TclScope()   
    script = remove_leading_whitespaces(r"""
    set x 1
    
    if {$x == 2} {puts "$x is 2"} else {puts "$x is not 2"}
    
    if {$x != 1} {
        puts "$x is != 1"
    } else {
        puts "$x is 1"
    }
    """)
    printout = remove_leading_whitespaces(\
    r"""1 is not 2
    1 is 1""")
    stdouttest(sh, capsys, script, printout) 
    
def test_tutorial11(capsys):
    sh = TclScope()   
    script = remove_leading_whitespaces(r"""
    proc sum {arg1 arg2} {
        set x [expr {$arg1 + $arg2}];
        return $x
    }
    
    puts " The sum of 2 + 3 is: [sum 2 3]\n\n"
    """)
    printout = remove_leading_whitespaces(\
    r""" The sum of 2 + 3 is: 5
    
    """)
    stdouttest(sh, capsys, script, printout) 
    
    with pytest.raises(TclError):
        sh('puts " The sum of 2 + 3 is: [sum 2]\n\n"')
    
def test_tutorial12(capsys):
    sh = TclScope()   
    script = remove_leading_whitespaces(r"""
    proc example {first {second 0} args} {
        if {$second == "0"} {
            puts "There is only one argument and it is: $first"
            return 1
        } else {
            if {$args == ""} {
                puts "There are two arguments - $first and $second"
                return 2
            } else {
                puts "There are many arguments - $first and $second and $args"
                return "many"
            }
        }
    }
    
    set count1 [example ONE]
    set count2 [example ONE TWO]
    set count3 [example ONE TWO THREE ]
    set count4 [example ONE TWO THREE FOUR]
    
    puts "The example was called with a varying number of arguments:"
    puts ">   $count1, $count2, $count3, and $count4"
    """)
    printout = remove_leading_whitespaces(\
    r"""There is only one argument and it is: ONE
    There are two arguments - ONE and TWO
    There are many arguments - ONE and TWO and THREE
    There are many arguments - ONE and TWO and THREE FOUR
    The example was called with a varying number of arguments:
    >   1, 2, many, and many""")
    stdouttest(sh, capsys, script, printout) 
    
def test_info():
    sh = TclScope() 
    assert sh("info exists a") == "0"
    sh("set a 10")
    assert sh("info exists a") == "1"
    