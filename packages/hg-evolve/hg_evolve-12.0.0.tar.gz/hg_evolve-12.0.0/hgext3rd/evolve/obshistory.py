# Code dedicated to display and exploration of the obsolescence history
#
# This module content aims at being upstreamed enventually.
#
# Copyright 2017 Octobus SAS <contact@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import re

from mercurial import (
    commands,
    context,
    error,
    graphmod,
    logcmdutil,
    mdiff,
    merge,
    node as nodemod,
    obsutil,
    patch,
    pycompat,
    registrar,
    scmutil,
    util,
)

from mercurial.utils import dateutil

from mercurial.i18n import _

from . import (
    exthelper,
)

eh = exthelper.exthelper()

# Config
efd = {b'default': True} # pass a default value unless the config is registered

@eh.extsetup
def enableeffectflags(ui):
    item = (getattr(ui, '_knownconfig', {})
            .get(b'experimental', {})
            .get(b'evolution.effect-flags'))
    if item is not None:
        item.default = True
        efd.clear()

@eh.extsetup
def addtouchnoise(ui):
    obsutil.METABLACKLIST.append(re.compile(br'^__touch-noise__$'))
    obsutil.METABLACKLIST.append(re.compile(br'^divergence_source_local$'))
    obsutil.METABLACKLIST.append(re.compile(br'^divergence_source_other$'))

