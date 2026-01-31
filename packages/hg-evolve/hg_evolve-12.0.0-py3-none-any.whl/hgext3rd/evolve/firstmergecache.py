# Code dedicated to the cache of 'max(merge()) and ::X'
#
# These stable ranges are use for obsolescence markers discovery
#
# Copyright 2017 Pierre-Yves David <pierre-yves.david@ens-lyon.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import array

from mercurial.i18n import _
from mercurial import (
    localrepo,
    node as nodemod,
)

from mercurial.utils.stringutil import forcebytestr

from . import (
    error,
    exthelper,
    genericcaches,
    utility,
)

filterparents = utility.filterparents

eh = exthelper.exthelper()

@eh.command(b'debugfirstmergecache', [])
def debugfirstmergecache(ui, repo, **opts):
    """display the contents of firstmergecache"""
    cache = repo.firstmergecache
    cache.save(repo)
    for r in repo:
        ctx = repo[r]
        ui.write(b'%s %d\n' % (ctx, cache.get(r)))

@eh.reposetup
def setupcache(ui, repo):

    class firstmergecacherepo(repo.__class__):

        @localrepo.unfilteredpropertycache
        def firstmergecache(self):
            cache = firstmergecache()
            cache.update(self)
            return cache

        @localrepo.unfilteredmethod
        def destroyed(self):
            if r'firstmergecache' in vars(self):
                self.firstmergecache.clear()
            super(firstmergecacherepo, self).destroyed()

        @localrepo.unfilteredmethod
        def updatecaches(self, tr=None, **kwargs):
            if utility.shouldwarmcache(self, tr):
                self.firstmergecache.update(self)
                self.firstmergecache.save(self)
            super(firstmergecacherepo, self).updatecaches(tr, **kwargs)

    repo.__class__ = firstmergecacherepo

class firstmergecache(genericcaches.changelogsourcebase):

    _filepath = b'evoext-firstmerge-00'
    _cachename = b'evo-ext-firstmerge'

    def __init__(self):
        super(firstmergecache, self).__init__()
        self._data = array.array(r'l')

    def get(self, rev):
        if len(self._data) <= rev:
            raise error.ProgrammingError(b'firstmergecache must be warmed before use')
        return self._data[rev]

    def _updatefrom(self, repo, data):
        """compute the rev of one revision, assert previous revision has an hot cache
        """
        cl = repo.unfiltered().changelog
        total = len(data)

        progress = repo.ui.makeprogress(b'updating firstmerge cache', _(b'changesets'), total)
        progress.update(0)
        for idx, rev in enumerate(data, 1):
            assert rev == len(self._data), (rev, len(self._data))
            self._data.append(self._firstmerge(cl, rev))
            if not (idx % 10000): # progress as a too high performance impact
                revstr = b'' if rev is None else (b'rev %d' % rev)
                progress.update(idx, item=revstr)
        progress.complete()

    def _firstmerge(self, changelog, rev):
        cl = changelog
        ps = filterparents(cl.parentrevs(rev))
        if not ps:
            return nodemod.nullrev
        elif len(ps) == 1:
            # linear commit case
            return self.get(ps[0])
        else:
            return rev

    # cache internal logic

    def clear(self, reset=False):
        """invalidate the cache content

        if 'reset' is passed, we detected a strip and the cache will have to be
        recomputed.

        Subclasses MUST overide this method to actually affect the cache data.
        """
        super(firstmergecache, self).clear()
        self._data = array.array(r'l')

    # crude version of a cache, to show the kind of information we have to store

    def load(self, repo):
        """load data from disk"""
        assert repo.filtername is None

        data = repo.cachevfs.tryread(self._filepath)
        self._cachekey = self.emptykey
        self._data = array.array(r'l')
        if data:
            headerdata = data[:self._cachekeysize]
            cachekey = self._deserializecachekey(headerdata)
            expected = self._datastruct.size * (cachekey[0] + 1)
            data = data[self._cachekeysize:]
            if len(data) == expected:
                self._data.extend(self._deserializedata(data))
                self._cachekey = cachekey
            else:
                repo.ui.debug(b'firstmergecache file seems to be corrupted, '
                              b'it will be rebuilt from scratch\n')
        self._ondiskkey = self._cachekey

    def save(self, repo):
        """save the data to disk
        """
        if self._cachekey is None or self._cachekey == self._ondiskkey:
            return

        try:
            cachefile = repo.cachevfs(self._filepath, b'w', atomictemp=True)
            headerdata = self._serializecachekey()
            cachefile.write(headerdata)
            cachefile.write(self._serializedata(self._data))
            cachefile.close()
            self._ondiskkey = self._cachekey
        except (IOError, OSError) as exc:
            repo.ui.log(b'firstmergecache', b'could not write update %s\n' % forcebytestr(exc))
            repo.ui.debug(b'firstmergecache: could not write update %s\n' % forcebytestr(exc))
