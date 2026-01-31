# Copyright 2017 FUJIWARA Katsunori <foozy@lares.dti.ne.jp>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
"""
Compatibility module
"""
from __future__ import absolute_import

from mercurial import (
    cmdutil,
    extensions,
    scmutil,
)

# hg <= 7.1 (28dbb31f7317)
try:
    cleanup_nodes = cmdutil.cleanup_nodes
except AttributeError:
    cleanup_nodes = scmutil.cleanupnodes  # pytype: disable=module-attr

# hg <= 7.1 (6ca1d7250a7b)
try:
    from mercurial.cmd_impls import update as updatemod
    hg_update = updatemod.update
except (AttributeError, ImportError):
    from mercurial import hg
    hg_update = hg.update  # pytype: disable=module-attr

def branchmapitems(branchmap):
    if hasattr(branchmap, 'iteritems'):
        # py2 compat
        return branchmap.iteritems()
    if hasattr(branchmap, 'items'):
        return branchmap.items()
    return [(b, branchmap.branchheads(b, closed=True)) for b in branchmap]

def overridecommitstatus(overridefn):
    code = cmdutil.commitstatus.__code__
    if r'head_change' in code.co_varnames:
        # commitstatus(repo, node, head_change=None, tip=None, **opts)
        extensions.wrapfunction(cmdutil, 'commitstatus', overridefn)
    elif r'opts' in code.co_varnames[code.co_argcount:]:
        # commitstatus(repo, node, branch, bheads=None, tip=None, **opts)
        # hg <= 7.1 (45c5b012cffc)
        extensions.wrapfunction(cmdutil, 'commitstatus', overridefn)
