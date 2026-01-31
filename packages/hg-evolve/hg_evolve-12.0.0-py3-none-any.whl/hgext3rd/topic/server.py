# topic/server.py - server specific behavior with topic
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
from mercurial.i18n import _

from mercurial import (
    error,
    extensions,
    localrepo,
    repoview,
    wireprototypes,
    wireprotov1peer,
    wireprotov1server,
)

from mercurial.utils import repoviewutil

from . import (
    common,
    compat,
    constants,
)

### Visibility restriction
#
# Serving draft changesets with topics to clients without topic extension can
# confuse them, because they won't see the topic label and will consider them
# normal anonymous heads. Instead we have the option to not serve changesets
# with topics to clients without topic support.
#
# To achieve this, we alter the behavior of the standard `heads` commands and
# introduce a new `heads` command that only clients with topic will know about.

# compat version of the wireprotocommand decorator, taken from evolve compat

FILTERNAME = b'served-no-topic'

def computeunservedtopic(repo, visibilityexceptions=None):
    assert not repo.changelog.filteredrevs
    filteredrevs = repoview.filtertable[b'served'](repo, visibilityexceptions).copy()
    mutable = repoview.filtertable[b'immutable'](repo, visibilityexceptions)
    consider = mutable - filteredrevs
    cl = repo.changelog
    extrafiltered = set()
    for r in consider:
        if cl.changelogrevision(r).extra.get(constants.extrakey, b''):
            extrafiltered.add(r)
    if extrafiltered:
        extrafiltered = set(repo.revs('%ld::%ld', extrafiltered, consider))
        filteredrevs = frozenset(filteredrevs | extrafiltered)
    return filteredrevs

def wrapheads(orig, repo, proto):
    """wrap head to hide topic^W draft changeset to old client"""
    hidetopics = repo.ui.configbool(b'experimental', b'topic.server-gate-topic-changesets')
    if common.hastopicext(repo) and hidetopics:
        h = repo.filtered(FILTERNAME).heads()
        return wireprototypes.bytesresponse(wireprototypes.encodelist(h) + b'\n')
    return orig(repo, proto)

def topicheads(repo, proto):
    """Same as the normal wireprotocol command, but accessing with a different end point."""
    h = repo.heads()
    return wireprototypes.bytesresponse(wireprototypes.encodelist(h) + b'\n')

def tns_heads(repo, proto, namespaces):
    """wireprotocol command to filter heads based on topic namespaces"""
    if not common.hastopicext(repo):
        return topicheads(repo, proto)

    namespaces = wireprototypes.decodelist(namespaces)
    if b'*' in namespaces:
        # pulling all topic namespaces, all changesets are visible
        h = repo.heads()
    else:
        # only changesets in the selected topic namespaces are visible
        h = []
        bm = repo.branchmaptns()
        for branch, nodes in compat.branchmapitems(bm):
            namedbranch, tns, topic = common.parsefqbn(branch)
            if tns == b'none' or tns in namespaces:
                h.extend(nodes)
    return wireprototypes.bytesresponse(wireprototypes.encodelist(h) + b'\n')

def wireprotocaps(orig, repo, proto):
    """advertise the new topic specific `head` command for client with topic"""
    caps = orig(repo, proto)
    if common.hastopicext(repo) and repo.peer().capable(b'topics'):
        caps.append(b'_exttopics_heads')
        if repo.ui.configbool(b'phases', b'publish'):
            mode = b'all'
        elif repo.ui.configbool(b'experimental', b'topic.publish-bare-branch'):
            mode = b'auto'
        else:
            mode = b'none'
        caps.append(b'ext-topics-publish=%s' % mode)
        caps.append(b'ext-topics-tns-heads')
    return caps

def setupserver(ui):
    extensions.wrapfunction(wireprotov1server, 'heads', wrapheads)
    wireprotov1server.commands.pop(b'heads')
    wireprotov1server.wireprotocommand(b'heads', permission=b'pull')(wireprotov1server.heads)
    wireprotov1server.wireprotocommand(b'_exttopics_heads', permission=b'pull')(topicheads)
    wireprotov1server.wireprotocommand(b'tns_heads', b'namespaces', permission=b'pull')(tns_heads)
    extensions.wrapfunction(wireprotov1server, '_capabilities', wireprotocaps)

    @wireprotov1peer.batchable
    def wp_tns_heads(self, namespaces):
        def decode(d):
            try:
                return wireprototypes.decodelist(d[:-1])
            except ValueError:
                self._abort(error.ResponseError(_(b"unexpected response:"), d))

        return {b'namespaces': wireprototypes.encodelist(namespaces)}, decode

    wireprotov1peer.wirepeer.tns_heads = wp_tns_heads

    class topicpeerexecutor(wireprotov1peer.peerexecutor):

        def callcommand(self, command, args):
            if command == b'heads':
                if self._peer.capable(b'ext-topics-tns-heads'):
                    command = b'tns_heads'
                    if self._peer.ui.configbool(b'_internal', b'tns-explicit-target', False):
                        args[b'namespaces'] = [b'*']
                    else:
                        args[b'namespaces'] = self._peer.ui.configlist(b'experimental', b'tns-default-pull-namespaces', [b'*'])
                elif self._peer.capable(b'_exttopics_heads'):
                    command = b'_exttopics_heads'
                    if getattr(self._peer, '_exttopics_heads', None) is None:
                        self._peer._exttopics_heads = self._peer.heads
            s = super(topicpeerexecutor, self)
            return s.callcommand(command, args)

    wireprotov1peer.peerexecutor = topicpeerexecutor

    class topiccommandexecutor(localrepo.localcommandexecutor):
        def callcommand(self, command, args):
            if command == b'heads':
                if self._peer.capable(b'ext-topics-tns-heads'):
                    command = b'tns_heads'
                    if self._peer.ui.configbool(b'_internal', b'tns-explicit-target', False):
                        args[b'namespaces'] = [b'*']
                    else:
                        args[b'namespaces'] = self._peer.ui.configlist(b'experimental', b'tns-default-pull-namespaces', [b'*'])
            s = super(topiccommandexecutor, self)
            return s.callcommand(command, args)

    localrepo.localcommandexecutor = topiccommandexecutor

    if FILTERNAME not in repoview.filtertable:
        repoview.filtertable[FILTERNAME] = computeunservedtopic
        repoviewutil.subsettable[FILTERNAME] = b'immutable'
        repoviewutil.subsettable[b'served'] = FILTERNAME
