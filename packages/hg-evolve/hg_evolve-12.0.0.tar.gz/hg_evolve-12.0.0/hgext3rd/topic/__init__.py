# __init__.py - topic extension
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
"""support for topic branches

Topic branches are lightweight branches which fade out when changes are
finalized (move to the public phase).

Compared to bookmark, topic is reference carried by each changesets of the
series instead of just the single head revision.  Topic are quite similar to
the way named branch work, except they eventually fade away when the changeset
becomes part of the immutable history. Changeset can belong to both a topic and
a named branch, but as long as it is mutable, its topic identity will prevail.
As a result, default destination for 'update', 'merge', etc...  will take topic
into account. When a topic is active these operations will only consider other
changesets on that topic (and, in some occurrence, bare changeset on same
branch).  When no topic is active, changeset with topic will be ignored and
only bare one on the same branch will be taken in account.

There is currently two commands to be used with that extension: 'topics' and
'stack'.

The 'hg topics' command is used to set the current topic, change and list
existing one. 'hg topics --verbose' will list various information related to
each topic.

The 'stack' will show you information about the stack of commit belonging to
your current topic.

Topic is offering you aliases reference to changeset in your current topic
stack as 's#'. For example, 's1' refers to the root of your stack, 's2' to the
second commits, etc. The 'hg stack' command show these number. 's0' can be used
to refer to the parent of the topic root. Updating using `hg up s0` will keep
the topic active.

Push behavior will change a bit with topic. When pushing to a publishing
repository the changesets will turn public and the topic data on them will fade
away. The logic regarding pushing new heads will behave has before, ignore any
topic related data. When pushing to a non-publishing repository (supporting
topic), the head checking will be done taking topic data into account.
Push will complain about multiple heads on a branch if you push multiple heads
with no topic information on them (or multiple public heads). But pushing a new
topic will not requires any specific flag. However, pushing multiple heads on a
topic will be met with the usual warning.

The 'evolve' extension takes 'topic' into account. 'hg evolve --all'
will evolve all changesets in the active topic. In addition, by default. 'hg
next' and 'hg prev' will stick to the current topic.

Be aware that this extension is still an experiment, commands and other features
are likely to be change/adjusted/dropped over time as we refine the concept.

topic-mode
==========

The topic extension can be configured to ensure the user do not forget to add
a topic when committing a new topic::

    [experimental]
    # behavior when commit is made without an active topic
    topic-mode = ignore # do nothing special (default)
    topic-mode = warning # print a warning
    topic-mode = enforce # abort the commit (except for merge)
    topic-mode = enforce-all # abort the commit (even for merge)
    topic-mode = random # use a randomized generated topic (except for merge)
    topic-mode = random-all # use a randomized generated topic (even for merge)

Single head enforcing
=====================

The extensions come with an option to enforce that there is only one heads for
each name in the repository at any time.

::

    [experimental]
    enforce-single-head = yes

Publishing behavior
===================

Topics vanish when changesets move to the public phase. Moving to the public
phase usually happens on push, but it is possible to modify this behavior. The
server needs to have specific config for this.

* everything pushed becomes public (the default)::

    [phases]
    publish = yes

* nothing pushed turns public::

    [phases]
    publish = no

* topic branches are not published, changesets without topic are::

    [phases]
    publish = no
    [experimental]
    topic.publish-bare-branch = yes

In addition, :hg:`push` command has a ``--publish`` flag. When used, the pushed
revisions are published if the push succeeds. It also applies to common
revisions selected by the push.

One can prevent any publishing from happening in a repository using::

    [experimental]
    topic.allow-publish = no

Server side visibility
======================

Serving changesets with topics to clients without topic extension can get
confusing. Such clients will have multiple anonymous heads without a clear way
to distinguish them. They will also "lose" the canonical heads of the branch.

To avoid this confusion, server can be configured to only serve changesets with
topics to clients with the topic extension (version 9.3+). This might become
the default in future::

    [experimental]
    topic.server-gate-topic-changesets = yes

Explicitly merging in the target branch
=======================================

By default, Mercurial will not let your merge a topic into its target branch if
that topic is already based on the head of that branch. In other word,
Mercurial will not let your create a merge that will eventually have two
parents in the same branches, one parent being the ancestors of the other
parent. This behavior can be lifted using the following config::

    [experimental]
    topic.linear-merge = allow-from-bare-branch

When this option is set to `allow-from-bare-branch`, it is possible to merge a
topic branch from a bare branch (commit an active topic (eg: public one))
regardless of the topology. The result would typically looks like that::

   @    summary: resulting merge commit
   |\\   branch:  my-branch
   | |
   | o  summary: some more change in a topic, the merge "target"
   | |  branch:  my-branch
   | |  topic:   my-topic
   | |
   | o  summary: some change in a topic
   |/   branch:  my-branch
   |    topic:   my-topic
   |
   o    summary: previous head of the branch, the merge "source"
   |    branch:  my-branch
"""

from __future__ import absolute_import

import errno
import functools
import re
import time
import weakref

from mercurial.i18n import _
from mercurial import (
    bookmarks,
    bundlerepo,
    changelog,
    cmdutil,
    commands,
    configitems,
    context,
    encoding,
    error,
    exchange,
    extensions,
    localrepo,
    lock as lockmod,
    logcmdutil,
    merge,
    namespaces,
    node,
    obsolete,
    obsutil,
    patch,
    phases,
    pycompat,
    registrar,
    rewriteutil,
    scmutil,
    smartset,
    templatefilters,
    util,
)

from . import (
    common,
    compat,
    constants,
    destination,
    discovery,
    flow,
    randomname,
    revset as topicrevset,
    server,
    stack,
    topicmap,
)

cmdtable = {}
command = registrar.command(cmdtable)
colortable = {b'topic.active': b'green',
              b'topic.list.unstablecount': b'red',
              b'topic.list.headcount.multiple': b'yellow',
              b'topic.list.behindcount': b'cyan',
              b'topic.list.behinderror': b'red',
              b'stack.index': b'yellow',
              b'stack.index.base': b'none dim',
              b'stack.desc.base': b'none dim',
              b'stack.shortnode.base': b'none dim',
              b'stack.state.base': b'dim',
              b'stack.state.clean': b'green',
              b'stack.index.current': b'cyan',       # random pick
              b'stack.state.current': b'cyan bold',  # random pick
              b'stack.desc.current': b'cyan',        # random pick
              b'stack.shortnode.current': b'cyan',   # random pick
              b'stack.state.orphan': b'red',
              b'stack.state.content-divergent': b'red',
              b'stack.state.phase-divergent': b'red',
              b'stack.summary.behindcount': b'cyan',
              b'stack.summary.behinderror': b'red',
              b'stack.summary.headcount.multiple': b'yellow',
              # default color to help log output and thg
              # (first pick I could think off, update as needed
              b'log.topic': b'green_background',
              }

__version__ = b'2.0.0'

testedwith = b'6.7 6.8 6.9 7.0 7.1 7.2'
minimumhgversion = b'6.7'
buglink = b'https://foss.heptapod.net/mercurial/mercurial-devel/-/issues?label_name%5B%5D=topic-experiment'

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'experimental', b'enforce-topic',
           default=False,
)
configitem(b'experimental', b'enforce-single-head',
           default=False,
)
configitem(b'experimental', b'topic-mode',
           default=None,
)
configitem(b'experimental', b'topic.publish-bare-branch',
           default=False,
)
configitem(b'experimental', b'topic.allow-publish',
           default=configitems.dynamicdefault,
)
configitem(b'_internal', b'keep-topic',
           default=False,
)
# used for signaling that ctx.branch() shouldn't return fqbn even if topic is
# enabled for local repo
configitem(b'_internal', b'tns-disable-fqbn',
           default=False,
)
# used for signaling that push will publish changesets
configitem(b'_internal', b'tns-publish',
           default=False,
)
# used for signaling that the current command has explicit target arguments
# (e.g. --rev or --branch) and we should ignore tns-default-* config
configitem(b'_internal', b'tns-explicit-target',
           default=False,
)
# used for selecting what topic and topic namespace values take priority during
# some history rewriting operations: 'local' prefers active topic and tns,
# 'other' prefers values in commit extras, if there are any
configitem(b'_internal', b'topic-source',
           default=b'other',
)
configitem(b'devel', b'tns-report-transactions',
           default=lambda: [],
)
# used for allowing users to rewrite history only in their "own" topic
# namespaces
configitem(b'experimental', b'tns-allow-rewrite',
           default=configitems.dynamicdefault,
)
configitem(b'experimental', b'tns-default-pull-namespaces',
           default=configitems.dynamicdefault,
)
configitem(b'experimental', b'tns-reject-push',
           default=False,
)
configitem(b'experimental', b'topic-mode.server',
           default=configitems.dynamicdefault,
)
configitem(b'experimental', b'topic.server-gate-topic-changesets',
           default=False,
)
configitem(b'experimental', b'topic.linear-merge',
           default="reject",
)

