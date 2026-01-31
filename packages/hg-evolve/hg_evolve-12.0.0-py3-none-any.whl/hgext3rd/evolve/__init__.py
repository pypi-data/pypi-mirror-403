# Copyright 2011 Peter Arrenbrecht <peter.arrenbrecht@gmail.com>
#                Logilab SA        <contact@logilab.fr>
#                Pierre-Yves David <pierre-yves.david@ens-lyon.org>
#                Patrick Mezard <patrick@mezard.eu>
#                Octobus <contact@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
"""extends Mercurial feature related to Changeset Evolution

This extension:

- provides several commands to mutate history and deal with resulting issues,
- enable the changeset-evolution feature for Mercurial,
- improves some aspect of the early implementation in Mercurial core,

While many feature related to changeset evolution are directly handled by core
this extensions contains significant additions recommended to any user of
changeset evolution.

With the extension various evolution events will display warning (new unstable
changesets, obsolete working copy parent, improved error when accessing hidden
revision, etc).

In addition, the extension contains better discovery protocol for obsolescence
markers. This means less obs-markers will have to be pushed and pulled around,
speeding up such operation.

Some improvement and bug fixes available in newer version of Mercurial are also
backported to older version of Mercurial by this extension. Some older
experimental protocols are also supported for a longer time in the extension to
help people transitioning. (The extension is currently compatible down to
Mercurial version 6.7).

New Config::

    [experimental]
    # Set to control the behavior when pushing draft changesets to a publishing
    # repository. Possible value:
    # * ignore: current core behavior (default)
    # * warn: proceed with the push, but issue a warning
    # * abort: abort the push
    auto-publish = ignore

    # For some large repositories with few markers, the current method for
    # obsolescence marker discovery can get in the way. You can disable it by
    # setting the following configuration option to "no". Then all pushes and
    # pulls will re-exchange all markers every time.
    evolution.obsdiscovery = yes

Obsolescence Markers Discovery
------------------------------

The evolve extension containts an experimental new protocol to discover common
markers between local and remote repositories.

"Large" repositories (hundreds of thousands) will take some time to warm the
necessary cache. Some key algorithm has a naive implementation that can result
in large memory or CPU Load.

The following config controls the new protocol::

  [experimental]

  # enable new discovery protocol
  # default to "yes"
  obshashrange = yes

  # control cache warming at the end of transaction
  #   yes:  warm all caches at the end of each transaction
  #         (recommended for server),
  #   off:  warm no caches at the end of transaction,
  #         (no cache overhead during transaction,
  #          but cache will be warm from scratch on usage)
  #   auto: warm cache at the end of server side transaction(ie: push)
  #         (default).
  obshashrange.warm-cache = 'auto'

When you switch to using this protocol, we recommand that you explicitly warm
cache for your server side repositories.::

  $ hg debugupdatecache

It is recommended to enable the blackbox extension. It gathers useful data about
the experiment. It is shipped with Mercurial so no extra install is needed::

    [extensions]
    blackbox =

Finally one more option is available to help tame the experimental
implementation of some of the algorithms::

    [experimental]
    # automatically disable obshashrange related computation and capabilities
    # if the repository has more than N revisions.  This is meant to help large
    # server deployment to enable the feature on smaller repositories while
    # ensuring no large repository will get affected.
    obshashrange.max-revs = 100000 # default is None

For very large repositories, it might be useful to disable obsmarkers discovery
(make sure you follow release announcements to know when you might want to turn
it back on)::

    [experimental]
    evolution.obsdiscovery = no

Effect Flag Experiment
----------------------

Evolve also records what changed between two evolutions of a changeset. For
example, having this information is helpful to understand what changed between
an obsolete changeset and its tipmost successors.

Evolve currently records:

    - Meta changes, user, date
    - Tree movement, branch and parent, did the changeset moved?
    - Description, was the commit description edited
    - Diff, was there apart from potential diff change due to rebase a change in the diff?

These flags are lightweight and can be combined, so it's easy to see if 4
evolutions of the same changeset has just updated the description or if the
content changed and you need to review again the diff.

The effect flag recording is enabled by default in Evolve 6.4.0 so you have
nothing to do to enjoy it. Now every new evolution that you create will have
the effect flag attached.

The following config control the effect flag recording::

  [experimental]
  # uncomment to deactivate the registration of effect flags in obs markers
  # evolution.effect-flags = false

You can display the effect flags with the command obslog, so if you have a
changeset and you update only the message, you will see::

    $ hg commit -m "WIP
    $ hg commit -m "A better commit message!"
    $ hg obslog .
   @  8e9045855628 (3133) A better commit message!
   |
   x  7863a5bb5763 (3132) WIP
        rewritten(description) by Boris Feld <boris.feld@octobus.net> (Fri Jun 02 12:00:24 2017 +0200) as 8e9045855628

Servers does not need to activate the effect flag recording. Effect flags that
you create will not cause interference with other clients or servers without
the effect flag recording.

In-memory Evolve Experiment
---------------------------

The :hg:`evolve` command normally creates new changesets by writing the
files to the working copy and then committing them from there. You can
tell it to create the changesets without touching the working copy by
setting this config::

  [experimental]
  evolution.in-memory = yes

It will still update the working copy in case of conflicts.

Template keywords
-----------------

Evolve provides one template keyword that helps explore obsolescence history:

  - obsorigin, for each changeset display a line summarizing what changed
    between the changeset and its predecessors. Depending on the verbosity
    level (-q and -v) it displays the users that created the obsmarkers and the
    date range of these operations.

Evolve used to provide these template keywords, which since have been included
in core Mercurial (see :hg:`help templates -v`):

  - obsolete
  - obsfate (including obsfatedata, see also obsfate* template functions)

For compatibility, this extension also provides the following aliases to
template keywords from core Mercurial:

  - precursors (deprecated, use predecessors instead)
  - successors (deprecated, use successorssets instead)
  - troubles (deprecated, use instabilities instead)

Revset predicates
-----------------

Evolve provides several revset predicates:

  - unstable
  - troubled (deprecated, use unstable instead)
  - suspended
  - predecessors
  - precursors (deprecated, use predecessors instead)
  - allpredecessors
  - allprecursors (deprecated, use allpredecessors instead)
  - successors
  - allsuccessors

Note that successors revset in evolve is not the same as successors revset in
core Mercurial 4.3+. In evolve this revset returns only immediate successors,
as opposed to all successors. Use "allsuccessors(set)" to obtain all
successors.

See :hg:`help revsets -v` for more information.
"""

