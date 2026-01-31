============================
Testing extensions isolation
============================

In this test case, we check that a repository using the extensions can co-exist
with a repository not using the extension.

  $ . $TESTDIR/testlib/common.sh

Setup
=====

Create repo

  $ hg init repo-evo
  $ cat > repo-evo/.hg/hgrc << EOF
  > [extensions]
  > evolve=
  > EOF
  $ hg init repo-topic
  $ cat > repo-topic/.hg/hgrc << EOF
  > [extensions]
  > topic=
  > EOF
  $ hg init repo-both
  $ cat > repo-both/.hg/hgrc << EOF
  > [extensions]
  > evolve=
  > topic=
  > EOF
  $ hg init repo-no-ext

check setup

  $ hg -R repo-evo  help -e evolve | head -n 1
  warning: --repository ignored
  evolve extension - extends Mercurial feature related to Changeset Evolution
  $ hg -R repo-both  help -e evolve | head -n 1
  warning: --repository ignored
  evolve extension - extends Mercurial feature related to Changeset Evolution
  $ hg -R repo-no-ext help -e evolve
  warning: --repository ignored
  abort: no such help topic: evolve
  (try 'hg help --keyword evolve')
  [10]
  $ hg -R repo-no-ext help -e topic
  warning: --repository ignored
  abort: no such help topic: topic
  (try 'hg help --keyword topic')
  [10]

start hgweb dir for all repo

  $ cat > hgweb.conf << EOF
  > [paths]
  > / = *
  > EOF

  $ hg serve -p $HGPORT -d --pid-file=hg.pid --web-conf hgweb.conf -A access.log -E error.log
  $ cat hg.pid >> $DAEMON_PIDS

Test isolation
--------------

As of 4.9 (and previous version). It seems like extensions are displayed as
enabled even for repository where they are not supposed to be. See the output
tagged `no-false`.

(however, topic and evolve are not supposed to affect other repository as shown
in the rest of this test).

  $ get-with-headers.py $LOCALIP:$HGPORT 'repo-no-ext/help/extensions' | grep 'enabled extensions' -A 7
  [1]
  $ get-with-headers.py $LOCALIP:$HGPORT 'repo-evo/help/extensions' | grep 'enabled extensions' -A 7
  enabled extensions:
  </p>
  <dl>
   <dt>evolve
   <dd>extends Mercurial feature related to Changeset Evolution
  </dl>
  <p>
  disabled extensions:
  $ get-with-headers.py $LOCALIP:$HGPORT 'repo-topic/help/extensions' | grep 'enabled extensions' -A 7
  enabled extensions:
  </p>
  <dl>
   <dt>evolve (no-false !)
   <dd>extends Mercurial feature related to Changeset Evolution (no-false !)
   <dt>topic
   <dd>support for topic branches
  </dl>
  $ get-with-headers.py $LOCALIP:$HGPORT 'repo-both/help/extensions' | grep 'enabled extensions' -A 9
  enabled extensions:
  </p>
  <dl>
   <dt>evolve
   <dd>extends Mercurial feature related to Changeset Evolution
   <dt>topic
   <dd>support for topic branches
  </dl>
  <p>
  disabled extensions:
  $ get-with-headers.py $LOCALIP:$HGPORT 'repo-no-ext/help/extensions' | grep 'enabled extensions' -A 9
  enabled extensions: (no-false !)
  </p> (no-false !)
  <dl> (no-false !)
   <dt>evolve (no-false !)
   <dd>extends Mercurial feature related to Changeset Evolution (no-false !)
   <dt>topic (no-false !)
   <dd>support for topic branches (no-false !)
  </dl> (no-false !)
  <p> (no-false !)
  disabled extensions: (no-false !)

make sure repos don't affect each other (and check both ways)

Check evolve isolation
-----------------------

  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-no-ext | grep -E 'topics|evoext'
  [1]
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-evo | grep -E 'topics|evoext'
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-no-ext | grep -E 'topics|evoext'
  [1]

Check topic isolation
---------------------

  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-no-ext | grep -E 'topics|evoext'
  [1]
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-topic | grep -E 'topics|evoext'
    _exttopics_heads
    ext-topics-publish=all
    ext-topics-tns-heads
    topics
    topics-namespaces
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-no-ext | grep -E 'topics|evoext'
  [1]

Check coupled isolation
-----------------------

  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-no-ext | grep -E 'topics|evoext'
  [1]
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-both | grep -E 'topics|evoext'
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1
    _exttopics_heads
    ext-topics-publish=all
    ext-topics-tns-heads
    topics
    topics-namespaces
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-evo | grep -E 'topics|evoext'
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-topic | grep -E 'topics|evoext'
    _exttopics_heads
    ext-topics-publish=all
    ext-topics-tns-heads
    topics
    topics-namespaces
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-evo | grep -E 'topics|evoext'
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1
  $ hg debugcapabilities http://$LOCALIP:$HGPORT/repo-no-ext | grep -E 'topics|evoext'
  [1]

Final cleanup
-------------

  $ cat error.log

  $ $RUNTESTDIR/killdaemons.py $DAEMON_PIDS