def extsetup(ui):
    # register config that strictly belong to other code (thg, core, etc)
    #
    # To ensure all config items we used are registered, we register them if
    # nobody else did so far.
    extraitem = functools.partial(configitems._register, ui._knownconfig)
    if (b'experimental' not in ui._knownconfig
            or not ui._knownconfig[b'experimental'].get(b'thg.displaynames')):
        extraitem(b'experimental', b'thg.displaynames',
                  default=None,
        )
    if (b'devel' not in ui._knownconfig
            or not ui._knownconfig[b'devel'].get(b'randomseed')):
        extraitem(b'devel', b'randomseed',
                  default=None,
        )

def _contexttns(self, force=False):
    if not force and not self.mutable():
        return b'none'
    cache = getattr(self._repo, '_tnscache', None)
    # topic loaded, but not enabled (eg: multiple repo in the same process)
    if cache is None:
        return b'none'
    # topic namespace is meaningless when topic is not set
    if not self.topic(force):
        return b'none'
    if self.rev() is None:
        # don't cache volatile ctx instances that aren't stored on-disk yet
        return self.extra().get(b'topic-namespace', b'none')
    tns = cache.get(self.rev())
    if tns is None:
        tns = self.extra().get(b'topic-namespace', b'none')
        self._repo._tnscache[self.rev()] = tns
    return tns

context.basectx.topic_namespace = _contexttns

def _contexttopic(self, force=False):
    if not (force or self.mutable()):
        return b''
    cache = getattr(self._repo, '_topiccache', None)
    # topic loaded, but not enabled (eg: multiple repo in the same process)
    if cache is None:
        return b''
    if self.rev() is None:
        # don't cache volatile ctx instances that aren't stored on-disk yet
        return self.extra().get(constants.extrakey, b'')
    topic = cache.get(self.rev())
    if topic is None:
        topic = self.extra().get(constants.extrakey, b'')
        self._repo._topiccache[self.rev()] = topic
    return topic

context.basectx.topic = _contexttopic

def _contexttopicidx(self):
    topic = self.topic()
    if not topic or self.obsolete():
        # XXX we might want to include s0 here,
        # however s0 is related to  'currenttopic' which has no place here.
        return None
    revlist = stack.stack(self._repo, topic=topic)
    try:
        return revlist.index(self.rev())
    except IndexError:
        # Lets move to the last ctx of the current topic
        return None
context.basectx.topicidx = _contexttopicidx

def _contextfqbn(self):
    """return branch//namespace/topic of the changeset, also known as fully
    qualified branch name
    """
    branch = encoding.tolocal(self.extra()[b'branch'])
    return common.formatfqbn(branch, self.topic_namespace(), self.topic())

context.basectx.fqbn = _contextfqbn

stackrev = re.compile(br'^s\d+$')
topicrev = re.compile(br'^t\d+$')

hastopicext = common.hastopicext

def _namemap(repo, name):
    revs = None
    if stackrev.match(name):
        idx = int(name[1:])
        tname = topic = repo.currenttopic
        if topic:
            ttype = b'topic'
            revs = list(stack.stack(repo, topic=topic))
        else:
            ttype = b'branch'
            tname = branch = repo[None].branch()
            revs = list(stack.stack(repo, branch=branch))
    elif topicrev.match(name):
        idx = int(name[1:])
        ttype = b'topic'
        tname = topic = repo.currenttopic
        if not tname:
            raise error.Abort(_(b'cannot resolve "%s": no active topic') % name)
        revs = list(stack.stack(repo, topic=topic))

    if revs is not None:
        try:
            r = revs[idx]
        except IndexError:
            if ttype == b'topic':
                msg = _(b'cannot resolve "%s": %s "%s" has only %d changesets')
            elif ttype == b'branch':
                msg = _(b'cannot resolve "%s": %s "%s" has only %d non-public changesets')
            raise error.Abort(msg % (name, ttype, tname, len(revs) - 1))
        # t0 or s0 can be None
        if r == -1 and idx == 0:
            msg = _(b'the %s "%s" has no %s')
            raise error.Abort(msg % (ttype, tname, name))
        return [repo[r].node()]
    if name not in repo.topics:
        return []
    node = repo.changelog.node
    return [node(rev) for rev in repo.revs(b'topic(%s)', name)]

def _nodemap(repo, node):
    ctx = repo[node]
    t = ctx.topic()
    if t and ctx.phase() > phases.public:
        return [t]
    return []

def wrap_summary(orig, ui, repo, *args, **kwargs):
    with discovery.override_context_branch(repo) as repo:
        return orig(ui, repo, *args, **kwargs)

def wrap_tag_cmd(orig, ui, repo, *args, **kwargs):
    with discovery.override_context_branch(repo) as repo:
        return orig(ui, repo, *args, **kwargs)

def wrapwctxbranch(orig, self):
    branch = orig(self)
    return common.formatfqbn(branch=branch)

def wrapwctxdirty(orig, self, missing=False, merge=True, branch=True):
    """check whether a working directory is modified"""
    # check subrepos first
    for s in sorted(self.substate):
        if self.sub(s).dirty(missing=missing):
            return True
    # check current working dir
    return (
        (merge and self.p2())
        or (branch and self.branch() != common.formatfqbn(branch=self.p1().branch()))
        or self.modified()
        or self.added()
        or self.removed()
        or (missing and self.deleted())
    )

def find_affected_tns(repo, tr):
    origrepolen = tr.changes[b'origrepolen']
    unfi = repo.unfiltered()

    affected = set()
    # These are the new changesets that weren't in the repo before this
    # transaction
    for rev in smartset.spanset(repo, start=origrepolen):
        ctx = unfi[rev]
        tns = ctx.topic_namespace()
        affected.add(tns)

    # These are the changesets obsoleted by this transaction
    for rev in obsutil.getobsoleted(repo, tr):
        ctx = unfi[rev]
        tns = ctx.topic_namespace()
        affected.add(tns)

    # Phase movements, we only care about:
    # - publishing changesets (since they lose topic namespace)
    # - forcefully making changesets draft again
    # - turning secret changesets draft and making them visible to peers
    tnsphases = (phases.secret, phases.draft)
    for revs, (old, new) in tr.changes[b'phases']:
        if old not in tnsphases and new not in tnsphases:
            # Skip phase movement if there is no phase (old or new) that has
            # visible topic namespace (i.e. draft and secret)
            continue
        revs = [rev for rev in revs if rev < origrepolen]
        for rev in revs:
            ctx = unfi[rev]
            tns = ctx.topic_namespace(force=True)
            affected.add(tns)

    # We want to detect any bookmark movement, even within one topic namespace
    for name, nodes in tr.changes[b'bookmarks'].items():
        for n in nodes:
            if n is not None and n in unfi:
                ctx = unfi[n]
                tns = ctx.topic_namespace()
                affected.add(tns)

    # We don't care about changesets without topic namespace
    affected.discard(b'none')

    tr.changes[b'tns'] = affected
    report_affected_tns(repo, tr)

def report_affected_tns(repo, tr):
    report = set(repo.ui.configlist(b'devel', b'tns-report-transactions'))
    # transaction names sometimes also have a URL after a newline byte
    trnames = (trname.partition(b'\n')[0] for trname in tr._names)
    if b'*' not in report:
        # * matches any transaction
        if not any(trname in report for trname in trnames):
            return

    if tr.changes[b'tns']:
        repo.ui.status(b'topic namespaces affected: %s\n' % b' '.join(sorted(tr.changes[b'tns'])))