evolutionhelptext = b"""
Obsolescence markers make it possible to mark changesets that have been
deleted or superseded in a new version of the changeset.

Unlike the previous way of handling such changes, by stripping the old
changesets from the repository, obsolescence markers can be propagated
between repositories. This allows for a safe and simple way of exchanging
mutable history and altering it after the fact. Changeset phases are
respected, such that only draft and secret changesets can be altered (see
:hg:`help phases` for details).

Obsolescence is tracked using "obsolete markers", a piece of metadata
tracking which changesets have been made obsolete, potential successors for
a given changeset, the moment the changeset was marked as obsolete, and the
user who performed the rewriting operation. The markers are stored
separately from standard changeset data can be exchanged without any of the
precursor changesets, preventing unnecessary exchange of obsolescence data.

The complete set of obsolescence markers describes a history of changeset
modifications that is orthogonal to the repository history of file
modifications. This changeset history allows for detection and automatic
resolution of edge cases arising from multiple users rewriting the same part
of history concurrently.

Current feature status
======================

This feature is still in development.  If you see this help, you have enabled an
extension that turned this feature on.

Obsolescence markers will be exchanged between repositories that explicitly
assert support for the obsolescence feature (this can currently only be done
via an extension).

Instability
===========

Rewriting changesets might introduce instability.

There are two main kinds of instability: orphaning and diverging.

Orphans are changesets left behind when their ancestors are rewritten.
Divergence has two variants:

* Content-divergence occurs when independent rewrites of the same changesets
  lead to different results.

* Phase-divergence occurs when the old (obsolete) version of a changeset
  becomes public.

It is possible to prevent local creation of orphans by using the following config::

    [experimental]
    evolution=createmarkers,allnewcommands,exchange

You can also enable that option explicitly::

    [experimental]
    evolution=createmarkers,allnewcommands,allowunstable,exchange

or simply::

    [experimental]
    evolution=all

To prevent users from creating content divergence, a check is performed by
default on the revisions being rewritten, and the operation is aborted if it
creates divergence. If users want to allow creating content divergent
changesets, this check can be turned off by setting the following config::

    [experimental]
    evolution.allowdivergence=True
"""

import sys

import mercurial

from mercurial import (
    bookmarks as bookmarksmod,
    cmdutil,
    commands,
    error,
    help,
    hg,
    lock as lockmod,
    merge,
    node as nodemod,
    obsolete,
    pycompat,
    registrar,
    state as statemod,
    util,
)

from mercurial.i18n import _
from mercurial.node import nullid

from . import (
    compat,
    debugcmd,
    cmdrewrite,
    state,
    evolvecmd,
    exthelper,
    headchecking,
    metadata,
    obscache,
    obsexchange,
    obshashtree,
    obshistory,
    revset,
    rewind,
    templatekw,
    utility,
)

TROUBLES = compat.TROUBLES
__version__ = metadata.__version__
testedwith = metadata.testedwith
minimumhgversion = metadata.minimumhgversion
buglink = metadata.buglink

# Flags for enabling optional parts of evolve
commandopt = b'allnewcommands'

obsexcmsg = utility.obsexcmsg

colortable = {b'evolve.node': b'yellow',
              b'evolve.user': b'green',
              b'evolve.rev': b'blue',
              b'evolve.short_description': b'',
              b'evolve.date': b'cyan',
              b'evolve.current_rev': b'bold',
              b'evolve.verb': b'',
              b'evolve.operation': b'bold'
              }

