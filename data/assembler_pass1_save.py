"""
Assembler for DM2018W assembly language,
pre-pass that resolves symbolic labels into
addresses.

The instructions to be transformed are:

     BC label
becomes:
    MOVE  PC,0,PC[<relative>]
where <relative> is the difference between the current
instruction and the instruction at the label.

     STORE rx, label
becomes:
    STORE  rx,r0,PC[<relative>]
and
     LOAD  rx, label
becomes:
    LOAD  rx,r0,PC[<relative>]
where <relative> is the difference between the current
instruction and the instruction at the label.

"""
from instr_format import Instruction
import memory
import argparse

from typing import Union, List, Tuple
from enum import Enum, auto

import sys
import io
import re
import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Configuration constants
ERROR_LIMIT = 5  # Abandon assembly if we exceed this


# Exceptions raised by this module
class SyntaxError(Exception):
    pass


###
# Although the DM2018W instruction set is very simple, a source
# line can still come in several forms.  Each form (even comments)
# can start with a label.
###

class AsmSrcKind(Enum):
    """Distinguish which kind of assembly language instruction
    we have matched.  Each element of the enum corresponds to
    one of the regular expressions below.
    """
    # Blank or just a comment, optionally
    # with a label
    COMMENT = auto()
    # Fully specified  (all addresses resolved)
    FULL = auto()
    # With symbolic label to be resolved
    SYMBOLIC = auto()
    # A data location, not an instruction
    DATA = auto()


# Lines that contain only a comment (and possibly a label).
# This includes blank lines and labels on a line by themselves.
#
ASM_COMMENT_PAT = re.compile(r"""
   # Optional label
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   \s*
   # Optional comment follows # or ;
   (
     (?P<comment>[\#;].*)
   )?
   \s*$
   """, re.X)

# Instructions with fully specified fields. We can generate
# code directly from these.  In the transformation phase we
# pass these through unchanged, just keeping track of how much
# room they require in the final object code.
ASM_FULL_PAT = re.compile(r"""
   # Optional label
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   # The instruction proper
   \s*
    (?P<opcode>    [a-zA-Z]+)           # Opcode
    (/ (?P<predicate> [a-zA-Z]+) )?   # Predicate (optional)
    \s+
    (?P<target>    r[0-9]+),            # Target register
    (?P<src1>      r[0-9]+),            # Source register 1
    (?P<src2>      r[0-9]+)             # Source register 2
    (\[ (?P<offset>[-]?[0-9]+) \])?     # Offset (optional)
   # Optional comment follows # or ;
   (
     \s*
     (?P<comment>[\#;].*)
   )?
   \s*$
   """, re.X)

# A data word in memory; not a DM2018W instruction
#
ASM_DATA_PAT = re.compile(r"""
   # Optional label
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   # The instruction proper
   \s*
    (?P<opcode>    DATA)           # Opcode
   # Optional data value
   \s*
   (?P<value>  (0x[a-fA-F0-9]+)
             | ([0-9]+))?
    # Optional comment follows # or ;
   (
     \s*
     (?P<comment>[\#;].*)
   )?
   \s*$
   """, re.X)

# Instructions with pseudo operations, e.g.,
# Branch, Store, Load with just a label as operand.
# We must transform these to fully specified instructions
# before generating code for them.
ASM_SYMBOLIC_PAT = re.compile(r"""
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   # The instruction proper
   \s*
   (
     (?P<opcode>    (STORE)|(LOAD)|(JUMP))  # Opcode
     (/ (?P<predicate> [a-zA-Z]+) )?        # Predicate (optional)
     \s+
     ((?P<target>    r[0-9]+),)?            # Optionally one register
     (?P<symbol>     [a-zA-Z][a-zA-Z0-9_]*) # Symbolic label
   )
   # Optional comment follows # or ;
   (
     \s*
     (?P<comment>[\#;].*)
   )?
   \s*$
   """, re.X)

PATTERNS = [(ASM_FULL_PAT, AsmSrcKind.FULL),
            (ASM_DATA_PAT, AsmSrcKind.DATA),
            (ASM_SYMBOLIC_PAT, AsmSrcKind.SYMBOLIC),
            (ASM_COMMENT_PAT, AsmSrcKind.COMMENT)
            ]

