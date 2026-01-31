from __future__ import absolute_import

from mercurial import (
    error,
    registrar,
    revset,
)

from mercurial.utils import stringutil

from . import (
    destination,
    stack,
)

# hg <= 7.1 (63d119607447)
try:
    from mercurial.revset_predicates import _notpublic
except ImportError:
    from mercurial.revset import _notpublic  # pytype: disable=import-error

revsetpredicate = registrar.revsetpredicate()

def getstringstrict(x, err):
    if x and x[0] == b'string':
        return x[1]
    raise error.ParseError(err)

@revsetpredicate(b'topicnamespace([string or set])')
def topicnamespaceset(repo, subset, x):
    """All changesets with the specified topic namespace or the topic
    namespaces of the given changesets. Without the argument, all changesets
    with any non-empty topic namespace.

    Pattern matching is supported for `string`. See
    :hg:`help revisions.patterns`.
    """
    args = revset.getargs(x, 0, 1, b'topicnamespace takes one or no arguments')

    mutable = _notpublic(repo, revset.fullreposet(repo), ())

    if not args:
        return (subset & mutable).filter(lambda r: repo[r].topic_namespace() != b'none')

    try:
        tns = getstringstrict(args[0], b'')
    except error.ParseError:
        # not a string, but another revset
        pass
    else:
        kind, pattern, matcher = stringutil.stringmatcher(tns)

        if tns.startswith(b'literal:') and pattern not in repo.topic_namespaces:
            raise error.RepoLookupError(b"topic namespace '%s' does not exist" % pattern)

        def matches(r):
            tns = repo[r].topic_namespace()
            if tns == b'none':
                return False
            return matcher(tns)

        return (subset & mutable).filter(matches)

    s = revset.getset(repo, revset.fullreposet(repo), x)
    namespaces = {repo[r].topic_namespace() for r in s}
    namespaces.discard(b'none')

    def matches(r):
        tns = repo[r].topic_namespace()
        if tns == b'none':
            return False
        return tns in namespaces

    return (subset & mutable).filter(matches)

@revsetpredicate(b'topic([string or set])')
def topicset(repo, subset, x):
    """All changesets with the specified topic or the topics of the given
    changesets. Without the argument, all changesets with any topic specified.

    Pattern matching is supported for `string`. See
    :hg:`help revisions.patterns`.
    """
    args = revset.getargs(x, 0, 1, b'topic takes one or no arguments')

    mutable = _notpublic(repo, revset.fullreposet(repo), ())

    if not args:
        return (subset & mutable).filter(lambda r: bool(repo[r].topic()))

    try:
        topic = getstringstrict(args[0], b'')
    except error.ParseError:
        # not a string, but another revset
        pass
    else:
        kind, pattern, matcher = stringutil.stringmatcher(topic)

        if topic.startswith(b'literal:') and pattern not in repo.topics:
            raise error.RepoLookupError(b"topic '%s' does not exist" % pattern)

        def matches(r):
            topic = repo[r].topic()
            if not topic:
                return False
            return matcher(topic)

        return (subset & mutable).filter(matches)

    s = revset.getset(repo, revset.fullreposet(repo), x)
    topics = {repo[r].topic() for r in s}
    topics.discard(b'')

    def matches(r):
        topic = repo[r].topic()
        if not topic:
            return False
        return topic in topics

    return (subset & mutable).filter(matches)

@revsetpredicate(b'ngtip([branch])')
def ngtipset(repo, subset, x):
    """The tip of a branch, ignoring changesets with a topic.

    Name is horrible so that people change it.
    """
    args = revset.getargs(x, 1, 1, b'ngtip takes one argument')
    # match a specific topic
    branch = revset.getstring(args[0], b'ngtip requires a string')
    if branch == b'.':
        branch = repo[b'.'].branch()
    # list of length 1
    revs = [repo[node].rev() for node in destination.ngtip(repo, branch)]
    return subset & revset.baseset(revs)

@revsetpredicate(b'stack()')
def stackset(repo, subset, x):
    """All relevant changes in the current topic.

    This is roughly equivalent to 'topic(.) - obsolete()' with a sorting moving
    unstable changeset after their future parent (as if evolve were already
    run).
    """
    err = b'stack takes no arguments, it works on current topic'
    revset.getargs(x, 0, 0, err)
    topic = None
    branch = None
    if repo.currenttopic:
        topic = repo.currenttopic
    else:
        branch = repo[None].branch()
    return revset.baseset(stack.stack(repo, branch=branch, topic=topic)[1:]) & subset

def stacksubrel(repo, subset, x, rel, z, order):
    """This is a revset-flavored implementation of stack aliases.

    The syntax is: rev#stack[n] or rev#s[n]. Plenty of logic is borrowed
    from topic._namemap, but unlike that function, which prefers to abort
    (e.g. when stack index is too high), this returns empty set to be more
    revset-friendly.
    """
    a, b = revset.getintrange(
        z,
        b'relation subscript must be an integer or a range',
        b'relation subscript bounds must be integers',
        None, None)

    s = revset.getset(repo, revset.fullreposet(repo), x)
    if not s:
        return revset.baseset()

    def getrange(st, a, b):
        start = 1 if a is None else a
        end = len(st.revs) if b is None else b + 1
        return range(start, end)

    revs = []
    for r in s:
        topic = repo[r].topic()
        if topic:
            st = stack.stack(repo, topic=topic)
        else:
            st = stack.stack(repo, branch=repo[r].branch())
        for n in getrange(st, a, b):
            if abs(n) >= len(st.revs):
                # also means stack base is not accessible with n < 0, which
                # is by design
                continue
            if n == 0 and b != 0 and a != 0:
                # quirk: we don't want stack base unless specifically asked
                # for it (at least one of the indices is 0)
                continue
            rev = st.revs[n]
            if rev == -1 and n == 0:
                continue
            if rev not in revs:
                revs.append(rev)

    return subset & revset.baseset(revs)

revset.subscriptrelations[b'stack'] = stacksubrel
revset.subscriptrelations[b's'] = stacksubrel

def topicsubrel(repo, subset, x, *args):
    subset &= topicset(repo, subset, x)
    return revset.generationssubrel(repo, subset, x, *args)

revset.subscriptrelations[b'topic'] = topicsubrel
revset.subscriptrelations[b't'] = topicsubrel

def stackrel(repo, subset, x, rel, order):
    z = (b'rangeall', None)
    return stacksubrel(repo, subset, x, rel, z, order)

revset.relations[b'stack'] = stackrel
revset.relations[b's'] = stackrel
