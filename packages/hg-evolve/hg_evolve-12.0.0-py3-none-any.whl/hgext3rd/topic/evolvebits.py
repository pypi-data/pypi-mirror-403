import collections

from mercurial import (
    obsutil,
)

# Copied from evolve 081605c2e9b6

def builddependencies(repo, revs):
    """returns dependency graphs giving an order to solve instability of revs
    (see _orderrevs for more information on usage)"""

    # For each troubled revision we keep track of what instability if any should
    # be resolved in order to resolve it. Example:
    # dependencies = {3: [6], 6:[]}
    # Means that: 6 has no dependency, 3 depends on 6 to be solved
    dependencies = {}
    # rdependencies is the inverted dict of dependencies
    rdependencies = collections.defaultdict(set)

    for r in revs:
        dependencies[r] = set()
        for p in repo[r].parents():
            try:
                succ = _singlesuccessor(repo, p)
            except MultipleSuccessorsError as exc:
                dependencies[r] = exc.successorssets
                continue
            if succ in revs:
                dependencies[r].add(succ)
                rdependencies[succ].add(r)
    return dependencies, rdependencies

def _singlesuccessor(repo, p):
    """returns p (as rev) if not obsolete or its unique latest successors

    fail if there are no such successor"""

    if not p.obsolete():
        return p.rev()
    obs = repo[p]
    ui = repo.ui
    cache = {}
    newer = obsutil.successorssets(repo, obs.node(), cache=cache)
    # search of a parent which is not killed
    while not newer:
        ui.debug(b"stabilize target %s is plain dead,"
                 b" trying to stabilize on its parent\n" %
                 obs)
        obs = obs.p1()
        newer = obsutil.successorssets(repo, obs.node(), cache=cache)
    if 1 < len(newer):
        # divergence case
        # we should pick as arbitrary one
        raise MultipleSuccessorsError(newer)
    elif 1 < len(newer[0]):
        splitheads = list(repo.revs(b'heads(%ln::%ln)', newer[0], newer[0]))
        if 1 < len(splitheads):
            # split case, See if we can make sense of it.
            raise MultipleSuccessorsError(newer)
        return splitheads[0]

    return repo[newer[0][0]].rev()

class MultipleSuccessorsError(RuntimeError):
    """Exception raised by _singlesuccessor when multiple successor sets exists

    The object contains the list of successorssets in its 'successorssets'
    attribute to call to easily recover.
    """

    def __init__(self, successorssets):
        self.successorssets = successorssets