aliases, entry = compat.find_cmd(b'commit', commands.table)

# This extension contains the following code
#
# - Extension Helper code
# - Obsolescence cache
# - ...
# - Older format compat

eh = exthelper.exthelper()
eh.merge(debugcmd.eh)
eh.merge(evolvecmd.eh)
eh.merge(obsexchange.eh)
eh.merge(obshashtree.eh)
eh.merge(obscache.eh)
eh.merge(obshistory.eh)
eh.merge(templatekw.eh)
eh.merge(compat.eh)
eh.merge(cmdrewrite.eh)
eh.merge(rewind.eh)
eh.merge(headchecking.eh)
eh.merge(revset.eh)
uisetup = eh.finaluisetup
extsetup = eh.finalextsetup
reposetup = eh.finalreposetup
cmdtable = eh.cmdtable
configtable = eh.configtable
templatekeyword = eh.templatekeyword
revsetpredicate = eh.revsetpredicate

# Configuration
eh.configitem(b'experimental', b'evolutioncommands', [])
eh.configitem(b'experimental', b'evolution.allnewcommands', None)
eh.configitem(b'experimental', b'evolution.divergence-resolution-minimal', False)
eh.configitem(b'experimental', b'evolution.in-memory', b'false')

#####################################################################
### Option configuration                                          ###
#####################################################################

@eh.reposetup # must be the first of its kin.
def _configureoptions(ui, repo):
    # If no capabilities are specified, enable everything.
    # This is so existing evolve users don't need to change their config.
    evolveopts = repo.ui.configlist(b'experimental', b'evolution')
    if not evolveopts:
        evolveopts = [b'all']
        repo.ui.setconfig(b'experimental', b'evolution', evolveopts, b'evolve')
    if obsolete.isenabled(repo, b'exchange'):
        # if no config explicitly set, disable bundle1
        if not isinstance(repo.ui.config(b'server', b'bundle1'), bytes):
            repo.ui.setconfig(b'server', b'bundle1', False, b'evolve')

    class trdescrepo(repo.__class__):

        def transaction(self, desc, *args, **kwargs):
            tr = super(trdescrepo, self).transaction(desc, *args, **kwargs)
            tr.desc = desc
            return tr

    repo.__class__ = trdescrepo

@eh.uisetup
def _configurecmdoptions(ui):
    # Unregister evolve commands if the command capability is not specified.
    #
    # This must be in the same function as the option configuration above to
    # guarantee it happens after the above configuration, but before the
    # extsetup functions.
    evolvecommands = ui.configlist(b'experimental', b'evolutioncommands')
    evolveopts = ui.configlist(b'experimental', b'evolution')
    if evolveopts and (commandopt not in evolveopts
                       and b'all' not in evolveopts):
        # We build whitelist containing the commands we want to enable
        whitelist = set()
        for cmd in evolvecommands:
            matchingevolvecommands = [e for e in cmdtable.keys() if cmd in e]
            if not matchingevolvecommands:
                raise error.Abort(_(b'unknown command: %s') % cmd)
            elif len(matchingevolvecommands) > 1:
                matchstr = b', '.join(matchingevolvecommands)
                msg = _(b"ambiguous command specification: '%s' matches [%s]")
                raise error.Abort(msg % (cmd, matchstr))
            else:
                whitelist.add(matchingevolvecommands[0])
        for disabledcmd in set(cmdtable) - whitelist:
            del cmdtable[disabledcmd]

#####################################################################
### Additional Utilities                                          ###
#####################################################################

# This section contains a lot of small utility function and method

# - Function to create markers
# - useful alias pstatus and pdiff (should probably go in evolve)
# - "troubles" method on changectx
# - function to travel through the obsolescence graph
# - function to find useful changeset to stabilize


### Useful alias

@eh.uisetup
def setupparentcommand(ui):

    _alias, statuscmd = compat.find_cmd(b'status', commands.table)
    inapplicable = {b'rev', b'change'}
    pstatusopts = [o for o in statuscmd[1] if o[1] not in inapplicable]

    @eh.command(b'pstatus', pstatusopts,
                helpcategory=registrar.command.CATEGORY_WORKING_DIRECTORY)
    def pstatus(ui, repo, *args, **kwargs):
        """show status combining committed and uncommitted changes

        This show the combined status of the current working copy parent commit and
        the uncommitted change in the working copy itself. The status displayed
        match the content of the commit that a bare :hg:`amend` will creates.

        See :hg:`help status` for details."""
        kwargs['rev'] = [b'.^']
        return statuscmd[0](ui, repo, *args, **kwargs)

    _alias, diffcmd = compat.find_cmd(b'diff', commands.table)
    inapplicable = {b'rev', b'from', b'to', b'change'}
    pdiffopts = [o for o in diffcmd[1] if o[1] not in inapplicable]

    @eh.command(b'pdiff', pdiffopts,
                helpcategory=registrar.command.CATEGORY_WORKING_DIRECTORY)
    def pdiff(ui, repo, *args, **kwargs):
        """show diff combining committed and uncommitted changes

        This show the combined diff of the current working copy parent commit and
        the uncommitted change in the working copy itself. The diff displayed
        match the content of the commit that a bare :hg:`amend` will creates.

        See :hg:`help diff` for details."""
        kwargs['rev'] = [b'.^']
        return diffcmd[0](ui, repo, *args, **kwargs)

