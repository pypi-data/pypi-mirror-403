"""
Wrap 'retained_extras_on_rebase' (from either mercurial or evolve) to retain
the "useful" extra.
"""

from mercurial import rewriteutil

def extsetup(ui):
    rewriteutil.retained_extras_on_rebase.add(b'useful')
