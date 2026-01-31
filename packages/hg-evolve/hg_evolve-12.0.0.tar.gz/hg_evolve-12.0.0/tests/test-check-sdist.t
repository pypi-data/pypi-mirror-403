Enable obsolescence to avoid the warning issue when obsmarkers are found


  $ if ! "$PYTHON" -c "from setuptools import setup" ; then
  >     echo "skipped: setuptools not installed" >&2
  >     exit 80
  > fi

  $ cat << EOF >> "$HGRCPATH"
  > [experimental]
  > evolution = all
  > EOF

  $ cd "$TESTDIR"/..

Archiving to a separate location to avoid hardlink mess when the repo is shared

#if test-repo

  $ . "$RUNTESTDIR/helpers-testrepo.sh"
  $ testrepohg archive --rev 'wdir()' "$TESTTMP"/hg-evolve
  $ cd "$TESTTMP"/hg-evolve

#endif

  $ "$PYTHON" setup.py check --metadata --restructuredtext
  running check

  $ "$PYTHON" setup.py sdist --dist-dir "$TESTTMP"/dist > /dev/null 2>&1
  $ cd "$TESTTMP"/dist

  $ find hg?evolve-*.tar.gz -size +800000c
  hg?evolve-*.tar.gz (glob)

  $ tar -tzf hg?evolve-*.tar.gz | sed 's|^hg.evolve-[^/]*/||' | sort > ../files
  $ grep -E '^tests/test-.*\.(t|py)$' ../files > ../test-files
  $ grep -E -v '^tests/test-.*\.(t|py)$' ../files > ../other-files
  $ wc -l ../other-files
  [ \t]*[0-9]{3} ../other-files (re)
  $ wc -l ../test-files
  [ \t]*[0-9]{3} ../test-files (re)
  $ grep -F debian ../files
  tests/test-check-debian.t
  $ grep -F __init__.py ../files
  hgext3rd/__init__.py
  hgext3rd/evolve/__init__.py
  hgext3rd/evolve/thirdparty/__init__.py
  hgext3rd/topic/__init__.py
  $ grep -F common.sh ../files
  docs/tutorial/testlib/common.sh
  tests/testlib/common.sh
  $ grep -F README ../files
  README.rst
  docs/README
  docs/tutorial/README.rst
  hgext3rd/topic/README

  $ grep -E '(gitlab|contrib|hack|format-source)' ../files
  [1]
  $ grep -F netlify ../files
  [1]

#if twine
  $ twine --no-color check *
  Checking hg?evolve-*.tar.gz: PASSED (glob)
#endif