@eh.uisetup
def _installalias(ui):
    odiffalias = b"diff --hidden --rev 'limit(predecessors(.),1)' --rev ."
    if ui.config(b'alias', b'odiff', None) is None:
        ui.setconfig(b'alias', b'odiff',
                     odiffalias,
                     b'evolve')
    if ui.config(b'alias', b'obsdiff', None) is None:
        ui.setconfig(b'alias', b'obsdiff',
                     odiffalias,
                     b'evolve')

#####################################################################
### Various trouble warning                                       ###
#####################################################################

# This section take care of issue warning to the user when troubles appear

def _warnobsoletewc(ui, repo, prevnode=None, wasobs=None):
    rev = repo[b'.']

    if not rev.obsolete():
        return

    if rev.node() == prevnode and wasobs:
        return
    msg = _(b"working directory parent is obsolete! (%s)\n")
    shortnode = nodemod.short(rev.node())

    ui.warn(msg % shortnode)

    # Check that evolve is activated for performance reasons
    evolvecommandenabled = any(b'evolve' in e for e in cmdtable)
    if ui.quiet or not evolvecommandenabled:
        return

    # Show a warning for helping the user to solve the issue
    reason, successors = obshistory._getobsfateandsuccs(repo, rev.node())

    if reason == b'pruned':
        solvemsg = _(b"use 'hg evolve' to update to its parent successor")
    elif reason == b'diverged':
        debugcommand = b"hg evolve --list --content-divergent"
        basemsg = _(b"%s has diverged, use '%s' to resolve the issue")
        solvemsg = basemsg % (shortnode, debugcommand)
    elif reason == b'superseded':
        msg = _(b"use 'hg evolve' to update to its successor: %s")
        solvemsg = msg % successors[0]
    elif reason == b'superseded_split':
        msg = _(b"use 'hg evolve' to update to its tipmost successor: %s")

        if len(successors) <= 2:
            solvemsg = msg % b", ".join(successors)
        else:
            firstsuccessors = b", ".join(successors[:2])
            remainingnumber = len(successors) - 2
            successorsmsg = _(b"%s and %d more") % (firstsuccessors, remainingnumber)
            solvemsg = msg % successorsmsg
    else:
        raise ValueError(reason)

    ui.warn(b"(%s)\n" % solvemsg)

@eh.wrapcommand(b"update")
@eh.wrapcommand(b"pull")
def wrapmayobsoletewc(origfn, ui, repo, *args, **opts):
    """Warn that the working directory parent is an obsolete changeset"""
    ctx = repo[b'.']
    node = ctx.node()
    isobs = ctx.obsolete()

    def warnobsolete(*args):
        _warnobsoletewc(ui, repo, node, isobs)
    wlock = None
    try:
        wlock = repo.wlock()
        repo._afterlock(warnobsolete)
        res = origfn(ui, repo, *args, **opts)
    finally:
        lockmod.release(wlock)
    return res

@eh.wrapcommand(b"parents")
def wrapparents(origfn, ui, repo, *args, **opts):
    res = origfn(ui, repo, *args, **opts)
    _warnobsoletewc(ui, repo)
    return res

@eh.wrapfunction(mercurial.exchange, 'push')
def push(orig, repo, *args, **opts):
    """Add a hint for "hg evolve" when troubles make push fails
    """
    try:
        return orig(repo, *args, **opts)
    except error.Abort as ex:
        hint = _(b"use 'hg evolve' to get a stable history "
                 b"or --force to ignore warnings")
        if (len(ex.args) >= 1
            and ex.args[0].startswith(b'push includes ')
            and ex.hint is None):
            ex.hint = hint
        raise

def summaryhook(ui, repo):
    evolvestate = state.cmdstate(repo)
    if evolvestate:
        # i18n: column positioning for "hg summary"
        ui.status(_(b'evolve: (evolve --continue)\n'))

@eh.extsetup
def obssummarysetup(ui):
    cmdutil.summaryhooks.add(b'evolve', summaryhook)

#####################################################################
### Old Evolve extension content                                  ###
#####################################################################

### new command
#############################

@eh.uisetup
def _installimportobsolete(ui):
    entry = compat.find_cmd(b'import', commands.table)[1]
    entry[1].append((b'', b'obsolete', False,
                     _(b'mark the old node as obsoleted by '
                       b'the created commit')))

def _getnodefrompatch(patch, dest):
    patchnode = patch.get(b'nodeid')
    if patchnode is not None:
        dest[b'node'] = nodemod.bin(patchnode)