def wrapmakebundlerepository(orig, ui, repopath, bundlepath):
    repo = orig(ui, repopath, bundlepath)

    # We want bundle repos to also have caches for topic extension, because we
    # want to, for example, see topic and topic namespaces in `hg incoming`
    # regardless if the bundle repo has topic extension, as long as local repo
    # has topic enabled.
    class topicbundlerepo(repo.__class__):
        @util.propertycache
        def _tnscache(self):
            return {}

        @util.propertycache
        def _topiccache(self):
            return {}

        def invalidatecaches(self):
            self._tnscache.clear()
            self._topiccache.clear()
            super(topicbundlerepo, self).invalidatecaches()

    repo.__class__ = topicbundlerepo
    return repo

def uisetup(ui):
    # we are not compatible with branch-cache-v3 yet
    ui.setconfig(
        b'experimental',
        b'branch-cache-v3',
        b'no',
        b'topic-extension',
    )

    destination.modsetup(ui)
    discovery.modsetup(ui)
    topicmap.modsetup(ui)
    setupimportexport(ui)

    extensions.afterloaded(b'rebase', _fixrebase)

    entry = extensions.wrapcommand(commands.table, b'commit', commitwrap)
    entry[1].append((b't', b'topic', b'',
                     _(b"use specified topic"), _(b'TOPIC')))

    entry = extensions.wrapcommand(commands.table, b'push', pushoutgoingwrap)
    entry[1].append((b't', b'topic', b'',
                     _(b"topic to push"), _(b'TOPIC')))

    entry = extensions.wrapcommand(commands.table, b'outgoing',
                                   pushoutgoingwrap)
    entry[1].append((b't', b'topic', b'',
                     _(b"topic to push"), _(b'TOPIC')))

    extensions.wrapfunction(cmdutil, 'buildcommittext', committextwrap)
    extensions.wrapfunction(merge, '_update', mergeupdatewrap)
    # We need to check whether t0 or b0 or s0 is passed to override the default update
    # behaviour of changing topic and I can't find a better way
    # to do that as scmutil.revsingle returns the rev number and hence we can't
    # plug into logic for this into mergemod.update().
    extensions.wrapcommand(commands.table, b'update', checkt0)

    extensions.wrapcommand(commands.table, b'summary', wrap_summary)

    extensions.wrapcommand(commands.table, b'tag', wrap_tag_cmd)

    try:
        evolve = extensions.find(b'evolve')
        extensions.wrapfunction(evolve.rewriteutil, "presplitupdate",
                                wrappresplitupdate)
    except (KeyError, AttributeError):
        pass

    cmdutil.summaryhooks.add(b'topic', summaryhook)

    # Wrap workingctx extra to return the topic name
    extensions.wrapfunction(context.workingctx, '__init__', wrapinit)
    # Wrap workingctx.branch() to return branch name in the "//" format
    extensions.wrapfunction(context.workingctx, 'branch', wrapwctxbranch)
    # Wrap workingctx.dirty() to check branch//namespace/topic
    extensions.wrapfunction(context.workingctx, 'dirty', wrapwctxdirty)
    # Wrap changelog.add to drop empty topic
    extensions.wrapfunction(changelog.changelog, 'add', wrapadd)
    # Make exchange._checkpublish handle experimental.topic.publish-bare-branch
    extensions.wrapfunction(exchange, '_checkpublish',
                            flow.replacecheckpublish)

    try:
        histedit = extensions.find(b'histedit')
    except KeyError:
        pass
    else:
        # Make histedit preserve topics of edited commits
        extensions.wrapfunction(histedit.histeditaction, 'applychange',
                                applychangewrap)

    # Wrapping precheck() both in core and in evolve to make sure all rewrite
    # operations that could use precheck() are covered
    extensions.wrapfunction(rewriteutil, 'precheck', wrapprecheck)
    try:
        evolve = extensions.find(b'evolve')
        extensions.wrapfunction(evolve.rewriteutil, 'precheck', wrapprecheck)
    except (KeyError, AttributeError):
        pass

    extensions.wrapfunction(bundlerepo, 'makebundlerepository', wrapmakebundlerepository)

    server.setupserver(ui)

