# Copyright 2017 Octobus <contact@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
"""
Compatibility module
"""

from mercurial import (
    cmdutil,
    context,
    copies as copiesmod,
    hg,
    scmutil,
    util,
)

# hg <= 7.1 (d32b62bf63c8)
try:
    from mercurial.main_script import cmd_finder
    find_cmd = cmd_finder.find_cmd
except (AttributeError, ImportError):
    find_cmd = cmdutil.findcmd  # pytype: disable=module-attr

# hg <= 7.1 (7c6e323cb685)
try:
    bail_if_changed = scmutil.bail_if_changed
except AttributeError:
    bail_if_changed = cmdutil.bailifchanged  # pytype: disable=module-attr

# hg <= 7.1 (28dbb31f7317)
try:
    cleanup_nodes = cmdutil.cleanup_nodes
except AttributeError:
    cleanup_nodes = scmutil.cleanupnodes  # pytype: disable=module-attr

# hg <= 7.1 (6ca1d7250a7b)
try:
    from mercurial.cmd_impls import update as updatemod
    hg_show_stats = updatemod.show_stats
    hg_update = updatemod.update
    hg_update_totally = updatemod.update_totally
except (AttributeError, ImportError):
    hg_show_stats = hg._showstats  # pytype: disable=module-attr
    hg_update = hg.update  # pytype: disable=module-attr
    hg_update_totally = hg.updatetotally  # pytype: disable=module-attr

from . import (
    exthelper,
)

eh = exthelper.exthelper()

# Evolution renaming compat

TROUBLES = {
    r'ORPHAN': b'orphan',
    r'CONTENTDIVERGENT': b'content-divergent',
    r'PHASEDIVERGENT': b'phase-divergent',
}

