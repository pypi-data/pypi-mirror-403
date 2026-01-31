#!/usr/bin/env python
"""
This script takes `minimumhgversion` and `testedwith` values from the first
file (e.g. hgext3rd/evolve/metadata.py) and mercurial package versions from the
second file (e.g. debian/control) and compares them using a set of rules to
find any issues.

Rules:

    - if `minimumhgversion` is a feature release, the first version from
      `testedwith` should belong to that feature release

    - if `minimumhgversion` is a bugfix release, the first version from
      `testedwith` should be the same

    - mercurial package versions (from both Depends and Build-Depends sections)
      should match `minimumhgversion`

Usage: $0 MFILE CFILE where MFILE contains extension metadata and CFILE is a
debian/control file.
"""

from __future__ import print_function

import argparse
import os
import re

def grepall(workdir, linere):
    for root, dirs, files in os.walk(workdir):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            path = os.path.join(root, fname)
            with open(path, 'r') as src:
                for line in src:
                    for groups in linere.findall(line):
                        yield path, groups

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mfile', help='.py file with `testedwith`')
    ap.add_argument('cfile', help='debian/control file')

    opts = ap.parse_args()

    mre = re.compile(r"^minimumhgversion = b'([0-9.]+)'")
    mtre = re.compile(r"^testedwith = b'([0-9.]+) ")
    minversion = ''
    mintestedversion = ''

    with open(opts.mfile, 'r') as src:
        for line in src:
            if not minversion:
                groups = mre.findall(line)
                if groups:
                    minversion = groups[0]
            if not mintestedversion:
                groups = mtre.findall(line)
                if groups:
                    mintestedversion = groups[0]

    if not minversion:
        print('could not find `minimumhgversion` variable in %s' % opts.mfile)

    if not mintestedversion:
        print('could not find `testedwith` variable in %s' % opts.mfile)

    if minversion.count('.') > 1:
        # `minversion` is a bugfix release
        if minversion != mintestedversion:
            print('`minimumhgversion` is a bugfix release, the first version '
                  'in `testedwith` should be the same: %s and %s'
                  % (minversion, mintestedversion))

    else:
        # matching X.Y to determine the "feature release" version
        frelre = re.compile(r"([0-9]+).([0-9]+)")

        if frelre.findall(minversion) != frelre.findall(mintestedversion):
            print('the first version in `testedwith` does not belong to the '
                  'same feature release as `minimumhgversion`: %s and %s'
                  % (mintestedversion, minversion))

    cre = re.compile(r"^ mercurial \(>= ([0-9.]+)\)")
    depversion = ''

    with open(opts.cfile, 'r') as src:
        for line in src:
            groups = cre.findall(line)
            if groups:
                depversion = groups[0]
                if minversion != depversion:
                    print('versions differ: %s from `minimumhgversion`, %s '
                          'from dependencies' % (minversion, depversion))

    if not depversion:
        print('could not find dependency on mercurial in %s' % opts.cfile)

if __name__ == '__main__':
    main()
