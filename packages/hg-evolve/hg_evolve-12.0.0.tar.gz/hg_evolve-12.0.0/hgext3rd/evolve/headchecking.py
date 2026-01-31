from __future__ import absolute_import

import functools

from mercurial import (
    discovery,
    error,
    extensions,
    phases,
    scmutil,
    util,
)

from mercurial.i18n import _


from . import (
    exthelper,
)

eh = exthelper.exthelper()


@eh.uisetup
def uisetup(ui):
    extensions.wrapfunction(discovery, '_postprocessobsolete', _postprocessobsolete)

def branchinfo(pushop, repo, node):
    return repo[node].branch()

# taken from 7d5455b988ec + branchinfo abstraction.
def _postprocessobsolete(orig, pushop, futurecommon, candidate_newhs):
    """post process the list of new heads with obsolescence information

    Exists as a sub-function to contain the complexity and allow extensions to
    experiment with smarter logic.

    Returns (newheads, discarded_heads) tuple
    """
    pushingmarkerfor = discovery.pushingmarkerfor
    # known issue
    #
    # * We "silently" skip processing on all changeset unknown locally
    #
    # * if <nh> is public on the remote, it won't be affected by obsolete
    #     marker and a new is created

    # define various utilities and containers
    repo = pushop.repo
    unfi = repo.unfiltered()
    torev = unfi.changelog.index.get_rev
    public = phases.public
    getphase = unfi._phasecache.phase
    ispublic = lambda r: getphase(unfi, r) == public
    ispushed = lambda n: torev(n) in futurecommon
    hasoutmarker = functools.partial(pushingmarkerfor, unfi.obsstore, ispushed)
    successorsmarkers = unfi.obsstore.successors
    newhs = set()  # final set of new heads
    discarded = set()  # new head of fully replaced branch

    localcandidate = set()  # candidate heads known locally
    unknownheads = set()  # candidate heads unknown locally
    for h in candidate_newhs:
        if h in unfi:
            localcandidate.add(h)
        else:
            if successorsmarkers.get(h) is not None:
                msg = (
                    b'checkheads: remote head unknown locally has'
                    b' local marker: %s\n'
                )
                repo.ui.debug(msg % hex(h))
            unknownheads.add(h)

    # fast path the simple case
    if len(localcandidate) == 1:
        return unknownheads | set(candidate_newhs), set()

    # actually process branch replacement
    while localcandidate:
        nh = localcandidate.pop()
        current_branch = branchinfo(pushop, unfi, nh)
        # run this check early to skip the evaluation of the whole branch
        if ispublic(torev(nh)) or not unfi[nh].obsolete():
            newhs.add(nh)
            continue

        # Get all revs/nodes on the branch exclusive to this head
        # (already filtered heads are "ignored"))
        branchrevs = unfi.revs(
            b'only(%n, (%ln+%ln))', nh, localcandidate, newhs
        )

        branchnodes = []
        for r in branchrevs:
            ctx = unfi[r]
            if ctx.branch() == current_branch:
                branchnodes.append(ctx.node())

        # The branch won't be hidden on the remote if
        # * any part of it is public,
        # * any part of it is considered part of the result by previous logic,
        # * if we have no markers to push to obsolete it.
        if (
            any(ispublic(torev(n)) for n in branchnodes)
            or (any(torev(n) in futurecommon and not unfi[n].obsolete() for n in branchnodes))
            # XXX `hasoutmarker` does not guarantee the changeset to be
            # obsolete, nor obsoleted by the push.
            or any(not hasoutmarker(n) for n in branchnodes)
        ):
            newhs.add(nh)
        else:
            # note: there is a corner case if there is a merge in the branch.
            # we might end up with -more- heads.  However, these heads are not
            # "added" by the push, but more by the "removal" on the remote so I
            # think is a okay to ignore them,
            discarded.add(nh)
    newhs |= unknownheads
    return newhs, discarded

def _get_branch_name(ctx):
    # make it easy for extension with the branch logic there
    branch = ctx.branch()
    if util.safehasattr(ctx, 'topic'):
        branch = ctx.fqbn()
    return branch

def _filter_obsolete_heads(repo, heads):
    """filter heads to return non-obsolete ones

    Given a list of heads (on the same named branch) return a new list of heads
    where the obsolete part have been skimmed out.
    """
    new_heads = []
    old_heads = heads[:]
    while old_heads:
        rh = old_heads.pop()
        ctx = repo[rh]

        # run this check early to skip the evaluation of the whole branch
        if not ctx.obsolete():
            new_heads.append(rh)
            continue

        current_name = _get_branch_name(ctx)

        # Get all revs/nodes on the branch exclusive to this head
        # (already filtered heads are "ignored"))
        sections_revs = repo.revs(
            b'only(%d, (%ld+%ld))', rh, old_heads, new_heads,
        )
        keep_revs = []
        for r in sections_revs:
            ctx = repo[r]
            if ctx.obsolete():
                continue
            if _get_branch_name(ctx) != current_name:
                continue
            keep_revs.append(r)
        for h in repo.revs(b'heads(%ld and (::%ld))', sections_revs, keep_revs):
            new_heads.append(h)
    new_heads.sort()
    return new_heads

def enforcesinglehead(orig, repo, tr, desc, accountclosed=False, filtername=b'visible'):
    """check that no named branch has multiple heads

    COMPAT: this is the same as the upstream version as of c701f616d852, except
    for the _filter_obsolete_heads call.
    """
    nodesummaries = scmutil.nodesummaries
    if desc in (b'strip', b'repair'):
        # skip the logic during strip
        return
    visible = repo.filtered(filtername)
    # possible improvement: we could restrict the check to affected branch
    bm = visible.branchmap()
    cl = repo.changelog
    to_rev = cl.rev
    to_node = cl.node
    for name in bm:
        all_heads = bm.branchheads(name, closed=accountclosed)
        all_heads = [to_rev(n) for n in all_heads]
        heads = _filter_obsolete_heads(repo, all_heads)
        heads = [to_node(r) for r in heads]
        if len(heads) > 1:
            msg = _(b'rejecting multiple heads on branch "%s"')
            msg %= name
            hint = _(b'%d heads: %s')
            hint %= (len(heads), nodesummaries(repo, heads))
            raise error.Abort(msg, hint=hint)
