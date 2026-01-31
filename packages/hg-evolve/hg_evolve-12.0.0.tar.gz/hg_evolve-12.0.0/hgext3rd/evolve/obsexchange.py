# Code dedicated to the exchange of obsolescence markers
#
# Copyright 2017 Pierre-Yves David <pierre-yves.david@ens-lyon.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from mercurial import (
    bundle2,
    error,
    exchange,
    extensions,
    node,
    obsolete,
    pushkey,
    wireprototypes,
    wireprotov1server
)

from mercurial.hgweb import common as hgwebcommon

from . import (
    exthelper,
    utility,
    obsdiscovery,
)

eh = exthelper.exthelper()
eh.merge(obsdiscovery.eh)
obsexcmsg = utility.obsexcmsg

eh.configitem(b'experimental', b'verbose-obsolescence-exchange', False)

_bestformat = max(obsolete.formats.keys())

#####################################################
### Support for subset specification in getbundle ###
#####################################################

# Adds support for the 'evo_obscommon' argument to getbundle This argument use
# the data recovered from the discovery to request only a subpart of the
# obsolete subtree.

@eh.uisetup
def addgetbundleargs(self):
    gboptsmap = wireprototypes.GETBUNDLE_ARGUMENTS
    gboptsmap[b'evo_obscommon'] = b'nodes'
    gboptsmap[b'evo_missing_nodes'] = b'nodes'

ARGUMENTS_LIMIT = 200

OVERFLOW_MSG = b"""obsmarkers differ for %d common nodes
|
| This might be too much for the remote HTTP server that doesn't accept
| arguments through POST request. (config: experimental.httppostargs=yes)
|
| Falling back to a less efficient fetching method.
|
| More efficient fetching method is possible and will be used in the future.\n
"""

@eh.wrapfunction(exchange, '_pullbundle2extraprepare')
def _addobscommontob2pull(orig, pullop, kwargs):
    ret = orig(pullop, kwargs)
    ui = pullop.repo.ui
    if (b'obsmarkers' in kwargs
        and pullop.remote.capable(b'_evoext_getbundle_obscommon')):
        boundaries = obsdiscovery.buildpullobsmarkersboundaries(pullop)
        use_common = True
        if b'missing' in boundaries:
            use_common = False
            missing = boundaries[b'missing']
            limitedarguments = pullop.remote.limitedarguments
            if limitedarguments and len(missing) > ARGUMENTS_LIMIT:
                obsexcmsg(ui, OVERFLOW_MSG % len(missing))
                use_common = True
            else:
                if missing:
                    obsexcmsg(ui, b'request obsmarkers for %d common nodes\n'
                              % len(missing))
                kwargs[b'evo_missing_nodes'] = missing
        if use_common and b'common' in boundaries:
            common = boundaries[b'common']
            if common != pullop.common:
                obsexcmsg(ui, b'request obsmarkers for some common nodes\n')
            if common != [node.nullid]:
                kwargs[b'evo_obscommon'] = common
    return ret

def _getbundleobsmarkerpart(orig, bundler, repo, source, **kwargs):
    if not (set([r'evo_obscommon', r'evo_missing_nodes']) & set(kwargs)):
        return orig(bundler, repo, source, **kwargs)

    if kwargs.get('obsmarkers', False):
        heads = kwargs.get('heads')
        if r'evo_obscommon' in kwargs:
            if heads is None:
                heads = repo.heads()
            obscommon = kwargs.get('evo_obscommon', ())
            if obscommon:
                obsset = repo.unfiltered().set(b'::%ln - ::%ln', heads, obscommon)
            else:
                obsset = repo.unfiltered().set(b'::%ln', heads)
            subset = [c.node() for c in obsset]
        else:
            common = kwargs.get('common')
            subset = [c.node() for c in repo.unfiltered().set(b'only(%ln, %ln)', heads, common)]
            subset += kwargs['evo_missing_nodes']
        markers = repo.obsstore.relevantmarkers(subset)
        bundle2.buildobsmarkerspart(bundler, markers)

def _obscommon_capabilities(orig, repo, proto):
    """wrapper to advertise new capability"""
    caps = orig(repo, proto)
    if obsolete.isenabled(repo, obsolete.exchangeopt):
        caps.append(b'_evoext_getbundle_obscommon')
    return caps

@eh.extsetup
def extsetup_obscommon(ui):
    gboptsmap = wireprototypes.GETBUNDLE_ARGUMENTS
    gboptsmap[b'evo_obscommon'] = b'nodes'

    # wrap module content
    origfunc = exchange.getbundle2partsmapping[b'obsmarkers']

    def newfunc(*args, **kwargs):
        return _getbundleobsmarkerpart(origfunc, *args, **kwargs)
    exchange.getbundle2partsmapping[b'obsmarkers'] = newfunc

    extensions.wrapfunction(wireprotov1server, '_capabilities',
                            _obscommon_capabilities)

abortmsg = b"won't exchange obsmarkers through pushkey"
hint = b"upgrade your client or server to use the bundle2 protocol"

class HTTPCompatibleAbort(hgwebcommon.ErrorResponse, error.Abort):
    def __init__(self, message, code, hint=None):
        # initialisation of each class is a bit messy.
        # We explicitly do the dispatch
        hgwebcommon.ErrorResponse.__init__(self, 410, message)
        error.Abort.__init__(self, message, hint=hint)

def forbidpushkey(repo=None, key=None, old=None, new=None):
    """prevent exchange through pushkey"""
    err = HTTPCompatibleAbort(abortmsg, 410, hint=hint)
    raise err

def forbidlistkey(repo=None, key=None, old=None, new=None):
    """prevent exchange through pushkey"""
    if obsolete.isenabled(repo, obsolete.exchangeopt):
        err = HTTPCompatibleAbort(abortmsg, 410, hint=hint)
        raise err
    return {}

@eh.uisetup
def setuppushkeyforbidding(ui):
    pushkey._namespaces[b'obsolete'] = (forbidpushkey, forbidlistkey)
