# Module dedicated to host history rewriting commands
#
# Copyright 2017 Octobus <contact@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# Status: Stabilization of the API in progress
#
#   The final set of command should go into core.

from __future__ import absolute_import

import random

from mercurial import (
    bookmarks as bookmarksmod,
    cmdutil,
    commands,
    context,
    copies,
    error,
    lock as lockmod,
    merge,
    node,
    obsolete,
    patch,
    pathutil,
    phases,
    pycompat,
    registrar,
    rewriteutil as corerewriteutil,
    scmutil,
    util,
    repair,
)

from mercurial.utils import dateutil

from mercurial.i18n import _

from . import (
    compat,
    state,
    exthelper,
    rewriteutil,
    utility,
    evolvecmd,
)

eh = exthelper.exthelper()

walkopts = commands.walkopts
commitopts = commands.commitopts
commitopts2 = commands.commitopts2
mergetoolopts = commands.mergetoolopts
stringio = util.stringio
precheck_contentdiv = rewriteutil.precheck_contentdiv

# option added by evolve

def _checknotesize(ui, opts):
    """ make sure note is of valid format """

    note = opts.get('note')
    if not note:
        return

    if len(note) > 255:
        raise error.Abort(_(b"cannot store a note of more than 255 bytes"))
    if b'\n' in note:
        raise error.Abort(_(b"note cannot contain a newline"))

def _resolveoptions(ui, opts):
    """modify commit options dict to handle related options

    For now, all it does is figure out the commit date: respect -D unless
    -d was supplied.
    """
    # N.B. this is extremely similar to setupheaderopts() in mq.py
    if not opts.get('date') and opts.get('current_date'):
        opts['date'] = b'%d %d' % dateutil.makedate()
    if not opts.get('user') and opts.get('current_user'):
        opts['user'] = ui.username()

commitopts3 = [
    (b'D', b'current-date', None,
     _(b'record the current date as commit date')),
    (b'U', b'current-user', None,
     _(b'record the current user as committer')),
]

interactiveopt = [[b'i', b'interactive', None, _(b'use interactive mode')]]

@eh.command(
    b'amend|refresh',
    [(b'A', b'addremove', None,
      _(b'mark new/missing files as added/removed before committing')),
     (b'a', b'all', False, _(b"match all files")),
     (b'e', b'edit', False, _(b'invoke editor on commit messages')),
     (b'', b'extract', False, _(b'extract changes from the commit to the working copy')),
     (b'', b'patch', False, _(b'make changes to wdir parent by editing patch')),
     (b'', b'close-branch', None,
      _(b'mark a branch as closed, hiding it from the branch list')),
     (b's', b'secret', None, _(b'use the secret phase for committing')),
     (b'n', b'note', b'', _(b'store a note on amend'), _(b'TEXT')),
     ] + walkopts + commitopts + commitopts2 + commitopts3 + interactiveopt,
    _(b'[OPTION]... [FILE]...'),
    helpcategory=registrar.command.CATEGORY_COMMITTING,
    helpbasic=True,
)
def amend(ui, repo, *pats, **opts):
    """combine a changeset with updates and replace it with a new one

    Commits a new changeset incorporating both the changes to the given files
    and all the changes from the current parent changeset into the repository.

    See :hg:`commit` for details about committing changes.

    If you don't specify -m, the parent's message will be reused.

    If --extract is specified, the behavior of `hg amend` is reversed: Changes
    to selected files in the checked out revision appear again as uncommitted
    changed in the working directory.

    Returns 0 on success, 1 if nothing changed.
    """
    _checknotesize(ui, opts)
    opts = opts.copy()
    if opts.get('patch') and opts.get('extract'):
        raise error.Abort(_(b'cannot use both --patch and --extract'))
    if opts.get('patch'):
        return amendpatch(ui, repo, *pats, **opts)
    if opts.get('extract'):
        return uncommit(ui, repo, *pats, **opts)
    else:
        if opts.pop('all', False):
            # add an include for all
            include = list(opts.get('include'))
            include.append(b're:.*')
        edit = opts.pop('edit', False)
        log = opts.get('logfile')
        opts['amend'] = True
        _resolveoptions(ui, opts)
        _alias, commitcmd = compat.find_cmd(b'commit', commands.table)
        with repo.wlock(), repo.lock():
            if not (edit or opts['message'] or log):
                opts['message'] = repo[b'.'].description()
            corerewriteutil.precheck(repo, [repo[b'.'].rev()], action=b'amend')
            return commitcmd[0](ui, repo, *pats, **opts)

def amendpatch(ui, repo, *pats, **opts):
    """logic for --patch flag of `hg amend` command."""
    with repo.wlock(), repo.lock(), repo.transaction(b'amend') as tr:
        compat.bail_if_changed(repo)
        # first get the patch
        old = repo[b'.']
        p1 = old.p1()
        corerewriteutil.precheck(repo, [old.rev()], b'amend')
        diffopts = patch.difffeatureopts(repo.ui, whitespace=True)
        diffopts.nodates = True
        diffopts.git = True
        fp = stringio()
        _writectxmetadata(repo, old, fp)
        matcher = scmutil.match(old, pats, opts)
        for chunk, label in patch.diffui(repo, p1.node(), old.node(),
                                         match=matcher,
                                         opts=diffopts):
            fp.write(chunk)
        newnode = _editandapply(ui, repo, pats, old, p1, fp, diffopts)
        if newnode == old.node():
            raise error.Abort(_(b"nothing changed"))
        metadata = {}
        if opts.get('note'):
            metadata[b'note'] = opts['note']
        replacements = {(old.node(),): [newnode]}
        compat.cleanup_nodes(repo, replacements, operation=b'amend',
                             metadata=metadata)
        phases.retractboundary(repo, tr, old.phase(), [newnode])
        merge.clean_update(repo[newnode])

def _editandapply(ui, repo, pats, old, p1, fp, diffopts):
    newnode = None
    while newnode is None:
        fp.seek(0)
        previous_patch = fp.getvalue()
        newpatch = ui.edit(fp.getvalue(), old.user(), action=b"diff")

        afp = stringio()
        afp.write(newpatch)
        if pats:
            # write rest of the files in the patch
            restmatcher = scmutil.match(old, [], opts={b'exclude': pats})
            for chunk, label in patch.diffui(repo, p1.node(), old.node(),
                                             match=restmatcher,
                                             opts=diffopts):
                afp.write(chunk)

        user_patch = afp.getvalue()
        if not user_patch:
            raise error.Abort(_(b"empty patch file, amend aborted"))
        if user_patch == previous_patch:
            raise error.Abort(_(b"patch unchanged"))
        afp.seek(0)
        # write the patch to repo and get the newnode
        try:
            newnode = _writepatch(ui, repo, old, afp)
        except patch.PatchError as err:
            ui.write_err(_(b"failed to apply edited patch: %s\n") % err)
            defaultchoice = 0 # yes
            if not ui.interactive:
                defaultchoice = 1 # no
            retrychoice = _(b'try to fix the patch (yn)?$$ &Yes $$ &No')
            if ui.promptchoice(retrychoice, default=defaultchoice):
                raise error.Abort(_(b"Could not apply amended path"))
            else:
                # consider a third choice where we restore the original patch
                fp = stringio()
                fp.write(user_patch)
    return newnode