def parse_line(line: str) -> dict:
    """Parse one line of assembly code.
    Returns a dict containing the matched fields,
    some of which may be empty.  Raises SyntaxError
    if the line does not match assembly language
    syntax. Sets the 'kind' field to indicate
    which of the patterns was matched.
    """
    # log.debug("\nParsing assembler line: '{}'".format(line))
    # Try each kind of pattern
    for pattern, kind in PATTERNS:
        match = pattern.fullmatch(line)
        if match:
            fields = match.groupdict()
            fields["kind"] = kind
            # log.debug("Extracted fields {}".format(fields))
            return fields
    raise SyntaxError("Assembler syntax error in {}".format(line))


def resolve_labels(lines: List[str]) -> Tuple[dict, int]:
    """First pass over instructions --- build table mapping
    labels to addresses.  Returns the table and a count
    of errors.
    """
    error_count = 0
    addr = 0  # Address of next instruction
    symtab = {}
    for lnum in range(len(lines)):
        line = lines[lnum]
        log.debug("Pass 1 line {} addr {}: {}".format(lnum, addr, line))
        try:
            fields = parse_line(line)
            # Any kind of line, including a comment, could start
            # with a label.
            if fields["label"]:
                lab = fields["label"]
                if lab in symtab:
                    print("Duplicate label {} on line {}".format(lab, lnum))
                    error_count += 1
                else:
                    symtab[lab] = addr
            # Any kind of line except a comment takes up one
            # word in memory.
            if fields["kind"] != AsmSrcKind.COMMENT:
                addr += 1

        except SyntaxError as e:
            error_count += 1
            print("Syntax error in line {}: {}".format(lnum, line))
        except KeyError as e:
            error_count += 1
            print("Unknown word in line {}: {}".format(lnum, e))
        except Exception as e:
            error_count += 1
            print("Exception encountered in line {}: {}".format(lnum, e))
        if error_count > ERROR_LIMIT:
            print("Too many errors; abandoning")
            sys.exit(1)
    return symtab, error_count


def build_resolved(fields: dict, addr: int, symtab: dict) -> str:
    """ Given the matched fields of a symbolic
    operation, a current address,
    and a table mapping labels to addresses, return
    a fully resolved DM2018W source code instruction
    with PC-relative addressing.
    """
    op = fields["opcode"]
    predicate = fields["predicate"]
    if predicate:
        predicate = "/{}".format(predicate)
    else:
        predicate = ""

    target = fields["target"] or "r0"
    if fields["label"] == None:
        label = ""
    else:
        label = "{}: ".format(fields["label"])

    # All symbolic addresses are PC-relative
    symbol = fields["symbol"]
    if symbol not in symtab:
        raise KeyError("Use of undefined label: {}".format(symbol))
    pc_relative = symtab[symbol] - addr

    if op == "STORE" or op == "LOAD":
        operand = fields["target"]
        return "{} {} {},r0,r15[{}]  # Access variable '{}'".format(label, op, operand, pc_relative, symbol)
    elif op == "JUMP":
        return "{}   ADD{}  r15,r0,r15[{}] #Jump to {}".format(label, predicate, pc_relative, symbol)
    else:
        assert False, "Should not reach this point"


def transform_instructions(lines: List[str], symtab: dict) -> None:
    """Second pass:  Construct the instructions, using the
    symbol table.  Only instructions that matched the 'SYMBOLIC'
    pattern need to be transformed.
    """
    addr = 0
    for lnum in range(len(lines)):
        line = lines[lnum]
        log.debug("Pass 2 line {}, addr {}, {}".format(lnum, addr, line))
        # We rewrite pseudo-instructions with labels
        fields = parse_line(line)
        if fields["kind"] == AsmSrcKind.SYMBOLIC:
            try:
                lines[lnum] = build_resolved(fields, addr, symtab)
            except KeyError as e:
                print("Syntax error: unresolved symbol: {}".format(fields["symbol"]))
        if fields["kind"] != AsmSrcKind.COMMENT:
            addr += 1


def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Assembler address resolution")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                        help="Duck Machine assembly code file")
    parser.add_argument("outfile", type=argparse.FileType('w'),
                        nargs="?", default=sys.stdout,
                        help="Output file for resolved assembly code")
    args = parser.parse_args()
    return args


def main():
    """"Pre-process a Duck Machine assembler file to
    convert labels to addresses.
    """
    args = cli()
    source_lines = [line.rstrip() for line in args.sourcefile.readlines()]
    symtab, n_errors = resolve_labels(source_lines)
    log.debug("Symbol table: {}".format(symtab))
    if n_errors == 0:
        transform_instructions(source_lines, symtab)
    if n_errors == 0:
        for line in source_lines:
            print(line, file=args.outfile)
    args.outfile.close()

    log.debug("Done")


if __name__ == "__main__":
    main()
