import hghave

@hghave.check("docgraph-ext", "Extension to generate graph from repository")
def docgraph():
    try:
        import hgext.docgraph
        hgext.docgraph.cmdtable # trigger import
    except ImportError:
        try:
            import hgext3rd.docgraph
            hgext3rd.docgraph.cmdtable # trigger import
        except ImportError:
            return False
    return True

@hghave.check("flake8-mod", "Flake8 linter as a Python module")
def has_flake8():
    try:
        import flake8

        flake8.__version__
    except ImportError:
        return False
    else:
        return True

@hghave.check("pyflakes-mod", "Pyflakes linter as a Python module")
def has_pyflakes_mod():
    try:
        import pyflakes

        pyflakes.__version__
    except ImportError:
        return False
    else:
        return True

@hghave.check("check-manifest", "check-manifest MANIFEST.in checking tool")
def has_check_manifest():
    return hghave.matchoutput('check-manifest --version 2>&1',
                              br'check-manifest version')

@hghave.check("twine", "twine utility for publishing Python packages")
def has_twine():
    return hghave.matchoutput('twine --help 2>&1',
                              br'usage: twine .*\bcheck\b')

@hghave.check("delta-compression", "Delta compression")
def has_delta_compression():
    try:
        from mercurial.util import compression
        return getattr(compression.compressormanager, 'supported_wire_delta_compression', None) is not None
    except (AttributeError, ImportError):
        return False