@eh.wrapfunction(mercurial.cmdutil, 'tryimportone')
def tryimportone(orig, ui, repo, hunk, parents, opts, *args, **kwargs):
    expected = {b'node': None}
    _getnodefrompatch(hunk, expected)
    ret = orig(ui, repo, hunk, parents, opts, *args, **kwargs)
    created = ret[1]
    if (opts[b'obsolete'] and None not in (created, expected[b'node'])
        and created != expected[b'node']):
        tr = repo.transaction(b'import-obs')
        try:
            metadata = {b'user': ui.username()}
            repo.obsstore.create(tr, expected[b'node'], (created,),
                                 metadata=metadata)
            tr.close()
        finally:
            tr.release()
    return ret


def _deprecatealias(oldalias, newalias):
    '''Deprecates an alias for a command in favour of another

    Creates a new entry in the command table for the old alias. It creates a
    wrapper that has its synopsis set to show that is has been deprecated.
    The documentation will be replace with a pointer to the new alias.
    If a user invokes the command a deprecation warning will be printed and
    the command of the *new* alias will be invoked.

    This function is loosely based on the extensions.wrapcommand function.
    '''
    try:
        aliases, entry = compat.find_cmd(newalias, cmdtable)
    except error.UnknownCommand:
        # Commands may be disabled
        return
    for alias, e in cmdtable.items():
        if e is entry:
            break

    synopsis = b'(DEPRECATED)'
    if len(entry) > 2:
        fn, opts, _syn = entry
    else:
        fn, opts, = entry
    deprecationwarning = _(b'%s have been deprecated in favor of %s\n') % (
        oldalias, newalias)

    def newfn(*args, **kwargs):
        ui = args[0]
        ui.warn(deprecationwarning)
        util.checksignature(fn)(*args, **kwargs)
    newfn.__doc__ = pycompat.sysstr(deprecationwarning + b' (DEPRECATED)')
    cmdwrapper = eh.command(oldalias, opts, synopsis)
    cmdwrapper(newfn)

@eh.extsetup
def deprecatealiases(ui):
    _deprecatealias(b'gup', b'next')
    _deprecatealias(b'gdown', b'previous')

def _gettopic(ctx):
    """handle topic fetching with or without the extension"""
    return getattr(ctx, 'topic', lambda: b'')()

def _gettopicidx(ctx):
    """handle topic fetching with or without the extension"""
    return getattr(ctx, 'topicidx', lambda: None)()

def _getcurrenttopic(repo):
    return getattr(repo, 'currenttopic', b'')

def _prevupdate(repo, display, target, bookmark, dryrun, mergeopt):
    if dryrun:
        repo.ui.write(_(b'hg update %s;\n') % target)
        if bookmark is not None:
            repo.ui.write(_(b'hg bookmark %s -r %s;\n')
                          % (bookmark, target))
    else:
        updatecheck = None
        # --merge is passed, we don't need to care about commands.update.check
        # config option
        if mergeopt:
            updatecheck = b'none'
        try:
            ret = compat.hg_update_totally(repo.ui, repo, target.node(), None,
                                           updatecheck=updatecheck)
        except error.Abort as exc:
            # replace the hint to mention about --merge option
            exc.hint = _(b'do you want --merge?')
            raise
        if not ret:
            tr = lock = None
            try:
                lock = repo.lock()
                tr = repo.transaction(b'previous')
                if bookmark is not None:
                    bmchanges = [(bookmark, target.node())]
                    repo._bookmarks.applychanges(repo, tr, bmchanges)
                else:
                    bookmarksmod.deactivate(repo)
                tr.close()
            finally:
                lockmod.release(tr, lock)

    if not repo.ui.quiet:
        display(target)

def _findprevtarget(repo, display, movebookmark=False, topic=True):
    target = bookmark = None
    wkctx = repo[None]
    p1 = wkctx.p1()
    parents = p1.parents()
    currenttopic = _getcurrenttopic(repo)

    # we do not filter in the 1 case to allow prev to t0
    if currenttopic and topic and _gettopicidx(p1) != 1:
        parents = [repo[utility._singlesuccessor(repo, ctx)] if ctx.mutable() else ctx
                   for ctx in parents]
        parents = [ctx for ctx in parents if ctx.topic() == currenttopic]

    # issue message for the various case
    if p1.node() == nullid:
        repo.ui.warn(_(b'already at repository root\n'))
    elif not parents and currenttopic:
        repo.ui.warn(_(b'no parent in topic "%s"\n') % currenttopic)
        repo.ui.warn(_(b'(do you want --no-topic)\n'))
    elif len(parents) == 1:
        target = parents[0]
        bookmark = None
        if movebookmark:
            bookmark = repo._activebookmark
    else:
        header = _(b"multiple parents, choose one to update:")
        prevs = [p.rev() for p in parents]
        selectedrev = utility.revselectionprompt(repo.ui, repo, prevs, header)
        if selectedrev is None:
            for p in parents:
                display(p)
            repo.ui.warn(_(b'multiple parents, explicitly update to one\n'))
        else:
            target = repo[selectedrev]
    return target, bookmark

