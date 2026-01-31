  $ . "$TESTDIR/testlib/topic_setup.sh"

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > topic.publish-bare-branch = yes
  > topic.server-gate-topic-changesets = yes
  > 
  > [extensions]
  > evolve =
  > 
  > [phases]
  > publish = no
  > 
  > [ui]
  > ssh = "$PYTHON" "$RUNTESTDIR/dummyssh"
  > EOF

  $ hg init server
  $ cd server

  $ echo a > a
  $ hg commit -qAm root
  $ hg phase --public -r 'all()'

  $ cd ..

  $ hg clone ssh://user@dummy/server client-topic1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 6569b5a81c7e
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg clone ssh://user@dummy/server client-topic2
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 6569b5a81c7e
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg version -v -R client-topic1
  warning: --repository ignored
  Mercurial Distributed SCM (*) (glob)
  (see https://mercurial-scm.org for more information)
  
  Copyright (C) 2005-* (glob)
  This is free software; see the source for copying conditions. There is NO
  warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
  
  Enabled extensions:
  
    evolve  external  * (glob)
    rebase  internal  
    topic   external  * (glob)
  $ hg clone ssh://user@dummy/server client-plain
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 6569b5a81c7e
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cat << EOF >> client-plain/.hg/hgrc
  > [extensions]
  > topic = !
  > EOF
  $ hg version -v -R client-plain
  warning: --repository ignored
  Mercurial Distributed SCM (*) (glob)
  (see https://mercurial-scm.org for more information)
  
  Copyright (C) 2005-* (glob)
  This is free software; see the source for copying conditions. There is NO
  warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
  
  Enabled extensions:
  
    evolve  external  * (glob)
    rebase  internal  

Make two commits, with and without a topic, and push them to the server

  $ cd client-topic1
  $ echo b > b
  $ hg topic some-work
  marked working directory as topic: some-work
  $ hg commit -Am 'adding b (topic)'
  adding b
  active topic 'some-work' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo c > c
  $ hg commit -Am 'adding c (no topic)'
  adding c
  $ hg up some-work
  switching to topic some-work
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg topic --clear
  $ echo d > d
  $ hg commit -Am 'adding d (no topic)'
  adding d
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ hg log -r 'all() - 0'
  changeset:   1:2a2e8b3520f2
  topic:       some-work
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding b (topic)
  
  changeset:   2:b46feb4d24f9
  parent:      0:6569b5a81c7e
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding c (no topic)
  
  changeset:   3:be22ca6e89ea
  tag:         tip
  parent:      1:2a2e8b3520f2
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding d (no topic)
  

(disable the bare publishing to put a bare draft on the server)

  $ cat << EOF >> ../server/.hg/hgrc
  > [experimental]
  > topic.publish-bare-branch = no
  > EOF
  $ hg push --force
  pushing to ssh://user@dummy/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 3 files (+1 heads)
  $ cd ..
  $ hg --cwd server phase -r 'tip'
  3: draft

Clients with topic can exchange draft changesets both with and without a topic through the server

  $ hg --cwd client-topic2 pull
  pulling from ssh://user@dummy/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files (+1 heads)
  new changesets 2a2e8b3520f2:be22ca6e89ea (3 drafts)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg --cwd client-topic2 log -r 'all() - 0'
  changeset:   1:2a2e8b3520f2
  topic:       some-work
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding b (topic)
  
  changeset:   2:b46feb4d24f9
  parent:      0:6569b5a81c7e
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding c (no topic)
  
  changeset:   3:be22ca6e89ea
  tag:         tip
  parent:      1:2a2e8b3520f2
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding d (no topic)
  

Client without topic only sees draft changesets if they don't have a topic

  $ hg --cwd client-plain pull
  pulling from ssh://user@dummy/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets b46feb4d24f9 (1 drafts)
  (run 'hg update' to get a working copy)
  $ hg --cwd client-plain phase -r 'all() - 0'
  1: draft
  $ hg --cwd client-plain log -r 'all() - 0'
  changeset:   1:b46feb4d24f9
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     adding c (no topic)
  