def _writepatch(ui, repo, old, fp):
    """utility function to use filestore and patchrepo to apply a patch to the
    repository with metadata being extracted from the patch"""
    patchcontext = patch.extract(ui, fp)
    pold = old.p1()

    with patchcontext as metadata:
        # store the metadata from the patch to variables
        parents = (metadata.get(b'p1'), metadata.get(b'p2'))
        date = metadata.get(b'date') or old.date()
        branch = metadata.get(b'branch') or old.branch()
        user = metadata.get(b'user') or old.user()
        # XXX: we must extract extras from the patchfile too
        extra = old.extra()
        message = metadata.get(b'message') or old.description()
        store = patch.filestore()
        fp.seek(0)
        try:
            files = set()
            # beware: next line may raise a PatchError to be handled by the caller
            # of this function
            patch.patchrepo(ui, repo, pold, store, fp, 1, b'',
                            files=files, eolmode=None)

            memctx = context.memctx(repo, parents, message, files=files,
                                    filectxfn=store,
                                    user=user,
                                    date=date,
                                    branch=branch,
                                    extra=extra)
            newcm = memctx.commit()
        finally:
            store.close()
    return newcm

def _writectxmetadata(repo, ctx, fp):
    nodeval = scmutil.binnode(ctx)
    parents = [p.node() for p in ctx.parents() if p]
    branch = ctx.branch()
    if parents:
        prev = parents[0]
    else:
        prev = node.nullid

    fp.write(b"# HG changeset patch\n")
    fp.write(b"# User %s\n" % ctx.user())
    fp.write(b"# Date %d %d\n" % ctx.date())
    fp.write(b"#      %s\n" % dateutil.datestr(ctx.date()))
    if branch and branch != b'default':
        fp.write(b"# Branch %s\n" % branch)
    fp.write(b"# Node ID %s\n" % node.hex(nodeval))
    fp.write(b"# Parent  %s\n" % node.hex(prev))
    if len(parents) > 1:
        fp.write(b"# Parent  %s\n" % node.hex(parents[1]))

    for headerid in cmdutil.extraexport:
        header = cmdutil.extraexportmap[headerid](1, ctx)
        if header is not None:
            fp.write(b'# %s\n' % header)
    fp.write(ctx.description().rstrip())
    fp.write(b"\n\n")

def _touchedbetween(repo, source, dest, match=None):
    touched = set()
    st = repo.status(source, dest, match=match)
    touched.update(st.modified)
    touched.update(st.added)
    touched.update(st.removed)
    return touched

def _commitfiltered(repo, ctx, match, target=None, message=None, user=None,
                    date=None):
    """Recommit ctx with changed files not in match. Return the new
    node identifier, or None if nothing changed.
    """
    base = ctx.p1()
    if target is None:
        target = base
    # ctx
    initialfiles = _touchedbetween(repo, base, ctx)
    if base == target:
        affected = set(f for f in initialfiles if match(f))
        newcontent = set()
    else:
        affected = _touchedbetween(repo, target, ctx, match=match)
        newcontent = _touchedbetween(repo, target, base, match=match)
    # The commit touchs all existing files
    # + all file that needs a new content
    # - the file affected bny uncommit with the same content than base.
    files = (initialfiles - affected) | newcontent
    if not newcontent and files == initialfiles:
        return None

    # Filter copies
    copied = copies.pathcopies(target, ctx)
    copied = dict((dst, src) for dst, src in copied.items()
                  if dst in files)

    def filectxfn(repo, memctx, path, contentctx=ctx, redirect=newcontent):
        if path in redirect:
            return filectxfn(repo, memctx, path, contentctx=target, redirect=())
        if path not in contentctx:
            return None
        fctx = contentctx[path]
        flags = fctx.flags()
        mctx = context.memfilectx(repo, ctx, fctx.path(), fctx.data(),
                                  islink=b'l' in flags,
                                  isexec=b'x' in flags,
                                  copysource=copied.get(path))
        return mctx

    if message is None:
        message = ctx.description()
    if not user:
        user = ctx.user()
    if not date:
        date = ctx.date()
    new = context.memctx(repo,
                         parents=[base.node(), node.nullid],
                         text=message,
                         files=files,
                         filectxfn=filectxfn,
                         user=user,
                         date=date,
                         extra=ctx.extra())
    # commitctx always create a new revision, no need to check
    newid = repo.commitctx(new)
    return newid