hg48 = util.safehasattr(copiesmod, 'stringutil')
# code imported from Mercurial core at ae17555ef93f + patch
def fixedcopytracing(repo, c1, c2, base):
    """A complete copy-patse of copies._fullcopytrace with a one line fix to
    handle when the base is not parent of both c1 and c2. This should be
    converted in a compat function once https://phab.mercurial-scm.org/D3896
    gets in and once we drop support for 4.9, this should be removed."""

    from mercurial import pathutil
    copies = copiesmod

    # In certain scenarios (e.g. graft, update or rebase), base can be
    # overridden We still need to know a real common ancestor in this case We
    # can't just compute _c1.ancestor(_c2) and compare it to ca, because there
    # can be multiple common ancestors, e.g. in case of bidmerge.  Because our
    # caller may not know if the revision passed in lieu of the CA is a genuine
    # common ancestor or not without explicitly checking it, it's better to
    # determine that here.
    #
    # base.isancestorof(wc) is False, work around that
    _c1 = c1.p1() if c1.rev() is None else c1
    _c2 = c2.p1() if c2.rev() is None else c2
    # an endpoint is "dirty" if it isn't a descendant of the merge base
    # if we have a dirty endpoint, we need to trigger graft logic, and also
    # keep track of which endpoint is dirty
    dirtyc1 = not base.isancestorof(_c1)
    dirtyc2 = not base.isancestorof(_c2)
    graft = dirtyc1 or dirtyc2
    tca = base
    if graft:
        tca = _c1.ancestor(_c2)

    limit = copies._findlimit(repo, c1, c2)  # pytype: disable=module-attr
    if limit is None:
        # no common ancestor, no copies
        return {}, {}, {}, {}, {}
    repo.ui.debug(b"  searching for copies back to rev %d\n" % limit)

    m1 = c1.manifest()
    m2 = c2.manifest()
    mb = base.manifest()

    # gather data from _checkcopies:
    # - diverge = record all diverges in this dict
    # - copy = record all non-divergent copies in this dict
    # - fullcopy = record all copies in this dict
    # - incomplete = record non-divergent partial copies here
    # - incompletediverge = record divergent partial copies here
    diverge = {} # divergence data is shared
    incompletediverge = {}
    data1 = {b'copy': {},
             b'fullcopy': {},
             b'incomplete': {},
             b'diverge': diverge,
             b'incompletediverge': incompletediverge,
             }
    data2 = {b'copy': {},
             b'fullcopy': {},
             b'incomplete': {},
             b'diverge': diverge,
             b'incompletediverge': incompletediverge,
             }

    # find interesting file sets from manifests
    if hg48:
        addedinm1 = m1.filesnotin(mb, repo.narrowmatch())
        addedinm2 = m2.filesnotin(mb, repo.narrowmatch())
    else:
        addedinm1 = m1.filesnotin(mb)
        addedinm2 = m2.filesnotin(mb)
    bothnew = sorted(addedinm1 & addedinm2)
    if tca == base:
        # unmatched file from base
        u1r, u2r = copies._computenonoverlap(repo, c1, c2, addedinm1, addedinm2)  # pytype: disable=module-attr
        u1u, u2u = u1r, u2r
    else:
        # unmatched file from base (DAG rotation in the graft case)
        u1r, u2r = copies._computenonoverlap(repo, c1, c2, addedinm1, addedinm2,  # pytype: disable=module-attr
                                             baselabel=b'base')
        # unmatched file from topological common ancestors (no DAG rotation)
        # need to recompute this for directory move handling when grafting
        mta = tca.manifest()
        if hg48:
            m1f = m1.filesnotin(mta, repo.narrowmatch())
            m2f = m2.filesnotin(mta, repo.narrowmatch())
            baselabel = b'topological common ancestor'
            u1u, u2u = copies._computenonoverlap(repo, c1, c2, m1f, m2f,  # pytype: disable=module-attr
                                                 baselabel=baselabel)
        else:
            u1u, u2u = copies._computenonoverlap(repo, c1, c2, m1.filesnotin(mta),  # pytype: disable=module-attr
                                                 m2.filesnotin(mta),
                                                 baselabel=b'topological common ancestor')

    for f in u1u:
        copies._checkcopies(c1, c2, f, base, tca, dirtyc1, limit, data1)  # pytype: disable=module-attr

    for f in u2u:
        copies._checkcopies(c2, c1, f, base, tca, dirtyc2, limit, data2)  # pytype: disable=module-attr

    copy = dict(data1[b'copy'])
    copy.update(data2[b'copy'])
    fullcopy = dict(data1[b'fullcopy'])
    fullcopy.update(data2[b'fullcopy'])

    if dirtyc1:
        copies._combinecopies(data2[b'incomplete'], data1[b'incomplete'], copy, diverge,  # pytype: disable=module-attr
                              incompletediverge)
    else:
        copies._combinecopies(data1[b'incomplete'], data2[b'incomplete'], copy, diverge,  # pytype: disable=module-attr
                              incompletediverge)

    renamedelete = {}
    renamedeleteset = set()
    divergeset = set()
    for of, fl in list(diverge.items()):
        if len(fl) == 1 or of in c1 or of in c2:
            del diverge[of] # not actually divergent, or not a rename
            if of not in c1 and of not in c2:
                # renamed on one side, deleted on the other side, but filter
                # out files that have been renamed and then deleted
                renamedelete[of] = [f for f in fl if f in c1 or f in c2]
                renamedeleteset.update(fl) # reverse map for below
        else:
            divergeset.update(fl) # reverse map for below

    if bothnew:
        repo.ui.debug(b"  unmatched files new in both:\n   %s\n"
                      % b"\n   ".join(bothnew))
    bothdiverge = {}
    bothincompletediverge = {}
    remainder = {}
    both1 = {b'copy': {},
             b'fullcopy': {},
             b'incomplete': {},
             b'diverge': bothdiverge,
             b'incompletediverge': bothincompletediverge
             }
    both2 = {b'copy': {},
             b'fullcopy': {},
             b'incomplete': {},
             b'diverge': bothdiverge,
             b'incompletediverge': bothincompletediverge
             }
    for f in bothnew:
        copies._checkcopies(c1, c2, f, base, tca, dirtyc1, limit, both1)  # pytype: disable=module-attr
        copies._checkcopies(c2, c1, f, base, tca, dirtyc2, limit, both2)  # pytype: disable=module-attr

    if dirtyc1 and dirtyc2:
        pass
    elif dirtyc1:
        # incomplete copies may only be found on the "dirty" side for bothnew
        assert not both2[b'incomplete']
        remainder = copies._combinecopies({}, both1[b'incomplete'], copy, bothdiverge,  # pytype: disable=module-attr
                                          bothincompletediverge)
    elif dirtyc2:
        assert not both1[b'incomplete']
        remainder = copies._combinecopies({}, both2[b'incomplete'], copy, bothdiverge,  # pytype: disable=module-attr
                                          bothincompletediverge)
    else:
        # incomplete copies and divergences can't happen outside grafts
        assert not both1[b'incomplete']
        assert not both2[b'incomplete']
        assert not bothincompletediverge
    for f in remainder:
        assert f not in bothdiverge
        ic = remainder[f]
        if ic[0] in (m1 if dirtyc1 else m2):
            # backed-out rename on one side, but watch out for deleted files
            bothdiverge[f] = ic
    for of, fl in bothdiverge.items():
        if len(fl) == 2 and fl[0] == fl[1]:
            copy[fl[0]] = of # not actually divergent, just matching renames

    if fullcopy and repo.ui.debugflag:
        repo.ui.debug(b"  all copies found (* = to merge, ! = divergent, "
                      b"% = renamed and deleted):\n")
        for f in sorted(fullcopy):
            note = b""
            if f in copy:
                note += b"*"
            if f in divergeset:
                note += b"!"
            if f in renamedeleteset:
                note += b"%"
            repo.ui.debug(b"   src: '%s' -> dst: '%s' %s\n" % (fullcopy[f], f,
                                                               note))
    del divergeset

    if not fullcopy:
        return copy, {}, diverge, renamedelete, {}

    repo.ui.debug(b"  checking for directory renames\n")

    # generate a directory move map
    d1, d2 = c1.dirs(), c2.dirs()
    # Hack for adding '', which is not otherwise added, to d1 and d2
    d1.addpath(b'/')
    d2.addpath(b'/')
    invalid = set()
    dirmove = {}

    # examine each file copy for a potential directory move, which is
    # when all the files in a directory are moved to a new directory
    for dst, src in fullcopy.items():
        dsrc, ddst = pathutil.dirname(src), pathutil.dirname(dst)
        if dsrc in invalid:
            # already seen to be uninteresting
            continue
        elif dsrc in d1 and ddst in d1:
            # directory wasn't entirely moved locally
            invalid.add(dsrc + b"/")
        elif dsrc in d2 and ddst in d2:
            # directory wasn't entirely moved remotely
            invalid.add(dsrc + b"/")
        elif dsrc + b"/" in dirmove and dirmove[dsrc + b"/"] != ddst + b"/":
            # files from the same directory moved to two different places
            invalid.add(dsrc + b"/")
        else:
            # looks good so far
            dirmove[dsrc + b"/"] = ddst + b"/"

    for i in invalid:
        if i in dirmove:
            del dirmove[i]
    del d1, d2, invalid

    if not dirmove:
        return copy, {}, diverge, renamedelete, {}

    for d in dirmove:
        repo.ui.debug(b"   discovered dir src: '%s' -> dst: '%s'\n" %
                      (d, dirmove[d]))

    movewithdir = {}
    # check unaccounted nonoverlapping files against directory moves
    for f in u1r + u2r:
        if f not in fullcopy:
            for d in dirmove:
                if f.startswith(d):
                    # new file added in a directory that was moved, move it
                    df = dirmove[d] + f[len(d):]
                    if df not in copy:
                        movewithdir[f] = df
                        repo.ui.debug((b"   pending file src: '%s' -> "
                                       b"dst: '%s'\n") % (f, df))
                    break

    return copy, movewithdir, diverge, renamedelete, dirmove

