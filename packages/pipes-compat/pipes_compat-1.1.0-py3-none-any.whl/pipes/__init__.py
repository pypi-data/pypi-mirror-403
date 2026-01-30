"""
Compatibility shim for the removed 'pipes' module.

The 'pipes' module was deprecated in Python 3.11 and removed in Python 3.13.
This package provides a compatibility layer for packages that still depend on it.

"""

import os
import re
import tempfile
from shlex import quote

__all__ = ["Template", "quote"]

# Conversion step kinds
FILEIN_FILEOUT = "ff"  # Must read & write real files
STDIN_FILEOUT = "-f"  # Must write a real file
FILEIN_STDOUT = "f-"  # Must read a real file
STDIN_STDOUT = "--"  # Normal pipeline element
SOURCE = ".-"  # Must be first, writes stdout
SINK = "-."  # Must be last, reads stdin

stepkinds = [FILEIN_FILEOUT, STDIN_FILEOUT, FILEIN_STDOUT, STDIN_STDOUT, SOURCE, SINK]


class Template:
    """Class representing a pipeline template."""

    def __init__(self) -> None:
        """Template() returns a fresh pipeline template."""
        self.debugging: object = 0
        self.reset()

    def __repr__(self) -> str:
        """t.__repr__() implements repr(t)."""
        return f"<Template instance, steps={self.steps!r}>"

    def reset(self) -> None:
        """t.reset() restores a pipeline template to its initial state."""
        self.steps: list[tuple[str, str]] = []

    def clone(self) -> "Template":
        """t.clone() returns a new pipeline template with identical
        initial state as the current one."""
        t = Template()
        t.steps = self.steps[:]
        t.debugging = self.debugging
        return t

    def debug(self, flag: object) -> None:
        """t.debug(flag) turns debugging on or off."""
        self.debugging = flag

    def append(self, cmd: str, kind: str) -> None:
        """t.append(cmd, kind) adds a new step at the end."""
        if not isinstance(cmd, str):
            raise TypeError("Template.append: cmd must be a string")
        if kind not in stepkinds:
            raise ValueError(f"Template.append: bad kind {kind!r}")
        if kind == SOURCE:
            raise ValueError("Template.append: SOURCE can only be prepended")
        if self.steps and self.steps[-1][1] == SINK:
            raise ValueError("Template.append: already ends with SINK")
        if kind[0] == "f" and not re.search(r"\$IN\b", cmd):
            raise ValueError("Template.append: missing $IN in cmd")
        if kind[1] == "f" and not re.search(r"\$OUT\b", cmd):
            raise ValueError("Template.append: missing $OUT in cmd")
        self.steps.append((cmd, kind))

    def prepend(self, cmd: str, kind: str) -> None:
        """t.prepend(cmd, kind) adds a new step at the front."""
        if not isinstance(cmd, str):
            raise TypeError("Template.prepend: cmd must be a string")
        if kind not in stepkinds:
            raise ValueError(f"Template.prepend: bad kind {kind!r}")
        if kind == SINK:
            raise ValueError("Template.prepend: SINK can only be appended")
        if self.steps and self.steps[0][1] == SOURCE:
            raise ValueError("Template.prepend: already begins with SOURCE")
        if kind[0] == "f" and not re.search(r"\$IN\b", cmd):
            raise ValueError("Template.prepend: missing $IN in cmd")
        if kind[1] == "f" and not re.search(r"\$OUT\b", cmd):
            raise ValueError("Template.prepend: missing $OUT in cmd")
        self.steps.insert(0, (cmd, kind))

    def open(self, file: str, rw: str):
        """t.open(file, rw) returns a pipe or file object open for
        reading or writing; the file is the other end of the pipeline."""
        if rw == "r":
            return self.open_r(file)
        if rw == "w":
            return self.open_w(file)
        raise ValueError(f"Template.open: rw must be 'r' or 'w', not {rw!r}")

    def open_r(self, file: str):
        """t.open_r(file) and t.open_w(file) implement
        t.open(file, 'r') and t.open(file, 'w') respectively."""
        if not self.steps:
            return open(file)
        if self.steps[-1][1] == SINK:
            raise ValueError("Template.open_r: pipeline ends with SINK")
        cmd = self.makepipeline(file, "")
        return os.popen(cmd, "r")

    def open_w(self, file: str):
        if not self.steps:
            return open(file, "w")
        if self.steps[0][1] == SOURCE:
            raise ValueError("Template.open_w: pipeline begins with SOURCE")
        cmd = self.makepipeline("", file)
        return os.popen(cmd, "w")

    def copy(self, infile: str, outfile: str) -> int:
        """t.copy(infile, outfile) copies infile to outfile through the pipeline."""
        return os.system(self.makepipeline(infile, outfile))

    def makepipeline(self, infile: str, outfile: str) -> str:
        """Build the shell command for the pipeline."""
        cmd = makepipeline(infile, self.steps, outfile)
        if self.debugging:
            print(cmd)
            cmd = "set -x; " + cmd
        return cmd


