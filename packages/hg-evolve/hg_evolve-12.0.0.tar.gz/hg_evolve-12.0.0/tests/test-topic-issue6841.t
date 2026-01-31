New clones shouldn't have topics in any on-disk caches (issue6841)
https://bz.mercurial-scm.org/show_bug.cgi?id=6841

  $ . "$TESTDIR/testlib/common.sh"

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > topic =
  > [phases]
  > publish = no
  > [ui]
  > ssh = "$PYTHON" "$RUNTESTDIR/dummyssh"
  > EOF

  $ hg init orig
  $ hg clone orig publishing -q
  $ cat >> publishing/.hg/hgrc << EOF
  > [phases]
  > publish = yes
  > EOF

  $ cd orig
  $ mkcommit ROOT
  $ hg push ../publishing
  pushing to ../publishing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo foo > foo
  $ hg topic topic-foo
  marked working directory as topic: topic-foo
  $ hg ci -qAm foo

  $ cd ..

cloning via ssh to use wire protocol

  $ hg clone ssh://user@dummy/orig new-clone -q
  $ cd new-clone

on-disk caches are using bare branch names only

  $ f -Hq .hg/cache/rbc-names-v?
  0000: 64 65 66 61 75 6c 74                            |default|
  $ grep topic-foo .hg/cache/*
  [1]

and pushing works fine

  $ hg push ssh://user@dummy/publishing
  pushing to ssh://user@dummy/publishing
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

  $ cd ..
