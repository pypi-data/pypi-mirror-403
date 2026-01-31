#!/usr/bin/env python3

import argparse
import os
import re


ignored_patterns = [
    re.compile(r'^#if'),
    re.compile(r'^#else'),
    re.compile(r'^#endif'),
    re.compile(r'#rest-ignore$'),
]


def rstify(orig):
    """Take contents of a .t file and produce reStructuredText"""
    newlines = []

    code_block_mode = False
    sphinx_directive_mode = False

    for line in orig.splitlines():

        # Empty lines doesn't change output
        if not line:
            newlines.append(line)
            code_block_mode = False
            sphinx_directive_mode = False
            continue

        ignored = False
        for pattern in ignored_patterns:
            if pattern.search(line):
                ignored = True
                break
        if ignored:
            continue

        # Sphinx directives mode
        if line.startswith('  .. '):

            # Insert a empty line to makes sphinx happy
            newlines.append("")

            # And unindent the directive
            line = line[2:]
            sphinx_directive_mode = True

        # Code mode
        codeline = line.startswith('  ')
        if codeline and not sphinx_directive_mode:
            if code_block_mode is False:
                newlines.extend(['::', ''])

            code_block_mode = True

        newlines.append(line)

    return "\n".join(newlines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('testfile', help='.t file to transform')

    opts = ap.parse_args()

    with open(opts.testfile) as f:
        content = f.read()
    rst = rstify(content)
    target = os.path.splitext(opts.testfile)[0] + '.rst'
    with open(target, 'w') as f:
        f.write(rst)


if __name__ == '__main__':
    main()
