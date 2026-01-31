============================================================
Test detection of topic name space affected by a transaction
============================================================

Reporting affected topic namespaces in transactions

  $ . "$TESTDIR/testlib/common.sh"

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > evolve =
  > topic =
  > [phases]
  > publish = no
  > [devel]
  > tns-report-transactions = push
  > EOF

  $ hg init orig

case 1: new changeset (draft with topic namespace)
==================================================

topic namespace of that changeset is reported

  $ hg clone orig case-1 -q
  $ cd orig

  $ echo apple > a
  $ hg ci -qAm apple

  $ hg push ../case-1
  pushing to ../case-1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo banana > b
  $ hg debug-topic-namespace bob
  marked working directory as topic namespace: bob
  $ hg topic b
  marked working directory as topic: b
  $ hg ci -qAm 'banana'

  $ hg push ../case-1
  pushing to ../case-1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: bob
  added 1 changesets with 1 changes to 1 files

  $ cd ..

case 2: obsmarker affecting known changeset
===========================================

topic namespaces of both the precursor and the successor are affected

  $ hg clone orig case-2 -q
  $ cd orig

  $ echo broccoli > b
  $ hg debug-topic-namespace bruce
  $ hg ci --amend -m 'broccoli'

  $ hg push ../case-2
  pushing to ../case-2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: bob bruce
  added 1 changesets with 1 changes to 1 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets

  $ cd ..

case 3: phase divergence
========================

3 phase divergence resolution can point to a thing but not affect it (probably not affected)

In this case, the pushed changeset comes with an obsmarker whose predecessors
has the `charlie` topic-namespace and the successors has the `carol`
topic-namespace. However, that obsolescence is part of a phase-divergence
fixup, so we should now mark `coconut` as affected since it is already public.

  $ hg clone orig case-3 -q
  $ cd orig

  $ hg debug-topic-namespace charlie
  $ hg topic c
  $ echo coconut > c
  $ hg ci -qAm 'coconut'

  $ hg debug-topic-namespace carol
  $ echo cloudberry > c
  $ hg ci --amend -m 'cloudberry'

  $ hg phase --hidden -r 'desc("coconut")' --public
  1 new phase-divergent changesets

  $ hg evolve --phase-divergent
  recreate:[s1] cloudberry
  atop:[3] coconut
  committed as 9f1abc6f4a6f
  working directory is now at 9f1abc6f4a6f

  $ hg push ../case-3
  pushing to ../case-3
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: bruce carol
  added 2 changesets with 2 changes to 1 files
  2 new obsolescence markers

  $ cd ..

case 4: phase movement: publishing drafts
=========================================

topic namespaces of published changesets are affected

  $ hg clone orig case-4 -q
  $ cd orig

  $ hg push ../case-4 --publish
  pushing to ../case-4
  searching for changes
  no changes found
  topic namespaces affected: carol
  active topic 'c' is now empty
  (use 'hg topic --clear' to clear it if needed)
  [1]

  $ cd ..

case 5: bookmark movement
=========================

Bookmark movement that affect tns (like putting a bookmark on obsolete
changesets) their topic namespaces reappear and are therefore reported

  $ hg clone orig case-5 -q
  $ cd orig

  $ hg debug-topic-namespace dana
  $ hg topic d
  $ echo durian > d
  $ hg ci -qAm 'durian'

  $ hg push ../case-5
  pushing to ../case-5
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: dana
  added 1 changesets with 1 changes to 1 files

  $ hg debug-topic-namespace dave
  $ echo dragonfruit > d
  $ hg ci --amend -m 'dragonfruit'

  $ hg push ../case-5
  pushing to ../case-5
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: dana dave
  added 1 changesets with 1 changes to 1 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets

  $ hg bookmark --hidden -r 'desc("durian")' @
  bookmarking hidden changeset c56d89b2348b
  (hidden revision 'c56d89b2348b' was rewritten as: 7fc662c4767d)

  $ hg push ../case-5 -B @
  pushing to ../case-5
  searching for changes
  no changes found
  topic namespaces affected: dana
  exporting bookmark @
  [1]

  $ cd ..

case 6: phase movement: publishing secret changesets
====================================================

(that are known on the server)

topic namespaces of published changesets are affected

  $ hg clone orig case-6 -q
  $ cd orig

XXX: we see "active topic is now empty" twice because stack doesn't handle topic namespaces yet

  $ hg push ../case-6 -r . --publish
  pushing to ../case-6
  searching for changes
  no changes found
  topic namespaces affected: dave
  active topic 'd' is now empty
  active topic 'd' is now empty
  (use 'hg topic --clear' to clear it if needed)
  [1]

previous topic namespace is resurrected...

  $ hg phase --secret --force -r . --config 'devel.tns-report-transactions=phase'
  topic namespaces affected: dave
  active topic 'd' grew its first changeset
  (see 'hg help topics' for more information)

...just to disappear again

  $ hg push ../case-6 -r . --config 'devel.tns-report-transactions=*'
  pushing to ../case-6
  searching for changes
  no changes found
  topic namespaces affected: dave
  active topic 'd' is now empty
  (use 'hg topic --clear' to clear it if needed)
  [1]

  $ cd ..

case 7: phase movement: secret->draft on the server
===================================================

changeset becomes visible to peers, so its topic namespace is affected

  $ hg clone orig case-7 -q
  $ cd orig

  $ hg phase --draft --force -r tip
  active topic 'd' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg phase --secret --force -r tip -R ../case-7
  active topic 'd' grew its first changeset
  (see 'hg help topics' for more information)

  $ hg push ../case-7 -r . --config 'devel.tns-report-transactions=*'
  pushing to ../case-7
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: dave
  added 0 changesets with 0 changes to 1 files
  active topic 'd' grew its first changeset
  (see 'hg help topics' for more information)

  $ cd ..

case: 99 pushing obsmarker for an unknown changeset
===================================================
doesn't affect any topic namespace, we report nothing

  $ hg clone orig case-99 -q
  $ cd orig

  $ hg debugobsolete aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa `getid "desc('dragonfruit')"`
  1 new obsolescence markers

  $ hg push ../case-99
  pushing to ../case-99
  searching for changes
  no changes found
  1 new obsolescence markers
  [1]

  $ cd ..