def reposetup(ui, repo):
    if not isinstance(repo, localrepo.localrepository):
        return # this can be a peer in the ssh case (puzzling)

    repo = repo.unfiltered()

    if repo.ui.config(b'experimental', b'thg.displaynames') is None:
        repo.ui.setconfig(b'experimental', b'thg.displaynames', b'topics',
                          source=b'topic-extension')

    # BUG: inmemory rebase drops the topic, and fails to switch to the new
    # topic.  Disable inmemory rebase for now.
    if repo.ui.configbool(b'rebase', b'experimental.inmemory'):
        repo.ui.setconfig(b'rebase', b'experimental.inmemory', b'False',
                          source=b'topic-extension')

    class topicrepo(repo.__class__):

        # attribute for other code to distinct between repo with topic and repo without
        hastopicext = True

        def _restrictcapabilities(self, caps):
            caps = super(topicrepo, self)._restrictcapabilities(caps)
            caps.add(b'topics')
            caps.add(b'topics-namespaces')
            if self.ui.configbool(b'phases', b'publish'):
                mode = b'all'
            elif self.ui.configbool(b'experimental',
                                    b'topic.publish-bare-branch'):
                mode = b'auto'
            else:
                mode = b'none'
            caps.add(b'ext-topics-publish=%s' % mode)
            caps.add(b'ext-topics-tns-heads')
            return caps

        def commit(self, *args, **kwargs):
            configoverride = util.nullcontextmanager()
            if self.currenttopic != self[b'.'].topic():
                # bypass the core "nothing changed" logic
                configoverride = self.ui.configoverride({
                    (b'ui', b'allowemptycommit'): True
                }, b'topic-extension')
            with configoverride:
                return super(topicrepo, self).commit(*args, **kwargs)

        def commitctx(self, ctx, *args, **kwargs):
            if isinstance(ctx, context.workingcommitctx):
                tns = self.currenttns
                topic = self.currenttopic
                # topic source:
                # - 'local': we need to put currently active tns and topic into
                #   commit extras in any case
                # - 'other': we could use active tns and topic, but only if
                #   commit extras don't already have them
                ts = self.ui.config(b'_internal', b'topic-source')
                if ts == b'local' or (tns != b'none' and b'topic-namespace' not in ctx.extra()):
                    # default value will be dropped from extra later on
                    ctx.extra()[b'topic-namespace'] = tns
                if ts == b'local' or (topic and constants.extrakey not in ctx.extra()):
                    # empty value will be dropped from extra later on
                    ctx.extra()[constants.extrakey] = topic
            return super(topicrepo, self).commitctx(ctx, *args, **kwargs)

        @util.propertycache
        def _tnscache(self):
            return {}

        @property
        def topic_namespaces(self):
            if self._topic_namespaces is not None:
                return self._topic_namespaces
            namespaces = set([b'none', self.currenttns])
            for c in self.set(b'not public()'):
                namespaces.add(c.topic_namespace())
            namespaces.remove(b'none')
            self._topic_namespaces = namespaces
            return namespaces

        def wlock(self, wait=True, **kwargs):
            wlock = super(topicrepo, self).wlock(wait=wait, **kwargs)
            # we should definitely drop this at some point, but it depends on
            # our own release schedule, not core's, so here's hg 1.0
            # hg <= 1.0 (cfa08c88a5c4)
            if wlock is not None and wlock.held:
                try:
                    if self.vfs.read(b'topic-namespace') == b'none':
                        repo.vfs.unlinkpath(b'topic-namespace')
                except IOError as err:
                    if err.errno != errno.ENOENT:
                        raise
            return wlock

        @property
        def currenttns(self):
            tns = self.vfs.tryread(b'topic-namespace') or b'none'
            return encoding.tolocal(tns)

        @util.propertycache
        def _topiccache(self):
            return {}

        @property
        def topics(self):
            if self._topics is not None:
                return self._topics
            topics = set([b'', self.currenttopic])
            for c in self.set(b'not public()'):
                topics.add(c.topic())
            topics.remove(b'')
            self._topics = topics
            return topics

        @property
        def currenttopic(self):
            topic = self.vfs.tryread(b'topic')
            return encoding.tolocal(topic)

        # overwritten at the instance level by topicmap.py
        _autobranchmaptopic = True

        def branchmap(self, topic=None, convertbm=False):
            if topic is None:
                topic = getattr(self, '_autobranchmaptopic', False)
            topicfilter = topicmap.topicfilter(self.filtername)
            if not topic or topicfilter == self.filtername:
                return super(topicrepo, self).branchmap()
            bm = self.filtered(topicfilter).branchmap()
            if convertbm:
                for key in list(bm):
                    branch, tns, topic = common.parsefqbn(key)
                    if topic:
                        value = bm._entries.pop(key)
                        # we lose namespace when converting to ":" format
                        key = b'%s:%s' % (branch, topic)
                        bm._entries[key] = value
            return bm

        def branchmaptns(self, topic=None):
            """branchmap using fqbn as keys"""
            if topic is None:
                topic = getattr(self, '_autobranchmaptopic', False)
            topicfilter = topicmap.topicfilter(self.filtername)
            if not topic or topicfilter == self.filtername:
                return super(topicrepo, self).branchmap()
            return self.filtered(topicfilter).branchmap()

        def branchheads(self, branch=None, start=None, closed=False):
            if branch is None:
                branch = self[None].branch()
                branch = common.formatfqbn(branch, self.currenttns, self.currenttopic)
            return super(topicrepo, self).branchheads(branch=branch,
                                                      start=start,
                                                      closed=closed)

        def invalidatecaches(self):
            self._tnscache.clear()
            self._topiccache.clear()
            super(topicrepo, self).invalidatecaches()

        def invalidatevolatilesets(self):
            # XXX we might be able to move this to something invalidated less often
            super(topicrepo, self).invalidatevolatilesets()
            self._topic_namespaces = None
            self._topics = None

        def peer(self, *args, **kwargs):
            peer = super(topicrepo, self).peer(*args, **kwargs)
            if getattr(peer, '_repo', None) is not None: # localpeer
                class topicpeer(peer.__class__):
                    def branchmap(self):
                        usetopic = not self._repo.publishing()
                        return self._repo.branchmap(topic=usetopic, convertbm=usetopic)

                    def branchmaptns(self):
                        usetopic = not self._repo.publishing()
                        return self._repo.branchmaptns(topic=usetopic)

                    def tns_heads(self, namespaces):
                        if b'*' in namespaces:
                            # pulling all topic namespaces, all changesets are visible
                            return self._repo.heads()
                        else:
                            # only changesets in the selected topic namespaces are visible
                            h = []
                            bm = self._repo.branchmaptns()
                            for branch, nodes in compat.branchmapitems(bm):
                                namedbranch, tns, topic = common.parsefqbn(branch)
                                if tns == b'none' or tns in namespaces:
                                    h.extend(nodes)
                            return h
                peer.__class__ = topicpeer
            return peer

        def transaction(self, desc, *a, **k):
            ctr = self.currenttransaction()
            tr = super(topicrepo, self).transaction(desc, *a, **k)
            if desc in (b'strip', b'repair') or ctr is not None:
                return tr

            reporef = weakref.ref(self)
            if self.ui.configbool(b'experimental', b'enforce-single-head'):
                def _validate_single_head(tr2):
                    repo = reporef()
                    flow.enforcesinglehead(repo, tr2)

                tr.addvalidator(b'000-enforce-single-head', _validate_single_head)

            topicmodeserver = self.ui.config(b'experimental',
                                             b'topic-mode.server', b'ignore')
            publishbare = self.ui.configbool(b'experimental',
                                             b'topic.publish-bare-branch')
            ispush = desc.startswith((b'push', b'serve'))
            if (topicmodeserver != b'ignore' and ispush):
                def _validate_untopiced(tr2):
                    repo = reporef()
                    flow.rejectuntopicedchangeset(repo, tr2)

                tr.addvalidator(b'000-reject-untopiced', _validate_untopiced)

            elif publishbare and ispush:
                origclose = tr.close
                trref = weakref.ref(tr)

                def close():
                    repo = reporef()
                    tr2 = trref()
                    flow.publishbarebranch(repo, tr2)
                    origclose()
                tr.close = close
            allow_publish = self.ui.configbool(b'experimental',
                                               b'topic.allow-publish',
                                               True)
            if not allow_publish:
                def _validate_publish(tr2):
                    repo = reporef()
                    flow.reject_publish(repo, tr2)

                tr.addvalidator(b'000-reject-publish', _validate_publish)

            if self.ui.configbool(b'experimental', b'tns-reject-push'):

                def _validate_csets_with_tns(tr2):
                    repo = reporef()
                    flow.reject_csets_with_tns(repo, tr2)

                tr.addvalidator(b'000-reject-csets-with-tns', _validate_csets_with_tns)

            def _validate_affected_tns(tr2):
                repo = reporef()
                find_affected_tns(repo, tr2)

            tr.addvalidator(b'999-find-affected-tns', _validate_affected_tns)

            # real transaction start
            ct = self.currenttopic
            if not ct:
                return tr
            ctwasempty = stack.stack(self, topic=ct).changesetcount == 0

            reporef = weakref.ref(self)

            def currenttopicempty(tr):
                # check active topic emptiness
                repo = reporef()
                csetcount = stack.stack(repo, topic=ct).changesetcount
                empty = csetcount == 0
                if empty and not ctwasempty:
                    ui.status(b"active topic '%s' is now empty\n"
                              % ui.label(ct, b'topic.active'))
                    if (b'phase' in tr._names
                            or any(n.startswith(b'push-response')
                                   for n in tr._names)):
                        ui.status(_(b"(use 'hg topic --clear' to clear it if needed)\n"))
                hint = _(b"(see 'hg help topics' for more information)\n")
                if ctwasempty and not empty:
                    if csetcount == 1:
                        msg = _(b"active topic '%s' grew its first changeset\n%s")
                        ui.status(msg % (ui.label(ct, b'topic.active'), hint))
                    else:
                        msg = _(b"active topic '%s' grew its %d first changesets\n%s")
                        ui.status(msg % (ui.label(ct, b'topic.active'), csetcount, hint))

            tr.addpostclose(b'signalcurrenttopicempty', currenttopicempty)
            return tr

    repo.__class__ = topicrepo
    repo._topic_namespaces = None
    repo._topics = None
    if util.safehasattr(repo, 'names'):
        repo.names.addnamespace(namespaces.namespace(
            b'topics', b'topic', namemap=_namemap, nodemap=_nodemap,
            listnames=lambda repo: repo.topics))

templatekeyword = registrar.templatekeyword()

@templatekeyword(b'topic', requires={b'ctx'})
def topickw(context, mapping):
    """String. The topic of the changeset"""
    ctx = context.resource(mapping, b'ctx')
    return ctx.topic()

@templatekeyword(b'topicidx', requires={b'ctx'})
def topicidxkw(context, mapping):
    """Integer. Index of the changeset as a stack alias"""
    ctx = context.resource(mapping, b'ctx')
    return ctx.topicidx()

@templatekeyword(b'topic_namespace', requires={b'ctx'})
def topicnamespacekw(context, mapping):
    """String. The topic namespace of the changeset"""
    ctx = context.resource(mapping, b'ctx')
    return ctx.topic_namespace()

@templatekeyword(b'fqbn', requires={b'ctx'})
def fqbnkw(context, mapping):
    """String. The branch//namespace/topic of the changeset"""
    ctx = context.resource(mapping, b'ctx')
    return ctx.fqbn()

def wrapinit(orig, self, repo, *args, **kwargs):
    orig(self, repo, *args, **kwargs)
    if not hastopicext(repo):
        return
    if b'topic-namespace' not in self._extra:
        if getattr(repo, 'currenttns', b''):
            self._extra[b'topic-namespace'] = repo.currenttns
        else:
            # Default value will be dropped from extra by another hack at the changegroup level
            self._extra[b'topic-namespace'] = b'none'
    if constants.extrakey not in self._extra:
        if getattr(repo, 'currenttopic', b''):
            self._extra[constants.extrakey] = repo.currenttopic
        else:
            # Empty key will be dropped from extra by another hack at the changegroup level
            self._extra[constants.extrakey] = b''

