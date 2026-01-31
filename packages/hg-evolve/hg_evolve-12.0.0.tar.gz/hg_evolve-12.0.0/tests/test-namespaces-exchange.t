Limiting topic namespaces during exchange based on a config option

  $ . "$TESTDIR/testlib/common.sh"

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > topic =
  > [phases]
  > publish = no
  > [ui]
  > ssh = "$PYTHON" "$RUNTESTDIR/dummyssh"
  > [devel]
  > tns-report-transactions = pull
  > [ui]
  > logtemplate = "{rev}: {desc} {fqbn} ({phase})\n"
  > EOF

  $ hg init orig

#testcases local ssh http

#if http
  $ hg serve -R orig -n test -p $HGPORT -d --pid-file=hg.pid -A access.log -E errors.log
  $ cat hg.pid >> $DAEMON_PIDS
#endif

we advertise the new capability, including during local exchange

#if local
  $ hg debugcapabilities orig | grep topics
    ext-topics-publish=none
    ext-topics-tns-heads
    topics
    topics-namespaces
#endif
#if ssh
  $ hg debugcapabilities ssh://user@dummy/orig | grep topics
    _exttopics_heads
    ext-topics-publish=none
    ext-topics-tns-heads
    topics
    topics-namespaces
#endif
#if http
  $ hg debugcapabilities http://localhost:$HGPORT/ | grep topics
    _exttopics_heads
    ext-topics-publish=none
    ext-topics-tns-heads
    topics
    topics-namespaces
#endif

#if local
  $ hg clone orig clone -q
#endif
#if ssh
  $ hg clone ssh://user@dummy/orig clone -q
#endif
#if http
  $ hg clone http://localhost:$HGPORT/ clone -q
#endif

  $ cd orig

changesets without topic namespace are freely exchanged

  $ echo apple > a
  $ hg debug-topic-namespace --clear
  $ hg topic apple
  marked working directory as topic: apple
  $ hg ci -qAm apple

  $ hg log -r . -T '{rev}: {join(extras, " ")}\n'
  0: branch=default topic=apple

  $ hg incoming -R ../clone
  comparing with * (glob)
  0: apple default//apple (draft)

  $ hg pull -R ../clone
  pulling from * (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets bf4c1d971543 (1 drafts)
  (run 'hg update' to get a working copy)

changesets with topic namespaces are only exchanged if configuration allows

  $ echo banana > b
  $ hg debug-topic-namespace bob
  marked working directory as topic namespace: bob
  $ hg topic banana
  $ hg ci -qAm 'banana'

  $ hg incoming -R ../clone --config experimental.tns-default-pull-namespaces=foo
  comparing with * (glob)
  searching for changes
  no changes found
  [1]

  $ hg pull -R ../clone --config experimental.tns-default-pull-namespaces=foo
  pulling from * (glob)
  searching for changes
  no changes found

this config option takes a list of values

  $ hg incoming -R ../clone --config experimental.tns-default-pull-namespaces=foo,bob
  comparing with * (glob)
  searching for changes
  1: banana default//bob/banana (draft)

  $ hg pull -R ../clone --config experimental.tns-default-pull-namespaces=foo,bob
  pulling from * (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: bob
  added 1 changesets with 1 changes to 1 files
  new changesets ed9751f04a18 (1 drafts)
  (run 'hg update' to get a working copy)

we have a "permit all" config value

  $ echo coconut > c
  $ hg debug-topic-namespace charlie
  $ hg topic coconut
  $ hg ci -qAm 'coconut'

  $ hg incoming -R ../clone --config experimental.tns-default-pull-namespaces=*
  comparing with * (glob)
  searching for changes
  2: coconut default//charlie/coconut (draft)

  $ hg pull -R ../clone --config experimental.tns-default-pull-namespaces=*
  pulling from * (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: charlie
  added 1 changesets with 1 changes to 1 files
  new changesets 16d2440597e2 (1 drafts)
  (run 'hg update' to get a working copy)

testing the default value for this config option at the moment

  $ echo durian > d
  $ hg debug-topic-namespace dave
  $ hg topic durian
  $ hg ci -qAm 'durian'

  $ hg incoming -R ../clone
  comparing with * (glob)
  searching for changes
  3: durian default//dave/durian (draft)

  $ hg pull -R ../clone
  pulling from * (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  topic namespaces affected: dave
  added 1 changesets with 1 changes to 1 files
  new changesets d5d5dda52b2f (1 drafts)
  (run 'hg update' to get a working copy)

testing related config options
also specifying changesets and branches explicitly

  $ echo elderberry > e
  $ hg debug-topic-namespace eve
  $ hg topic elderberry
  $ hg ci -qAm 'elderberry'

  $ echo feijoa > f
  $ hg debug-topic-namespace frank
  $ hg topic feijoa
  $ hg ci -qAm 'feijoa'

global hgrc

  $ cat >> $HGRCPATH << EOF
  > [experimental]
  > tns-default-pull-namespaces = alice, bob, eve
  > EOF

  $ hg incoming -R ../clone
  comparing with * (glob)
  searching for changes
  4: elderberry default//eve/elderberry (draft)

global hgrc with explicit target

  $ hg incoming -R ../clone --rev tip
  comparing with * (glob)
  searching for changes
  4: elderberry default//eve/elderberry (draft)
  5: feijoa default//frank/feijoa (draft)

source repo hgrc (should not matter)

  $ cat >> ../orig/.hg/hgrc << EOF
  > [experimental]
  > tns-default-pull-namespaces = does, not, matter
  > EOF

  $ hg incoming -R ../clone
  comparing with * (glob)
  searching for changes
  4: elderberry default//eve/elderberry (draft)

local repo hgrc (overrides global hgrc)

  $ cat >> ../clone/.hg/hgrc << EOF
  > [experimental]
  > tns-default-pull-namespaces = frank
  > EOF

  $ hg incoming -R ../clone
  comparing with * (glob)
  searching for changes
  4: elderberry default//eve/elderberry (draft)
  5: feijoa default//frank/feijoa (draft)

local repo hgrc with explicit target

  $ hg incoming -R ../clone --rev 4
  comparing with * (glob)
  searching for changes
  4: elderberry default//eve/elderberry (draft)

#if http
  $ $RUNTESTDIR/killdaemons.py $DAEMON_PIDS
  $ cat $TESTTMP/errors.log
#endif

  $ hg branches
  default//frank/feijoa          5:c58726fdcfd8
  default//eve/elderberry        4:59694f5082fe (inactive)
  default//dave/durian           3:d5d5dda52b2f (inactive)
  default//charlie/coconut       2:16d2440597e2 (inactive)
  default//bob/banana            1:ed9751f04a18 (inactive)
  default//apple                 0:bf4c1d971543 (inactive)

  $ cd ..
