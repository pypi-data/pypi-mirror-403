#require test-repo

Enable obsolescence to avoid the warning issue when obsmarkers are found

  $ . "$RUNTESTDIR/helpers-testrepo.sh"

  $ cd "$TESTDIR"/..

Checking all non-public tagged revisions up to the current commit, see our
release checklist for more ideas

  $ for node in `testrepohg log --rev 'tag() and ::. and not public() and not desc("# no-check-commit")' --template '{node|short}\n'`; do
  >   tags=`testrepohg log --rev $node --template '{tags}\n'`
  >   if echo "$tags" | grep -q ' '; then
  >     echo "Revision $node is tagged multiple times: $tags"
  >   fi
  >   branch=`testrepohg log --rev $node --template '{branch}\n'`
  >   if [ "$branch" != "stable" ]; then
  >     echo "Revision $node is not on stable branch: $branch"
  >   fi
  >   # Here we skip:
  >   # - pullbundle because it usually has no changes (so no version bump)
  >   if testrepohg grep --rev $node '^__version__ = .*\.dev' hgext3rd/evolve/ hgext3rd/topic/; then
  >     echo "Versions should not end with .dev at tagged revision $node"
  >   fi
  >   entry=`testrepohg cat --rev $node CHANGELOG | grep -F "$tags"`
  >   if [ -z "$entry" ]; then
  >     echo "Revision $node has no CHANGELOG entry for $tags"
  >   fi
  >   if echo "$entry" | grep -E -vq ' -- [0-9]{4}-[0-9]{2}-[0-9]{2}'; then
  >     echo "CHANGELOG entry for $tags should have a date in YYYY-MM-DD format: $entry"
  >   fi
  >   entry=`testrepohg cat --rev $node debian/changelog | grep -F "$tags"`
  >   if [ -z "$entry" ]; then
  >     echo "Revision $node has no debian/changelog entry for $tags"
  >   fi
  > done