def wrapadd(orig, cl, manifest, files, desc, transaction, p1, p2, user,
            date=None, extra=None):
    if b'topic-namespace' in extra and extra[b'topic-namespace'] == b'none':
        extra = extra.copy()
        del extra[b'topic-namespace']
    if constants.extrakey in extra and not extra[constants.extrakey]:
        extra = extra.copy()
        del extra[constants.extrakey]
    if constants.extrakey not in extra and b'topic-namespace' in extra:
        # if topic is not in extra, drop namespace as well
        extra = extra.copy()
        del extra[b'topic-namespace']
    return orig(cl, manifest, files, desc, transaction, p1, p2, user,
                date=date, extra=extra)

def applychangewrap(orig, self):
    orig(self)
    repo = self.repo
    rulectx = repo[self.node]

    topic = None
    if util.safehasattr(rulectx, 'topic'):
        topic = rulectx.topic()
    _changecurrenttopic(repo, topic)


# revset predicates are automatically registered at loading via this symbol
revsetpredicate = topicrevset.revsetpredicate

@command(b'topics', [
        (b'', b'clear', False, b'clear active topic if any'),
        (b'r', b'rev', [], b'revset of existing revisions', _(b'REV')),
        (b'l', b'list', False, b'show the stack of changeset in the topic'),
        (b'', b'age', False, b'show when you last touched the topics'),
        (b'', b'current', None, b'display the current topic only'),
    ] + commands.formatteropts,
    _(b'hg topics [OPTION]... [-r REV]... [TOPIC]'),
    helpcategory=registrar.command.CATEGORY_CHANGE_ORGANIZATION,
)
def topics(ui, repo, topic=None, **opts):
    """View current topic, set current topic, change topic for a set of revisions, or see all topics.

    Clear topic on existing topiced revisions::

      hg topics --rev <related revset> --clear

    Change topic on some revisions::

      hg topics <newtopicname> --rev <related revset>

    Clear current topic::

      hg topics --clear

    Set current topic::

      hg topics <topicname>

    List of topics::

      hg topics

    List of topics sorted according to their last touched time displaying last
    touched time and the user who last touched the topic::

      hg topics --age

    The active topic (if any) will be prepended with a "*".

    The `--current` flag helps to take active topic into account. For
    example, if you want to set the topic on all the draft changesets to the
    active topic, you can do:
        `hg topics -r "draft()" --current`

    The --verbose version of this command display various information on the state of each topic."""

    clear = opts.get('clear')
    list = opts.get('list')
    rev = opts.get('rev')
    current = opts.get('current')
    age = opts.get('age')

    if current and topic:
        raise error.InputError(_(b"cannot use --current when setting a topic"))
    if current and clear:
        raise error.InputError(_(b"cannot use --current and --clear"))
    if clear and topic:
        raise error.InputError(_(b"cannot use --clear when setting a topic"))
    if age and topic:
        raise error.InputError(_(b"cannot use --age while setting a topic"))

    cmdutil.check_incompatible_arguments(opts, 'list', ('clear', 'rev'))

    touchedrevs = set()
    if rev:
        touchedrevs = scmutil.revrange(repo, rev)

    if topic:
        topic = topic.strip()
        if not topic:
            raise error.InputError(_(b"topic names cannot consist entirely of whitespace"))
        # Have some restrictions on the topic name just like bookmark name
        scmutil.checknewlabel(repo, topic, b'topic')

        helptxt = _(b"topic names can only consist of alphanumeric, '-',"
                    b" '_' and '.' characters")
        try:
            utopic = encoding.unifromlocal(topic)
        except error.Abort:
            # Maybe we should allow these topic names as well, as long as they
            # don't break any other rules
            utopic = ''
        rmatch = re.match(r'[-_.\w]+', utopic, re.UNICODE)
        if not utopic or not rmatch or rmatch.group(0) != utopic:
            raise error.InputError(_(b"invalid topic name: '%s'") % topic, hint=helptxt)

    if list:
        ui.pager(b'topics')
        if not topic:
            topic = repo.currenttopic
        if not topic:
            raise error.Abort(_(b'no active topic to list'))
        return stack.showstack(ui, repo, topic=topic,
                               opts=pycompat.byteskwargs(opts))

    if touchedrevs:
        if not obsolete.isenabled(repo, obsolete.createmarkersopt):
            raise error.Abort(_(b'must have obsolete enabled to change topics'))
        if clear:
            topic = None
        elif opts.get('current'):
            topic = repo.currenttopic
        elif not topic:
            raise error.Abort(b'changing topic requires a topic name or --clear')
        if repo.revs(b'%ld and public()', touchedrevs):
            raise error.Abort(b"can't change topic of a public change")
        wl = lock = txn = None
        try:
            wl = repo.wlock()
            lock = repo.lock()
            txn = repo.transaction(b'rewrite-topics')
            rewrote = _changetopics(ui, repo, touchedrevs, topic)
            txn.close()
            if topic is None:
                ui.status(b'cleared topic on %d changesets\n' % rewrote)
            else:
                ui.status(b'changed topic on %d changesets to "%s"\n' % (rewrote,
                                                                         topic))
        finally:
            lockmod.release(txn, lock, wl)
            repo.invalidate()
        return

    ct = repo.currenttopic
    if clear:
        if ct:
            st = stack.stack(repo, topic=ct)
            if not st:
                ui.status(_(b'clearing empty topic "%s"\n') % ct)
        return _changecurrenttopic(repo, None)

    if topic:
        if not ct:
            ui.status(_(b'marked working directory as topic: %s\n')
                      % ui.label(topic, b'topic.active'))
        return _changecurrenttopic(repo, topic)

    ui.pager(b'topics')
    # `hg topic --current`
    ret = 0
    if current and not ct:
        ui.write_err(_(b'no active topic\n'))
        ret = 1
    elif current:
        fm = ui.formatter(b'topic', pycompat.byteskwargs(opts))
        namemask = b'%s\n'
        label = b'topic.active'
        fm.startitem()
        fm.write(b'topic', namemask, ct, label=label)
        fm.end()
    else:
        _listtopics(ui, repo, opts)
    return ret

@command(b'stack', [
        (b'c', b'children', None,
            _(b'display data about children outside of the stack'))
    ] + commands.formatteropts,
    _(b'hg stack [TOPIC]'),
    helpcategory=registrar.command.CATEGORY_CHANGE_NAVIGATION,
)
def cmdstack(ui, repo, topic=b'', **opts):
    """list all changesets in a topic and other information

    List the current topic by default.

    The --verbose version shows short nodes for the commits also.
    """
    if not topic:
        topic = None
    branch = None
    if topic is None and repo.currenttopic:
        topic = repo.currenttopic
    if topic is None:
        branch = repo[None].branch()
    ui.pager(b'stack')
    return stack.showstack(ui, repo, branch=branch, topic=topic,
                           opts=pycompat.byteskwargs(opts))

@command(b'debugcb|debugconvertbookmark', [
        (b'b', b'bookmark', b'', _(b'bookmark to convert to topic')),
        (b'', b'all', None, _(b'convert all bookmarks to topics')),
    ],
    _(b'[-b BOOKMARK] [--all]'))
def debugconvertbookmark(ui, repo, **opts):
    """Converts a bookmark to a topic with the same name.
    """

    bookmark = opts.get('bookmark')
    convertall = opts.get('all')

    if convertall and bookmark:
        raise error.Abort(_(b"cannot use '--all' and '-b' together"))
    if not (convertall or bookmark):
        raise error.Abort(_(b"you must specify either '--all' or '-b'"))

    bmstore = repo._bookmarks

    nodetobook = {}
    for book, revnode in bmstore.items():
        if nodetobook.get(revnode):
            nodetobook[revnode].append(book)
        else:
            nodetobook[revnode] = [book]

    # a list of nodes which we have skipped so that we don't print the skip
    # warning repeatedly
    skipped = []

    actions = {}

    lock = wlock = tr = None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        if bookmark:
            try:
                node = bmstore[bookmark]
            except KeyError:
                raise error.Abort(_(b"no such bookmark exists: '%s'") % bookmark)

            revnum = repo[node].rev()
            if len(nodetobook[node]) > 1:
                ui.status(_(b"skipping revision %d as it has multiple "
                            b"bookmarks on it\n") % revnum)
                return
            targetrevs = _findconvertbmarktopic(repo, bookmark)
            if targetrevs:
                actions[(bookmark, revnum)] = targetrevs

        elif convertall:
            for bmark, revnode in sorted(bmstore.items()):
                revnum = repo[revnode].rev()
                if revnum in skipped:
                    continue
                if len(nodetobook[revnode]) > 1:
                    ui.status(_(b"skipping revision %d as it has multiple "
                                b"bookmarks on it\n") % revnum)
                    skipped.append(revnum)
                    continue
                if bmark == b'@':
                    continue
                targetrevs = _findconvertbmarktopic(repo, bmark)
                if targetrevs:
                    actions[(bmark, revnum)] = targetrevs

        if actions:
            try:
                tr = repo.transaction(b'debugconvertbookmark')
                for ((bmark, revnum), targetrevs) in sorted(actions.items()):
                    _applyconvertbmarktopic(ui, repo, targetrevs, revnum, bmark, tr)
                tr.close()
            finally:
                tr.release()
    finally:
        lockmod.release(lock, wlock)

