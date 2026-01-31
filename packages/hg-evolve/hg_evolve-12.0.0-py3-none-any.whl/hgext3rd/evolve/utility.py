# Various utility function for the evolve extension
#
# Copyright 2017 Pierre-Yves David <pierre-yves.david@ens-lyon.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import functools

from mercurial import (
    obsutil,
)

from mercurial.i18n import _

from mercurial.node import nullrev
from mercurial import (
    cmdutil
)

shorttemplate = b"[{label('evolve.rev', rev)}] {desc|firstline}\n"
stacktemplate = b"""[{label('evolve.rev', if(topicidx, "s{topicidx}", rev))}] {desc|firstline}\n"""

def obsexcmsg(ui, message, important=False):
    verbose = ui.configbool(b'experimental', b'verbose-obsolescence-exchange')
    if verbose:
        message = b'OBSEXC: ' + message
    if important or verbose:
        ui.status(message)

def filterparents(parents):
    """filter nullrev parents

    (and other crazyness)"""
    p1, p2 = parents
    if p1 == nullrev and p2 == nullrev:
        return ()
    elif p1 != nullrev and (p2 == nullrev or p1 == p2):
        return (p1,)
    elif p1 == nullrev and p2 != nullrev:
        return (p2,)
    else:
        return parents

def shouldwarmcache(repo, tr):
    configbool = repo.ui.configbool
    config = repo.ui.config
    desc = getattr(tr, 'desc', b'')

    autocase = False
    if tr is None and not getattr(repo, '_destroying', False):
        autocase = True
    elif desc.startswith(b'serve'):
        autocase = True
    elif desc.startswith(b'push') and not desc.startswith(b'push-response'):
        autocase = True

    autocache = config(b'experimental', b'obshashrange.warm-cache',
                       b'auto') == b'auto'
    if autocache:
        warm = autocase
    else:
        # note: we should not get to the default case
        warm = configbool(b'experimental', b'obshashrange.warm-cache')
    if not configbool(b'experimental', b'obshashrange'):
        return False
    if not warm:
        return False
    maxrevs = repo.ui.configint(b'experimental', b'obshashrange.max-revs')
    if maxrevs is not None and maxrevs < len(repo.unfiltered()):
        return False
    return True

class MultipleSuccessorsError(RuntimeError):
    """Exception raised by _singlesuccessor() when multiple successor sets exists

    Attributes:
        rev               the revision that has multiple successor sets
        successorssets    the list of successorssets to call to easily recover
        divergenceflag    indicate that changeset has divergent rewriting
        splitflag         indicate that changeset was split
    """

    def __init__(self, rev, successorssets):
        self.rev = rev
        self.successorssets = successorssets
        self.divergenceflag = len(successorssets) > 1
        self.splitflag = len(successorssets[0]) > 1

def builddependencies(repo, revs):
    """returns dependency graphs giving an order to solve instability of revs
    (see _orderrevs for more information on usage)"""

    # For each troubled revision we keep track of what instability if any should
    # be resolved in order to resolve it. Example:
    # dependencies = {3: [6], 6:[]}
    # Means that: 6 has no dependency, 3 depends on 6 to be solved
    dependencies = {}

    for r in revs:
        dependencies[r] = set()
        for p in repo[r].parents():
            for succ in _successorrevs(repo, p):
                if succ in revs:
                    dependencies[r].add(succ)

    # rdependencies is the inverted dict of dependencies
    rdependencies = {r: set() for r in revs}
    for r, deps in dependencies.items():
        for dep in deps:
            rdependencies[dep].add(r)

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
    if len(newer) > 1 or len(newer[0]) > 1:
        raise MultipleSuccessorsError(obs.rev(), newer)

    return repo[newer[0][0]].rev()

def select_split_successor(ui, repo, ctx):
    """Return most suitable split successor of <ctx> for evolution.

    If all successors are on one topological branch, we choose tipmost successor.
    Otherwise, we ask user to choose an evolve destination.

    Return ``None`` if no successor selected.
    """
    targets = obsutil.successorssets(repo, ctx.node())[0]
    assert targets
    targetrevs = [repo[r].rev() for r in targets]
    heads = repo.revs(b'heads(%ld::%ld)', targetrevs, targetrevs)
    if len(heads) > 1:
        cheader = (_(b"changeset %s split over multiple topological"
                     b" branches, choose an evolve destination:") % ctx)
        selectedrev = revselectionprompt(ui, repo, list(heads), cheader)
        if selectedrev is None:
            return
        succ = repo[selectedrev]
    else:
        succ = repo[heads.first()]
    return repo[succ].rev()

def _successorrevs(repo, ctx):
    try:
        return {_singlesuccessor(repo, ctx)}
    except MultipleSuccessorsError as exc:
        return {repo[node].rev()
                for successorsset in exc.successorssets
                for node in successorsset}

def revselectionprompt(ui, repo, revs, customheader=b""):
    """function to prompt user to choose a revision from all the revs and return
    that revision for further tasks

    revs is a list of rev number of revision from which one revision should be
    choosed by the user
    customheader is a text which the caller wants as the header of the prompt
    which will list revisions to select

    returns value is:
        rev number of revision choosed: if user choose a revision
        None: if user entered a wrong input, user quit the prompt,
              ui.interactive is not set
    """

    # ui.interactive is not set, fallback to default behavior and avoid showing
    # the prompt
    if not ui.interactive():
        return None

    promptmsg = customheader + b"\n"
    for idx, rev in enumerate(revs):
        curctx = repo[rev]
        revmsg = b"%d: [%s] %s\n" % (idx + 1, curctx,
                                     curctx.description().split(b"\n")[0])
        promptmsg += revmsg

    promptmsg += _(b"q: quit the prompt\n")
    promptmsg += _(b"enter the index of the revision you want to select:")
    idxselected = ui.prompt(promptmsg)

    intidx = None
    try:
        intidx = int(idxselected)
    except ValueError:
        if idxselected == b'q':
            return None
        ui.write_err(_(b"invalid value '%s' entered for index\n") % idxselected)
        return None

    if intidx > len(revs) or intidx <= 0:
        # we can make this error message better
        ui.write_err(_(b"invalid value '%d' entered for index\n") % intidx)
        return None

    return revs[intidx - 1]

def mergeusers(ui, base, divergent, other):
    """Return the merged user from two divergent changesets.

    Perform merge using 3-way merge. If unable to merge, concatenate
    the two users.
    """
    baseuser = base.user()
    divuser = divergent.user()
    othuser = other.user()

    if divuser == othuser:
        return divuser
    else:
        if baseuser == divuser:
            return othuser
        elif baseuser == othuser:
            return divuser
        else:
            # all three are different, lets concatenate the two authors
            # XXX: should we let the user know about concatenation of authors
            #      by printing some message (or maybe in verbose mode)
            users = set(divuser.split(b', '))
            users.update(othuser.split(b', '))
            user = b', '.join(sorted(users))
            return user

def _show(ui, command, default_spec, ctx):
    """internal function used by the *_ctx_displayer function"""
    text = cmdutil.format_changeset_summary(
        ui,
        ctx,
        command=command,
        default_spec=default_spec,
    )
    ui.write(b'%s\n' % text)

def short_ctx_displayer(ui, repo, command):
    """return a function writing a short summary line for one changectx"""
    return functools.partial(_show, ui, command, shorttemplate)

def stack_ctx_displayer(ui, repo, command):
    """return a function writing a stack summary line for one changectx"""
    return functools.partial(_show, ui, command, stacktemplate)
