from __future__ import absolute_import

from mercurial import (
    node as nodemod,
    obsolete,
    revset,
)

from . import (
    exthelper,
    rewind,
)

try:
    from mercurial import revset_predicates
    revset_predicates.unstable
except ImportError:
    # hg <= 7.1 (63d119607447)
    from mercurial import revset as revset_predicates


eh = exthelper.exthelper()

#####################################################################
### experimental behavior                                         ###
#####################################################################

getrevs = obsolete.getrevs

### Unstable revset symbol

@eh.revsetpredicate(b'troubled()')    # legacy name
def revsettroubled(repo, subset, x):
    return revset_predicates.unstable(repo, subset, x)

### Obsolescence graph

# XXX SOME MAJOR CLEAN UP TO DO HERE XXX

def _precursors(repo, s, includeidentical=False):
    """Precursor of a changeset"""
    cs = set()
    getrev = repo.changelog.index.get_rev
    markerbysubj = repo.obsstore.predecessors
    node = repo.changelog.node
    for r in s:
        for p in markerbysubj.get(node(r), ()):
            if not includeidentical and p[2] & rewind.identicalflag:
                continue
            pr = getrev(p[0])
            if pr is not None:
                cs.add(pr)
    cs -= repo.changelog.filteredrevs # nodemap has no filtering
    return cs

def _allprecursors(repo, s):  # XXX we need a better naming
    """transitive precursors of a subset"""
    node = repo.changelog.node
    toproceed = [node(r) for r in s]
    seen = set()
    allsubjects = repo.obsstore.predecessors
    while toproceed:
        nc = toproceed.pop()
        for mark in allsubjects.get(nc, ()):
            np = mark[0]
            if np not in seen:
                seen.add(np)
                toproceed.append(np)
    getrev = repo.changelog.index.get_rev
    cs = set()
    for p in seen:
        pr = getrev(p)
        if pr is not None:
            cs.add(pr)
    cs -= repo.changelog.filteredrevs # nodemap has no filtering
    return cs

def _successors(repo, s):
    """Successors of a changeset"""
    cs = set()
    node = repo.changelog.node
    getrev = repo.changelog.index.get_rev
    markerbyobj = repo.obsstore.successors
    for r in s:
        for p in markerbyobj.get(node(r), ()):
            for sub in p[1]:
                sr = getrev(sub)
                if sr is not None:
                    cs.add(sr)
    cs -= repo.changelog.filteredrevs # nodemap has no filtering
    return cs

def _allsuccessors(repo, s, haltonflags=0):  # XXX we need a better naming
    """transitive successors of a subset

    haltonflags allows to provide flags which prevent the evaluation of a
    marker.  """
    node = repo.changelog.node
    toproceed = [node(r) for r in s]
    seen = set()
    allobjects = repo.obsstore.successors
    while toproceed:
        nc = toproceed.pop()
        for mark in allobjects.get(nc, ()):
            if mark[2] & haltonflags:
                continue
            for sub in mark[1]:
                if sub == nodemod.nullid:
                    continue # should not be here!
                if sub not in seen:
                    seen.add(sub)
                    toproceed.append(sub)
    getrev = repo.changelog.index.get_rev
    cs = set()
    for s in seen:
        sr = getrev(s)
        if sr is not None:
            cs.add(sr)
    cs -= repo.changelog.filteredrevs # nodemap has no filtering
    return cs

#####################################################################
### Extending revsets                                             ###
#####################################################################

# this section adds several useful revset predicates not yet in core.
# they are subject to changes

### XXX I'm not sure this revset is useful
@eh.revsetpredicate(b'suspended()')
def revsetsuspended(repo, subset, x):
    """Obsolete changesets with non-obsolete descendants.
    """
    revset.getargs(x, 0, 0, b'suspended takes no arguments')
    suspended = revset.baseset(getrevs(repo, b'suspended'))
    suspended.sort()
    return subset & suspended

@eh.revsetpredicate(b'predecessors(set)')
def revsetpredecessors(repo, subset, x):
    """Immediate predecessors of changesets in set.
    """
    s = revset.getset(repo, revset.fullreposet(repo), x)
    s = revset.baseset(_precursors(repo, s))
    s.sort()
    return subset & s

@eh.revsetpredicate(b'precursors(set)')   # legacy name for predecessors
def revsetprecursors(repo, subset, x):
    return revsetpredecessors(repo, subset, x)

@eh.revsetpredicate(b'allpredecessors(set)')
def revsetallpredecessors(repo, subset, x):
    """Transitive predecessors of changesets in set.
    """
    s = revset.getset(repo, revset.fullreposet(repo), x)
    s = revset.baseset(_allprecursors(repo, s))
    s.sort()
    return subset & s

@eh.revsetpredicate(b'allprecursors(set)')   # legacy name for allpredecessors
def revsetallprecursors(repo, subset, x):
    return revsetallpredecessors(repo, subset, x)

@eh.revsetpredicate(b'successors(set)')
def revsetsuccessors(repo, subset, x):
    """Immediate successors of changesets in set.
    """
    s = revset.getset(repo, revset.fullreposet(repo), x)
    s = revset.baseset(_successors(repo, s))
    s.sort()
    return subset & s

@eh.revsetpredicate(b'allsuccessors(set)')
def revsetallsuccessors(repo, subset, x):
    """Transitive successors of changesets in set.
    """
    s = revset.getset(repo, revset.fullreposet(repo), x)
    s = revset.baseset(_allsuccessors(repo, s))
    s.sort()
    return subset & s