@eh.command(
    b'previous',
    [(b'B', b'move-bookmark', False,
        _(b'move active bookmark after update')),
     (b'm', b'merge', False, _(b'bring uncommitted change along')),
     (b'', b'no-topic', False, _(b'ignore topic and move topologically')),
     (b'n', b'dry-run', False,
        _(b'do not perform actions, just print what would be done'))],
    b'[OPTION]...',
    helpcategory=registrar.command.CATEGORY_WORKING_DIRECTORY,
    helpbasic=True,
)
def cmdprevious(ui, repo, **opts):
    """update to parent revision

    Displays the summary line of the destination for clarity."""
    wlock = None
    dryrunopt = opts['dry_run']
    mergeopt = opts['merge']
    if not dryrunopt:
        wlock = repo.wlock()
    try:
        wkctx = repo[None]
        wparents = wkctx.parents()
        if len(wparents) != 1:
            raise error.StateError(_(b'merge in progress'))
        if not mergeopt:
            # we only skip the check if noconflict is set
            if ui.config(b'commands', b'update.check') == b'noconflict':
                pass
            else:
                compat.bail_if_changed(repo, hint=_(b'do you want --merge?'))

        topic = not opts.get("no_topic", False)
        hastopic = bool(_getcurrenttopic(repo))

        display = utility.short_ctx_displayer(ui, repo, b'previous')
        if topic and hastopic:
            display = utility.stack_ctx_displayer(ui, repo, b'previous')

        target, bookmark = _findprevtarget(repo, display,
                                           opts.get('move_bookmark'), topic)
        if target is not None:
            configoverride = util.nullcontextmanager()
            if topic and _getcurrenttopic(repo) != _gettopic(target):
                configoverride = repo.ui.configoverride({
                    (b'_internal', b'keep-topic'): b'yes'
                }, source=b'previous')
            with configoverride:
                _prevupdate(repo, display, target, bookmark, dryrunopt,
                            mergeopt)
            return 0
        else:
            return 1
    finally:
        lockmod.release(wlock)

@eh.command(
    b'next',
    [(b'B', b'move-bookmark', False,
        _(b'move active bookmark after update')),
     (b'm', b'merge', False, _(b'bring uncommitted change along')),
     (b'', b'evolve', True, _(b'evolve the next changeset if necessary')),
     (b'', b'no-topic', False, _(b'ignore topic and move topologically')),
     (b'n', b'dry-run', False,
      _(b'do not perform actions, just print what would be done')),
     (b'', b'abort', False, _(b'abort the interrupted next'))],
    b'[OPTION]...',
    helpcategory=registrar.command.CATEGORY_WORKING_DIRECTORY,
    helpbasic=True,
)
def cmdnext(ui, repo, **opts):
    """update to next child revision

    If necessary, evolve the next changeset. Use --no-evolve to disable this
    behavior.

    Displays the summary line of the destination for clarity.
    """
    wlock = None
    dryrunopt = opts['dry_run']
    abortopt = opts['abort']

    cmdutil.check_incompatible_arguments(opts, 'abort', ['move_bookmark', 'merge'])
    if abortopt:
        evolvestate = state.cmdstate(repo)
        if not evolvestate:
            raise error.StateError(_(b'no interrupted next to abort'))

        evolvestate.load()
        if evolvestate[b'command'] != b'next':
            raise error.StateError(_(b'no interrupted next to abort'))

        pctx = repo[b'.']
        merge.clean_update(pctx)
        ui.status(_(b'next aborted\n'))
        ui.status(_(b'working directory is now at %s\n')
                  % ui.label(bytes(pctx), b'evolve.node'))
        evolvestate.delete()
        return 0

    if not dryrunopt:
        wlock = repo.wlock()
    try:
        wkctx = repo[None]
        wparents = wkctx.parents()
        if len(wparents) != 1:
            raise error.StateError(_(b'merge in progress'))

        children = [ctx for ctx in wparents[0].children() if not ctx.obsolete()]
        topic = _getcurrenttopic(repo)
        filtered = set()
        display = utility.short_ctx_displayer(ui, repo, b'next')
        if topic and not opts['no_topic']:
            filtered = set(ctx.rev() for ctx in children if ctx.topic() != topic)
            children = [ctx for ctx in children if ctx.rev() not in filtered]
            display = utility.stack_ctx_displayer(ui, repo, b'next')
            opts['stacktemplate'] = True

        # check if we need to evolve while updating to the next child revision
        needevolve = False
        aspchildren = evolvecmd._aspiringchildren(repo, [repo[b'.'].rev()])
        if topic and not opts['no_topic']:
            filtered.update(rev for rev in aspchildren
                            if repo[rev].topic() != topic)
            aspchildren = [rev for rev in aspchildren if rev not in filtered]

        # Let's make sure we don't have any duplicates between children and
        # aspiring children
        filtered.update(ctx.rev() for ctx in children)
        aspchildren = [rev for rev in aspchildren if rev not in filtered]

        # To catch and prevent the case when `next` would get confused by split,
        # lets filter those aspiring children which can be stablized on one of
        # the aspiring children itself.
        aspirants = set(aspchildren)
        for aspchild in aspchildren:
            possdests = evolvecmd._possibledestination(repo, aspchild)
            if possdests & aspirants:
                filtered.add(aspchild)
        aspchildren = [rev for rev in aspchildren if rev not in filtered]
        if aspchildren:
            needevolve = True

        # check if working directory is clean before we evolve the next cset
        if needevolve and opts['evolve']:
            hint = _(b'use `hg amend`, `hg revert` or `hg shelve`')
            compat.bail_if_changed(repo, hint=hint)
        elif not opts['merge']:
            # we only skip the check if noconflict is set
            if ui.config(b'commands', b'update.check') == b'noconflict':
                pass
            else:
                compat.bail_if_changed(repo, hint=_(b'do you want --merge?'))

        if len(children) == 1 and (not opts['evolve'] or not aspchildren):
            c = children[0]
            return _updatetonext(ui, repo, c, display, opts)
        elif children:
            cheader = _(b"ambiguous next changeset, choose one to update:")
            crevs = [c.rev() for c in children] + aspchildren
            selectedrev = utility.revselectionprompt(ui, repo, crevs, cheader)
            if selectedrev is None:
                ui.warn(_(b"ambiguous next changeset:\n"))
                for rev in crevs:
                    display(repo[rev])
                ui.warn(_(b"explicitly update to one of them\n"))
                return 1
            else:
                if selectedrev in aspchildren:
                    return _nextevolve(ui, repo, selectedrev, opts)
                return _updatetonext(ui, repo, repo[selectedrev], display, opts)
        else:
            if not opts['evolve'] or not aspchildren:
                if filtered:
                    ui.warn(_(b'no children on topic "%s"\n') % topic)
                    ui.warn(_(b'do you want --no-topic\n'))
                else:
                    ui.warn(_(b'no children\n'))
                if aspchildren:
                    msg = _(b'(%i unstable changesets to be evolved here, '
                            b'do you want --evolve?)\n')
                    ui.warn(msg % len(aspchildren))
                return 1
            elif len(aspchildren) > 1:
                cheader = _(b"ambiguous next (unstable) changeset, choose one to"
                            b" evolve and update:")
                selectedrev = utility.revselectionprompt(ui, repo,
                                                         aspchildren, cheader)
                if selectedrev is None:
                    ui.warn(_(b"ambiguous next (unstable) changeset:\n"))
                    for c in aspchildren:
                        display(repo[c])
                    ui.warn(_(b"(run 'hg evolve --rev REV' on one of them)\n"))
                    return 1
                else:
                    return _nextevolve(ui, repo, repo[selectedrev], opts)
            else:
                return _nextevolve(ui, repo, aspchildren[0], opts)
    finally:
        lockmod.release(wlock)

