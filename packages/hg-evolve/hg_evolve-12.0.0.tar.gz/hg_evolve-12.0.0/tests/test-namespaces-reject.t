Rejecting changesets with any topic namespaces during push

  $ . "$TESTDIR/testlib/common.sh"

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > topic =
  > [phases]
  > publish = no
  > [devel]
  > tns-report-transactions = push
  > [ui]
  > logtemplate = "{rev}: {desc} {fqbn} ({phase})\n"
  > EOF

  $ hg init orig
  $ hg clone orig clone -q

  $ cd clone

changesets without topic namespace are freely exchanged

  $ echo apple > a
  $ hg debug-topic-namespace --clear
  $ hg topic apple
  marked working directory as topic: apple
  $ hg ci -qAm apple

  $ hg log -r . -T '{rev}: {join(extras, " ")}\n'
  0: branch=default topic=apple

  $ hg push
  pushing to * (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

changesets with topic namespaces are rejected when server configuration disallows

  $ cat >> ../orig/.hg/hgrc << EOF
  > [experimental]
  > tns-reject-push = yes
  > EOF

  $ echo banana > b
  $ hg debug-topic-namespace bob
  marked working directory as topic namespace: bob
  $ hg topic banana
  $ hg ci -qAm 'banana'

  $ hg push
  pushing to $TESTTMP/orig
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  transaction abort!
  rollback completed
  abort: rejecting draft changesets with topic namespace: ed9751f04a18
  [255]

changesets with topic namespaces are only exchanged if server configuration allows

  $ cat >> ../orig/.hg/hgrc << EOF
  > [experimental]
  > tns-reject-push = no
  > EOF

  $ hg push
  pushing to $TESTTMP/orig
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: bob
  added 1 changesets with 1 changes to 1 files

  $ cd ..