def makepipeline(infile: str, steps: list[tuple[str, str]], outfile: str) -> str:
    """Build a shell command to execute the pipeline.

    Args:
        infile: Input file path, or '' for stdin.
        steps: List of (command, kind) tuples.
        outfile: Output file path, or '' for stdout.

    Returns:
        Shell command string.
    """
    # Build a list with for each command:
    # [input filename or '', command string, kind, output filename or '']
    pipeline: list[list] = []
    for cmd, kind in steps:
        pipeline.append(["", cmd, kind, ""])

    # Make sure there is at least one step
    if not pipeline:
        pipeline.append(["", "cat", "--", ""])

    # Take care of the input and output ends
    cmd, kind = pipeline[0][1:3]
    if kind[0] == "f" and not infile:
        pipeline.insert(0, ["", "cat", "--", ""])
    pipeline[0][0] = infile

    cmd, kind = pipeline[-1][1:3]
    if kind[1] == "f" and not outfile:
        pipeline.append(["", "cat", "--", ""])
    pipeline[-1][-1] = outfile

    # Invent temporary files to connect stages that need files
    garbage: list[str] = []
    for i in range(1, len(pipeline)):
        lkind = pipeline[i - 1][2]
        rkind = pipeline[i][2]
        if lkind[1] == "f" or rkind[0] == "f":
            fd, temp = tempfile.mkstemp()
            os.close(fd)
            garbage.append(temp)
            pipeline[i - 1][-1] = pipeline[i][0] = temp

    # Build the command strings with proper I/O redirection
    for item in pipeline:
        inf, cmd, kind, outf = item
        if kind[1] == "f":
            cmd = "OUT=" + quote(outf) + "; " + cmd
        if kind[0] == "f":
            cmd = "IN=" + quote(inf) + "; " + cmd
        if kind[0] == "-" and inf:
            cmd = cmd + " <" + quote(inf)
        if kind[1] == "-" and outf:
            cmd = cmd + " >" + quote(outf)
        item[1] = cmd

    # Join the commands into a pipeline
    cmdlist = pipeline[0][1]
    for item in pipeline[1:]:
        cmd, kind = item[1:3]
        if item[0] == "":
            if "f" in kind:
                cmd = "{ " + cmd + "; }"
            cmdlist = cmdlist + " |\n" + cmd
        else:
            cmdlist = cmdlist + "\n" + cmd

    # Add cleanup for temporary files
    if garbage:
        rmcmd = "rm -f"
        for file in garbage:
            rmcmd = rmcmd + " " + quote(file)
        trapcmd = "trap " + quote(rmcmd + "; exit") + " 1 2 3 13 14 15"
        cmdlist = trapcmd + "\n" + cmdlist + "\n" + rmcmd

    return cmdlist
