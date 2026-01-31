from os.path import dirname, join

from setuptools import setup

META_PATH = 'hgext3rd/evolve/metadata.py'

def get_metadata():
    meta = {}
    fullpath = join(dirname(__file__), META_PATH)
    with open(fullpath, 'r') as fp:
        exec(fp.read(), meta)
    return meta

def get_version():
    '''Read version info from a file without importing it'''
    return get_metadata()['__version__'].decode()

def min_hg_version():
    '''Read version info from a file without importing it'''
    return get_metadata()['minimumhgversion']

py_packages = [
    'hgext3rd',
    'hgext3rd.evolve',
    'hgext3rd.evolve.thirdparty',
    'hgext3rd.topic',
]
py_packagedir = {
    'hgext3rd': join(dirname(__file__), 'hgext3rd')
}

py_versions = '>=3.6.2, <4'

setup(
    name='hg-evolve',
    version=get_version(),
    author='Pierre-Yves David',
    author_email='pierre-yves.david@ens-lyon.org',
    maintainer='Pierre-Yves David',
    maintainer_email='pierre-yves.david@ens-lyon.org',
    url='https://www.mercurial-scm.org/doc/evolution/',
    description='Flexible evolution of Mercurial history.',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    long_description_content_type='text/x-rst',
    keywords='hg mercurial',
    license='GPLv2+',
    packages=py_packages,
    package_dir=py_packagedir,
    python_requires=py_versions
)