# inspired from mercurial.repair.stripbmrevset
CONVERTBOOKREVSET = b"""
not public() and (
    ancestors(bookmark(%s))
    and not ancestors(
        (
            (head() and not bookmark(%s))
            or (bookmark() - bookmark(%s))
        ) - (
            descendants(bookmark(%s))
            - bookmark(%s)
        )
    )
)
"""

def _findconvertbmarktopic(repo, bmark):
    """find revisions unambiguously defined by a bookmark

    find all changesets under the bookmark and under that bookmark only.
    """
    return repo.revs(CONVERTBOOKREVSET, bmark, bmark, bmark, bmark, bmark)

def _applyconvertbmarktopic(ui, repo, revs, old, bmark, tr):
    """apply bookmark conversion to topic

    Sets a topic as same as bname to all the changesets under the bookmark
    and delete the bookmark, if topic is set to any changeset

    old is the revision on which bookmark bmark is and tr is transaction object.
    """

    rewrote = _changetopics(ui, repo, revs, bmark)
    # We didn't changed topic to any changesets because the revset
    # returned an empty set of revisions, so let's skip deleting the
    # bookmark corresponding to which we didn't put a topic on any
    # changeset
    if rewrote == 0:
        return
    ui.status(_(b'changed topic to "%s" on %d revisions\n') % (bmark,
              rewrote))
    ui.debug(b'removing bookmark "%s" from "%d"\n' % (bmark, old))
    bookmarks.delete(repo, tr, [bmark])

def _changecurrenttopic(repo, newtopic):
    """changes the current topic."""

    if newtopic:
        with repo.wlock():
            repo.vfs.write(b'topic', newtopic)
    else:
        if repo.vfs.exists(b'topic'):
            repo.vfs.unlink(b'topic')

def _changetopics(ui, repo, revs, newtopic):
    """ Changes topic to newtopic of all the revisions in the revset and return
    the count of revisions whose topic has been changed.
    """
    rewrote = 0
    p1 = None
    p2 = None
    successors = {}
    for r in revs:
        c = repo[r]

        if len(c.parents()) > 1:
            # ctx.files() isn't reliable for merges, so fall back to the
            # slower repo.status() method
            st = c.p1().status(c)
            files = set(st.modified) | set(st.added) | set(st.removed)
        else:
            files = set(c.files())

        def filectxfn(repo, ctx, path):
            try:
                return c[path]
            except error.ManifestLookupError:
                return None
        fixedextra = dict(c.extra())
        ui.debug(b'old node id is %s\n' % node.hex(c.node()))
        ui.debug(b'origextra: %r\n' % fixedextra)
        oldtopic = fixedextra.get(constants.extrakey, None)
        if oldtopic == newtopic:
            continue
        if newtopic is None:
            del fixedextra[constants.extrakey]
        else:
            fixedextra[constants.extrakey] = newtopic
        fixedextra[constants.changekey] = c.hex()
        ui.debug(b'changing topic of %s from %s to %s\n' % (
            c, oldtopic or b'<none>', newtopic or b'<none>'))
        ui.debug(b'fixedextra: %r\n' % fixedextra)
        # While changing topic of set of linear commits, make sure that
        # we base our commits on new parent rather than old parent which
        # was obsoleted while changing the topic
        p1 = c.p1().node()
        p2 = c.p2().node()
        if p1 in successors:
            p1 = successors[p1][0]
        if p2 in successors:
            p2 = successors[p2][0]
        mc = context.memctx(repo,
                            (p1, p2),
                            c.description(),
                            files,
                            filectxfn,
                            user=c.user(),
                            date=c.date(),
                            extra=fixedextra)

        # phase handling
        commitphase = c.phase()
        overrides = {(b'phases', b'new-commit'): commitphase}
        with repo.ui.configoverride(overrides, b'changetopic'):
            newnode = repo.commitctx(mc)

        successors[c.node()] = (newnode,)
        ui.debug(b'new node id is %s\n' % node.hex(newnode))
        rewrote += 1

    # create obsmarkers and move bookmarks
    # XXX we should be creating marker as we go instead of only at the end,
    # this makes the operations more modulars
    compat.cleanup_nodes(repo, successors, b'changetopics')

    # move the working copy too
    wctx = repo[None]
    # in-progress merge is a bit too complex for now.
    if len(wctx.parents()) == 1:
        newid = successors.get(wctx.p1().node())
        if newid is not None:
            compat.hg_update(repo, newid[0], quietempty=True)
    return rewrote

def _listtopics(ui, repo, opts):
    fm = ui.formatter(b'topics', pycompat.byteskwargs(opts))
    activetopic = repo.currenttopic
    namemask = b'%s'
    if repo.topics:
        maxwidth = max(len(t) for t in repo.topics)
        namemask = b'%%-%is' % maxwidth
    if opts.get('age'):
        # here we sort by age and topic name
        topicsdata = sorted(_getlasttouched(repo, repo.topics))
    else:
        # here we sort by topic name only
        topicsdata = (
            (None, topic, None, None)
            for topic in sorted(repo.topics)
        )
    for age, topic, date, user in topicsdata:
        fm.startitem()
        marker = b' '
        label = b'topic'
        active = (topic == activetopic)
        if active:
            marker = b'*'
            label = b'topic.active'
        if not ui.quiet:
            # registering the active data is made explicitly later
            fm.plain(b' %s ' % marker, label=label)
        fm.write(b'topic', namemask, topic, label=label)
        fm.data(active=active)

        if ui.quiet:
            fm.plain(b'\n')
            continue
        fm.plain(b' (')
        if date:
            if age == -1:
                timestr = b'empty and active'
            else:
                timestr = templatefilters.age(date)
            fm.write(b'lasttouched', b'%s', timestr, label=b'topic.list.time')
        if user:
            fm.write(b'usertouched', b' by %s', user, label=b'topic.list.user')
        if date:
            fm.plain(b', ')
        data = stack.stack(repo, topic=topic)
        if ui.verbose:
            fm.write(b'branches+', b'on branch: %s',
                     b'+'.join(data.branches), # XXX use list directly after 4.0 is released
                     label=b'topic.list.branches')

            fm.plain(b', ')
        fm.write(b'changesetcount', b'%d changesets', data.changesetcount,
                 label=b'topic.list.changesetcount')

        if data.unstablecount:
            fm.plain(b', ')
            fm.write(b'unstablecount', b'%d unstable',
                     data.unstablecount,
                     label=b'topic.list.unstablecount')

        headcount = len(data.heads)
        if 1 < headcount:
            fm.plain(b', ')
            fm.write(b'headcount', b'%d heads',
                     headcount,
                     label=b'topic.list.headcount.multiple')

        if ui.verbose:
            # XXX we should include the data even when not verbose

            behindcount = data.behindcount
            if 0 < behindcount:
                fm.plain(b', ')
                fm.write(b'behindcount', b'%d behind',
                         behindcount,
                         label=b'topic.list.behindcount')
            elif -1 == behindcount:
                fm.plain(b', ')
                fm.write(b'behinderror', b'%s',
                         _(b'ambiguous destination: %s') % data.behinderror,
                         label=b'topic.list.behinderror')
        fm.plain(b')\n')
    fm.end()

