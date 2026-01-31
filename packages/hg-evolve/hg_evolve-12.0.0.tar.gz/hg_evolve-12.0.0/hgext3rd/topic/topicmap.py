import hashlib

from mercurial.i18n import _
from mercurial.node import nullid
from mercurial import (
    branchmap,
    changegroup,
    cmdutil,
    extensions,
    repoview,
    util,
)

from mercurial.utils import repoviewutil

from . import (
    common,
    compat,
    discovery,
)

basefilter = set([b'base', b'immutable'])
def topicfilter(name):
    """return a "topic" version of a filter level"""
    if name in basefilter:
        return name
    elif name is None:
        return None
    elif name.endswith(b'-topic'):
        return name
    else:
        return name + b'-topic'

def istopicfilter(filtername):
    if filtername is None:
        return False
    return filtername.endswith(b'-topic')

def gettopicrepo(repo):
    if not common.hastopicext(repo):
        return repo
    filtername = topicfilter(repo.filtername)
    if filtername is None or filtername == repo.filtername:
        return repo
    return repo.filtered(filtername)

def _setuptopicfilter(ui):
    """extend the filter related mapping with topic related one"""
    # filter level not affected by topic that we should not override

    for plainname in list(repoview.filtertable):
        newfilter = topicfilter(plainname)
        if newfilter == plainname:
            # filter level not affected by topic that we should not override
            continue

        def revsfunc(repo, name=plainname):
            return repoview.filterrevs(repo, name)

        base = topicfilter(repoviewutil.subsettable[plainname])

        if newfilter not in repoview.filtertable:
            repoview.filtertable[newfilter] = revsfunc
            repoviewutil.subsettable[newfilter] = base
    repoview.filtertable[b'unfiltered-topic'] = lambda repo: frozenset()
    repoviewutil.subsettable[b'unfiltered-topic'] = b'visible-topic'

def _phaseshash(repo, maxrev):
    """uniq ID for a phase matching a set of rev"""
    cl = repo.changelog
    fr = cl.filteredrevs
    nppr = repo._phasecache.nonpublicphaseroots(repo)
    revs = sorted(set(r for r in nppr if r not in fr and r < maxrev))
    key = nullid
    if revs:
        s = hashlib.sha1()
        for rev in revs:
            s.update(b'%d;' % rev)
        key = s.digest()
    return key

def modsetup(ui):
    """call at uisetup time to install various wrappings"""
    _setuptopicfilter(ui)
    _wrapbmcache(ui)
    extensions.wrapfunction(changegroup.cg1unpacker, 'apply', cgapply)
    if util.safehasattr(cmdutil, 'future_head_change'):
        extensions.wrapfunction(cmdutil, 'future_head_change', fhchange)
        compat.overridecommitstatus(commitstatusv4)
    else:
        # hg <= 7.1 (45c5b012cffc)
        compat.overridecommitstatus(commitstatus)

def cgapply(orig, self, repo, *args, **kwargs):
    """make sure a topicmap is used when applying a changegroup"""
    newfilter = topicfilter(repo.filtername)
    if newfilter is None:
        other = repo
    else:
        other = repo.filtered(newfilter)
    return orig(self, other, *args, **kwargs)

def fhchange(orig, repo, close_branch=False):
    """same as cmdutil.future_head_change() in core, but with topics"""
    with discovery.override_context_branch(repo) as repo:
        return orig(repo, close_branch)

def commitstatus(orig, repo, node, branch, bheads=None, tip=None, **opts):
    # wrap commit status use the topic branch heads
    ctx = repo[node]
    ctxbranch = common.formatfqbn(branch=ctx.branch())
    if ctx.topic() and ctxbranch == branch:
        bheads = repo.branchheads(b"%s:%s" % (branch, ctx.topic()))

    with discovery.override_context_branch(repo) as repo:
        ret = orig(repo, node, branch, bheads=bheads, tip=tip, **opts)

    # logic copy-pasted from cmdutil.commitstatus()
    if ctx.topic():
        return ret
    parents = ctx.parents()

    if (not opts.get('amend') and bheads and node not in bheads and not any(
        p.node() in bheads and common.formatfqbn(branch=p.branch()) == branch
        for p in parents
    )):
        repo.ui.status(_(b"(consider using topic for lightweight branches."
                         b" See 'hg help topic')\n"))

    return ret