@eh.command(
    b'uncommit',
    [(b'a', b'all', None, _(b'uncommit all changes when no arguments given')),
     (b'i', b'interactive', False, _(b'interactive mode to uncommit (EXPERIMENTAL)')),
     (b'r', b'rev', b'', _(b'revert commit content to REV instead'), _(b'REV')),
     (b'', b'revert', False, _(b'discard working directory changes after uncommit')),
     (b'n', b'note', b'', _(b'store a note on uncommit'), _(b'TEXT')),
     ] + commands.walkopts + commitopts + commitopts2 + commitopts3,
    _(b'[OPTION]... [FILE]...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
)
def uncommit(ui, repo, *pats, **opts):
    """move changes from parent revision to working directory

    Changes to selected files in the checked out revision appear again as
    uncommitted changed in the working directory. A new revision
    without the selected changes is created, becomes the checked out
    revision, and obsoletes the previous one.

    The --include option specifies patterns to uncommit.
    The --exclude option specifies patterns to keep in the commit.

    The --rev argument let you change the commit file to a content of another
    revision. It still does not change the content of your file in the working
    directory.

    .. container:: verbose

       The --interactive option lets you select hunks interactively to uncommit.
       You can uncommit parts of file using this option.

    Return 0 if changed files are uncommitted.
    """

    _checknotesize(ui, opts)
    _resolveoptions(ui, opts) # process commitopts3
    interactive = opts.get('interactive')
    wlock = lock = tr = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        wctx = repo[None]
        if len(wctx.parents()) <= 0:
            raise error.Abort(_(b"cannot uncommit null changeset"))
        if len(wctx.parents()) > 1:
            raise error.Abort(_(b"cannot uncommit while merging"))
        old = repo[b'.']
        corerewriteutil.precheck(repo, [repo[b'.'].rev()], action=b'uncommit')
        if len(old.parents()) > 1:
            raise error.Abort(_(b"cannot uncommit merge changeset"))
        oldphase = old.phase()

        rev = None
        if opts.get('rev'):
            rev = scmutil.revsingle(repo, opts.get('rev'))
            ctx = repo[None]
            if ctx.p1() == rev or ctx.p2() == rev:
                raise error.Abort(_(b"cannot uncommit to parent changeset"))

        onahead = old.rev() in repo.changelog.headrevs()
        disallowunstable = not obsolete.isenabled(repo,
                                                  obsolete.allowunstableopt)
        if disallowunstable and not onahead:
            raise error.Abort(_(b"cannot uncommit in the middle of a stack"))

        match = scmutil.match(old, pats, pycompat.byteskwargs(opts))

        # Check all explicitly given files; abort if there's a problem.
        if match.files():
            s = old.status(old.p1(), match, listclean=True)
            eligible = set(s.added) | set(s.modified) | set(s.removed)

            badfiles = set(match.files()) - eligible

            # Naming a parent directory of an eligible file is OK, even
            # if not everything tracked in that directory can be
            # uncommitted.
            if badfiles:
                badfiles -= set([f for f in pathutil.dirs(eligible)])

            uipathfn = scmutil.getuipathfn(repo)

            for f in sorted(badfiles):
                if f in s.clean:
                    hint = _(b"file was not changed in working directory "
                             b"parent")
                elif repo.wvfs.exists(f):
                    hint = _(b"file was untracked in working directory parent")
                else:
                    hint = _(b"file does not exist")

                raise error.Abort(_(b'cannot uncommit "%s"')
                                  % uipathfn(f), hint=hint)

        # Recommit the filtered changeset
        tr = repo.transaction(b'uncommit')
        if interactive:
            opts['all'] = True
            newid = _interactiveuncommit(ui, repo, old, match)
        else:
            newid = None
            includeorexclude = opts.get('include') or opts.get('exclude')
            if (pats or includeorexclude or opts.get('all')):
                if not (opts['message'] or opts['logfile']):
                    opts['message'] = old.description()
                message = cmdutil.logmessage(ui, pycompat.byteskwargs(opts))
                newid = _commitfiltered(repo, old, match, target=rev,
                                        message=message, user=opts.get('user'),
                                        date=opts.get('date'))
            if newid is None:
                raise error.Abort(_(b'nothing to uncommit'),
                                  hint=_(b"use --all to uncommit all files"))

        # metadata to be stored in obsmarker
        metadata = {}
        if opts.get('note'):
            metadata[b'note'] = opts['note']

        replacements = {(old.node(),): [newid]}
        compat.cleanup_nodes(repo, replacements, operation=b"uncommit",
                             metadata=metadata)
        phases.retractboundary(repo, tr, oldphase, [newid])
        if opts.get('revert'):
            merge.clean_update(repo[newid])
        else:
            with repo.dirstate.changing_parents(repo):
                scmutil.movedirstate(repo, repo[newid], match)
        if not repo[newid].files():
            ui.warn(_(b"new changeset is empty\n"))
            ui.status(_(b"(use 'hg prune .' to remove it)\n"))
        tr.close()
    finally:
        lockmod.release(tr, lock, wlock)

def _interactiveuncommit(ui, repo, old, match):
    """ The function which contains all the logic for interactively uncommiting
    a commit. This function makes a temporary commit with the chunks which user
    selected to uncommit. After that the diff of the parent and that commit is
    applied to the working directory and committed again which results in the
    new commit which should be one after uncommitted.
    """

    # create a temporary commit with hunks user selected
    tempnode = _createtempcommit(ui, repo, old, match)

    diffopts = patch.difffeatureopts(repo.ui, whitespace=True)
    diffopts.nodates = True
    diffopts.git = True
    fp = stringio()
    for chunk, label in patch.diffui(repo, tempnode, old.node(), None,
                                     opts=diffopts):
        fp.write(chunk)

    fp.seek(0)
    newnode = _patchtocommit(ui, repo, old, fp)
    # creating obs marker temp -> ()
    obsolete.createmarkers(repo, [(repo[tempnode], ())], operation=b"uncommit")
    return newnode

def _createtempcommit(ui, repo, old, match):
    """ Creates a temporary commit for `uncommit --interative` which contains
    the hunks which were selected by the user to uncommit.
    """

    pold = old.p1()
    # The logic to interactively selecting something copied from
    # cmdutil.revert()
    diffopts = patch.difffeatureopts(repo.ui, whitespace=True)
    diffopts.nodates = True
    diffopts.git = True
    diff = patch.diff(repo, pold.node(), old.node(), match, opts=diffopts)
    originalchunks = patch.parsepatch(diff)
    # XXX: The interactive selection is buggy and does not let you
    # uncommit a removed file partially.
    # TODO: wrap the operations in mercurial/patch.py and mercurial/crecord.py
    # to add uncommit as an operation taking care of BC.
    chunks, opts = cmdutil.recordfilter(
        repo.ui,
        originalchunks,
        match,
        operation=b'discard',
    )
    if not chunks:
        raise error.Abort(_(b"nothing selected to uncommit"))
    fp = stringio()
    for c in chunks:
        c.write(fp)

    fp.seek(0)
    oldnode = node.short(old.node())
    message = b'temporary commit for uncommiting %s' % oldnode
    tempnode = _patchtocommit(ui, repo, old, fp, message)
    return tempnode

def _patchtocommit(ui, repo, old, fp, message=None):
    """ A function which will apply the patch to the working directory and
    make a commit whose parents are same as that of old argument. The message
    argument tells us whether to use the message of the old commit or a
    different message which is passed. Returns the node of new commit made.
    """
    pold = old.p1()
    parents = (old.p1().node(), old.p2().node())
    date = old.date()
    branch = old.branch()
    user = old.user()
    extra = old.extra().copy()
    extra[b'uncommit_source'] = node.short(old.node())

    if not message:
        message = old.description()
    store = patch.filestore()
    try:
        files = set()
        try:
            patch.patchrepo(ui, repo, pold, store, fp, 1, b'',
                            files=files, eolmode=None)
        except patch.PatchError as err:
            raise error.Abort(pycompat.bytestr(err))

        finally:
            del fp

        memctx = context.memctx(repo, parents, message, files=files,
                                filectxfn=store,
                                user=user,
                                date=date,
                                branch=branch,
                                extra=extra)
        newcm = memctx.commit()
    finally:
        store.close()
    return newcm

@eh.command(
    b'fold|squash',
    [(b'r', b'rev', [], _(b"revision to fold"), _(b'REV')),
     (b'', b'exact', None, _(b"only fold specified revisions")),
     (b'', b'from', None, _(b"fold revisions linearly to working copy parent")),
     (b'n', b'note', b'', _(b'store a note on fold'), _(b'TEXT')),
     ] + commitopts + commitopts2 + commitopts3,
    _(b'hg fold [OPTION]... [-r] REV...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
    helpbasic=True,
)
def fold(ui, repo, *revs, **opts):
    """fold multiple revisions into a single one

    With --from, folds all the revisions linearly between the given revisions
    and the parent of the working directory.

    With --exact, folds only the specified revisions while ignoring the
    parent of the working directory. In this case, the given revisions must
    form a linear unbroken chain.

    .. container:: verbose

     Some examples:

     - Fold the current revision with its parent::

         hg fold --from .^

     - Fold all draft revisions with working directory parent::

         hg fold --from 'draft()'

       See :hg:`help phases` for more about draft revisions and
       :hg:`help revsets` for more about the `draft()` keyword

     - Fold revisions between 3 and 6 with the working directory parent::

         hg fold --from 3::6

     - Fold revisions 3 and 4::

        hg fold "3 + 4" --exact

     - Only fold revisions linearly between foo and @::

         hg fold foo::@ --exact
    """
    _checknotesize(ui, opts)
    _resolveoptions(ui, opts)
    revs = list(revs)
    revs.extend(opts['rev'])
    if not revs:
        raise error.Abort(_(b'no revisions specified'))

    revs = scmutil.revrange(repo, revs)

    if opts['from'] and opts['exact']:
        raise error.Abort(_(b'cannot use both --from and --exact'))
    elif opts['from']:
        # Try to extend given revision starting from the working directory
        extrevs = repo.revs(b'(%ld::.) or (.::%ld)', revs, revs)
        discardedrevs = [r for r in revs if r not in extrevs]
        if discardedrevs:
            msg = _(b"cannot fold non-linear revisions")
            hint = _(b"given revisions are unrelated to parent of working"
                     b" directory")
            raise error.Abort(msg, hint=hint)
        revs = extrevs
    elif opts['exact']:
        # Nothing to do; "revs" is already set correctly
        pass
    else:
        raise error.Abort(_(b'must specify either --from or --exact'))

    if not revs:
        raise error.Abort(_(b'specified revisions evaluate to an empty set'),
                          hint=_(b'use different revision arguments'))
    elif len(revs) == 1:
        ui.write_err(_(b'single revision specified, nothing to fold\n'))
        return 1

    # Sort so combined commit message of `hg fold --exact -r . -r .^` is
    # in topological order.
    revs.sort()

    wlock = lock = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()

        root, head, p2 = rewriteutil.foldcheck(repo, revs)

        tr = repo.transaction(b'fold')
        try:
            commitopts = opts.copy()
            allctx = [repo[r] for r in revs]
            targetphase = max(c.phase() for c in allctx)

            if commitopts.get('message') or commitopts.get('logfile'):
                commitopts['edit'] = False
            else:
                msgs = [b"HG: This is a fold of %d changesets." % len(allctx)]
                msgs += [b"HG: Commit message of changeset %d.\n\n%s\n" %
                         (c.rev(), c.description()) for c in allctx]
                commitopts['message'] = b"\n".join(msgs)
                commitopts['edit'] = True

            metadata = {}
            if opts.get('note'):
                metadata[b'note'] = opts['note']

            commitopts = pycompat.byteskwargs(commitopts)
            newid, unusedvariable = rewriteutil.rewrite(repo, root,
                                                        head,
                                                        [root.p1().node(),
                                                         p2.node()],
                                                        commitopts=commitopts)
            phases.retractboundary(repo, tr, targetphase, [newid])
            replacements = {tuple(ctx.node() for ctx in allctx): [newid]}
            compat.cleanup_nodes(repo, replacements, operation=b"fold",
                                 metadata=metadata)
            tr.close()
        finally:
            tr.release()
        ui.status(b'%i changesets folded\n' % len(revs))
        if repo[b'.'].rev() in revs:
            compat.hg_update(repo, newid)
    finally:
        lockmod.release(lock, wlock)

@eh.command(
    b'metaedit',
    [(b'r', b'rev', [], _(b"revision to edit"), _(b'REV')),
     (b'', b'fold', None, _(b"also fold specified revisions into one")),
     (b'n', b'note', b'', _(b'store a note on metaedit'), _(b'TEXT')),
     ] + commitopts + commitopts2 + commitopts3,
    _(b'hg metaedit [OPTION]... [[-r] REV]...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
)
def metaedit(ui, repo, *revs, **opts):
    """edit commit information

    Edits the commit information for the specified revisions. By default, edits
    commit information for the working directory parent.

    With --fold, also folds multiple revisions into one if necessary. In this
    case, the given revisions must form a linear unbroken chain.

    .. container:: verbose

     Some examples:

     - Edit the commit message for the working directory parent::

         hg metaedit

     - Change the username for the working directory parent::

         hg metaedit --user 'New User <new-email@example.com>'

     - Combine all draft revisions that are ancestors of foo but not of @ into
       one::

         hg metaedit --fold 'draft() and only(foo,@)'

       See :hg:`help phases` for more about draft revisions, and
       :hg:`help revsets` for more about the `draft()` and `only()` keywords.
    """
    _checknotesize(ui, opts)
    _resolveoptions(ui, opts)
    revs = list(revs)
    revs.extend(opts['rev'])
    if not revs:
        if opts['fold']:
            raise error.Abort(_(b'revisions must be specified with --fold'))
        revs = [b'.']

    with repo.wlock(), repo.lock():
        revs = scmutil.revrange(repo, revs)
        if not opts['fold'] and len(revs) > 1:
            # TODO: handle multiple revisions. This is somewhat tricky because
            # if we want to edit a series of commits:
            #
            #   a ---- b ---- c
            #
            # we need to rewrite a first, then directly rewrite b on top of the
            # new a, then rewrite c on top of the new b. So we need to handle
            # revisions in topological order.
            raise error.Abort(_(b'editing multiple revisions without --fold is '
                                b'not currently supported'))

        if opts['fold']:
            root, head, p2 = rewriteutil.foldcheck(repo, revs)
        else:
            if repo.revs(b"%ld and public()", revs):
                raise error.Abort(_(b'cannot edit commit information for public '
                                    b'revisions'))
            newunstable = rewriteutil.disallowednewunstable(repo, revs)
            if newunstable:
                msg = _(b'cannot edit commit information in the middle'
                        b' of a stack')
                hint = _(b'%s will become unstable and new unstable changes'
                         b' are not allowed')
                hint %= repo[newunstable.first()]
                raise error.Abort(msg, hint=hint)
            root = head = repo[revs.first()]
            p2 = root.p2()

        wctx = repo[None]
        p1 = wctx.p1()
        tr = repo.transaction(b'metaedit')
        newp1 = None
        try:
            commitopts = opts.copy()
            allctx = [repo[r] for r in revs]
            targetphase = max(c.phase() for c in allctx)

            if commitopts.get('message') or commitopts.get('logfile'):
                commitopts['edit'] = False
            else:
                if opts['fold']:
                    msgs = [b"HG: This is a fold of %d changesets." % len(allctx)]
                    msgs += [b"HG: Commit message of changeset %d.\n\n%s\n" %
                             (c.rev(), c.description()) for c in allctx]
                else:
                    msgs = [head.description()]
                commitopts['message'] = b"\n".join(msgs)
                commitopts['edit'] = True

            if not commitopts['fold'] and not commitopts['date']:
                commitopts['date'] = root.date()
            commitopts = pycompat.byteskwargs(commitopts)
            newid, created = rewriteutil.rewrite(repo, root, head,
                                                 [root.p1().node(),
                                                  p2.node()],
                                                 commitopts=commitopts)
            if created:
                if p1.rev() in revs:
                    newp1 = newid
                # metadata to be stored on obsmarker
                metadata = {}
                if opts.get('note'):
                    metadata[b'note'] = opts['note']

                phases.retractboundary(repo, tr, targetphase, [newid])
                replacements = {tuple(ctx.node() for ctx in allctx): (newid,)}
                compat.cleanup_nodes(repo, replacements, operation=b"metaedit",
                                     metadata=metadata)
            else:
                ui.status(_(b"nothing changed\n"))
            tr.close()
        finally:
            tr.release()

        if opts['fold']:
            ui.status(b'%i changesets folded\n' % len(revs))
        if newp1 is not None:
            compat.hg_update(repo, newp1)

metadataopts = [
    (b'd', b'date', b'',
     _(b'record the specified date in metadata'), _(b'DATE')),
    (b'u', b'user', b'',
     _(b'record the specified user in metadata'), _(b'USER')),
]

def _getmetadata(**opts):
    metadata = {}
    date = opts.get('date')
    user = opts.get('user')
    if date:
        metadata[b'date'] = b'%i %i' % dateutil.parsedate(date)
    if user:
        metadata[b'user'] = user
    return metadata

@eh.command(
    b'prune|obsolete',
    [(b'n', b'new', [], _(b"successor changeset (DEPRECATED)")),
     (b's', b'successor', [], _(b"successor changeset"), _(b'REV')),
     (b'r', b'rev', [], _(b"revisions to prune"), _(b'REV')),
     (b'k', b'keep', None, _(b"does not modify working copy during prune")),
     (b'n', b'note', b'', _(b'store a note on prune'), _(b'TEXT')),
     (b'', b'pair', False, _(b"record a pairing, such as a rebase or divergence resolution "
                             b"(pairing multiple precursors to multiple successors)")),
     (b'', b'biject', False, _(b"alias to --pair (DEPRECATED)")),
     (b'', b'fold', False,
      _(b"record a fold (multiple precursors, one successor)")),
     (b'', b'split', False,
      _(b"record a split (one precursor, multiple successors)")),
     (b'B', b'bookmark', [], _(b"remove revs only reachable from given"
                               b" bookmark"), _(b'BOOKMARK'))] + metadataopts,
    _(b'[OPTION]... [-r] REV...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
    helpbasic=True,
)
# XXX -U  --noupdate option to prevent wc update and or bookmarks update ?
def cmdprune(ui, repo, *revs, **opts):
    """mark changesets as obsolete or succeeded by another changeset

    Pruning changesets marks them obsolete, hiding them from the
    history log, provided they have no descendants. Otherwise, all
    such descendants that aren't themselves obsolete become
    "unstable". Use :hg:`evolve` to handle this situation.

    When you prune the parent of your working copy, Mercurial updates the working
    copy to a non-obsolete parent.

    You can use ``-s/--successor`` to tell Mercurial that a newer version
    (successor) of the pruned changeset exists. Mercurial records successor
    revisions in obsolescence markers.

    If you prune a single revision and specify multiple revisions in
    ``-s/--successor``, you are recording a "split" and must acknowledge it by
    passing ``--split``. Similarly, when you prune multiple changesets with a
    single successor, you must pass the ``--fold`` option.

    If you want to supersede multiple revisions at the same time, use the
    ``--pair`` option to pair the pruned precursor and successor changesets.
    This is commonly useful for resolving history divergence, or when someone
    else edits history without obsolescence enabled.

    .. container:: verbose

        ``hg prune A::B -s C::D --pair`` will mark all revisions in the A::B
        range as superseded by the revisions in C::D. Both revsets need to have
        the same number of changesets.
    """
    _checknotesize(ui, opts)
    revs = scmutil.revrange(repo, list(revs) + opts.get('rev'))
    succs = opts['new'] + opts['successor']
    bookmarks = set(opts.get('bookmark'))
    metadata = _getmetadata(**opts)
    biject = opts.get('pair') or opts.get('biject')
    fold = opts.get('fold')
    split = opts.get('split')

    cmdutil.check_at_most_one_arg(opts, 'pair', 'fold', 'split')
    cmdutil.check_at_most_one_arg(opts, 'biject', 'fold', 'split')

    if bookmarks:
        reachablefrombookmark = rewriteutil.reachablefrombookmark
        repomarks, revs = reachablefrombookmark(repo, revs, bookmarks)
        if not revs:
            # no revisions to prune - delete bookmark immediately
            rewriteutil.deletebookmark(repo, repomarks, bookmarks)

    if not revs:
        raise error.InputError(_(b'no revisions specified to prune'))

    wlock = lock = tr = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        corerewriteutil.precheck(repo, revs, b'prune', check_divergence=bool(succs))
        tr = repo.transaction(b'prune')
        # defines pruned changesets
        precs = []
        revs.sort()
        for p in revs:
            cp = repo[p]
            precs.append(cp)
        if not precs:
            raise error.Abort(b'nothing to prune')

        # defines successors changesets
        sucs = scmutil.revrange(repo, succs)
        sucs.sort()
        sucs = tuple(repo[n] for n in sucs)
        if not biject and len(sucs) > 1 and len(precs) > 1:
            msg = b"cannot use multiple successors for multiple precursors"
            hint = _(b"use --pair to mark a series as a replacement"
                     b" for another")
            raise error.InputError(msg, hint=hint)
        elif biject and len(sucs) != len(precs):
            msg = b"cannot use %d successors for %d precursors"\
                % (len(sucs), len(precs))
            raise error.InputError(msg)
        elif (len(precs) == 1 and len(sucs) > 1) and not split:
            msg = b"please add --split if you want to do a split"
            raise error.InputError(msg)
        elif len(sucs) == 1 and len(precs) > 1 and not fold:
            msg = b"please add --fold if you want to do a fold"
            raise error.InputError(msg)
        elif biject:
            replacements = {(p.node(),): [s.node()] for p, s in zip(precs, sucs)}
        else:
            replacements = {(p.node(),): [s.node() for s in sucs] for p in precs}

        wdp = repo[b'.']

        if wdp in precs:
            if len(sucs) == 1 and len(precs) == 1:
                # '.' killed, so update to the successor
                newnode = sucs[0]
            elif biject:
                # find the exact successor of '.'
                newnode = sucs[precs.index(wdp)]
            else:
                # update to an unkilled parent
                newnode = wdp

                while newnode in precs or newnode.obsolete():
                    newnode = newnode.p1()
        else:
            # no need to update anywhere as wdp is not related to revs
            # being pruned
            newnode = wdp

        if newnode.node() != wdp.node():
            if opts.get('keep', False):
                # This is largely the same as the implementation in
                # strip.stripcmd(). We might want to refactor this somewhere
                # common at some point.

                # only reset the dirstate for files that would actually change
                # between the working context and uctx
                descendantrevs = repo.revs(b"%d::." % newnode.rev())
                changedfiles = []
                for rev in descendantrevs:
                    # blindly reset the files, regardless of what actually
                    # changed
                    changedfiles.extend(repo[rev].files())

                # reset files that only changed in the dirstate too
                dirstate = repo.dirstate
                dirchanges = (
                    f
                    for f in dirstate
                    if not dirstate.get_entry(f).maybe_clean
                )
                changedfiles.extend(dirchanges)
                with repo.dirstate.changing_parents(repo):
                    repo.dirstate.rebuild(newnode.node(), newnode.manifest(),
                                          changedfiles)
                dirstate.write(tr)
            else:
                bookactive = repo._activebookmark
                # Active bookmark that we don't want to delete (with -B option)
                # we deactivate and move it before the update and reactivate it
                # after
                movebookmark = bookactive and not bookmarks
                if movebookmark:
                    bookmarksmod.deactivate(repo)
                    bmchanges = [(bookactive, newnode.node())]
                    repo._bookmarks.applychanges(repo, tr, bmchanges)
                commands.update(ui, repo, newnode.hex())
                ui.status(_(b'working directory is now at %s\n')
                          % ui.label(bytes(newnode), b'evolve.node'))
                if movebookmark:
                    bookmarksmod.activate(repo, bookactive)

        # update bookmarks
        if bookmarks:
            rewriteutil.deletebookmark(repo, repomarks, bookmarks)

        # store note in metadata
        if opts.get('note'):
            metadata[b'note'] = opts['note']

        precrevs = (precursor.rev() for precursor in precs)
        moves = {}
        for ctx in repo.unfiltered().set(b'bookmark() and %ld', precrevs):
            # used to be:
            #
            #   ldest = list(repo.set('max((::%d) - obsolete())', ctx))
            #   if ldest:
            #      c = ldest[0]
            #
            # but then revset took a lazy arrow in the knee and became much
            # slower. The new forms makes as much sense and a much faster.
            for dest in ctx.ancestors():
                if not dest.obsolete() and (dest.node(),) not in replacements:
                    moves[ctx.node()] = dest.node()
                    break
        if len(sucs) == 1 and len(precs) > 1 and fold:
            replacements = {tuple(p.node() for p in precs): [s.node() for s in sucs]}
        compat.cleanup_nodes(repo, replacements, operation=b"prune", moves=moves,
                             metadata=metadata)

        # informs that changeset have been pruned
        ui.status(_(b'%i changesets pruned\n') % len(precs))

        tr.close()
    finally:
        lockmod.release(tr, lock, wlock)

@eh.command(
    b'split',
    [(b'i', b'interactive', True, _(b'use interactive mode')),
     (b'r', b'rev', [], _(b"revision to split"), _(b'REV')),
     (b'n', b'note', b'', _(b"store a note on split"), _(b'TEXT')),
     ] + commitopts + commitopts2 + commitopts3,
    _(b'hg split [OPTION]... [-r REV] [FILE]...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
    helpbasic=True,
)
def cmdsplit(ui, repo, *pats, **opts):
    """split a changeset into smaller changesets

    By default, split the current revision by prompting for all its hunks to be
    redistributed into new changesets.

    Use --rev to split a given changeset instead.

    If file patterns are specified only files matching these patterns will be
    considered to be split in earlier changesets. The files that doesn't match
    will be gathered in the last changeset.
    """
    _checknotesize(ui, opts)
    _resolveoptions(ui, opts)
    tr = wlock = lock = None
    newcommits = []
    iselect = opts.pop('interactive')

    revs = opts.get('rev')
    if not revs:
        revarg = b'.'
    elif len(revs) == 1:
        revarg = revs[0]
    else:
        # XXX --rev often accept multiple value, it seems safer to explicitly
        # complains here instead of just taking the last value.
        raise error.Abort(_(b'more than one revset is given'))

    # Save the current branch to restore it in the end
    savedbranch = repo.dirstate.branch()

    try:
        wlock = repo.wlock()
        lock = repo.lock()
        ctx = scmutil.revsingle(repo, revarg)
        rev = ctx.rev()
        compat.bail_if_changed(repo)
        corerewriteutil.precheck(repo, [rev], action=b'split')
        tr = repo.transaction(b'split')
        # make sure we respect the phase while splitting
        overrides = {(b'phases', b'new-commit'): ctx.phase()}

        if len(ctx.parents()) > 1:
            raise error.Abort(_(b"cannot split merge commits"))
        prev = ctx.p1()
        bmupdate = rewriteutil.bookmarksupdater(repo, ctx.node(), tr)
        bookactive = repo._activebookmark
        if bookactive is not None:
            b = ui.label(repo._activebookmark, b'bookmarks')
            ui.status(_(b"(leaving bookmark %s)\n") % b)
        bookmarksmod.deactivate(repo)

        # Prepare the working directory
        rewriteutil.presplitupdate(repo, ui, prev, ctx)

        def haschanges(matcher=None):
            st = repo.status(match=matcher)
            return st.modified or st.added or st.removed or st.deleted
        msg = (b"HG: This is the original pre-split commit message. "
               b"Edit it as appropriate.\n\n")
        msg += ctx.description()
        opts['message'] = msg
        opts['edit'] = True
        if not opts['user']:
            opts['user'] = ctx.user()

        # Set the right branch
        # XXX-TODO: Find a way to set the branch without altering the dirstate
        repo.dirstate.setbranch(ctx.branch(), repo.currenttransaction())

        if pats:
            # refresh the wctx used for the matcher
            matcher = scmutil.match(repo[None], pats)
        else:
            matcher = scmutil.matchall(repo)

        while haschanges():

            if haschanges(matcher):
                if iselect:
                    with repo.ui.configoverride(overrides, b'split'):
                        cmdutil.dorecord(ui, repo, commands.commit, b'commit',
                                         False, cmdutil.recordfilter, *pats,
                                         **opts)
                    # TODO: Does no seem like the best way to do this
                    # We should make dorecord return the newly created commit
                    newcommits.append(repo[b'.'])
                elif not pats:
                    msg = _(b"no files of directories specified")
                    hint = _(b"do you want --interactive")
                    raise error.Abort(msg, hint=hint)
                else:
                    with repo.ui.configoverride(overrides, b'split'):
                        commands.commit(ui, repo, *pats, **opts)
                    newcommits.append(repo[b'.'])
            if pats:
                # refresh the wctx used for the matcher
                matcher = scmutil.match(repo[None], pats)
            else:
                matcher = scmutil.matchall(repo)

            if haschanges(matcher):
                nextaction = None
                while nextaction is None:
                    nextaction = ui.prompt(b'continue splitting? [Ycdq?]', default=b'y')
                    if nextaction == b'c':
                        with repo.ui.configoverride(overrides, b'split'):
                            commands.commit(ui, repo, **opts)
                        newcommits.append(repo[b'.'])
                        break
                    elif nextaction == b'q':
                        raise error.Abort(_(b'user quit'))
                    elif nextaction == b'd':
                        # TODO: We should offer a way for the user to confirm
                        # what is the remaining changes, either via a separate
                        # diff action or by showing the remaining and
                        # prompting for confirmation
                        ui.status(_(b'discarding remaining changes\n'))
                        target = newcommits[-1]
                        args = []
                        kwargs = {}
                        if pats:
                            status = repo.status(match=matcher)
                            dirty = set()
                            dirty.update(status.modified)
                            dirty.update(status.added)
                            dirty.update(status.removed)
                            dirty.update(status.deleted)
                            args += sorted(dirty)
                        else:
                            kwargs[r'all'] = True
                        cmdutil.revert(ui, repo, repo[target], *args, **kwargs)
                    elif nextaction == b'?':
                        nextaction = None
                        ui.write(_(b"y - yes, continue selection\n"))
                        ui.write(_(b"c - commit, select all remaining changes\n"))
                        ui.write(_(b"d - discard, discard remaining changes\n"))
                        ui.write(_(b"q - quit, abort the split\n"))
                        ui.write(_(b"? - ?, display help\n"))
                else:
                    continue
                break # propagate the previous break
            else:
                ui.status(_(b"no more changes to split\n"))
                if haschanges():
                    # XXX: Should we show a message for informing the user
                    # that we create another commit with remaining changes?
                    with repo.ui.configoverride(overrides, b'split'):
                        commands.commit(ui, repo, **opts)
                    newcommits.append(repo[b'.'])
        if newcommits:
            tip = repo[newcommits[-1]]
            bmupdate(tip.node())
            if bookactive is not None:
                bookmarksmod.activate(repo, bookactive)
            metadata = {}
            if opts.get('note'):
                metadata[b'note'] = opts['note']
            obsolete.createmarkers(repo, [(repo[rev], newcommits)],
                                   metadata=metadata, operation=b"split")
        tr.close()
    finally:
        # Restore the old branch
        repo.dirstate.setbranch(savedbranch, repo.currenttransaction())

        lockmod.release(tr, lock, wlock)

@eh.command(
    b'touch',
    [(b'r', b'rev', [], _(b'revision to update'), _(b'REV')),
     (b'n', b'note', b'', _(b'store a note on touch'), _(b'TEXT')),
     (b'D', b'duplicate', False,
      b'do not mark the new revision as successor of the old one'),
     (b'A', b'allowdivergence', False,
      b'mark the new revision as successor of the old one potentially creating '
      b'divergence')],
    # allow to choose the seed ?
    _(b'[OPTION]... [-r] REV...'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
)
def touch(ui, repo, *revs, **opts):
    """create successors identical to their predecessors but the changeset ID

    This is used to "resurrect" changesets
    """
    _checknotesize(ui, opts)
    revs = list(revs)
    revs.extend(opts['rev'])
    if not revs:
        revs = [b'.']
    revs = scmutil.revrange(repo, revs)
    if not revs:
        ui.write_err(b'no revision to touch\n')
        return 1

    duplicate = opts['duplicate']
    if not duplicate:
        # Override allowdivergence=true because we'll do our own checking later
        # instead
        overrides = {(b'experimental', b'evolution.allowdivergence'): b"true"}
        with ui.configoverride(overrides, b'touch'):
            corerewriteutil.precheck(repo, revs, b'touch')
    display = utility.short_ctx_displayer(ui, repo, b'touch')
    with repo.wlock(), repo.lock(), repo.transaction(b'touch'):
        touchnodes(ui, repo, revs, display, **opts)

def touchnodes(ui, repo, revs, displayer, **opts):
    duplicate = opts['duplicate']
    allowdivergence = opts['allowdivergence']
    revs.sort() # ensure parent are run first
    newmapping = {}
    for r in revs:
        ctx = repo[r]
        extra = ctx.extra().copy()
        extra[b'__touch-noise__'] = b'%d' % random.randint(0, 0xffffffff)
        # search for touched parent
        p1 = ctx.p1().node()
        p2 = ctx.p2().node()
        p1 = newmapping.get(p1, p1)
        p2 = newmapping.get(p2, p2)

        if not (duplicate or allowdivergence):
            if precheck_contentdiv(repo, ctx):
                displayer(ctx)
                index = ui.promptchoice(
                    _(b"reviving this changeset will create divergence"
                      b" unless you make a duplicate.\n(a)llow divergence or"
                      b" (d)uplicate the changeset? $$ &Allowdivergence $$ "
                      b"&Duplicate"), 0)
                choice = [b'allowdivergence', b'duplicate'][index]
                if choice == b'duplicate':
                    duplicate = True

        extradict = {b'extra': extra}
        new, unusedvariable = rewriteutil.rewrite(repo, ctx, ctx,
                                                  [p1, p2],
                                                  commitopts=extradict)
        # store touched version to help potential children
        newmapping[ctx.node()] = new

        if not duplicate:
            metadata = {}
            if opts.get('note'):
                metadata[b'note'] = opts['note']
            obsolete.createmarkers(repo, [(ctx, (repo[new],))],
                                   metadata=metadata, operation=b"touch")
        tr = repo.currenttransaction()
        phases.retractboundary(repo, tr, ctx.phase(), [new])
        if ctx in repo[None].parents():
            with repo.dirstate.changing_parents(repo):
                repo.dirstate.setparents(new, node.nullid)

@eh.command(
    b'pick|grab',
    [(b'r', b'rev', b'', _(b'revision to pick'), _(b'REV')),
     (b'c', b'continue', False, b'continue interrupted pick'),
     (b'a', b'abort', False, b'abort interrupted pick'),
     ] + mergetoolopts,
    _(b'[OPTION]... [-r] REV'),
    helpcategory=registrar.command.CATEGORY_CHANGE_MANAGEMENT,
)
def cmdpick(ui, repo, *revs, **opts):
    """move a commit onto the working directory parent and update to it.

    The resulting changeset will have the current active topic. If there's no
    active topic set, the resulting changeset will also not have any topic.
    """

    cont = opts.get('continue')
    abort = opts.get('abort')

    if cont and abort:
        raise error.Abort(_(b"cannot specify both --continue and --abort"))

    revs = list(revs)
    if opts.get('rev'):
        revs.append(opts['rev'])

    with repo.wlock(), repo.lock():
        pickstate = state.cmdstate(repo, path=b'pickstate')
        pctx = repo[b'.']

        if cont:
            if revs:
                raise error.Abort(_(b"cannot specify both --continue and "
                                    b"revision"))
            if not pickstate:
                raise error.StateError(_(b"no interrupted pick state exists"))

            pickstate.load()
            orignode = pickstate[b'orignode']
            origctx = repo[orignode]

        elif abort:
            return abortpick(ui, repo, pickstate)
        else:
            compat.bail_if_changed(repo)
            revs = scmutil.revrange(repo, revs)
            if len(revs) > 1:
                raise error.Abort(_(b"specify just one revision"))
            elif not revs:
                raise error.Abort(_(b"empty revision set"))

            origctx = repo[revs.first()]

            if origctx in pctx.ancestors() or origctx.node() == pctx.node():
                raise error.Abort(_(b"cannot pick an ancestor revision"))

            corerewriteutil.precheck(repo, [origctx.rev()], b'pick')

            ui.status(_(b'picking %d:%s "%s"\n') %
                      (origctx.rev(), origctx,
                       origctx.description().split(b"\n", 1)[0]))
            overrides = {(b'ui', b'forcemerge'): opts.get('tool', b'')}
            with ui.configoverride(overrides, b'pick'):
                stats = merge.graft(repo, origctx, origctx.p1(),
                                    [b'local', b'destination'])
            if stats.unresolvedcount:
                pickstate.addopts({b'orignode': origctx.node(),
                                   b'oldpctx': pctx.node()})
                pickstate.save()
                raise error.InterventionRequired(_(b"unresolved merge conflicts"
                                                   b" (see hg help resolve)"))
        return _dopick(ui, repo, pickstate, origctx)

def _dopick(ui, repo, pickstate, origctx):
    """shared logic for performing or continuing a pick"""
    overrides = {
        (b'phases', b'new-commit'): origctx.phase(),
        (b'_internal', b'topic-source'): b'local',
    }
    new_desc = evolvecmd._rewrite_commit_message_hashes(repo,
                                                        origctx.description())
    with repo.ui.configoverride(overrides, b'pick'):
        newnode = repo.commit(text=new_desc, user=origctx.user(),
                              date=origctx.date(), extra=origctx.extra())
    repo.dirstate.setbranch(origctx.branch(), repo.currenttransaction())

    if pickstate:
        pickstate.delete()
    if newnode is None:
        replacements = {(origctx.node(),): []}
    else:
        newctx = repo[newnode]
        replacements = {(origctx.node(),): [newctx.node()]}
    compat.cleanup_nodes(repo, replacements, operation=b"pick")

    if newnode is None:
        ui.warn(_(b"note: picking %d:%s created no changes to commit\n") %
                (origctx.rev(), origctx))
        return 0

    return 0

def hgcontinuepick(ui, repo):
    """logic to continue pick using 'hg continue'"""
    with repo.wlock(), repo.lock():
        pickstate = state.cmdstate(repo, path=b'pickstate')
        pickstate.load()
        orignode = pickstate[b'orignode']
        origctx = repo[orignode]
        return _dopick(ui, repo, pickstate, origctx)

def abortpick(ui, repo, pickstate, abortcmd=False):
    """logic to abort pick"""
    if not pickstate and not abortcmd:
        raise error.StateError(_(b"no interrupted pick state exists"))
    pickstate.load()
    pctxnode = pickstate[b'oldpctx']
    merge.clean_update(repo[pctxnode])
    pickstate.delete()
    ui.status(_(b'pick aborted\n'))
    ui.status(_(b'working directory is now at %s\n')
              % node.short(pctxnode))
    return 0

def hgabortpick(ui, repo):
    """logic to abort pick using 'hg abort'"""
    with repo.wlock(), repo.lock():
        pickstate = state.cmdstate(repo, path=b'pickstate')
        return abortpick(ui, repo, pickstate, abortcmd=True)

@eh.command(
    b'fixup|fix-up',
    [
        (b'r', b'rev', b'', _(b'revision to amend'), _(b'REV')),
        (b'c', b'continue', False, _(b'continue an interrupted fixup')),
        (b'', b'abort', False, _(b'abort an interrupted fixup')),
    ],
    _(b'[OPTION]... [-r] REV'),
    helpcategory=registrar.command.CATEGORY_COMMITTING,
    helpbasic=True,
)
def fixup(ui, repo, node=None, **opts):
    """add working directory changes to an arbitrary revision

    A new changeset will be created, superseding the one specified. The new
    changeset will combine working directory changes with the changes in the
    target revision.

    This operation requires the working directory changes to be relocated onto
    the target revision, which might result in merge conflicts.

    If fixup is interrupted to manually resolve a conflict, it can be continued
    with --continue/-c, or aborted with --abort.

    Note that this command is fairly new and its behavior is still
    experimental. For example, the working copy will be left on a temporary,
    obsolete commit containing the fixed-up changes after the operation. This
    might change in the future.

    Returns 0 on success, 1 if nothing changed.
    """
    cmdutil.check_at_most_one_arg(opts, 'continue', 'abort')
    with repo.wlock(), repo.lock():
        return _perform_fixup(ui, repo, node, **opts)

def _perform_fixup(ui, repo, node, **opts):
    contopt = opts.get('continue')
    abortopt = opts.get('abort')
    if node or opts.get('rev'):
        if contopt:
            raise error.InputError(_(b'cannot specify a revision with --continue'))
        if abortopt:
            raise error.InputError(_(b'cannot specify a revision with --abort'))
    # state file for --continue/--abort cases
    fixup_state = state.cmdstate(repo, b'fixup-state')
    if contopt:
        if not fixup_state.exists():
            raise error.StateError(_(b'no interrupted fixup to continue'))
        fixup_state.load()
        return continuefixup(ui, repo, fixup_state)
    if abortopt:
        if not fixup_state.exists():
            raise error.StateError(_(b'no interrupted fixup to abort'))
        fixup_state.load()
        return abortfixup(ui, repo, fixup_state)

    if node and opts.get('rev'):
        raise error.InputError(_(b'please specify just one revision'))
    if not node:
        node = opts.get('rev')
    if not node:
        raise error.InputError(_(b'please specify a revision to fixup'))
    target_ctx = scmutil.revsingle(repo, node)

    fixup_state.addopts({
        b'bookmarkchanges': [],
        b'startnode': repo[b'.'].node(),
    })

    tr = repo.transaction(b'fixup')
    with util.acceptintervention(tr):
        overrides = {(b'ui', b'allowemptycommit'): False}
        with repo.ui.configoverride(overrides, b'fixup'):
            tempnode = repo.commit(
                text=b'temporary fixup commit', user=opts.get(b'user'),
                date=opts.get(b'date'))
            if tempnode is None:
                ui.status(_(b"nothing changed\n"))
                return 1
        fixup_state[b'tempnode'] = tempnode
        # XXX: storing 'tempnode' should be enough, but 'current'
        # is used by _relocate() logic
        fixup_state[b'current'] = tempnode
        fixup_state[b'target'] = target_ctx.node()
        with state.saver(fixup_state):
            # relocate temporary node to target revision
            newnode = evolvecmd._relocate(
                repo, repo[tempnode], target_ctx, fixup_state, update=False
            )
        # fold the two changesets
        revs = (repo[newnode].rev(), target_ctx.rev())
        root, head, p2 = rewriteutil.foldcheck(repo, revs)

        allctx = [repo[r] for r in revs]
        commitopts = {b'edit': False, b'message': target_ctx.description()}
        newid, unusedvariable = rewriteutil.rewrite(
            repo, root, head, [root.p1().node(), p2.node()],
            commitopts=commitopts
        )
        phases.retractboundary(repo, tr, target_ctx.phase(), [newid])
        replacements = {tuple(ctx.node() for ctx in allctx): [newid]}
        compat.cleanup_nodes(repo, replacements, operation=b'fixup')
        fixup_state.delete()
        merge.update(repo.unfiltered()[tempnode])
        return 0

def continuefixup(ui, repo, fixup_state):
    """logic for handling of `hg fixup --continue`"""
    target_node = fixup_state[b'target']
    tempnode = fixup_state[b'tempnode']
    target_ctx = repo[target_node]
    tr = repo.transaction(b'fixup')
    with util.acceptintervention(tr):
        newnode = evolvecmd._completerelocation(ui, repo, fixup_state)
        current = repo[fixup_state[b'current']]
        obsolete.createmarkers(repo, [(current, (repo[newnode],))],
                               operation=b'fixup')
        # fold the two changesets
        revs = (repo[newnode].rev(), target_ctx.rev())
        root, head, p2 = rewriteutil.foldcheck(repo, revs)

        allctx = [repo[r] for r in revs]
        commitopts = {b'edit': False, b'message': target_ctx.description()}
        newid, unusedvariable = rewriteutil.rewrite(
            repo, root, head, [root.p1().node(), p2.node()],
            commitopts=commitopts
        )
        phases.retractboundary(repo, tr, target_ctx.phase(), [newid])
        replacements = {tuple(ctx.node() for ctx in allctx): [newid]}
        compat.cleanup_nodes(repo, replacements, operation=b'fixup')
        fixup_state.delete()
        merge.update(repo.unfiltered()[tempnode])
        return 0

def hgcontinuefixup(ui, repo):
    """logic for handling `hg continue' for fixup"""
    with repo.wlock(), repo.lock():
        fixup_state = state.cmdstate(repo, b'fixup-state')
        fixup_state.load()
        return continuefixup(ui, repo, fixup_state)

def abortfixup(ui, repo, fixup_state):
    """logic for handling of `hg fixup --abort`"""
    with repo.wlock(), repo.lock():
        startnode = fixup_state[b'startnode']
        tempnode = fixup_state[b'tempnode']
        tempctx = repo[tempnode]
        merge.clean_update(repo[startnode])

        stats = merge.graft(repo, tempctx, tempctx.p1(), [b'graft', b'fixup'])
        # conflict is not possible, since grafting changes from descendant
        assert not stats.unresolvedcount
        repair.strip(ui, repo, [tempnode], backup=False)

    pctx = repo[b'.']
    ui.status(_(b'fixup aborted\n'))
    ui.status(_(b'working directory is now at %s\n') % pctx)
    fixup_state.delete()
    return 0

def hgabortfixup(ui, repo):
    """logic to abort fixup using 'hg abort'"""
    with repo.wlock(), repo.lock():
        fixup_state = state.cmdstate(repo, path=b'fixup-state')
        fixup_state.load()
        return abortfixup(ui, repo, fixup_state)
