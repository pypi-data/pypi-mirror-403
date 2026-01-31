  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

#testcases inmemory ondisk
#if inmemory
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution.in-memory = yes
  > EOF
#endif

  $ glog() {
  >   hg log -G --template '{rev}:{node|short}@{branch}({phase}) {desc|firstline}\n' "$@"
  > }

  $ hg init repo
  $ cd repo
  $ echo root > root
  $ hg ci -Am addroot
  adding root
  $ echo a > a
  $ hg ci -Am adda
  adding a
  $ echo b > b
  $ hg ci -Am addb
  adding b
  $ echo c > c
  $ hg ci -Am addc
  adding c
  $ glog
  @  3:7a7552255fb5@default(draft) addc
  |
  o  2:ef23d6ef94d6@default(draft) addb
  |
  o  1:93418d2c0979@default(draft) adda
  |
  o  0:c471ef929e6a@default(draft) addroot
  
  $ hg gdown
  gdown have been deprecated in favor of previous
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [2] addb
  $ echo b >> b
  $ hg amend
  1 new orphan changesets
  $ hg gdown
  gdown have been deprecated in favor of previous
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] adda
  $ echo a >> a
  $ hg amend
  1 new orphan changesets
  $ glog
  @  5:005fe5914f78@default(draft) adda
  |
  | *  4:22619daeed78@default(draft) addb
  | |
  | | *  3:7a7552255fb5@default(draft) addc
  | | |
  | | x  2:ef23d6ef94d6@default(draft) addb
  | |/
  | x  1:93418d2c0979@default(draft) adda
  |/
  o  0:c471ef929e6a@default(draft) addroot
  

Test stabilizing a predecessor child

  $ hg evolve -v --rev 'last(orphan())'
  move:[4] addb
  atop:[5] adda
  hg rebase -r 22619daeed78 -d 005fe5914f78
  resolving manifests
  getting b
  committing files:
  b
  committing manifest
  committing changelog
  resolving manifests (ondisk !)
  removing b (ondisk !)
  $ glog
  o  6:bede829dd2d3@default(draft) addb
  |
  @  5:005fe5914f78@default(draft) adda
  |
  | *  3:7a7552255fb5@default(draft) addc
  | |
  | x  2:ef23d6ef94d6@default(draft) addb
  | |
  | x  1:93418d2c0979@default(draft) adda
  |/
  o  0:c471ef929e6a@default(draft) addroot
  

Test stabilizing a descendant predecessor's child

  $ hg debugobsolete > successors.old
  $ hg evolve -v --update
  move:[3] addc
  atop:[6] addb
  hg rebase -r 7a7552255fb5 -d bede829dd2d3
  resolving manifests (ondisk !)
  getting b (ondisk !)
  resolving manifests
  getting c
  committing files:
  c
  committing manifest
  committing changelog
  resolving manifests (inmemory !)
  getting b (inmemory !)
  getting c (inmemory !)
  working directory is now at 65095d7d0dd5
  $ hg debugobsolete > successors.new
  $ diff -u successors.old successors.new
  --- successors.old* (glob)
  +++ successors.new* (glob)
  @@ -1,3 +1,4 @@
   ef23d6ef94d68dea65d20587dfecc8b33d165617 22619daeed78036f80fbd326b6852519c4f0c25e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
   93418d2c0979643ad446f621195e78720edb05b4 005fe5914f78e8bc64c7eba28117b0b1fa210d0d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
   22619daeed78036f80fbd326b6852519c4f0c25e bede829dd2d3b2ae9bf198c23432b250dc964458 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  +7a7552255fb5f8bd745e46fba6f0ca633a4dd716 65095d7d0dd5e4f15503bb7b1f433a5fe9bac052 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  [1]



  $ glog
  @  7:65095d7d0dd5@default(draft) addc
  |
  o  6:bede829dd2d3@default(draft) addb
  |
  o  5:005fe5914f78@default(draft) adda
  |
  o  0:c471ef929e6a@default(draft) addroot
  
  $ hg evolve -v
  no troubled changesets

Test behavior with --any

  $ hg up bede829dd2d3
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo b >> b
  $ hg amend
  1 new orphan changesets
  $ glog
  @  8:036cf654e942@default(draft) addb
  |
  | *  7:65095d7d0dd5@default(draft) addc
  | |
  | x  6:bede829dd2d3@default(draft) addb
  |/
  o  5:005fe5914f78@default(draft) adda
  |
  o  0:c471ef929e6a@default(draft) addroot
  
  $ hg up 65095d7d0dd5
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg evolve -v
  nothing to evolve on current working copy parent
  (1 other orphan in the repository, do you want --any or --rev)
  [2]
  $ hg evolve --any -v
  move:[7] addc
  atop:[8] addb
  hg rebase -r 65095d7d0dd5 -d 036cf654e942
  resolving manifests (ondisk !)
  removing c (ondisk !)
  getting b (ondisk !)
  resolving manifests
  getting c
  committing files:
  c
  committing manifest
  committing changelog
  resolving manifests (inmemory !)
  getting b (inmemory !)
  working directory is now at e99ecf51c867
  $ glog
  @  9:e99ecf51c867@default(draft) addc
  |
  o  8:036cf654e942@default(draft) addb
  |
  o  5:005fe5914f78@default(draft) adda
  |
  o  0:c471ef929e6a@default(draft) addroot
  
  $ hg evolve --any -v
  no orphan changesets to evolve
  [1]

Ambiguous evolution
  $ echo a > k
  $ hg add k
  $ hg ci -m firstambiguous
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo a > l
  $ hg add l
  $ hg ci -m secondambiguous
  created new head
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg commit --amend -m "newmessage"
  2 new orphan changesets
  $ hg log -G
  @  changeset:   12:49773ccde390
  |  tag:         tip
  |  parent:      8:036cf654e942
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     newmessage
  |
  | *  changeset:   11:a9892777b519
  | |  parent:      9:e99ecf51c867
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan
  | |  summary:     secondambiguous
  | |
  | | *  changeset:   10:0b6e26b2472d
  | |/   user:        test
  | |    date:        Thu Jan 01 00:00:00 1970 +0000
  | |    instability: orphan
  | |    summary:     firstambiguous
  | |
  | x  changeset:   9:e99ecf51c867
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    reworded using amend as 12:49773ccde390
  |    summary:     addc
  |
  o  changeset:   8:036cf654e942
  |  parent:      5:005fe5914f78
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     addb
  |
  o  changeset:   5:005fe5914f78
  |  parent:      0:c471ef929e6a
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     adda
  |
  o  changeset:   0:c471ef929e6a
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     addroot
  
  $ hg evolve --no-all
  abort: multiple evolve candidates
  (select one of *, * with --rev) (glob)
  [255]