def _nextevolve(ui, repo, aspchildren, opts):
    """logic for hg next command to evolve and update to an aspiring children"""

    compat.bail_if_changed(repo)
    evolvestate = state.cmdstate(repo, opts={b'command': b'next',
                                             b'bookmarkchanges': []})
    with repo.wlock(), repo.lock():
        tr = repo.transaction(b"evolve")
        with util.acceptintervention(tr):
            result = evolvecmd._solveone(ui, repo, repo[aspchildren],
                                         evolvestate, opts.get('dry_run'),
                                         False,
                                         lambda: None, category=b'orphan',
                                         stacktmplt=opts.get('stacktemplate',
                                                             False))
    # making sure a next commit is formed
    if result[0] and result[1]:
        # If using in-memory merge, _solveone() will not have updated the
        # working copy, so we need to do that.
        if evolvecmd.use_in_memory_merge(repo) and result[1]:
            merge.update(repo[result[1]])
        ui.status(_(b'working directory is now at %s\n')
                  % ui.label(bytes(repo[b'.']), b'evolve.node'))
    return 0

def _updatetonext(ui, repo, child, display, opts):
    """ logic for `hg next` command to update to children and move bookmarks if
    required """
    bm = repo._activebookmark
    shouldmove = opts.get('move_bookmark') and bm is not None
    if opts.get('dry_run'):
        ui.write(_(b'hg update %s;\n') % child)
        if shouldmove:
            ui.write(_(b'hg bookmark %s -r %s;\n') % (bm, child))
    else:
        updatecheck = None
        # --merge is passed, we don't need to care about commands.update.check
        # config option
        if opts['merge']:
            updatecheck = b'none'
        try:
            ret = compat.hg_update_totally(ui, repo, child.node(), None,
                                           updatecheck=updatecheck)
        except error.Abort as exc:
            # replace the hint to mention about --merge option
            exc.hint = _(b'do you want --merge?')
            raise

        if not ret:
            lock = tr = None
            try:
                lock = repo.lock()
                tr = repo.transaction(b'next')
                if shouldmove:
                    bmchanges = [(bm, child.node())]
                    repo._bookmarks.applychanges(repo, tr, bmchanges)
                else:
                    bookmarksmod.deactivate(repo)
                tr.close()
            finally:
                lockmod.release(tr, lock)
    if not ui.quiet:
        display(child)
    return 0

