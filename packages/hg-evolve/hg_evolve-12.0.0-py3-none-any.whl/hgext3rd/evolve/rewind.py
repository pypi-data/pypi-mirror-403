from __future__ import absolute_import

import collections
import hashlib

from mercurial import (
    cmdutil,
    error,
    merge,
    node as nodemod,
    obsolete,
    obsutil,
    registrar,
    scmutil,
    util,
)

from mercurial.utils import dateutil

from mercurial.i18n import _

from . import (
    compat,
    exthelper,
    obshistory,
    rewriteutil,
)

eh = exthelper.exthelper()

# flag in obsolescence markers to link to identical version
identicalflag = 4

@eh.command(
    b'rewind|undo',
    [(b'', b'to', [], _(b"rewind to these revisions"), _(b'REV')),
     (b'', b'as-divergence', None, _(b"preserve current latest successors")),
     (b'', b'exact', None, _(b"only rewind explicitly selected revisions")),
     (b'', b'from', [],
      _(b"rewind these revisions to their predecessors"), _(b'REV')),
     (b'k', b'keep', None,
      _(b"do not modify working directory during rewind")),
     (b'n', b'dry-run', False,
      _(b'do not perform actions, just print what would be done')),
     ],
    _(b'[--as-divergence] [--exact] [--keep] [--to REV]... [--from REV]...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
    helpbasic=True,
)
def rewind(ui, repo, **opts):
    """rewind a stack of changesets to a previous state

    This command can be used to restore stacks of changesets to an obsolete
    state, creating identical copies.

    There are two main ways to select the rewind target. Rewinding "from"
    changesets will restore the direct predecessors of these changesets (and
    obsolete the changeset you rewind from). Rewinding "to" will restore the
    changeset you have selected (and obsolete their latest successors).

    By default, we rewind from the working directory parents, restoring its
    predecessor.

    When we rewind to an obsolete version, we also rewind to all its obsolete
    ancestors. To only rewind to the explicitly selected changesets use the
    `--exact` flag. Using the `--exact` flag can restore some changesets as
    orphan.

    The latest successors of the obsolete changesets will be superseded by
    these new copies. This behavior can be disabled using `--as-divergence`,
    the current latest successors won't be affected and content-divergence will
    appear between them and the restored version of the obsolete changesets.

    Current rough edges:

      * fold: rewinding to only some of the initially folded changesets will be
              problematic. The fold result is marked obsolete and the part not
              rewinded to are "lost".  Please use --as-divergence when you
              need to perform such operation.

      * :hg:`rewind` might affect changesets outside the current stack. Without
              --exact, we also restore ancestors of the rewind target,
              obsoleting their latest successors (unless --as-divergent is
              provided). In some case, these latest successors will be on
              branches unrelated to the changeset you rewind from.
              (We plan to automatically detect this case in the future)

    """
    unfi = repo.unfiltered()

    successorsmap = collections.defaultdict(set)
    rewindmap = {}
    sscache = {}
    with repo.wlock(), repo.lock():
        # stay on the safe side: prevent local case in case we need to upgrade
        compat.bail_if_changed(repo)

        targets = _select_rewind_targets(repo, opts)

        extratargets = _walk_obsmarkers(ui, unfi, targets)
        targets.extend(extratargets)

        for rev in targets:
            ctx = unfi[rev]
            ssets = obsutil.successorssets(repo, ctx.node(), cache=sscache)
            if not opts['as_divergence'] and len(ssets) > 1:
                msg = _(b'rewind confused by divergence on %s') % ctx
                hint = _(b'solve divergence first or use "--as-divergence"')
                raise error.Abort(msg, hint=hint)
            for sset in ssets:
                for succ in sset:
                    successorsmap[succ].add(ctx.node())

        if opts['as_divergence']:
            successorsmap = {}

        if opts['dry_run']:
            ui.status(dryrun(unfi, targets, successorsmap, opts))
            return

        # Check that we can rewind these changesets
        with repo.transaction(b'rewind'):
            oldctx = repo[b'.']

            for rev in sorted(targets):
                ctx = unfi[rev]
                rewindmap[ctx.node()] = _revive_revision(unfi, rev, rewindmap)

            relationships = []
            cl = unfi.changelog
            wctxp = repo[None].p1()
            update_target = None
            for (source, dest) in sorted(successorsmap.items()):
                newdest = [rewindmap[d] for d in sorted(dest, key=cl.rev)]
                rel = (unfi[source], tuple(unfi[d] for d in newdest))
                relationships.append(rel)
                if wctxp.node() == source:
                    update_target = newdest[-1]
            destmap = util.sortdict()
            for src, dest in relationships:
                destmap.setdefault(dest, []).append(src)
            relationships = [
                (tuple(src), dest)
                for dest, src in destmap.items()
            ]
            obsolete.createmarkers(unfi, relationships, operation=b'rewind')
            if update_target is not None:
                if opts.get('keep'):
                    merge.clean_update(oldctx)

                    # This is largely the same as the implementation in
                    # strip.stripcmd() and cmdrewrite.cmdprune().

                    # only reset the dirstate for files that would actually
                    # change between the working context and the revived cset
                    newctx = repo[update_target]
                    changedfiles = []
                    for ctx in [oldctx, newctx]:
                        # blindly reset the files, regardless of what actually
                        # changed
                        changedfiles.extend(ctx.files())

                    # reset files that only changed in the dirstate too
                    dirstate = repo.dirstate
                    dirchanges = (
                        f
                        for f in dirstate
                        if not dirstate.get_entry(f).maybe_clean
                    )
                    changedfiles.extend(dirchanges)
                    with repo.dirstate.changing_parents(repo):
                        repo.dirstate.rebuild(newctx.node(), newctx.manifest(),
                                              changedfiles)

                    # TODO: implement restoration of copies/renames
                    # Ideally this step should be handled by dirstate.rebuild
                    # or scmutil.movedirstate, but right now there's no copy
                    # tracing across obsolescence relation (oldctx <-> newctx).
                    revertopts = {'no_backup': True, 'all': True,
                                  'rev': oldctx.node()}
                    with ui.configoverride({(b'ui', b'quiet'): True}):
                        cmdutil.revert(repo.ui, repo, oldctx, **revertopts)
                else:
                    merge.update(repo[update_target])

    ui.status(_(b'rewound to %d changesets\n') % len(targets))
    if successorsmap:
        ui.status(_(b'(%d changesets obsoleted)\n') % len(successorsmap))
    if update_target is not None and not opts.get('keep'):
        ui.status(_(b'working directory is now at %s\n') % repo[b'.'])

def _check_multiple_predecessors(targetnode, successor, targetset):
    """ check if a successor of one rewind target is already another target

        An example obsolescence marker tree:
        A0  A1  A2
        x - x - o

        When user tries to rewind A2 to both its predecessors with e.g.
        `hg rewind --to A0+A1`, this function will at one point be called with
        (A0, A1, [A0, A1]) as arguments. In that case it will raise an Abort
        and prevent rewind from succeeding.
    """
    if successor in targetset:
        msg = _(b'not rewinding, %s is a successor of %s')
        msg %= (nodemod.short(successor), nodemod.short(targetnode))
        hint = _(b'pick only one of these changesets, possibly with --exact')
        raise error.Abort(msg, hint=hint)

def _walk_successors(ui, unfi, targetset):
    """follow successors of targets and find the latest successors

    While doing that, check and abort if there are multiple unrelated
    predecessors in targetset.

    We also keep track of "source": when we reach a successor by following the
    obsmarker-graph starting from a certain target, we add `successor: target`
    pair to `source`. But we don't care about having more than one `target`
    (i.e. predecessor) for each `successor`, because `source` is used later on
    for finding "new" successors that we didn't find in this function.
    """
    source = {}
    latest = set()
    for targetnode in targetset:
        # following successors for each target node separately
        remaining = set([targetnode])
        while remaining:
            current = remaining.pop()
            markers = unfi.obsstore.successors.get(current, ())
            for marker in markers:
                for successor in marker[1]:
                    if successor in source:
                        # We have already reached this successor while
                        # processing this or any other targetnode. This means
                        # not every target node will get their latest successor
                        # found if e.g. there's a fold (and that is fine).
                        # (Also basic cycle protection.)
                        continue
                    # TODO: this could be moved to a post-processing stage
                    _check_multiple_predecessors(targetnode, successor, targetset)
                    source[successor] = current
                    remaining.add(successor)
            if not markers:
                latest.add(current)

    return latest, source

def _check_unknown_predecessors(unfi, nodes, source):
    """ check if any nodes are absent from both source and unfiltered repo

    If node is not in source, we might want it as an extra rewind target. But
    if it's also absent from local (unfiltered) repo, we need to warn user and
    abort.
    """
    missing = {
        node for node in nodes
        if node not in source and node not in unfi
    }
    if missing:
        msg = _(b'not rewinding, some predecessors are unknown locally: %s')
        msg %= b' '.join(nodemod.short(m) for m in missing)
        hint = _(b'try selecting all changesets to rewind to manually, '
                 b'possibly with --exact')
        raise error.Abort(msg, hint=hint)

def _walk_predecessors(ui, unfi, targetset, latest, source):
    """follow predecessors of targets, validate and suggest extra targets

    While doing that, check and abort if any fold components are unknown.

    Skip predecessors that are only reachable by following obsmarkers with
    "identical" flag, because these markers are for internal use and actual
    users don't want to revive such predecessors.

    Note: picking the first reached (IOW, the latest) predecessor is done on
    purpose. We don't want rewind to assume too much, but also, and more
    importantly, we don't want rewind to deal with any potential merge
    conflicts. And when rewind revives one of the latest predecessors and it is
    based on an obsolete changeset that was not revived, the revived changeset
    will simply be an orphan, and it will be up to the user to decide how they
    want to solve the trouble _after_ rewind is finished. This way of handling
    rewinds that may produce merge conflicts means less chance to lose work.
    """
    remaining = set(latest)
    seen = set(remaining)
    extratargets = []
    while remaining:
        successor = remaining.pop()
        markers = unfi.obsstore.predecessors.get(successor, ())
        data = (((marker[0],), (marker,)) for marker in markers)
        for (nodes, markers) in sorted(obshistory.groupbyfoldid(data)):
            # TODO: this could be moved to a post-processing stage
            _check_unknown_predecessors(unfi, nodes, source)
            for node in nodes:
                if node in seen:
                    # basic cycle protection
                    continue
                if node in source:
                    # we've been here while following successors
                    seen.add(node)
                    remaining.add(node)
                elif node not in targetset:
                    # skipping meta obsmarkers from previous rewind operations
                    identical = [m[2] & identicalflag for m in markers]
                    if not all(identical):
                        extratargets.append(unfi[node].rev())

    return extratargets

def _walk_obsmarkers(ui, unfi, targets):
    """walking of both successors and predecessors of changesets to rewind to

    This function:
        - traverses successors of every target, then
        - traverses predecessors of every latest successor of each target
        - returns reachable predecessors with content changes
    """
    node = unfi.changelog.node
    targetset = set(node(target) for target in targets)
    latest, source = _walk_successors(ui, unfi, targetset)
    extratargets = _walk_predecessors(ui, unfi, targetset, latest, source)

    return extratargets

def _select_rewind_targets(repo, opts):
    """select the revisions we should rewind to
    """
    unfi = repo.unfiltered()
    targets = set()
    revsto = opts.get('to')
    revsfrom = opts.get('from')
    if not (revsto or revsfrom):
        revsfrom.append(b'.')
    if revsto:
        targets.update(scmutil.revrange(repo, revsto))
    if revsfrom:
        succs = scmutil.revrange(repo, revsfrom)
        targets.update(unfi.revs(b'predecessors(%ld)', succs))

    if not targets:
        raise error.Abort(b'no revision to rewind to')

    if not opts['exact']:
        targets = unfi.revs(b'obsolete() and ::%ld', targets)

    return sorted(targets)

def _revive_revision(unfi, rev, rewindmap):
    """rewind a single revision rev.
    """
    ctx = unfi[rev]
    extra = ctx.extra().copy()
    # rewind hash should be unique over multiple rewind.
    user = unfi.ui.config(b'devel', b'user.obsmarker')
    if not user:
        user = unfi.ui.username()
    date = unfi.ui.configdate(b'devel', b'default-date')
    if date is None:
        date = dateutil.makedate()
    noise = b"%s\0%s\0%d\0%d" % (ctx.node(), user, date[0], date[1])
    extra[b'__rewind-hash__'] = hashlib.sha256(noise).hexdigest().encode('ascii')

    p1 = ctx.p1().node()
    p1 = rewindmap.get(p1, p1)
    p2 = ctx.p2().node()
    p2 = rewindmap.get(p2, p2)

    commitopts = {b'extra': extra, b'date': ctx.date()}

    new, unusedvariable = rewriteutil.rewrite(unfi, ctx, ctx,
                                              [p1, p2],
                                              commitopts=commitopts)

    obsolete.createmarkers(unfi, [(ctx, (unfi[new],))],
                           flag=identicalflag, operation=b'rewind')

    return new

def formatstatus(sources, destinations, asdiv=False):
    """format a status line for one group of changesets for rewind

    sources is a tuple of current successors, or None in case of rewinding to
    an earlier version of a pruned commit or when --as-divergence is used.

    destinations is a tuple of predecessors to rewind to.
    """
    if sources:
        return b'rewinding %s to %d changesets: %s\n' % (
            b' '.join(nodemod.short(src) for src in sources),
            len(destinations),
            b' '.join(nodemod.short(dest) for dest in destinations)
        )
    elif asdiv:
        msg = b'recreating %d changesets: %s\n'
    else:
        msg = b'rewinding a pruned commit to %d changesets: %s\n'
    return msg % (
        len(destinations),
        b' '.join(nodemod.short(dest) for dest in destinations)
    )

def dryrun(unfi, targets, successorsmap, opts):
    """explain what would rewind do, given targets, successorsmap and opts

    Returns a bytestring with one line per predecessors<->successors relation.
    """
    cl = unfi.changelog
    todo = b''
    rsm = collections.defaultdict(set) # reverse successors map
    for src, destinations in successorsmap.items():
        for dest in destinations:
            rsm[dest].add(src)
    if rsm and successorsmap:
        if len(rsm) < len(successorsmap):
            for dest in sorted(rsm, key=cl.rev):
                sources = sorted(rsm[dest], key=cl.rev)
                todo += formatstatus(sources, (dest,))
        else:
            for src in sorted(successorsmap, key=cl.rev):
                destinations = sorted(successorsmap[src], key=cl.rev)
                todo += formatstatus((src,), destinations)
    else:
        destinations = [unfi[rev].node() for rev in sorted(targets)]
        todo = formatstatus(None, destinations, opts['as_divergence'])
    return todo
