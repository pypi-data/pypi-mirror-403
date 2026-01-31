Testing topics on cases when we have multiple topics based on top
of other.
  $ . "$TESTDIR/testlib/topic_setup.sh"

Setup

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > [ui]
  > interactive = True
  > logtemplate = {rev} - \{{get(namespaces, "topics")}} {node|short} {desc} ({phase})\n
  > [extensions]
  > show =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

Test to make sure `hg evolve` don't solve troubles out of current stack:
------------------------------------------------------------------------

  $ hg init repo1
  $ cd repo1
  $ for ch in a b c; do
  > echo $ch > $ch
  > hg ci -Am "added "$ch --topic foo
  > done;
  adding a
  active topic 'foo' grew its first changeset
  (see 'hg help topics' for more information)
  adding b
  adding c

  $ echo d > d
  $ hg ci -Am "added d" --topic bar
  adding d
  active topic 'bar' grew its first changeset
  (see 'hg help topics' for more information)

  $ hg up -r "desc('added c')"
  > echo cc >> c
  switching to topic foo
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg amend
  1 new orphan changesets

  $ hg log -G
  @  4 - {foo} 0cc68cbf943a added c (draft)
  |
  | *  3 - {bar} 94b12ff0f44a added d (draft)
  | |
  | x  2 - {foo} 9c315cf1e7de added c (draft)
  |/
  o  1 - {foo} ead01932caf0 added b (draft)
  |
  o  0 - {foo} 853c9ec0849e added a (draft)
  

  $ hg stack
  ### topic: foo
  ### target: default (branch)
  s3@ added c (current)
  s2: added b
  s1: added a

As expected, evolve should deny to evolve here as there is no troubled csets in current stack:
  $ hg evolve --all
  nothing to evolve on current working copy parent
  (1 other orphan in the repository, do you want --any or --rev)
  [2]
