Checking affected topic namespaces before history rewrites
==========================================================

  $ . "$TESTDIR/testlib/common.sh"

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > evolve =
  > topic =
  > rebase =
  > histedit =
  > [phases]
  > publish = no
  > [experimental]
  > tns-allow-rewrite =
  > EOF

  $ hg init repo
  $ cd repo

Make sure general checks in precheck() happen before topic namespaces checks

  $ hg prune null
  abort: cannot prune the null revision
  (no changeset checked out)
  [10]

  $ echo apple > a
  $ hg ci -qAm apple

  $ hg debug-topic-namespace foo
  marked working directory as topic namespace: foo
  $ hg topic bar
  marked working directory as topic: bar
  $ echo banana > b
  $ hg ci -qAm 'banana'

Allowing topic namespaces with --config works correctly

  $ echo broccoli > b
  $ hg amend -m 'broccoli'
  abort: refusing to amend changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg amend -m 'broccoli' --config experimental.tns-allow-rewrite=foo,something-unrelated

  $ echo coconut > b
  $ hg ci -qAm 'coconut'

Testing history-rewriting commands from evolve extension

  $ hg amend -m 'coconut'
  abort: refusing to amend changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg amend --patch -m 'coconut'
  abort: refusing to amend changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg uncommit
  abort: refusing to uncommit changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg prune -r .
  abort: refusing to prune changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg split -r .
  abort: refusing to split changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg touch -r .
  abort: refusing to touch changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]

Testing core history-rewriting commands

  $ hg ci --amend
  abort: refusing to amend changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg branch different-branch --rev .
  abort: refusing to change branch of changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg rebase -r . -d null
  abort: refusing to rebase changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]
  $ hg histedit
  abort: refusing to edit changesets with these topic namespaces: foo
  (modify experimental.tns-allow-rewrite to allow rewriting changesets from these topic namespaces)
  [10]

  $ cd ..