@eh.wrapcommand(b'commit')
def commitwrapper(orig, ui, repo, *arg, **kwargs):
    tr = None
    if kwargs.get('amend', False):
        wlock = lock = None
    else:
        wlock = repo.wlock()
        lock = repo.lock()
    try:
        obsoleted = kwargs.get('obsolete', [])
        if obsoleted:
            obsoleted = repo.set(b'%lr', obsoleted)
        result = orig(ui, repo, *arg, **kwargs)
        if not result: # commit succeeded
            new = repo[b'tip']
            oldbookmarks = []
            markers = []
            for old in obsoleted:
                oldbookmarks.extend(repo.nodebookmarks(old.node()))
                markers.append((old, (new,)))
            if markers:
                obsolete.createmarkers(repo, markers, operation=b"amend")
            bmchanges = []
            for book in oldbookmarks:
                bmchanges.append((book, new.node()))
            if oldbookmarks:
                if not wlock:
                    wlock = repo.wlock()
                if not lock:
                    lock = repo.lock()
                tr = repo.transaction(b'commit')
                repo._bookmarks.applychanges(repo, tr, bmchanges)
                tr.close()
        return result
    finally:
        lockmod.release(tr, lock, wlock)

@eh.extsetup
def oldevolveextsetup(ui):
    entry = compat.find_cmd(b'commit', commands.table)[1]
    entry[1].append((b'o', b'obsolete', [],
                     _(b"make commit obsolete this revision (DEPRECATED)")))

@eh.wrapfunction(obsolete, '_checkinvalidmarkers')
def _checkinvalidmarkers(orig, repo, markers):
    """search for marker with invalid data and raise error if needed

    Exist as a separated function to allow the evolve extension for a more
    subtle handling.
    """
    if r'debugobsconvert' in sys.argv:
        return
    for mark in markers:
        if repo.nullid in mark[1]:
            msg = _(b'bad obsolescence marker detected: invalid successors nullid')
            hint = _(b'You should run `hg debugobsconvert`')
            raise error.Abort(msg, hint=hint)

@eh.command(
    b'debugobsconvert',
    [(b'', b'new-format', obsexchange._bestformat, _(b'Destination format for markers.'))],
    b'')
def debugobsconvert(ui, repo, new_format):
    origmarkers = repo.obsstore._all  # settle version
    if new_format == repo.obsstore._version:
        msg = _(b'New format is the same as the old format, not upgrading!')
        raise error.Abort(msg)
    with repo.lock():
        f = repo.svfs(b'obsstore', b'wb', atomictemp=True)
        known = set()
        markers = []
        for m in origmarkers:
            # filter out invalid markers
            if nullid in m[1]:
                m = list(m)
                m[1] = tuple(s for s in m[1] if s != nullid)
                m = tuple(m)
            if m in known:
                continue
            known.add(m)
            markers.append(m)
        ui.write(_(b'Old store is version %d, will rewrite in version %d\n') % (
            repo.obsstore._version, new_format))
        for data in obsolete.encodemarkers(markers, True, new_format):
            f.write(data)
        f.close()
    ui.write(_(b'Done!\n'))


def _helploader(ui):
    return help.gettext(evolutionhelptext)

@eh.uisetup
def _setuphelp(ui):
    for entry in help.helptable:
        if entry[0] == b"evolution":
            break
    else:
        help.helptable.append(([b"evolution"],
                               _(b"Safely Rewriting History"),
                               _helploader,
                               help.TOPIC_CATEGORY_CONCEPTS))
        help.helptable.sort()

evolvestateversion = 0

@eh.uisetup
def setupevolveunfinished(ui):
    _msg = _(b'To continue:    hg evolve --continue\n'
             b'To abort:       hg evolve --abort\n'
             b'To stop:        hg evolve --stop\n'
             b'(also see `hg help evolve.interrupted`)')
    statemod.addunfinished(b'evolve', fname=b'evolvestate',
                           continueflag=True, stopflag=True,
                           statushint=_msg,
                           abortfunc=evolvecmd.hgabortevolve,
                           continuefunc=evolvecmd.hgcontinueevolve)
    statemod.addunfinished(b'pick', fname=b'pickstate', continueflag=True,
                           abortfunc=cmdrewrite.hgabortpick,
                           continuefunc=cmdrewrite.hgcontinuepick)
    _fixup_msg = _(b'To continue:    hg fixup --continue\n'
                   b'To abort:       hg fixup --abort\n')
    statemod.addunfinished(b'fixup', fname=b'fixup-state',
                           continueflag=True, statushint=_fixup_msg,
                           abortfunc=cmdrewrite.hgabortfixup,
                           continuefunc=cmdrewrite.hgcontinuefixup)

@eh.wrapfunction(hg, 'clean')
def clean(orig, repo, *args, **kwargs):
    ret = orig(repo, *args, **kwargs)
    repo.vfs.unlinkpath(b'evolvestate', ignoremissing=True)
    return ret