# hg <= 6.9 (f071b18e1382)
# we detect a502f3f389b5 because it's close enough and touches the same code
def _detect_hit(code):
    """ detect a502f3f389b5 by inspecting variables of getfile()
    """
    return 'hit' in code.co_varnames[code.co_argcount:]
def _new_tomemctx(tomemctx):
    """ diving into tomemctx() to find and inspect the nested getfile()
    """
    return any(
        _detect_hit(c) for c in tomemctx.__code__.co_consts
        if util.safehasattr(c, 'co_varnames')
    )
if not _new_tomemctx(context.overlayworkingctx.tomemctx):
    def fixed_tomemctx(
        self,
        text,
        branch=None,
        extra=None,
        date=None,
        parents=None,
        user=None,
        editor=None,
    ):
        """Converts this ``overlayworkingctx`` into a ``memctx`` ready to be
        committed.

        ``text`` is the commit message.
        ``parents`` (optional) are rev numbers.
        """
        # Default parents to the wrapped context if not passed.
        if parents is None:
            parents = self.parents()
            if len(parents) == 1:
                parents = (parents[0], None)

        # ``parents`` is passed as rev numbers; convert to ``commitctxs``.
        if parents[1] is None:
            parents = (self._repo[parents[0]], None)
        else:
            parents = (self._repo[parents[0]], self._repo[parents[1]])

        files = self.files()

        def getfile(repo, memctx, path):
            hit = self._cache.get(path)
            ### FIXED PART ###
            if hit is None:
                return self.filectx(path)
            ### END FIXED PART ###
            elif hit[b'exists']:
                return context.memfilectx(
                    repo,
                    memctx,
                    path,
                    hit[b'data'],
                    b'l' in hit[b'flags'],
                    b'x' in hit[b'flags'],
                    hit[b'copied'],
                )
            else:
                # Returning None, but including the path in `files`, is
                # necessary for memctx to register a deletion.
                return None

        if branch is None:
            branch = self._wrappedctx.branch()

        return context.memctx(
            self._repo,
            parents,
            text,
            files,
            getfile,
            date=date,
            extra=extra,
            user=user,
            branch=branch,
            editor=editor,
        )

    context.overlayworkingctx.tomemctx = fixed_tomemctx
