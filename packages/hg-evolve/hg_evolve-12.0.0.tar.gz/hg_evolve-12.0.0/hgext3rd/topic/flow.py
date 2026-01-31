from __future__ import absolute_import

from mercurial import (
    error,
    exchange,
    node,
    phases,
)

from mercurial.i18n import _

from . import (
    compat,
)

def enforcesinglehead(repo, tr):
    bm = repo.filtered(b'visible').branchmap()
    for name, heads in compat.branchmapitems(bm):
        if len(heads) > 1:
            hexs = [node.short(n) for n in heads]
            raise error.Abort(_(b'%d heads on "%s"') % (len(heads), name),
                              hint=(b', '.join(hexs)))

def publishbarebranch(repo, tr):
    """Publish changeset without topic"""
    if b'node' not in tr.hookargs: # no new node
        return
    startnode = node.bin(tr.hookargs[b'node'])
    topublish = repo.revs(b'not public() and (%n:) - hidden() - topic()', startnode)
    if topublish:
        cl = repo.changelog
        nodes = [cl.node(r) for r in topublish]
        repo._phasecache.advanceboundary(repo, tr, phases.public, nodes)

def rejectuntopicedchangeset(repo, tr):
    """Reject the push if there are changeset without topic"""
    if b'node' not in tr.hookargs: # no new revs
        return

    startnode = node.bin(tr.hookargs[b'node'])

    mode = repo.ui.config(b'experimental', b'topic-mode.server', b'ignore')

    untopiced = repo.revs(b'not public() and (%n:) - hidden() - topic()', startnode)
    if untopiced:
        num = len(untopiced)
        cl = repo.changelog
        fnode = node.short(cl.node(untopiced.first()))
        if num == 1:
            msg = _(b"%s") % fnode
        else:
            msg = _(b"%s and %d more") % (fnode, num - 1)
        if mode == b'warning':
            fullmsg = _(b"pushed draft changeset without topic: %s\n")
            repo.ui.warn(fullmsg % msg)
        elif mode == b'enforce':
            fullmsg = _(b"rejecting draft changesets: %s")
            raise error.Abort(fullmsg % msg)
        else:
            repo.ui.warn(_(b"unknown 'topic-mode.server': %s\n" % mode))

def reject_publish(repo, tr):
    """prevent a transaction to be publish anything"""
    revranges = [
        r for r, (o, n) in tr.changes[b'phases']
        if n == phases.public
    ]
    published = {r for revrange in revranges for r in revrange}
    if published:
        r = min(published)
        msg = b"rejecting publishing of changeset %s" % repo[r]
        if len(published) > 1:
            msg += b' and %d others' % (len(published) - 1)
        raise error.Abort(msg)

def reject_csets_with_tns(repo, tr):
    """Reject the push if there are changesets with any topic namespace"""
    if b'node' not in tr.hookargs: # no new revs
        return

    reject = repo.ui.config(b'experimental', b'tns-reject-push')
    if not reject:
        return

    startnode = node.bin(tr.hookargs[b'node'])
    repo = repo.unfiltered()
    with_tns = repo.revs(b'not public() and extra("topic-namespace") and (%n:) - hidden()', startnode)
    if with_tns:
        num = len(with_tns)
        cl = repo.changelog
        fnode = node.short(cl.node(with_tns.first()))
        if num == 1:
            msg = _(b"%s") % fnode
        else:
            msg = _(b"%s and %d more") % (fnode, num - 1)
        fullmsg = _(b"rejecting draft changesets with topic namespace: %s")
        raise error.Abort(fullmsg % msg)

def replacecheckpublish(orig, pushop):
    listkeys = exchange.listkeys
    repo = pushop.repo
    ui = repo.ui
    behavior = ui.config(b'experimental', b'auto-publish')
    if pushop.publish or behavior not in (b'warn', b'confirm', b'abort'):
        return

    # possible modes are:
    #
    # none -> nothing is published on push
    # all  -> everything is published on push
    # auto -> only changeset without topic are published on push
    #
    # Unknown mode is assumed "all" for safety.
    #
    # TODO: do a wider brain storming about mode names.

    mode = b'all'
    remotephases = listkeys(pushop.remote, b'phases')
    if not remotephases.get(b'publishing', False):
        mode = b'none'
        for c in pushop.remote.capabilities():
            if c.startswith(b'ext-topics-publish'):
                mode = c.split(b'=', 1)[1]
                break
    if mode == b'none':
        return

    if pushop.revs is None:
        published = repo.filtered(b'served').revs(b'not public()')
    else:
        published = repo.revs(b'::%ln - public()', pushop.revs)
        # we want to use pushop.revs in the revset even if they themselves are
        # secret, but we don't want to have anything that the server won't see
        # in the result of this expression
        published &= repo.filtered(b'served')

    if mode == b'auto':
        published = repo.revs(b'%ld::(%ld - topic())', published, published)
    if published:
        if behavior == b'warn':
            ui.warn(
                _(b'%i changesets about to be published\n') % len(published)
            )
        elif behavior == b'confirm':
            if ui.promptchoice(
                _(b'push and publish %i changesets (yn)?$$ &Yes $$ &No')
                % len(published)
            ):
                raise error.CanceledError(_(b'user quit'))
        elif behavior == b'abort':
            msg = _(b'push would publish %i changesets') % len(published)
            hint = _(
                b"use --publish or adjust 'experimental.auto-publish'"
                b" config"
            )
            raise error.Abort(msg, hint=hint)
