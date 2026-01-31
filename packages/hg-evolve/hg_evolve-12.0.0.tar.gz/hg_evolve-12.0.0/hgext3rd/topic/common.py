# Copyright 2019 Pierre-Yves David <pierre-yves.david@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

def hastopicext(repo):
    """True if the repo use the topic extension"""
    return getattr(repo, 'hastopicext', False)

def parsefqbn(string):
    """parse branch//namespace/topic string into branch, namespace and topic

    >>> parsefqbn(b'branch//topic')
    ('branch', 'none', 'topic')
    >>> parsefqbn(b'//namespace/topic')
    ('default', 'namespace', 'topic')
    >>> parsefqbn(b'branch//')
    ('branch', 'none', '')
    >>> parsefqbn(b'//namespace/')
    ('default', 'namespace', '')
    >>> parsefqbn(b'/topic')
    ('/topic', 'none', '')
    >>> parsefqbn(b'//topic')
    ('default', 'none', 'topic')
    >>> parsefqbn(b'branch//namespace/topic')
    ('branch', 'namespace', 'topic')
    >>> parsefqbn(b'file:///tmp/branch//')
    ('file:///tmp/branch', 'none', '')
    >>> parsefqbn(b'http://example.com/branch//namespace/topic')
    ('http://example.com/branch', 'namespace', 'topic')
    """
    branch, sep, other = string.rpartition(b'//')
    if not sep:
        # when there's no // anywhere in the string, rpartition returns
        # untouched string as the 3rd element, and the first two are empty
        branch, other = other, b''
    if not branch:
        branch = b'default'
    tns, sep, topic = other.partition(b'/')
    if not sep:
        # when there's no / in the rest of the string, there can only be topic
        tns, topic = b'none', tns
    return branch, tns, topic

def formatfqbn(branch=b'', namespace=b'', topic=b'', short=True):
    """format branch, namespace and topic into branch//namespace/topic string

    >>> formatfqbn(branch=b'branch', topic=b'topic')
    'branch//topic'
    >>> formatfqbn(namespace=b'namespace', topic=b'topic')
    '//namespace/topic'
    >>> formatfqbn(branch=b'branch')
    'branch'
    >>> formatfqbn(branch=b'branch//')
    'branch////'
    >>> formatfqbn(branch=b'double//slash')
    'double//slash//'
    >>> formatfqbn(namespace=b'namespace')
    '//namespace/'
    >>> formatfqbn(branch=b'/topic')
    '/topic'
    >>> formatfqbn(topic=b'topic')
    '//topic'
    >>> formatfqbn(branch=b'branch', namespace=b'namespace', topic=b'topic')
    'branch//namespace/topic'
    >>> formatfqbn(branch=b'foo/bar', namespace=b'user26', topic=b'feature')
    'foo/bar//user26/feature'
    >>> formatfqbn(branch=b'http://example.com/branch', namespace=b'namespace', topic=b'topic')
    'http://example.com/branch//namespace/topic'
    """
    result = b''
    showbranch = True # branch and not (short and branch == b'default')
    shownamespace = namespace and not (short and namespace == b'none')
    if short and not showbranch and not shownamespace and not topic:
        # if there's nothing to show, show at least branch
        showbranch = True
    if showbranch:
        result += branch
    if shownamespace or topic or b'//' in branch:
        result += b'//'
    if shownamespace:
        result += namespace + b'/'
    result += topic
    return result

def upgradeformat(branch):
    """take branch and topic in ":" format and return fqbn in "//" format

    This function can be used for transforming branchmap contents of peers that
    don't support topic namespaces yet to work with peers with topic namespaces
    support.

    >>> upgradeformat(b'branch')
    'branch'
    >>> upgradeformat(b'branch:topic')
    'branch//topic'
    >>> upgradeformat(b'branch//')
    'branch////'
    >>> upgradeformat(b'branch//:topic')
    'branch////topic'
    """
    if b':' not in branch:
        # formatting anyway, because named branch could contain "//"
        return formatfqbn(branch=branch)
    # topic namespace cannot be extracted from ":" format
    branch, topic = branch.split(b':', 1)
    return formatfqbn(branch=branch, topic=topic)