def _getlasttouched(repo, topics):
    """
    Calculates the last time a topic was used. Returns a generator of 4-tuples:
    (age in seconds, topic name, date, and user who last touched the topic).
    """
    curtime = time.time()
    for topic in topics:
        age = -1
        user = None
        maxtime = (0, 0)
        trevs = repo.revs(b"topic(%s)", topic)
        # Need to check for the time of all changesets in the topic, whether
        # they are obsolete of non-heads
        # XXX: can we just rely on the max rev number for this
        for revs in trevs:
            rt = repo[revs].date()
            if rt[0] >= maxtime[0]:
                # Can store the rev to gather more info
                # latesthead = revs
                maxtime = rt
                user = repo[revs].user()
            # looking on the markers also to get more information and accurate
            # last touch time.
            obsmarkers = obsutil.getmarkers(repo, [repo[revs].node()])
            for marker in obsmarkers:
                rt = marker.date()
                if rt[0] > maxtime[0]:
                    user = marker.metadata().get(b'user', user)
                    maxtime = rt

        username = stack.parseusername(user)
        if trevs:
            age = curtime - maxtime[0]

        yield (age, topic, maxtime, username)

def summaryhook(ui, repo):
    t = getattr(repo, 'currenttopic', b'')
    if not t:
        return
    # i18n: column positioning for "hg summary"
    ui.write(_(b"topic:  %s\n") % ui.label(t, b'topic.active'))

_validmode = [
    b'ignore',
    b'warning',
    b'enforce',
    b'enforce-all',
    b'random',
    b'random-all',
]

def _configtopicmode(ui):
    """ Parse the config to get the topicmode
    """
    topicmode = ui.config(b'experimental', b'topic-mode')

    # Fallback to read enforce-topic
    if topicmode is None:
        enforcetopic = ui.configbool(b'experimental', b'enforce-topic')
        if enforcetopic:
            topicmode = b"enforce"
    if topicmode not in _validmode:
        topicmode = _validmode[0]

    return topicmode

def commitwrap(orig, ui, repo, *args, **opts):
    if not hastopicext(repo):
        return orig(ui, repo, *args, **opts)
    with repo.wlock():
        topicmode = _configtopicmode(ui)
        ismergecommit = len(repo[None].parents()) == 2

        notopic = not repo.currenttopic
        mayabort = (topicmode == b"enforce" and not ismergecommit)
        maywarn = (topicmode == b"warning"
                   or (topicmode == b"enforce" and ismergecommit))

        mayrandom = False
        if topicmode == b"random":
            mayrandom = not ismergecommit
        elif topicmode == b"random-all":
            mayrandom = True

        if topicmode == b'enforce-all':
            ismergecommit = False
            mayabort = True
            maywarn = False

        hint = _(b"see 'hg help -e topic.topic-mode' for details")
        if opts.get('topic'):
            t = opts['topic']
            repo.vfs.write(b'topic', t)
        elif opts.get('amend'):
            pass
        elif notopic and mayabort:
            msg = _(b"no active topic")
            raise error.Abort(msg, hint=hint)
        elif notopic and maywarn:
            ui.warn(_(b"warning: new draft commit without topic\n"))
            if not ui.quiet:
                ui.warn((b"(%s)\n") % hint)
        elif notopic and mayrandom:
            repo.vfs.write(b'topic', randomname.randomtopicname(ui))
        return orig(ui, repo, *args, **opts)

def committextwrap(orig, repo, ctx, subs, extramsg):
    ret = orig(repo, ctx, subs, extramsg)
    if hastopicext(repo):
        t = repo.currenttopic
        if t:
            ret = ret.replace(b"\nHG: branch",
                              b"\nHG: topic '%s'\nHG: branch" % t)
    return ret

def pushoutgoingwrap(orig, ui, repo, *args, **opts):
    if opts.get('topic'):
        topic = opts['topic']
        if topic == b'.':
            topic = repo.currenttopic
        topic = b'literal:' + topic
        topicrevs = repo.revs(b'topic(%s) - obsolete()', topic)
        opts.setdefault('rev', []).extend(topicrevs)
    return orig(ui, repo, *args, **opts)

def mergeupdatewrap(orig, repo, node, branchmerge, force, *args, **kwargs):
    matcher = kwargs.get('matcher')
    partial = not (matcher is None or matcher.always())
    wlock = repo.wlock()
    isrebase = False
    ist0 = False
    try:
        mergemode = repo.ui.config(b'experimental', b'topic.linear-merge')

        old = None
        if mergemode == b'allow-from-bare-branch' and not repo[None].topic():
            unfi = repo.unfiltered()
            oldrepo = repo
            old = unfi.__class__

            class overridebranch(old):
                def __getitem__(self, rev):
                    ret = super(overridebranch, self).__getitem__(rev)
                    if rev == node:
                        b = ret.branch()
                        tns = ret.topic_namespace()
                        t = ret.topic()
                        # topic is required for merging from bare branch
                        if t:
                            ret.branch = lambda: common.formatfqbn(b, tns, t)
                    return ret
            unfi.__class__ = overridebranch
            if repo.filtername is not None:
                repo = unfi.filtered(repo.filtername)

        try:
            ret = orig(repo, node, branchmerge, force, *args, **kwargs)
        finally:
            if old is not None:
                unfi.__class__ = old
                repo = oldrepo

        if not hastopicext(repo):
            return ret
        # The mergeupdatewrap function makes the destination's topic as the
        # current topic. This is right for merge but wrong for rebase. We check
        # if rebase is running and update the currenttopic to topic of new
        # rebased commit. We have explicitly stored in config if rebase is
        # running.
        otns = repo.currenttns
        ot = repo.currenttopic
        if repo.ui.hasconfig(b'experimental', b'topicrebase'):
            isrebase = True
        if repo.ui.configbool(b'_internal', b'keep-topic'):
            ist0 = True
        if ((not partial and not branchmerge) or isrebase) and not ist0:
            tns = b'none'
            t = b''
            pctx = repo[node]
            if pctx.phase() > phases.public:
                tns = pctx.topic_namespace()
                t = pctx.topic()
            _changecurrenttns(repo, tns)
            if tns != b'none' and tns != otns:
                repo.ui.status(_(b"switching to topic-namespace %s\n") % tns)
            _changecurrenttopic(repo, t)
            if t and t != ot:
                repo.ui.status(_(b"switching to topic %s\n") % t)
            if ot and not t:
                st = stack.stack(repo, topic=ot)
                if not st:
                    repo.ui.status(_(b'clearing empty topic "%s"\n') % ot)
        elif ist0:
            repo.ui.status(_(b"preserving the current topic '%s'\n") % ot)
        return ret
    finally:
        wlock.release()

def checkt0(orig, ui, repo, node=None, rev=None, *args, **kwargs):

    thezeros = set([b't0', b'b0', b's0'])
    configoverride = util.nullcontextmanager()
    if node in thezeros or rev in thezeros:
        configoverride = repo.ui.configoverride({
            (b'_internal', b'keep-topic'): b'yes'
        }, source=b'topic-extension')
    with configoverride:
        return orig(ui, repo, node=node, rev=rev, *args, **kwargs)

def _fixrebase(loaded):
    if not loaded:
        return

    def savetopic(ctx, extra):
        if ctx.topic():
            extra[constants.extrakey] = ctx.topic()
            if ctx.topic_namespace() != b'none':
                extra[b'topic-namespace'] = ctx.topic_namespace()

    def setrebaseconfig(orig, ui, repo, **opts):
        repo.ui.setconfig(b'experimental', b'topicrebase', b'yes',
                          source=b'topic-extension')
        return orig(ui, repo, **opts)

    def new_init(orig, *args, **kwargs):
        runtime = orig(*args, **kwargs)

        if util.safehasattr(runtime, 'extrafns'):
            runtime.extrafns.append(savetopic)

        return runtime

    try:
        rebase = extensions.find(b"rebase")
        extensions.wrapfunction(rebase.rebaseruntime, '__init__', new_init)
        # This exists to store in the config that rebase is running so that we can
        # update the topic according to rebase. This is a hack and should be removed
        # when we have better options.
        extensions.wrapcommand(rebase.cmdtable, b'rebase', setrebaseconfig)
    except KeyError:
        pass

## preserve topic during import/export

def _exporttns(seq, ctx):
    tns = ctx.topic_namespace()
    if tns != b'none':
        return b'EXP-Topic-Namespace %s' % tns
    return None