def commitstatusv4(orig, repo, node, head_change=None, tip=None, **opts):
    ctx = repo[node]

    if head_change is not None and ctx.topic():
        head_change.new_head = False

    with discovery.override_context_branch(repo) as repo:
        # technically core function doesn't need this context branch override,
        # but we do it anyway just in case
        ret = orig(repo, node, head_change=head_change, tip=tip, **opts)

    if tip is not None and repo.changelog.tip() == tip:
        # "commit already existed"
        return ret

    if ctx.topic():
        # we already use topic
        return ret

    if head_change is not None and head_change.new_head:
        repo.ui.status(_(b"(consider using topic for lightweight branches."
                         b" See 'hg help topic')\n"))

    return ret

def _wrapbmcache(ui):
    if util.safehasattr(branchmap, 'BranchCacheV2'):
        class TopicCache(_TopicCacheV2, branchmap.BranchCacheV2):
            pass
        branchmap.BranchCacheV2 = TopicCache

        class remotetopiccache(_TopicCacheV2, branchmap.remotebranchcache):
            pass
        branchmap.remotebranchcache = remotetopiccache
    else:
        # hg <= 6.7 (ec640dc9cebd)
        class topiccache(_topiccache, branchmap.branchcache):
            pass
        branchmap.branchcache = topiccache

        class remotetopiccache(_topiccache, branchmap.remotebranchcache):
            pass
        branchmap.remotebranchcache = remotetopiccache

        def _wrapupdatebmcachemethod(orig, self, repo):
            # pass in the bound method as the original
            return _wrapupdatebmcache(orig.__get__(self), repo)
        extensions.wrapfunction(branchmap.BranchMapCache, 'updatecache', _wrapupdatebmcachemethod)

def _wrapupdatebmcache(orig, repo):
    previous = getattr(repo, '_autobranchmaptopic', False)
    try:
        repo._autobranchmaptopic = False
        return orig(repo)
    finally:
        repo._autobranchmaptopic = previous

if util.safehasattr(branchmap, 'branchcache'):
    # we only use this in _topiccache that we only use in before 6.8
    #
    # hg <= 6.7 (82c1a388e86a)
    allbccls = (branchmap.branchcache, branchmap.remotebranchcache)

class _topiccache(object): # combine me with branchmap.branchcache

    def __init__(self, *args, **kwargs):
        super(_topiccache, self).__init__(*args, **kwargs)
        self.phaseshash = None

    def copy(self):
        """return an deep copy of the branchcache object"""
        assert isinstance(self, allbccls)  # help pytype
        args = (self._repo, self._entries, self.tipnode, self.tiprev, self.filteredhash,
                self._closednodes,)
        new = self.__class__(*args)
        new.phaseshash = self.phaseshash
        return new

    def load(self, repo, lineiter):
        """call branchmap.load(), and then transform branch names to be in the
        new "//" format
        """
        assert isinstance(self, branchmap.branchcache)  # help pytype
        super(_topiccache, self).load(repo, lineiter)

        for branch in tuple(self):
            formatted = common.formatfqbn(branch=branch)
            if branch != formatted:
                self._entries[formatted] = self._entries.pop(branch)

    def validfor(self, repo):
        """Is the cache content valid regarding a repo

        - False when cached tipnode is unknown or if we detect a strip.
        - True when cache is up to date or a subset of current repo."""
        assert isinstance(self, allbccls)  # help pytype
        valid = super(_topiccache, self).validfor(repo)
        if not valid:
            return False
        elif not istopicfilter(repo.filtername) or self.phaseshash is None:
            # phasehash at None means this is a branchmap
            # come from non topic thing
            return True
        else:
            try:
                valid = self.phaseshash == _phaseshash(repo, self.tiprev)
                return valid
            except IndexError:
                return False

    def write(self, repo):
        """write cache to disk if it's not topic-only, but first transform
        cache keys from branches in "//" format into bare branch names
        """
        # we expect mutable set to be small enough to be that computing it all
        # the time will be fast enough
        if not istopicfilter(repo.filtername):
            cache = self.copy()

            for formatted in tuple(cache):
                branch, tns, topic = common.parsefqbn(formatted)
                if branch != formatted:
                    cache._entries[branch] = cache._entries.pop(formatted)

            super(_topiccache, cache).write(repo)

    def update(self, repo, revgen):
        """Given a branchhead cache, self, that may have extra nodes or be
        missing heads, and a generator of nodes that are strictly a superset of
        heads missing, this function updates self to be correct.
        """
        assert isinstance(self, allbccls)  # help pytype
        if not istopicfilter(repo.filtername):
            self._verifyall()
            return super(_topiccache, self).update(repo, revgen)

        # See topic.discovery._headssummary(), where repo.unfiltered gets
        # overridden to return .filtered('unfiltered-topic'). revbranchcache
        # only can be created for unfiltered repo (filtername is None), so we
        # do that here, and this revbranchcache will be cached inside repo.
        # When we get rid of *-topic filters, then this workaround can be
        # removed too.
        repo.unfiltered().revbranchcache()

        self._verifyall()
        super(_topiccache, self).update(repo, revgen)
        self.phaseshash = _phaseshash(repo, self.tiprev)

