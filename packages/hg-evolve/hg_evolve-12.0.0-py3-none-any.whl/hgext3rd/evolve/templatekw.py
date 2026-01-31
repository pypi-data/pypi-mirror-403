# Copyright 2011 Peter Arrenbrecht <peter.arrenbrecht@gmail.com>
#                Logilab SA        <contact@logilab.fr>
#                Pierre-Yves David <pierre-yves.david@ens-lyon.org>
#                Patrick Mezard <patrick@mezard.eu>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
"""evolve templates
"""

from . import (
    exthelper,
    obshistory,
)

from mercurial import (
    templatekw,
    util
)

eh = exthelper.exthelper()

### template keywords

@eh.templatekeyword(b'troubles', requires={b'ctx', b'templ'})
def showtroubles(context, mapping):   # legacy name for instabilities
    ctx = context.resource(mapping, b'ctx')
    return templatekw.compatlist(context, mapping, b'trouble',
                                 ctx.instabilities(), plural=b'troubles')

@eh.templatekeyword(b'obsorigin', requires={b'ui', b'repo', b'ctx'})
def showobsorigin(context, mapping):
    ui = context.resource(mapping, b'ui')
    repo = context.resource(mapping, b'repo')
    ctx = context.resource(mapping, b'ctx')
    values = []
    r = obshistory.predecessorsandmarkers(repo, ctx.node())
    for (nodes, markers) in sorted(obshistory.groupbyfoldid(r)):
        v = obshistory.obsoriginprinter(ui, repo, nodes, markers)
        values.append(v)
    return templatekw.compatlist(context, mapping, b'origin', values)

_sp = templatekw.showpredecessors
if util.safehasattr(_sp, '_requires'):
    def showprecursors(context, mapping):
        return _sp(context, mapping)
    showprecursors.__doc__ = _sp._origdoc
    _tk = templatekw.templatekeyword(b"precursors", requires=_sp._requires)
    _tk(showprecursors)
else:
    templatekw.keywords[b"precursors"] = _sp

_ss = templatekw.showsuccessorssets
if util.safehasattr(_ss, '_requires'):
    def showsuccessors(context, mapping):
        return _ss(context, mapping)
    showsuccessors.__doc__ = _ss._origdoc
    _tk = templatekw.templatekeyword(b"successors", requires=_ss._requires)
    _tk(showsuccessors)
else:
    templatekw.keywords[b"successors"] = _ss