@eh.command(
    b'obslog|olog',
    [(b'G', b'graph', True, _(b"show the revision DAG")),
     (b'r', b'rev', [], _(b'show the specified revision or revset'), _(b'REV')),
     (b'a', b'all', False, _(b'show all related changesets, not only precursors')),
     (b'p', b'patch', False, _(b'show the patch between two obs versions')),
     (b'f', b'filternonlocal', False, _(b'filter out non local commits')),
     (b'o', b'origin', True, _(b'show origin of changesets instead of fate')),
     ] + commands.formatteropts,
    _(b'hg obslog [OPTION]... [[-r] REV]...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_NAVIGATION)
def cmdobshistory(ui, repo, *revs, **opts):
    """show the obsolescence history of the specified revisions

    If no revision range is specified, we display the log for the current
    working copy parent.

    By default this command prints the selected revisions and all its
    precursors. For precursors pointing on existing revisions in the repository,
    it will display revisions node id, revision number and the first line of the
    description. For precursors pointing on non existing revisions in the
    repository (that can happen when exchanging obsolescence-markers), display
    only the node id.

    In both case, for each node, its obsolescence marker will be displayed with
    the obsolescence operation (rewritten or pruned) in addition of the user and
    date of the operation.

    The output is a graph by default but can deactivated with the option
    '--no-graph'.

    'o' is a changeset, '@' is a working directory parent, 'x' is obsolete,
    and '+' represents a fork where the changeset from the lines below is a
    parent of the 'o' merge on the same line.

    Paths in the DAG are represented with '|', '/' and so forth.

    Returns 0 on success.
    """
    ui.pager(b'obslog')
    revs = list(revs) + opts['rev']
    if not revs:
        revs = [b'.']
    revs = scmutil.revrange(repo, revs)

    # Use the default template unless the user provided one.
    if not opts['template']:
        opts['template'] = DEFAULT_TEMPLATE

    if opts['graph']:
        return displaygraph(ui, repo, revs, opts)

    revs.reverse()
    displayrevs(ui, repo, revs, opts)

TEMPLATE_MISSING_NODE = b"""{label("evolve.node evolve.missing_change_ctx", node|short)}"""
TEMPLATE_PRESENT_NODE = b"""{label("evolve.node", node|short)} {label("evolve.rev", "({rev})")} {label("evolve.short_description", desc|firstline)}"""
TEMPLATE_FIRST_LINE = b"""{if(rev, "%(presentnode)s", "%(missingnode)s")}""" % {
    b"presentnode": TEMPLATE_PRESENT_NODE,
    b"missingnode": TEMPLATE_MISSING_NODE
}
TEMPLATE_PREDNODES = b"""{label("evolve.node", join(prednodes % "{prednode|short}", ", "))}"""
TEMPLATE_SUCCNODES = b"""{label("evolve.node", join(succnodes % "{succnode|short}", ", "))}"""
TEMPLATE_NODES = b"""{if(prednodes, "from %(prednodes)s")}{if(succnodes, "as %(succnodes)s")}""" % {
    b"prednodes": TEMPLATE_PREDNODES,
    b"succnodes": TEMPLATE_SUCCNODES
}
TEMPLATE_REWRITE = b"""{label("evolve.verb", verb)}{if(effects, "({join(effects, ", ")})")}"""
TEMPLATE_OPERATIONS = b"""{if(operations, "using {label("evolve.operation", join(operations, ", "))}")}"""
TEMPLATE_USERS = b"""by {label("evolve.user", join(users, ", "))}"""
TEMPLATE_ONE_DATE = b"""({date(max(dates), "%a %b %d %H:%M:%S %Y %1%2")})"""
TEMPLATE_MANY_DATES = b"""(between {date(min(dates), "%a %b %d %H:%M:%S %Y %1%2")} and {date(max(dates), "%a %b %d %H:%M:%S %Y %1%2")})"""
TEMPLATE_DATES = b"""{label("evolve.date", ifeq(min(dates), max(dates), "%(onedate)s", "%(manydates)s"))}""" % {
    b"onedate": TEMPLATE_ONE_DATE,
    b"manydates": TEMPLATE_MANY_DATES
}
TEMPLATE_NOTES = b"""{if(notes, notes % "\n    note: {label("evolve.note", note)}")}"""
TEMPLATE_PATCH = b"""{if(patch, "{patch}")}{if(nopatchreason, "\n(No patch available, {nopatchreason})")}"""
DEFAULT_TEMPLATE = (b"""%(firstline)s
{markers %% "  {separate(" ", "%(rewrite)s", "%(nodes)s", "%(operations)s", "%(users)s", "%(dates)s")}%(notes)s{indent(descdiff, "    ")}{indent("%(patch)s", "    ")}\n"}
""") % {
    b"firstline": TEMPLATE_FIRST_LINE,
    b"rewrite": TEMPLATE_REWRITE,
    b"nodes": TEMPLATE_NODES,
    b"operations": TEMPLATE_OPERATIONS,
    b"users": TEMPLATE_USERS,
    b"dates": TEMPLATE_DATES,
    b"notes": TEMPLATE_NOTES,
    b"patch": TEMPLATE_PATCH,
}

def groupbyfoldid(predsets):
    """ Group nodes and related obsmarkers by fold-id metadata.
    """
    groups = {}
    for (nodes, markers) in predsets:
        grouped = False
        for marker in markers:
            metadata = dict(marker[3])
            foldid = metadata.get(b'fold-id')
            if foldid is not None:
                groups.setdefault(foldid, []).append((nodes, markers))
                grouped = True

        if not grouped:
            yield (nodes, markers)

    for foldid in sorted(groups):
        groupnodes = set()
        groupmarkers = set()
        for (nodes, markers) in groups[foldid]:
            groupnodes.update(nodes)
            groupmarkers.update(markers)
        yield (tuple(sorted(groupnodes)), tuple(sorted(groupmarkers)))

def predecessorsandmarkers(repo, node):
    """ Compute data needed for obsorigin.

    Return a generator of (nodes, markers) tuples, where nodes is a tuple of
    predecessor nodes and markers is a tuple of obsolescence markers.

    Using tuples for everything means no problems with sorted().
    """
    predecessors = repo.obsstore.predecessors
    stack = [(node, ())]
    seen = {node}

    while stack:
        node, path = stack.pop()

        for marker in sorted(predecessors.get(node, ())):
            prednode = marker[0]

            # Basic cycle protection
            if prednode in seen:
                continue
            seen.add(prednode)

            if prednode in repo:
                yield ((prednode,), path + (marker,))
            else:
                stack.append((prednode, path + (marker,)))

def _originmarkers(repo, ctx, filternonlocal):
    predecessors = repo.obsstore.predecessors
    successors = repo.obsstore.successors
    if filternonlocal:
        r = predecessorsandmarkers(repo, ctx.node())
        for (nodes, markers) in sorted(groupbyfoldid(r)):
            yield (nodes, markers)
    else:
        markers = predecessors.get(ctx.node(), ())
        data = (((marker[0],), (marker,)) for marker in markers)
        for (nodes, markers) in sorted(groupbyfoldid(data)):
            yield (nodes, markers)

    # finding prune markers
    for marker in successors.get(ctx.node(), ()):
        if not marker[1]:
            yield ((), (marker,))

def _fatemarkers(repo, ctx, filternonlocal):
    successors = repo.obsstore.successors
    if filternonlocal:
        r = obsutil.successorsandmarkers(repo, ctx)
        if r is None:
            r = []
        # replacing dicts and sets, they can't be compared
        data = [
            (succset[b'successors'], tuple(sorted(succset[b'markers'])))
            for succset in r
        ]
        for (nodes, markers) in sorted(data):
            if markers:
                yield (nodes, markers)
    else:
        markers = successors.get(ctx.node(), ())
        for marker in sorted(markers):
            yield (marker[1], [marker])

def _nodesandmarkers(repo, ctx, filternonlocal, origin):
    """ Return data for obslog and obsolescence-related template keywords.

    If `filternonlocal` is True, skip filtered nodes (but still gather
    obsolescence markers), otherwise the result will contain nodes unknown
    locally if they are found in the obsolescence markers.

    If `origin` is True, look at predecessors of ctx. Otherwise return
    successors and appropriate obsmarkers.
    """
    if origin:
        for (nodes, markers) in _originmarkers(repo, ctx, filternonlocal):
            yield (nodes, markers)
    else:
        for (nodes, markers) in _fatemarkers(repo, ctx, filternonlocal):
            yield (nodes, markers)

class obsmarker_printer(logcmdutil.changesetprinter):
    """show (available) information about a node

    We display the node, description (if available) and various information
    about obsolescence markers affecting it"""

    def __init__(self, ui, repo, *args, **kwargs):

        if kwargs.pop('obspatch', False):
            if logcmdutil.changesetdiffer is None:
                kwargs['matchfn'] = scmutil.matchall(repo)
            else:
                kwargs['differ'] = scmutil.matchall(repo)

        super(obsmarker_printer, self).__init__(ui, repo, *args, **kwargs)
        diffopts = kwargs.get('diffopts', {})
        self._includediff = diffopts and diffopts.get(b'patch')
        self.template = diffopts and diffopts.get(b'template')
        self.filter = diffopts and diffopts.get(b'filternonlocal')
        self.origin = diffopts and diffopts.get(b'origin')

    def show(self, ctx, copies=None, matchfn=None, **props):
        if self.buffered:
            self.ui.pushbuffer(labeled=True)

            changenode = ctx.node()

            _props = {b"template": self.template}
            fm = self.ui.formatter(b'debugobshistory', _props)

            displaynode(fm, self.repo, changenode)

            markerfm = fm.nested(b"markers")

            data = _nodesandmarkers(self.repo, ctx, self.filter, self.origin)
            for nodes, markers in data:
                displaymarkers(self.ui, markerfm, nodes, markers, ctx.node(),
                               self.repo, self._includediff,
                               successive=not self.origin)

            markerfm.end()

            fm.plain(b'\n')
            fm.end()

            self.hunk[ctx.node()] = self.ui.popbuffer()
        else:
            ### graph output is buffered only
            msg = b'cannot be used outside of the graphlog (yet)'
            raise error.ProgrammingError(msg)

    def flush(self, ctx):
        ''' changeset_printer has some logic around buffering data
        in self.headers that we don't use
        '''
        pass

class _NoPatchAvailable(Exception):
    """small internal exception

    Carries the reason of why we cannot offer a patch to `displaymarkers`.

    XXX: we could raise a more semantic reason and let `displaymarkers` create
    the message.
    """
    def __init__(self, reason):
        self.reason = reason
        super(_NoPatchAvailable, self).__init__()

def prepare_patch(repo, node, candidates, successive=True):
    """ Prepare 2 contexts for a diff between node and one of its candidates.

    `candidates` contains nodes, which can be either successors (`successive`
    is True) or predecessors (`successive` is False) of `node`.

    Return a (from_ctx, to_ctx) tuple of contexts. One of these contexts could
    be a result of in-memory rebase to align it with parents of the other
    context.
    """
    if node not in repo:
        raise _NoPatchAvailable(b"context is not local")

    if len(candidates) == 0:
        if successive:
            msg = b"no successors"
        else:
            msg = b"no predecessors"
        raise _NoPatchAvailable(msg)
    elif len(candidates) > 1:
        if successive:
            msg = b"too many successors (%d)"
        else:
            msg = b"too many predecessors (%d)"
        raise _NoPatchAvailable(msg % len(candidates))

    cand = candidates[0]

    if cand not in repo:
        if successive:
            msg = b"successor is unknown locally"
        else:
            msg = b"predecessor is unknown locally"
        raise _NoPatchAvailable(msg)

    node_ctx = repo[node]
    cand_ctx = repo[cand]

    # Check that both node and cand have the same parents
    nodep1, nodep2 = node_ctx.p1(), node_ctx.p2()
    candp1, candp2 = cand_ctx.p1(), cand_ctx.p2()

    if nodep1 != candp1:
        # XXX the case when both p1 and p2 changed could be better.
        #
        # For simplicity if both parents change, we currently only reflect the
        # impact on "p1" changeset. This should be improved at some point, but
        # this is good enough for now.
        cand_ctx = _rebase_cand(repo, cand_ctx, candp1, nodep1)
    elif nodep2 != candp2:
        cand_ctx = _rebase_cand(repo, cand_ctx, candp2, nodep2)
    if successive:
        return (node_ctx, cand_ctx)
    else:
        return (cand_ctx, node_ctx)


def _rebase_cand(repo, ctx, old_base, new_base):
    """return a view of ctx rebased in-memory from old_base to new_base

    This can be used to produce a patch in obslog even when changesets were
    rebased.
    """
    # XXX inspired by the diff.merge feature (mercurial.diffutil.diff_parent).
    # We should move this logic to core.
    base = context.overlayworkingctx(repo)
    base.setbase(ctx)
    configoverrides = {
        (b'ui', b'forcemerge'): b'internal:merge3-lie-about-conflicts'
    }
    with repo.ui.configoverride(configoverrides, b'obslog-diff'):
        with repo.ui.silent():
            merge._update(
                repo,
                new_base,
                labels=[
                    b'predecessor',
                    b'successor-parent',
                    b'predecessor-parent',
                ],
                force=True,
                branchmerge=True,
                wc=base,
                ancestor=old_base,
            )
    return base.tomemctx(text=ctx.description())

def getmarkerdescriptionpatch(repo, basedesc, succdesc):
    # description are stored without final new line,
    # add one to avoid ugly diff
    basedesc += b'\n'
    succdesc += b'\n'

    # fake file name
    basename = b"changeset-description"
    succname = b"changeset-description"

    uheaders, hunks = mdiff.unidiff(basedesc, b'', succdesc, b'',
                                    basename, succname, False)

    # Copied from patch.diff
    text = b''.join(sum((list(hlines) for hrange, hlines in hunks), []))
    patch = b"\n".join(uheaders + [text])

    return patch

class missingchangectx(object):
    ''' a minimal object mimicking changectx for change contexts
    references by obs markers but not available locally '''

    def __init__(self, repo, nodeid):
        self._repo = repo
        self._node = nodeid

    def node(self):
        return self._node

    def obsolete(self):
        # If we don't have it locally, it's obsolete
        return True

def findcycle(graph):
    """Return a set of vertices that form a cycle in the directed graph.

    The first detected cycle is returned. If there's no cycle, this function
    return None. The graph must be represented as a dictionary mapping vertices
    to iterables of neighbouring vertices. For example:

    >>> sorted(findcycle({1: (2,), 2: (3,), 3: (1,)}))
    [1, 2, 3]
    >>> print(findcycle({1: (2,), 2: (3,), 3: (4,)}))
    None

    Taken from: https://codereview.stackexchange.com/a/86067
    """
    visited = set()
    o = object()
    path = [o]
    path_set = set(path)
    stack = [iter(graph)]
    while stack:
        for v in sorted(stack[-1]):
            if v in path_set:
                path_set.remove(o)
                return path_set
            elif v not in visited:
                visited.add(v)
                path.append(v)
                path_set.add(v)
                stack.append(iter(graph.get(v, ())))
                break
        else:
            path_set.remove(path.pop())
            stack.pop()
    return None

def _obshistorywalker(repo, revs, walksuccessors=False, filternonlocal=False):
    """ Directly inspired by graphmod.dagwalker,
    walk the obs marker tree and yield
    (id, CHANGESET, ctx, [parentinfo]) tuples
    """

    # Get the list of nodes and links between them
    candidates, nodesucc, nodeprec = _obshistorywalker_links(repo, revs, walksuccessors)

    # Shown, set of nodes presents in items
    shown = set()

    def isvalidcandidate(candidate):
        """ Function to filter candidates, check the candidate succ are
        in shown set
        """
        return nodesucc.get(candidate, set()).issubset(shown)

    # While we have some nodes to show
    while candidates:

        # Filter out candidates, returns only nodes with all their successors
        # already shown
        validcandidates = list(filter(isvalidcandidate, candidates))

        # If we likely have a cycle
        if not validcandidates:
            cycle = findcycle(nodesucc)
            assert cycle

            # Then choose a random node from the cycle
            breaknode = sorted(cycle)[0]
            # And display it by force
            repo.ui.debug(b'obs-cycle detected, forcing display of %s\n'
                          % nodemod.short(breaknode))
            validcandidates = [breaknode]

        # Display all valid candidates
        for cand in sorted(validcandidates):
            # Remove candidate from candidates set
            candidates.remove(cand)
            # And remove it from nodesucc in case of future cycle detected
            try:
                del nodesucc[cand]
            except KeyError:
                pass

            shown.add(cand)

            # Add the right changectx class
            if cand in repo:
                changectx = repo[cand]
            else:
                if filternonlocal is False:
                    changectx = missingchangectx(repo, cand)
                else:
                    continue

            if filternonlocal is False:
                relations = nodeprec.get(cand, ())
            else:
                relations = obsutil.closestpredecessors(repo, cand)
            parents = [(graphmod.PARENT, x) for x in relations]
            yield (cand, graphmod.CHANGESET, changectx, parents)

def _obshistorywalker_links(repo, revs, walksuccessors=False):
    """ Iterate the obs history tree starting from revs, traversing
    each revision precursors recursively.
    If walksuccessors is True, also check that every successor has been
    walked, which ends up walking on all connected obs markers. It helps
    getting a better view with splits and divergences.
    Return a tuple of:
    - The list of node crossed
    - The dictionnary of each node successors, values are a set
    - The dictionnary of each node precursors, values are a list
    """
    precursors = repo.obsstore.predecessors
    successors = repo.obsstore.successors
    nodec = repo.changelog.node

    # Parents, set of parents nodes seen during walking the graph for node
    nodesucc = dict()
    # Childrens
    nodeprec = dict()

    nodes = [nodec(r) for r in revs]
    seen = set(nodes)

    # Iterate on each node
    while nodes:
        node = nodes.pop()

        precs = precursors.get(node, ())

        nodeprec[node] = []

        for prec in sorted(precs):
            precnode = prec[0]

            # Mark node as prec successor
            nodesucc.setdefault(precnode, set()).add(node)

            # Mark precnode as node precursor
            nodeprec[node].append(precnode)

            # Add prec for future processing if not node already processed
            if precnode not in seen:
                seen.add(precnode)
                nodes.append(precnode)

        # Also walk on successors if the option is enabled
        if walksuccessors:
            for successor in successors.get(node, ()):
                for succnodeid in successor[1]:
                    if succnodeid not in seen:
                        seen.add(succnodeid)
                        nodes.append(succnodeid)

    return sorted(seen), nodesucc, nodeprec

def displaygraph(ui, repo, revs, opts):

    displayer = obsmarker_printer(ui, repo.unfiltered(), obspatch=True,
                                  diffopts=pycompat.byteskwargs(opts),
                                  buffered=True)
    edges = graphmod.asciiedges
    walker = _obshistorywalker(repo.unfiltered(), revs, opts.get('all', False),
                               opts.get('filternonlocal', False))
    logcmdutil.displaygraph(ui, repo, walker, displayer, edges)

def displayrevs(ui, repo, revs, opts):
    """ Display the obsolescence history for revset
    """
    fm = ui.formatter(b'debugobshistory', pycompat.byteskwargs(opts))
    predecessors = repo.obsstore.predecessors
    successors = repo.obsstore.successors
    nodec = repo.changelog.node
    unfi = repo.unfiltered()
    nodes = [nodec(r) for r in revs]
    seen = set(nodes)
    toshow = []

    origin = opts and opts.get('origin')
    walksuccessors = opts and opts.get('all')
    filternonlocal = opts and opts.get('filternonlocal')
    includediff = opts and opts.get('patch')

    while nodes:
        ctxnode = nodes.pop()

        if ctxnode in unfi:
            toshow.append(unfi[ctxnode])
        else:
            if filternonlocal is False:
                toshow.append(missingchangectx(unfi, ctxnode))

        preds = predecessors.get(ctxnode, ())
        for p in sorted(preds):
            # Only show nodes once
            if p[0] not in seen:
                seen.add(p[0])
                nodes.append(p[0])

        if walksuccessors:
            for successor in successors.get(ctxnode, ()):
                for s in successor[1]:
                    if s not in seen:
                        seen.add(s)
                        nodes.append(s)

    for ctx in toshow:
        displaynode(fm, unfi, ctx.node())

        markerfm = fm.nested(b"markers")

        data = _nodesandmarkers(unfi, ctx, filternonlocal, origin)
        for nodes_, markers in data:
            displaymarkers(ui, markerfm, nodes_, markers, ctx.node(), unfi,
                           includediff, successive=not origin)

        markerfm.end()

        fm.plain(b'\n')

    fm.end()

def displaynode(fm, repo, node):
    if node in repo:
        displayctx(fm, repo[node])
    else:
        displaymissingctx(fm, node)

def displayctx(fm, ctx):
    shortdescription = ctx.description().strip()
    if shortdescription:
        shortdescription = shortdescription.splitlines()[0]

    fm.startitem()
    fm.context(ctx=ctx)
    fm.data(node=ctx.hex())
    fm.plain(b'%s' % bytes(ctx), label=b"evolve.node")
    fm.plain(b' ')

    fm.plain(b'(%d)' % ctx.rev(), label=b"evolve.rev")
    fm.plain(b' ')

    fm.write(b'shortdescription', b'%s', shortdescription,
             label=b"evolve.short_description")
    fm.plain(b'\n')

def displaymissingctx(fm, nodewithoutctx):
    fm.startitem()
    fm.data(node=nodemod.hex(nodewithoutctx))
    fm.plain(nodemod.short(nodewithoutctx),
             label=b"evolve.node evolve.missing_change_ctx")
    fm.plain(b'\n')

def displaymarkers(ui, fm, nodes, markers, node, repo, includediff=False,
                   successive=True):
    fm.startitem()

    if successive:
        verb = _successorsetverb(nodes, markers)[b"verb"]
    else:
        verb = _predecessorsverb(nodes, markers)

    fm.data(verb=verb)

    effects = _markerseffects(markers)
    if effects:
        fmteffects = fm.formatlist(effects, b'effect', sep=b', ')
        fm.data(effects=fmteffects)

    if len(nodes) > 0:
        hexnodes = (nodemod.hex(node) for node in sorted(nodes))
        if successive:
            nodelist = fm.formatlist(hexnodes, b'succnode')
            fm.data(succnodes=nodelist)
        else:
            nodelist = fm.formatlist(hexnodes, b'prednode')
            fm.data(prednodes=nodelist)

    # Operations
    operations = obsutil.markersoperations(markers)
    if operations:
        fm.data(operations=fm.formatlist(operations, name=b'operation', sep=b', '))

    # Users
    users = obsutil.markersusers(markers)
    fm.data(users=fm.formatlist(users, name=b'user', sep=b', '))

    # Dates
    dates = obsutil.markersdates(markers)
    fm.data(dates=fm.formatlist(dates, name=b'date'))

    # Notes
    notes = _markersnotes(markers)
    if notes:
        fm.data(notes=fm.formatlist(notes, name=b'note', sep=b'\n'))

    # Patch display
    if includediff is True:

        try:
            actx, bctx = prepare_patch(repo, node, nodes, successive=successive)
            assert actx is not None
            assert bctx is not None
        except _NoPatchAvailable as exc:
            fm.data(nopatchreason=exc.reason)
        else:
            # Description patch
            descriptionpatch = getmarkerdescriptionpatch(repo,
                                                         actx.description(),
                                                         bctx.description())

            if descriptionpatch:
                # add the diffheader
                diffheader = b"diff -r %s -r %s changeset-description\n" %\
                             (actx, bctx)
                descriptionpatch = diffheader + descriptionpatch

                def tolist(text):
                    return [text]

                ui.pushbuffer(labeled=True)
                ui.write(b"\n")

                for chunk, label in patch.difflabel(tolist, descriptionpatch):
                    chunk = chunk.strip(b'\t')
                    ui.write(chunk, label=label)
                fm.write(b'descdiff', b'%s', ui.popbuffer())

            # Content patch
            ui.pushbuffer(labeled=True)
            diffopts = patch.diffallopts(repo.ui, {})
            matchfn = scmutil.matchall(repo)
            firstline = True
            linestart = True
            for chunk, label in patch.diffui(repo, actx, bctx,
                                             matchfn, opts=diffopts):
                if firstline:
                    ui.write(b'\n')
                    firstline = False
                if linestart:
                    linestart = False
                if chunk == b'\n':
                    linestart = True
                ui.write(chunk, label=label)
            fm.data(patch=ui.popbuffer())

def _prepare_hunk(hunk):
    """Drop all information but the username and patch"""
    cleanunk = []
    for line in hunk.splitlines():
        if line.startswith(b'# User') or not line.startswith(b'#'):
            if line.startswith(b'@@'):
                line = b'@@\n'
            cleanunk.append(line)
    return cleanunk

def _getdifflines(iterdiff):
    """return a cleaned up lines"""
    try:
        lines = next(iterdiff)
    except StopIteration:
        return None
    return _prepare_hunk(lines)

def _getobsfateandsuccs(repo, revnode):
    """ Return a tuple containing:
    - the reason a revision is obsolete (diverged, pruned or superseded)
    - the list of successors short node if the revision is neither pruned
    or has diverged
    """
    successorssets = obsutil.successorssets(repo, revnode)
    fate = obsutil._getobsfate(successorssets)

    # Apply node.short if we have no divergence
    if len(successorssets) == 1:
        successors = [nodemod.short(node_id) for node_id in successorssets[0]]
    else:
        successors = []
        for succset in successorssets:
            successors.append([nodemod.short(node_id) for node_id in succset])

    return (fate, successors)

def _markersnotes(markers):
    markersmeta = [dict(m[3]) for m in markers]
    notes = {meta.get(b'note') for meta in markersmeta}
    return sorted(note for note in notes if note)

EFFECTMAPPING = util.sortdict([
    (obsutil.DESCCHANGED, b'description'),
    (obsutil.METACHANGED, b'meta'),
    (obsutil.USERCHANGED, b'user'),
    (obsutil.DATECHANGED, b'date'),
    (obsutil.BRANCHCHANGED, b'branch'),
    (obsutil.PARENTCHANGED, b'parent'),
    (obsutil.DIFFCHANGED, b'content'),
])

def _markerseffects(markers):
    """ Return a list of effects as strings based on effect flags in markers
    """
    metadata = [dict(marker[3]) for marker in markers]
    ef1 = [data.get(b'ef1') for data in metadata]
    effects = []

    combined = 0
    for ef in ef1:
        if ef:
            combined |= int(ef)

    if combined:
        for key, value in EFFECTMAPPING.items():
            if combined & key:
                effects.append(value)

    return effects

VERBMAPPING = {
    obsutil.DESCCHANGED: b"reworded",
    obsutil.METACHANGED: b"meta-changed",
    obsutil.USERCHANGED: b"reauthored",
    obsutil.DATECHANGED: b"date-changed",
    obsutil.BRANCHCHANGED: b"branch-changed",
    obsutil.PARENTCHANGED: b"rebased",
    obsutil.DIFFCHANGED: b"amended"
}

def _markerspreciseverb(markers):
    """ Return a more precise verb based on effect flags in markers

    Return None if verb cannot be more precise than just "rewritten", i.e. when
    markers collectively have more than one effect in the flags.
    """
    metadata = [dict(marker[3]) for marker in markers]

    if len(metadata) == 1 and metadata[0].get(b'fold-id') is not None:
        return b'folded'

    ef1 = [data.get(b'ef1') for data in metadata]
    if all(ef1):
        combined = 0
        for ef in ef1:
            combined |= int(ef)

        # Combined will be in VERBMAPPING only if one bit is set
        if combined in VERBMAPPING:
            return VERBMAPPING[combined]

def _successorsetverb(successorset, markers):
    """ Return the verb summarizing the successorset
    """
    verb = None
    if not successorset:
        verb = b'pruned'
    elif len(successorset) == 1:
        verb = _markerspreciseverb(markers)

        if verb is None:
            verb = b'rewritten'
    else:
        verb = b'split'
    return {b'verb': verb}

def _predecessorsverb(predecessors, markers):
    """ Return the verb summarizing a set of predecessors and related markers.
    """
    verb = None
    if not predecessors:
        # we got successors instead of predecessors, and they are empty
        # (this is a special case for showing prunes)
        verb = b'pruned'
    elif len(markers) == 1 and len(markers[0][1]) > 1:
        # peeked at the successors to see if this is a split
        verb = b'split'
    elif len(predecessors) == 1:
        verb = _markerspreciseverb(markers)

        if verb is None:
            verb = b'rewritten'
    else:
        verb = b'folded'
    return verb

# Use a more advanced version of obsfateverb that uses effect-flag
@eh.wrapfunction(obsutil, 'obsfateverb')
def obsfateverb(orig, *args, **kwargs):
    return _successorsetverb(*args, **kwargs)[b'verb']

def obsoriginprinter(ui, repo, predecessors, markers):
    """ Build an obsorigin string for a single set of predecessors.
    """
    quiet = ui.quiet
    verbose = ui.verbose
    normal = not verbose and not quiet

    line = []

    # Verb
    line.append(_predecessorsverb(predecessors, markers))

    # Operations
    operations = obsutil.markersoperations(markers)
    if operations:
        line.append(b" using %s" % b", ".join(operations))

    # Predecessors
    if predecessors:
        unfi = repo.unfiltered()

        def formatnode(node):
            if node in unfi:
                return scmutil.formatchangeid(unfi[node])
            return nodemod.short(node)

        fmtpredecessors = [formatnode(pred) for pred in predecessors]
        line.append(b" from %s" % b", ".join(sorted(fmtpredecessors)))

    # Users
    users = obsutil.markersusers(markers)
    # Filter out current user in not verbose mode to reduce amount of
    # information
    if not verbose:
        currentuser = ui.username(acceptempty=True)
        if len(users) == 1 and currentuser in users:
            users = None

    if (verbose or normal) and users:
        line.append(b" by %s" % b", ".join(users))

    # Dates
    dates = obsutil.markersdates(markers)

    if dates and verbose:
        min_date = min(dates)
        max_date = max(dates)

        if min_date == max_date:
            fmtmin_date = dateutil.datestr(min_date, b'%Y-%m-%d %H:%M %1%2')
            line.append(b" (at %s)" % fmtmin_date)
        else:
            fmtmin_date = dateutil.datestr(min_date, b'%Y-%m-%d %H:%M %1%2')
            fmtmax_date = dateutil.datestr(max_date, b'%Y-%m-%d %H:%M %1%2')
            line.append(b" (between %s and %s)" % (fmtmin_date, fmtmax_date))

    return b"".join(line)