class _TopicCacheV2(object): # combine me with branchmap.BranchCacheV2

    def __init__(self, *args, **kwargs):
        super(_TopicCacheV2, self).__init__(*args, **kwargs)
        self.phaseshash = None

    def _load_heads(self, repo, lineiter):
        """call BranchCacheV2._load_heads(), and then transform branch names to
        be in the new "//" format
        """
        assert isinstance(self, branchmap.BranchCacheV2)  # help pytype
        super(_TopicCacheV2, self)._load_heads(repo, lineiter)

        for branch in tuple(self._entries):
            formatted = common.formatfqbn(branch=branch)
            if branch != formatted:
                self._entries[formatted] = self._entries.pop(branch)

    def validfor(self, repo):
        """Is the cache content valid regarding a repo

        - False when cached tipnode is unknown or if we detect a strip.
        - True when cache is up to date or a subset of current repo."""
        assert isinstance(self, (branchmap.BranchCacheV2, branchmap.remotebranchcache))  # help pytype
        valid = super(_TopicCacheV2, self).validfor(repo)
        if not valid:
            return False
        elif not istopicfilter(repo.filtername) or self.phaseshash is None:
            # phasehash at None means this is a branchmap
            # come from non topic thing
            return True
        else:
            try:
                valid = self.phaseshash == _phaseshash(repo, self.tiprev)
                return valid
            except IndexError:
                return False

    def write(self, repo):
        """write cache to disk if it's not topic-only, but first transform
        cache keys from branches in "//" format into bare branch names
        """
        # we expect mutable set to be small enough to be that computing it all
        # the time will be fast enough
        if not istopicfilter(repo.filtername):
            entries = self._entries.copy()

            for formatted in tuple(entries):
                branch, tns, topic = common.parsefqbn(formatted)
                if branch != formatted:
                    entries[branch] = entries.pop(formatted)

            oldentries = self._entries
            try:
                self._entries = entries
                super(_TopicCacheV2, self).write(repo)
            finally:
                self._entries = oldentries

    def update(self, repo, revgen):
        """Given a branchhead cache, self, that may have extra nodes or be
        missing heads, and a generator of nodes that are strictly a superset of
        heads missing, this function updates self to be correct.
        """
        assert isinstance(self, (branchmap.BranchCacheV2, branchmap.remotebranchcache))  # help pytype
        if not istopicfilter(repo.filtername):
            return super(_TopicCacheV2, self).update(repo, revgen)

        # See topic.discovery._headssummary(), where repo.unfiltered gets
        # overridden to return .filtered('unfiltered-topic'). revbranchcache
        # only can be created for unfiltered repo (filtername is None), so we
        # do that here, and this revbranchcache will be cached inside repo.
        # When we get rid of *-topic filters, then this workaround can be
        # removed too.
        repo.unfiltered().revbranchcache()

        super(_TopicCacheV2, self).update(repo, revgen)
        if util.safehasattr(self, 'tiprev'):
            # remotebranchcache doesn't have self.tiprev
            self.phaseshash = _phaseshash(repo, self.tiprev)