def _exporttopic(seq, ctx):
    topic = ctx.topic()
    if topic:
        return b'EXP-Topic %s' % topic
    return None

def _importtns(repo, patchdata, extra, opts):
    if b'topic-namespace' in patchdata:
        extra[b'topic-namespace'] = patchdata[b'topic-namespace']

def _importtopic(repo, patchdata, extra, opts):
    if b'topic' in patchdata:
        extra[b'topic'] = patchdata[b'topic']

def setupimportexport(ui):
    """run at ui setup time to install import/export logic"""
    cmdutil.extraexport.append(b'topic-namespace')
    cmdutil.extraexportmap[b'topic-namespace'] = _exporttns
    cmdutil.extraexport.append(b'topic')
    cmdutil.extraexportmap[b'topic'] = _exporttopic
    cmdutil.extrapreimport.append(b'topic-namespace')
    cmdutil.extrapreimportmap[b'topic-namespace'] = _importtns
    cmdutil.extrapreimport.append(b'topic')
    cmdutil.extrapreimportmap[b'topic'] = _importtopic
    patch.patchheadermap.append((b'EXP-Topic-Namespace', b'topic-namespace'))
    patch.patchheadermap.append((b'EXP-Topic', b'topic'))

## preserve topic during split

def wrappresplitupdate(original, repo, ui, prev, ctx):
    # Save topic of revision
    tns = None
    topic = None
    if util.safehasattr(ctx, 'topic_namespace'):
        tns = ctx.topic_namespace()
    if util.safehasattr(ctx, 'topic'):
        topic = ctx.topic()

    # Update the working directory
    original(repo, ui, prev, ctx)

    # Restore the topic if need
    if tns != b'none':
        _changecurrenttns(repo, tns)
    if topic:
        _changecurrenttopic(repo, topic)

def wrapprecheck(orig, repo, revs, action=b'rewrite', check_divergence=True):
    orig(repo, revs, action, check_divergence=check_divergence)

    # TODO: at some point in future the default will change from '*' to the
    # default topic namespace for the current user
    allow = set(repo.ui.configlist(b'experimental', b'tns-allow-rewrite', [b'*']))
    if b'*' not in allow:
        namespaces = set(repo[rev].topic_namespace() for rev in revs)
        disallowed = namespaces - allow
        if disallowed:
            msg = _(b"refusing to %s changesets with these topic namespaces: %s")
            msg %= (action, b' '.join(disallowed))
            hint = _(b"modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces")
            raise error.InputError(msg, hint=hint)

def _changecurrenttns(repo, tns):
    if tns != b'none':
        with repo.wlock():
            repo.vfs.write(b'topic-namespace', tns)
    else:
        repo.vfs.unlinkpath(b'topic-namespace', ignoremissing=True)

@command(b'debug-topic-namespace', [
        (b'', b'clear', False, b'clear active topic namespace if any'),
    ],
    _(b'[NAMESPACE|--clear]'))
def debugtopicnamespace(ui, repo, tns=None, **opts):
    """set or show the current topic namespace"""
    if opts.get('clear'):
        if tns:
            raise error.Abort(_(b"cannot use --clear when setting a topic namespace"))
        tns = b'none'
    elif not tns:
        ui.write(b'%s\n' % repo.currenttns)
        return
    if tns:
        tns = tns.strip()
        if not tns:
            raise error.Abort(_(b"topic namespace cannot consist entirely of whitespace"))
        if b'/' in tns:
            raise error.Abort(_(b"topic namespace cannot contain '/' character"))
        scmutil.checknewlabel(repo, tns, b'topic namespace')

        helptxt = _(b"topic namespace names can only consist of alphanumeric, "
                    b"'-', '_' and '.' characters")
        try:
            utns = encoding.unifromlocal(tns)
        except error.Abort:
            # Maybe we should allow these topic names as well, as long as they
            # don't break any other rules
            utns = ''
        rmatch = re.match(r'[-_.\w]+', utns, re.UNICODE)
        if not utns or not rmatch or rmatch.group(0) != utns:
            raise error.InputError(_(b"invalid topic namespace name: '%s'") % tns, hint=helptxt)
    ctns = repo.currenttns
    _changecurrenttns(repo, tns)
    if ctns == b'none' and tns != b'none':
        repo.ui.status(_(b'marked working directory as topic namespace: %s\n')
                       % tns)

@command(b'debug-topic-namespaces', [])
def debugtopicnamespaces(ui, repo, **opts):
    """list repository namespaces"""
    for tns in repo.topic_namespaces:
        ui.write(b'%s\n' % (tns,))

@command(b'debug-default-topic-namespace', [
        (b'', b'none', True, b'find changesets with topic-namespace=none'),
        (b'', b'default', False, b'find changesets with topic-namespace=default'),
        (b'', b'clear', False, b'remove topic namespace from commit extras'),
    ] + commands.formatteropts)
def debugdefaulttns(ui, repo, **opts):
    """list changesets with the default topic namespace in commit extras"""
    opts = pycompat.byteskwargs(opts)
    condition = []
    if opts[b'none']:
        condition += [b'extra("topic-namespace", "none")']
    if opts[b'default']:
        condition += [b'extra("topic-namespace", "default")']
    if not condition:
        condition = [b'none()']
    revs = repo.revs(b'not public() and not obsolete() and (%lr)', condition)
    if opts[b'clear']:
        with repo.wlock(), repo.lock(), repo.transaction(b'debug-default-topic-namespace'):
            successors = {}
            for rev in revs:
                _clear_tns_extras(ui, repo, rev, successors)
            compat.cleanup_nodes(repo, successors, b'debug-default-topic-namespace')
        return
    displayer = logcmdutil.changesetdisplayer(ui, repo, opts)
    logcmdutil.displayrevs(ui, repo, revs, displayer, None)

def _clear_tns_extras(ui, repo, rev, successors):
    ctx = repo[rev]

    if len(ctx.parents()) > 1:
        # ctx.files() isn't reliable for merges, so fall back to the
        # slower repo.status() method
        st = ctx.p1().status(ctx)
        files = set(st.modified) | set(st.added) | set(st.removed)
    else:
        files = set(ctx.files())

    def filectxfn(repo, unused, path):
        try:
            return ctx[path]
        except error.ManifestLookupError:
            return None

    extra = ctx.extra().copy()
    del extra[b'topic-namespace']

    p1 = ctx.p1().node()
    p2 = ctx.p2().node()
    if p1 in successors:
        p1 = successors[p1][0]
    if p2 in successors:
        p2 = successors[p2][0]
    mc = context.memctx(repo,
                        (p1, p2),
                        ctx.description(),
                        files,
                        filectxfn,
                        user=ctx.user(),
                        date=ctx.date(),
                        extra=extra)

    overrides = {(b'phases', b'new-commit'): ctx.phase()}
    with repo.ui.configoverride(overrides, b'debug-default-topic-namespace'):
        newnode = repo.commitctx(mc)

    successors[ctx.node()] = (newnode,)

@command(b'debug-parse-fqbn', commands.formatteropts, _(b'FQBN'), optionalrepo=True)
def debugparsefqbn(ui, repo, fqbn, **opts):
    """parse branch//namespace/topic string into its components"""
    branch, tns, topic = common.parsefqbn(fqbn)
    opts = pycompat.byteskwargs(opts)
    fm = ui.formatter(b'debug-parse-namespace', opts)
    fm.startitem()
    fm.write(b'branch', b'branch:    %s\n', branch)
    fm.write(b'topic_namespace', b'namespace: %s\n', tns)
    fm.write(b'topic', b'topic:     %s\n', topic)
    fm.end()

@command(b'debug-format-fqbn', [
        (b'b', b'branch', b'', b'branch'),
        (b'n', b'topic-namespace', b'', b'topic namespace'),
        (b't', b'topic', b'', b'topic'),
        (b's', b'short', False, b'short format'),
    ], optionalrepo=True)
def debugformatfqbn(ui, repo, **opts):
    """format branch, namespace and topic into branch//namespace/topic string"""
    short = common.formatfqbn(opts.get('branch'), opts.get('topic_namespace'), opts.get('topic'), opts.get('short'))
    ui.write(b'%s\n' % short)
