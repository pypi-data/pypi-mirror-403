  $ . $TESTDIR/testlib/common.sh

Global setup
============

  $ cat >> $HGRCPATH << EOF
  > [phases]
  > publish = false
  > [alias]
  > glf = log -GT "{rev}: {desc} ({files})"
  > glhf = log -GT "{rev}:{node|short} {desc} ({files})"
  > [extensions]
  > evolve =
  > EOF

  $ hg init rewind-testing-base
  $ cd rewind-testing-base
  $ echo a > root
  $ hg ci -qAm 'c_ROOT'
  $ echo a > A
  $ hg ci -qAm 'c_A0'
  $ echo a > B
  $ hg ci -qAm 'c_B0'

  $ hg log -G
  @  changeset:   2:7e594302a05d
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

  $ cd ..

Rewinding to a single changeset
===============================

  $ hg clone rewind-testing-base rewind-testing-single-prunes
  updating to branch default
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd rewind-testing-single-prunes

Prune changeset unrelated to the working copy
---------------------------------------------

update to an unrelated changeset

  $ hg up 'desc("c_ROOT")'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved

prune the head

  $ hg prune -r 'desc("c_B0")'
  1 changesets pruned
  $ hg log -G
  o  changeset:   1:579f120ba918
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  @  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

target selection

  $ hg rewind --hidden --to 'desc("c_B0")' --dry-run
  rewinding a pruned commit to 1 changesets: 7e594302a05d

actual rewind

  $ hg rewind --hidden --to 'desc("c_B0")'
  rewound to 1 changesets
  $ hg debugobsolete
  7e594302a05d3769b27be88fc3cdfd39d7498498 0 {579f120ba91885449adc92eedf48ef3569742cee} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 073989a581cf430a844192364fa37606357cbbc2 4 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog -r 'desc("c_B0")' --no-origin
  o  073989a581cf (3) c_B0
  |
  x  7e594302a05d (2) c_B0
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
       meta-changed(meta) as 073989a581cf using rewind by test (Thu Jan 01 00:00:00 1970 +0000)
  
  $ hg obslog -r 'desc("c_B0")'
  o  073989a581cf (3) c_B0
  |    meta-changed(meta) from 7e594302a05d using rewind by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  
  $ hg log -G
  o  changeset:   3:073989a581cf
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  @  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
XXX-TODO: fix the obsfate from "meta-changed as 3" to "identical" or something.

  $ hg log -G --hidden
  o  changeset:   3:073989a581cf
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  | x  changeset:   2:7e594302a05d
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    meta-changed using rewind as 3:073989a581cf
  |    summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  @  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

Other independent rewind creates a different revision
-----------------------------------------------------

note: we use "default-date" to make it a "different rewind"

  $ echo '[devel]' >> $HGRCPATH
  $ echo 'default-date = 1 0' >> $HGRCPATH

  $ hg prune 'desc("c_B0")'
  1 changesets pruned

target selection

  $ hg rewind --hidden --to 'min(desc("c_B0"))' --dry-run
  rewinding a pruned commit to 1 changesets: 7e594302a05d

actual rewind

  $ hg rewind --hidden --to 'min(desc("c_B0"))'
  rewound to 1 changesets
  $ hg debugobsolete
  7e594302a05d3769b27be88fc3cdfd39d7498498 0 {579f120ba91885449adc92eedf48ef3569742cee} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 073989a581cf430a844192364fa37606357cbbc2 4 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  073989a581cf430a844192364fa37606357cbbc2 0 {579f120ba91885449adc92eedf48ef3569742cee} (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 b13b032065ef57a68d9a4cead38ba0f34f95529b 4 (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog -r 'desc("c_B0")' --all --no-origin
  x  073989a581cf (3) c_B0
  |    pruned using prune by test (Thu Jan 01 00:00:01 1970 +0000)
  |
  | o  b13b032065ef (4) c_B0
  |/
  x  7e594302a05d (2) c_B0
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
       meta-changed(meta) as 073989a581cf using rewind by test (Thu Jan 01 00:00:00 1970 +0000)
       meta-changed(meta) as b13b032065ef using rewind by test (Thu Jan 01 00:00:01 1970 +0000)
  
  $ hg obslog -r 'desc("c_B0")' --all
  x  073989a581cf (3) c_B0
  |    meta-changed(meta) from 7e594302a05d using rewind by test (Thu Jan 01 00:00:00 1970 +0000)
  |    pruned using prune by test (Thu Jan 01 00:00:01 1970 +0000)
  |
  | o  b13b032065ef (4) c_B0
  |/     meta-changed(meta) from 7e594302a05d using rewind by test (Thu Jan 01 00:00:01 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  
  $ hg log -G
  o  changeset:   4:b13b032065ef
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  @  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ hg log -G --hidden
  o  changeset:   4:b13b032065ef
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  | x  changeset:   3:073989a581cf
  |/   parent:      1:579f120ba918
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    pruned using prune
  |    summary:     c_B0
  |
  | x  changeset:   2:7e594302a05d
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    meta-changed using rewind as 4:b13b032065ef
  |    obsolete:    meta-changed using rewind as 3:073989a581cf
  |    summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  @  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ cd ..

  $ hg clone rewind-testing-base rewind-testing-single-amends
  updating to branch default
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd rewind-testing-single-amends

Rewind a simple amend - creating content-divergence
---------------------------------------------------

  $ echo BB > B
  $ hg amend -m 'c_B1'
  $ hg log -G
  @  changeset:   3:25c8f5ab0c3b
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B1
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

target selection

  $ hg rewind --from 'desc("c_B1")' --as-divergence --dry-run
  recreating 1 changesets: 7e594302a05d
  $ hg rewind --hidden --to 'desc("c_B0")' --as-divergence --dry-run
  recreating 1 changesets: 7e594302a05d

actual rewind

  $ hg rewind --hidden --to 'desc("c_B0")' --as-divergence
  2 new content-divergent changesets
  rewound to 1 changesets
  $ hg debugobsolete
  7e594302a05d3769b27be88fc3cdfd39d7498498 25c8f5ab0c3bb569ec672570f1a901be4c6f032b 0 (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 b13b032065ef57a68d9a4cead38ba0f34f95529b 4 (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --rev 'desc("c_B0")' --no-origin
  *  b13b032065ef (4) c_B0
  |
  x  7e594302a05d (2) c_B0
       rewritten(description, content) as 25c8f5ab0c3b using amend by test (Thu Jan 01 00:00:01 1970 +0000)
       meta-changed(meta) as b13b032065ef using rewind by test (Thu Jan 01 00:00:01 1970 +0000)
  
  $ hg obslog --rev 'desc("c_B0")'
  *  b13b032065ef (4) c_B0
  |    meta-changed(meta) from 7e594302a05d using rewind by test (Thu Jan 01 00:00:01 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
  
  $ hg log -G
  *  changeset:   4:b13b032065ef
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     c_B0
  |
  | @  changeset:   3:25c8f5ab0c3b
  |/   parent:      1:579f120ba918
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    instability: content-divergent
  |    summary:     c_B1
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ hg log -G --hidden
  *  changeset:   4:b13b032065ef
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     c_B0
  |
  | @  changeset:   3:25c8f5ab0c3b
  |/   parent:      1:579f120ba918
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    instability: content-divergent
  |    summary:     c_B1
  |
  | x  changeset:   2:7e594302a05d
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    meta-changed using rewind as 4:b13b032065ef
  |    obsolete:    rewritten using amend as 3:25c8f5ab0c3b
  |    summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

rewind --dry-run output when rewinding with relevant divergence

  $ hg rewind --to 'min(desc("c_B0"))' --hidden --dry-run
  abort: rewind confused by divergence on 7e594302a05d
  (solve divergence first or use "--as-divergence")
  [255]
  $ hg rewind --to 'min(desc("c_B0"))' --hidden --as-divergence --dry-run
  recreating 1 changesets: 7e594302a05d

cleanup

  $ hg prune 'max(desc("c_B0"))'
  1 changesets pruned
  $ hg log -G
  @  changeset:   3:25c8f5ab0c3b
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B1
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

Rewind a simple amend - obsoleting the current latest successor
---------------------------------------------------------------

target selection

  $ hg rewind --hidden --to 'min(desc("c_B0"))' --dry-run
  rewinding 25c8f5ab0c3b to 1 changesets: 7e594302a05d

actual rewind

  $ echo 'default-date = 2 0' >> $HGRCPATH
  $ hg rewind --hidden --to 'min(desc("c_B0"))'
  rewound to 1 changesets
  (1 changesets obsoleted)
  working directory is now at 837cd997bb05
  $ hg debugobsolete
  7e594302a05d3769b27be88fc3cdfd39d7498498 25c8f5ab0c3bb569ec672570f1a901be4c6f032b 0 (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 b13b032065ef57a68d9a4cead38ba0f34f95529b 4 (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  b13b032065ef57a68d9a4cead38ba0f34f95529b 0 {579f120ba91885449adc92eedf48ef3569742cee} (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 837cd997bb05a27f8ed7d1ba3ff1e8422b9b464e 4 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  25c8f5ab0c3bb569ec672570f1a901be4c6f032b 837cd997bb05a27f8ed7d1ba3ff1e8422b9b464e 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '11', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --rev 'desc("c_B0")' --no-origin
  @    837cd997bb05 (5) c_B0
  |\
  x |  25c8f5ab0c3b (3) c_B1
  |/     rewritten(description, meta, content) as 837cd997bb05 using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       rewritten(description, content) as 25c8f5ab0c3b using amend by test (Thu Jan 01 00:00:01 1970 +0000)
       meta-changed(meta) as 837cd997bb05 using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
       meta-changed(meta) as b13b032065ef using rewind by test (Thu Jan 01 00:00:01 1970 +0000)
  
  $ hg obslog --rev 'desc("c_B0")'
  @    837cd997bb05 (5) c_B0
  |\     rewritten(description, meta, content) from 25c8f5ab0c3b using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  | |    meta-changed(meta) from 7e594302a05d using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  | |
  x |  25c8f5ab0c3b (3) c_B1
  |/     rewritten(description, content) from 7e594302a05d using amend by test (Thu Jan 01 00:00:01 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
  
  $ hg log -G
  @  changeset:   5:837cd997bb05
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ hg log -G --hidden
  @  changeset:   5:837cd997bb05
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  | x  changeset:   4:b13b032065ef
  |/   parent:      1:579f120ba918
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    pruned using prune
  |    summary:     c_B0
  |
  | x  changeset:   3:25c8f5ab0c3b
  |/   parent:      1:579f120ba918
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    rewritten using rewind as 5:837cd997bb05
  |    summary:     c_B1
  |
  | x  changeset:   2:7e594302a05d
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    meta-changed using rewind as 4:b13b032065ef
  |    obsolete:    meta-changed using rewind as 5:837cd997bb05
  |    obsolete:    rewritten using amend as 3:25c8f5ab0c3b
  |    summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ cd ..

  $ hg clone rewind-testing-base rewind-testing-single-split-fold
  updating to branch default
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd rewind-testing-single-split-fold

Rewind a simple split
---------------------

  $ echo C > C
  $ echo D > D
  $ hg ci -qAm 'c_CD0'
  $ hg split --config ui.interactive=yes << EOF
  > y
  > f
  > d
  > c
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding C
  adding D
  diff --git a/C b/C
  new file mode 100644
  examine changes to 'C'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +C
  record change 1/2 to 'C'?
  (enter ? for help) [Ynesfdaq?] f
  
  diff --git a/D b/D
  new file mode 100644
  examine changes to 'D'?
  (enter ? for help) [Ynesfdaq?] d
  
  created new head
  continue splitting? [Ycdq?] c
  $ hg log -G
  @  changeset:   5:9576e80d6851
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:02 1970 +0000
  |  summary:     c_CD0
  |
  o  changeset:   4:a0316c4c5417
  |  parent:      2:7e594302a05d
  |  user:        test
  |  date:        Thu Jan 01 00:00:02 1970 +0000
  |  summary:     c_CD0
  |
  o  changeset:   2:7e594302a05d
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ hg debugobsolete
  49fb7d900906b0a3d329e90da4dcb0a7582d3b6e a0316c4c54179357e71d068fb8884678ebc7c351 9576e80d6851ce79cd535e2dc5fa01b444d89a39 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '12', 'operation': 'split', 'user': 'test'}
  $ hg obslog --all --no-origin
  @  9576e80d6851 (5) c_CD0
  |
  | o  a0316c4c5417 (4) c_CD0
  |/
  x  49fb7d900906 (3) c_CD0
       split(parent, content) as 9576e80d6851, a0316c4c5417 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  
  $ hg obslog --all
  @  9576e80d6851 (5) c_CD0
  |    split(parent, content) from 49fb7d900906 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  |
  | o  a0316c4c5417 (4) c_CD0
  |/     split(parent, content) from 49fb7d900906 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  |
  x  49fb7d900906 (3) c_CD0
  

target selection

  $ hg rewind --from 'desc("c_CD0")' --dry-run
  rewinding a0316c4c5417 9576e80d6851 to 1 changesets: 49fb7d900906
  $ hg rewind --hidden --to 'min(desc("c_CD0"))' --dry-run
  rewinding a0316c4c5417 9576e80d6851 to 1 changesets: 49fb7d900906

actual rewind

  $ hg rewind --hidden --to 'min(desc("c_CD0"))'
  rewound to 1 changesets
  (2 changesets obsoleted)
  working directory is now at 4535d0af405c
  $ hg debugobsolete
  49fb7d900906b0a3d329e90da4dcb0a7582d3b6e a0316c4c54179357e71d068fb8884678ebc7c351 9576e80d6851ce79cd535e2dc5fa01b444d89a39 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '12', 'operation': 'split', 'user': 'test'}
  49fb7d900906b0a3d329e90da4dcb0a7582d3b6e 4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b 4 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  9576e80d6851ce79cd535e2dc5fa01b444d89a39 4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '14', 'fold-id': 'eeda726b', 'fold-idx': '1', 'fold-size': '2', 'operation': 'rewind', 'user': 'test'}
  a0316c4c54179357e71d068fb8884678ebc7c351 4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '10', 'fold-id': 'eeda726b', 'fold-idx': '2', 'fold-size': '2', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --no-origin
  @    4535d0af405c (6) c_CD0
  |\
  | \
  | |\
  | x |  9576e80d6851 (5) c_CD0
  |/ /     folded(meta, parent, content) as 4535d0af405c using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  | |
  | x  a0316c4c5417 (4) c_CD0
  |/     folded(meta, content) as 4535d0af405c using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  |
  x  49fb7d900906 (3) c_CD0
       meta-changed(meta) as 4535d0af405c using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
       split(parent, content) as 9576e80d6851, a0316c4c5417 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  
  $ hg obslog
  @    4535d0af405c (6) c_CD0
  |\     meta-changed(meta) from 49fb7d900906 using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  | |    folded(meta, parent, content) from 9576e80d6851, a0316c4c5417 using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  | |
  | \
  | |\
  | x |  9576e80d6851 (5) c_CD0
  |/ /     split(parent, content) from 49fb7d900906 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  | |
  | x  a0316c4c5417 (4) c_CD0
  |/     split(parent, content) from 49fb7d900906 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  |
  x  49fb7d900906 (3) c_CD0
  
  $ hg log -G
  @  changeset:   6:4535d0af405c
  |  tag:         tip
  |  parent:      2:7e594302a05d
  |  user:        test
  |  date:        Thu Jan 01 00:00:02 1970 +0000
  |  summary:     c_CD0
  |
  o  changeset:   2:7e594302a05d
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

Rewind a fold
-------------

  $ echo 'default-date = 3 0' >> $HGRCPATH

target selection

  $ hg rewind --from . --hidden --dry-run
  rewinding 4535d0af405c to 2 changesets: a0316c4c5417 9576e80d6851

  $ hg rewind --to '9576e80d6851+a0316c4c5417' --hidden --dry-run
  rewinding 4535d0af405c to 2 changesets: a0316c4c5417 9576e80d6851
  $ hg rewind --to '9576e80d6851' --hidden --dry-run
  rewinding 4535d0af405c to 2 changesets: a0316c4c5417 9576e80d6851
  $ hg rewind --to 'a0316c4c5417' --hidden --dry-run
  rewinding 4535d0af405c to 2 changesets: a0316c4c5417 9576e80d6851

  $ hg rewind --to '9576e80d6851' --exact --hidden --dry-run
  rewinding 4535d0af405c to 2 changesets: a0316c4c5417 9576e80d6851
  $ hg rewind --to 'a0316c4c5417' --exact --hidden --dry-run
  rewinding 4535d0af405c to 2 changesets: a0316c4c5417 9576e80d6851

actual rewind

  $ hg rewind --to '9576e80d6851+a0316c4c5417' --hidden
  rewound to 2 changesets
  (1 changesets obsoleted)
  working directory is now at 95d72d892df7
  $ hg debugobsolete
  49fb7d900906b0a3d329e90da4dcb0a7582d3b6e a0316c4c54179357e71d068fb8884678ebc7c351 9576e80d6851ce79cd535e2dc5fa01b444d89a39 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '12', 'operation': 'split', 'user': 'test'}
  49fb7d900906b0a3d329e90da4dcb0a7582d3b6e 4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b 4 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  9576e80d6851ce79cd535e2dc5fa01b444d89a39 4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '14', 'fold-id': 'eeda726b', 'fold-idx': '1', 'fold-size': '2', 'operation': 'rewind', 'user': 'test'}
  a0316c4c54179357e71d068fb8884678ebc7c351 4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b 0 (Thu Jan 01 00:00:02 1970 +0000) {'ef1': '10', 'fold-id': 'eeda726b', 'fold-idx': '2', 'fold-size': '2', 'operation': 'rewind', 'user': 'test'}
  a0316c4c54179357e71d068fb8884678ebc7c351 e76375de0bfc9c59bdd91067c901f3eed7d6c8fe 4 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  9576e80d6851ce79cd535e2dc5fa01b444d89a39 95d72d892df7fec59107e10914c5729bdf03665f 4 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  4535d0af405c1bf35f37b35f26ec6f9acfa6fe0b e76375de0bfc9c59bdd91067c901f3eed7d6c8fe 95d72d892df7fec59107e10914c5729bdf03665f 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '14', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog -r -2: --no-origin
  @    95d72d892df7 (8) c_CD0
  |\
  +---o  e76375de0bfc (7) c_CD0
  | | |
  x---+  4535d0af405c (6) c_CD0
  |\| |    split(meta, parent, content) as 95d72d892df7, e76375de0bfc using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  | | |
  | x |  9576e80d6851 (5) c_CD0
  |/ /     folded(meta, parent, content) as 4535d0af405c using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  | |      rewritten(meta, parent) as 95d72d892df7 using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  | |
  | x  a0316c4c5417 (4) c_CD0
  |/     folded(meta, content) as 4535d0af405c using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
  |      meta-changed(meta) as e76375de0bfc using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  49fb7d900906 (3) c_CD0
       meta-changed(meta) as 4535d0af405c using rewind by test (Thu Jan 01 00:00:02 1970 +0000)
       split(parent, content) as 9576e80d6851, a0316c4c5417 using split by test (Thu Jan 01 00:00:02 1970 +0000)
  
  $ hg log -G
  @  changeset:   8:95d72d892df7
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:02 1970 +0000
  |  summary:     c_CD0
  |
  o  changeset:   7:e76375de0bfc
  |  parent:      2:7e594302a05d
  |  user:        test
  |  date:        Thu Jan 01 00:00:02 1970 +0000
  |  summary:     c_CD0
  |
  o  changeset:   2:7e594302a05d
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ cd ..

Rewinding a stack
=================

  $ hg clone rewind-testing-base rewind-testing-stack
  updating to branch default
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd rewind-testing-stack

Rewinding the top of the stack only
-----------------------------------

  $ hg up 'desc("c_A0")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo AA >> A
  $ hg amend -m 'c_A1'
  1 new orphan changesets
  $ hg evolve --update
  move:[2] c_B0
  atop:[3] c_A1
  working directory is now at a65fceb2324a
  $ hg debugobsolete
  579f120ba91885449adc92eedf48ef3569742cee d952d1794ff657f5c2a82225d2e6307ed930b32f 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 a65fceb2324ae1eb1231610193d24a5fa02c7c0e 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r 'desc("c_A1")::' --no-origin
  @  a65fceb2324a (4) c_B0
  |
  | o  d952d1794ff6 (3) c_A1
  | |
  | x  579f120ba918 (1) c_A0
  |      rewritten(description, content) as d952d1794ff6 using amend by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       rebased(parent) as a65fceb2324a using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
  
  $ hg obslog -r 'desc("c_A1")::'
  @  a65fceb2324a (4) c_B0
  |    rebased(parent) from 7e594302a05d using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  | o  d952d1794ff6 (3) c_A1
  | |    rewritten(description, content) from 579f120ba918 using amend by test (Thu Jan 01 00:00:03 1970 +0000)
  | |
  | x  579f120ba918 (1) c_A0
  |
  x  7e594302a05d (2) c_B0
  
  $ hg log -G
  @  changeset:   4:a65fceb2324a
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   3:d952d1794ff6
  |  parent:      0:eba9c2249fe7
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A1
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

target selection

  $ hg rewind --hidden --to 'min(desc(c_B0))' --exact --dry-run
  rewinding a65fceb2324a to 1 changesets: 7e594302a05d

actual rewind

  $ hg rewind --hidden --to 'min(desc(c_B0))' --exact
  1 new orphan changesets
  rewound to 1 changesets
  (1 changesets obsoleted)
  working directory is now at ac979e0aac4e
  $ hg debugobsolete
  579f120ba91885449adc92eedf48ef3569742cee d952d1794ff657f5c2a82225d2e6307ed930b32f 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 a65fceb2324ae1eb1231610193d24a5fa02c7c0e 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 ac979e0aac4e63ccbbf88ac33942192942302766 4 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e ac979e0aac4e63ccbbf88ac33942192942302766 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --no-origin
  @    ac979e0aac4e (5) c_B0
  |\
  | x  a65fceb2324a (4) c_B0
  |/     rewritten(meta, parent) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       rebased(parent) as a65fceb2324a using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
       meta-changed(meta) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  
  $ hg obslog
  @    ac979e0aac4e (5) c_B0
  |\     meta-changed(meta) from 7e594302a05d using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  | |    rewritten(meta, parent) from a65fceb2324a using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  | |
  | x  a65fceb2324a (4) c_B0
  |/     rebased(parent) from 7e594302a05d using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
  
  $ hg log -G
  @  changeset:   5:ac979e0aac4e
  |  tag:         tip
  |  parent:      1:579f120ba918
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: orphan
  |  summary:     c_B0
  |
  | o  changeset:   3:d952d1794ff6
  | |  parent:      0:eba9c2249fe7
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     c_A1
  | |
  x |  changeset:   1:579f120ba918
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    rewritten using amend as 3:d952d1794ff6
  |    summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

  $ hg rewind --hidden --to 'allpredecessors(desc("c_B0"))' --dry-run
  abort: not rewinding, a65fceb2324a is a successor of 7e594302a05d
  (pick only one of these changesets, possibly with --exact)
  [255]
  $ hg rewind --hidden --to 'allpredecessors(desc("c_B0"))' --dry-run --exact
  abort: not rewinding, a65fceb2324a is a successor of 7e594302a05d
  (pick only one of these changesets, possibly with --exact)
  [255]
  $ hg rewind --hidden --to 'allpredecessors(desc("c_B0"))' --dry-run --as-divergence
  abort: not rewinding, a65fceb2324a is a successor of 7e594302a05d
  (pick only one of these changesets, possibly with --exact)
  [255]

Testing the defaults
--------------------

rewind with no arguments should be equivalent to `--from .`

  $ echo 'default-date = 4 0' >> $HGRCPATH
  $ hg rewind --dry-run
  rewinding ac979e0aac4e to 1 changesets: a65fceb2324a
  $ hg rewind
  rewound to 1 changesets
  (1 changesets obsoleted)
  working directory is now at a5dd64adbb2a
  $ hg log -G
  @  changeset:   6:a5dd64adbb2a
  |  tag:         tip
  |  parent:      3:d952d1794ff6
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   3:d952d1794ff6
  |  parent:      0:eba9c2249fe7
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A1
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ hg debugobsolete
  579f120ba91885449adc92eedf48ef3569742cee d952d1794ff657f5c2a82225d2e6307ed930b32f 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 a65fceb2324ae1eb1231610193d24a5fa02c7c0e 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 ac979e0aac4e63ccbbf88ac33942192942302766 4 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e ac979e0aac4e63ccbbf88ac33942192942302766 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e a5dd64adbb2af2e646859b35d0d7128daa73cb2b 4 (Thu Jan 01 00:00:04 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  ac979e0aac4e63ccbbf88ac33942192942302766 a5dd64adbb2af2e646859b35d0d7128daa73cb2b 0 (Thu Jan 01 00:00:04 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --no-origin
  @    a5dd64adbb2a (6) c_B0
  |\
  | x  ac979e0aac4e (5) c_B0
  |/|    rewritten(meta, parent) as a5dd64adbb2a using rewind by test (Thu Jan 01 00:00:04 1970 +0000)
  | |
  x |  a65fceb2324a (4) c_B0
  |/     meta-changed(meta) as a5dd64adbb2a using rewind by test (Thu Jan 01 00:00:04 1970 +0000)
  |      rewritten(meta, parent) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       rebased(parent) as a65fceb2324a using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
       meta-changed(meta) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  
Automatically rewinding the full stack (with --to)
--------------------------------------------------

target selection

  $ hg rewind --hidden --to 'predecessors(.)' --dry-run
  rewinding d952d1794ff6 to 1 changesets: 579f120ba918
  rewinding a5dd64adbb2a to 1 changesets: ac979e0aac4e

actual rewind

  $ echo 'default-date = 5 0' >> $HGRCPATH
  $ hg rewind --hidden --to 'predecessors(.)'
  rewound to 2 changesets
  (2 changesets obsoleted)
  working directory is now at 3f2d8862657d
  $ hg debugobsolete
  579f120ba91885449adc92eedf48ef3569742cee d952d1794ff657f5c2a82225d2e6307ed930b32f 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 a65fceb2324ae1eb1231610193d24a5fa02c7c0e 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 ac979e0aac4e63ccbbf88ac33942192942302766 4 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e ac979e0aac4e63ccbbf88ac33942192942302766 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e a5dd64adbb2af2e646859b35d0d7128daa73cb2b 4 (Thu Jan 01 00:00:04 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  ac979e0aac4e63ccbbf88ac33942192942302766 a5dd64adbb2af2e646859b35d0d7128daa73cb2b 0 (Thu Jan 01 00:00:04 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  579f120ba91885449adc92eedf48ef3569742cee 9c28b7ed3951fd15b20ab75449c1e0fdec445958 4 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  ac979e0aac4e63ccbbf88ac33942192942302766 3f2d8862657d20af331f0c0531f5228eef4d36c5 4 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  a5dd64adbb2af2e646859b35d0d7128daa73cb2b 3f2d8862657d20af331f0c0531f5228eef4d36c5 0 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  d952d1794ff657f5c2a82225d2e6307ed930b32f 9c28b7ed3951fd15b20ab75449c1e0fdec445958 0 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '11', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --no-origin
  @    3f2d8862657d (8) c_B0
  |\
  x |  a5dd64adbb2a (6) c_B0
  |\|    rewritten(meta, parent) as 3f2d8862657d using rewind by test (Thu Jan 01 00:00:05 1970 +0000)
  | |
  | x  ac979e0aac4e (5) c_B0
  |/|    rewritten(meta, parent) as 3f2d8862657d using rewind by test (Thu Jan 01 00:00:05 1970 +0000)
  | |    rewritten(meta, parent) as a5dd64adbb2a using rewind by test (Thu Jan 01 00:00:04 1970 +0000)
  | |
  x |  a65fceb2324a (4) c_B0
  |/     meta-changed(meta) as a5dd64adbb2a using rewind by test (Thu Jan 01 00:00:04 1970 +0000)
  |      rewritten(meta, parent) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       rebased(parent) as a65fceb2324a using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
       meta-changed(meta) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  
  $ hg log -G
  @  changeset:   8:3f2d8862657d
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   7:9c28b7ed3951
  |  parent:      0:eba9c2249fe7
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A0
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  

Automatically rewinding the full stack (with --from)
----------------------------------------------------

target selection

  $ hg rewind --from '.' --dry-run
  rewinding 9c28b7ed3951 to 1 changesets: d952d1794ff6
  rewinding 3f2d8862657d to 1 changesets: a5dd64adbb2a

actual rewind

  $ echo 'default-date = 6 0' >> $HGRCPATH
  $ hg rewind --from '.'
  rewound to 2 changesets
  (2 changesets obsoleted)
  working directory is now at d36d6d267714
  $ hg debugobsolete
  579f120ba91885449adc92eedf48ef3569742cee d952d1794ff657f5c2a82225d2e6307ed930b32f 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 a65fceb2324ae1eb1231610193d24a5fa02c7c0e 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  7e594302a05d3769b27be88fc3cdfd39d7498498 ac979e0aac4e63ccbbf88ac33942192942302766 4 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e ac979e0aac4e63ccbbf88ac33942192942302766 0 (Thu Jan 01 00:00:03 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  a65fceb2324ae1eb1231610193d24a5fa02c7c0e a5dd64adbb2af2e646859b35d0d7128daa73cb2b 4 (Thu Jan 01 00:00:04 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  ac979e0aac4e63ccbbf88ac33942192942302766 a5dd64adbb2af2e646859b35d0d7128daa73cb2b 0 (Thu Jan 01 00:00:04 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  579f120ba91885449adc92eedf48ef3569742cee 9c28b7ed3951fd15b20ab75449c1e0fdec445958 4 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  ac979e0aac4e63ccbbf88ac33942192942302766 3f2d8862657d20af331f0c0531f5228eef4d36c5 4 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  a5dd64adbb2af2e646859b35d0d7128daa73cb2b 3f2d8862657d20af331f0c0531f5228eef4d36c5 0 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  d952d1794ff657f5c2a82225d2e6307ed930b32f 9c28b7ed3951fd15b20ab75449c1e0fdec445958 0 (Thu Jan 01 00:00:05 1970 +0000) {'ef1': '11', 'operation': 'rewind', 'user': 'test'}
  d952d1794ff657f5c2a82225d2e6307ed930b32f fef4355b4cc9e2d3ddc154f60e4f4f1a286e9ce7 4 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  a5dd64adbb2af2e646859b35d0d7128daa73cb2b d36d6d267714108384f31762b6193c32f9f97514 4 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  3f2d8862657d20af331f0c0531f5228eef4d36c5 d36d6d267714108384f31762b6193c32f9f97514 0 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '6', 'operation': 'rewind', 'user': 'test'}
  9c28b7ed3951fd15b20ab75449c1e0fdec445958 fef4355b4cc9e2d3ddc154f60e4f4f1a286e9ce7 0 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '11', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --no-origin
  @    d36d6d267714 (10) c_B0
  |\
  x |  3f2d8862657d (8) c_B0
  |\|    rewritten(meta, parent) as d36d6d267714 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | |
  | x  a5dd64adbb2a (6) c_B0
  |/|    rewritten(meta, parent) as 3f2d8862657d using rewind by test (Thu Jan 01 00:00:05 1970 +0000)
  | |    rewritten(meta, parent) as d36d6d267714 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | |
  x |  ac979e0aac4e (5) c_B0
  |\|    rewritten(meta, parent) as 3f2d8862657d using rewind by test (Thu Jan 01 00:00:05 1970 +0000)
  | |    rewritten(meta, parent) as a5dd64adbb2a using rewind by test (Thu Jan 01 00:00:04 1970 +0000)
  | |
  | x  a65fceb2324a (4) c_B0
  |/     meta-changed(meta) as a5dd64adbb2a using rewind by test (Thu Jan 01 00:00:04 1970 +0000)
  |      rewritten(meta, parent) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  |
  x  7e594302a05d (2) c_B0
       rebased(parent) as a65fceb2324a using evolve by test (Thu Jan 01 00:00:03 1970 +0000)
       meta-changed(meta) as ac979e0aac4e using rewind by test (Thu Jan 01 00:00:03 1970 +0000)
  
  $ hg log -G
  @  changeset:   10:d36d6d267714
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B0
  |
  o  changeset:   9:fef4355b4cc9
  |  parent:      0:eba9c2249fe7
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A1
  |
  o  changeset:   0:eba9c2249fe7
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_ROOT
  
  $ cd ..

Merge commits
=============

  $ hg clone -q rewind-testing-base rewind-merge
  $ cd rewind-merge

  $ hg up --clean .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo foo > foo
  $ hg ci -qAm foo

  $ hg merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m merge
  $ hg st --change .
  A B

  $ echo bar > foo
  $ hg amend -m 'merge, but foo is now bar'
  $ hg st --change .
  M foo
  A B

  $ hg rewind --from .
  rewound to 1 changesets
  (1 changesets obsoleted)
  working directory is now at 9d325190bd87
  $ hg st --change .
  A B

  $ hg glf -r '. + allpredecessors(.) + parents(.)' --hidden
  @    6: merge ()
  |\
  +---x  5: merge, but foo is now bar (foo)
  | |/
  +---x  4: merge ()
  | |/
  | o  3: foo (foo)
  | |
  | ~
  o  2: c_B0 (B)
  |
  ~

  $ cd ..

Rewind --keep
=============

  $ hg init rewind-keep
  $ cd rewind-keep
  $ echo root > root
  $ hg ci -qAm 'root'

  $ echo apple > a
  $ echo banana > b
  $ hg ci -qAm initial

  $ hg rm b
  $ echo apricot > a
  $ echo coconut > c
  $ hg add c
  $ hg status
  M a
  A c
  R b
  $ hg amend -m amended
  $ hg glf --hidden
  @  2: amended (a c)
  |
  | x  1: initial (a b)
  |/
  o  0: root (root)
  

Clean wdir

  $ hg rewind --keep --to 'desc("initial")' --hidden
  rewound to 1 changesets
  (1 changesets obsoleted)
  $ hg debugobsolete
  30704102d912d9d35a3d51400c4c93ad1e8bc7f3 2ea5be2f87510c7d26d5866dec83b57a7d939c4a 0 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  30704102d912d9d35a3d51400c4c93ad1e8bc7f3 b4c97fddc16aa57693fa0a730d4b44ceb75bb35c 4 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  2ea5be2f87510c7d26d5866dec83b57a7d939c4a b4c97fddc16aa57693fa0a730d4b44ceb75bb35c 0 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '11', 'operation': 'rewind', 'user': 'test'}
  $ hg obslog --no-origin
  @    b4c97fddc16a (3) initial
  |\
  x |  2ea5be2f8751 (2) amended
  |/     rewritten(description, meta, content) as b4c97fddc16a using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  |
  x  30704102d912 (1) initial
       rewritten(description, content) as 2ea5be2f8751 using amend by test (Thu Jan 01 00:00:06 1970 +0000)
       meta-changed(meta) as b4c97fddc16a using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  
  $ hg obslog
  @    b4c97fddc16a (3) initial
  |\     rewritten(description, meta, content) from 2ea5be2f8751 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | |    meta-changed(meta) from 30704102d912 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | |
  x |  2ea5be2f8751 (2) amended
  |/     rewritten(description, content) from 30704102d912 using amend by test (Thu Jan 01 00:00:06 1970 +0000)
  |
  x  30704102d912 (1) initial
  
  $ hg glf --hidden
  @  3: initial (a b)
  |
  | x  2: amended (a c)
  |/
  | x  1: initial (a b)
  |/
  o  0: root (root)
  
  $ hg st
  M a
  A c
  R b

Making wdir even more dirty

  $ echo avocado > a
  $ echo durian > d
  $ hg st
  M a
  A c
  R b
  ? d

No rewinding without --keep

  $ hg rewind --to 'desc("amended")' --hidden
  abort: uncommitted changes
  [20]

XXX: Unfortunately, even with --keep it's not allowed

  $ hg rewind --keep --to 'desc("amended")' --hidden
  abort: uncommitted changes
  [20]

  $ cd ..

Extra cases related to folds
============================

folding with a changeset created after the rewind target
--------------------------------------------------------

..      B0 ⇠\
..      |    ⇠ AB2
.. A0 ⇠ A1 ⇠/

this simple test case introduces the idea of making rewind consider different
evolutions of fold components: "parent" evolution of A has more predecessors

  $ hg init extra-fold-case-1
  $ cd extra-fold-case-1

  $ echo R > R
  $ hg ci -qAm R
  $ echo A > A
  $ hg ci -qAm A0
  $ hg amend -m A1
  $ echo B > B
  $ hg ci -qAm B0
  $ hg fold -r 'desc("A1")::' -m AB2 --exact -q

  $ hg glhf --hidden
  @  4:7f9a5314ef94 AB2 (A B)
  |
  | x  3:16429ed4b6cb B0 (B)
  | |
  | x  2:3748b241cad8 A1 (A)
  |/
  | x  1:fa8956746c52 A0 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

target selection

when rewinding from a fold, rewind to all of its components (at various points
in their evolution) to not lose work

  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: fa8956746c52 16429ed4b6cb
  $ hg rewind --hidden --to 'desc("B0")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: 3748b241cad8 16429ed4b6cb
  $ hg rewind --from 'desc("AB2")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: 3748b241cad8 16429ed4b6cb

  $ hg rewind --hidden --to 'allpredecessors(desc("AB2"))' --dry-run
  abort: not rewinding, 3748b241cad8 is a successor of fa8956746c52
  (pick only one of these changesets, possibly with --exact)
  [255]

  $ cd ..

folding with a changeset we rebased onto
----------------------------------------

.. A0 ⇠ A1 ⇠\
..      |    ⇠ AB2
..      B0 ⇠/

similar to the previous case, but this time evolution of A has more
predecessors and at some point starts to be based on B

  $ hg init extra-fold-case-2
  $ cd extra-fold-case-2

  $ echo R > R
  $ hg ci -qAm R
  $ echo A > A
  $ hg ci -qAm A0
  $ hg up 'desc("R")' -q
  $ echo B > B
  $ hg ci -qAm B0
  $ echo A > A
  $ hg ci -qAm A1
  $ hg prune -r 'desc("A0")' -s 'desc("A1")'
  1 changesets pruned

  $ hg fold -r 'desc("B0")::' -m AB2 --exact -q

  $ hg glhf --hidden
  @  4:1988e9fe9517 AB2 (A B)
  |
  | x  3:7175ff74409b A1 (A)
  | |
  | x  2:d6ed1d624918 B0 (B)
  |/
  | x  1:fa8956746c52 A0 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

target selection

when rewinding from a fold, rewind to all of its components (at various points
in their evolution) to not lose work

  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: fa8956746c52 d6ed1d624918
  $ hg rewind --hidden --to 'desc("B0")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: d6ed1d624918 7175ff74409b
  $ hg rewind --from 'desc("AB2")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: d6ed1d624918 7175ff74409b

  $ cd ..

folding with a changeset that rebased on us
-------------------------------------------

.. B0 ⇠⇠⇠⇠ B1 ⇠\
.. |       |    ⇠ AB2
.. |  A0 ⇠ A1 ⇠/

now evolutions of A and B have the same amount of changesets, but at point 0
they aren't yet related

  $ hg init extra-fold-case-3
  $ cd extra-fold-case-3

  $ echo R > R
  $ hg ci -qAm R
  $ echo A > A
  $ hg ci -qAm A0
  $ hg amend -m A1
  $ hg up 'desc("R")' -q
  $ echo B > B
  $ hg ci -qAm B0
  $ hg up 'desc("A1")' -q
  $ echo B > B
  $ hg ci -qAm B1
  $ hg prune -r 'desc("B0")' -s 'desc("B1")'
  1 changesets pruned

  $ hg fold -r 'desc("A1")::' -m AB2 --exact -q

  $ hg glhf --hidden
  @  5:7f9a5314ef94 AB2 (A B)
  |
  | x  4:fe7a7d317e16 B1 (B)
  | |
  +---x  3:d6ed1d624918 B0 (B)
  | |
  | x  2:3748b241cad8 A1 (A)
  |/
  | x  1:fa8956746c52 A0 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

target selection

  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: fa8956746c52 fe7a7d317e16
  $ hg rewind --hidden --to 'desc("B0")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: 3748b241cad8 d6ed1d624918
  $ hg rewind --hidden --to 'desc("A1")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: 3748b241cad8 fe7a7d317e16
  $ hg rewind --hidden --to 'desc("B1")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: 3748b241cad8 fe7a7d317e16
  $ hg rewind --from 'desc("AB2")' --dry-run
  rewinding 7f9a5314ef94 to 2 changesets: 3748b241cad8 fe7a7d317e16

actual rewind

  $ hg rewind --hidden --to 'desc("A0")'
  1 new orphan changesets
  rewound to 2 changesets
  (1 changesets obsoleted)
  working directory is now at e492d2f9be46

after rewind to A0:
- A0' and B1' are successors to AB2 (split using rewind)
- A0' is a successor of A0 (operation: rewind)
- A0' is a child of R (just like A0)
- B1' is a successor of B1 (operation: rewind)
- B1' is a child of A1 (just like B1), and therefore an orphan

  $ hg obslog -a
  o    54b340ce1d87 (6) A0
  |\     split(description, meta, parent, content) from 7f9a5314ef94 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | |    meta-changed(meta) from fa8956746c52 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | |
  +---@  e492d2f9be46 (7) B1
  | | |    split(description, meta, parent, content) from 7f9a5314ef94 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | | |    meta-changed(meta) from fe7a7d317e16 using rewind by test (Thu Jan 01 00:00:06 1970 +0000)
  | | |
  x---+  7f9a5314ef94 (5) AB2
  | | |    folded(description, parent, content) from 3748b241cad8, fe7a7d317e16 using fold by test (Thu Jan 01 00:00:06 1970 +0000)
  | | |
  x | |  3748b241cad8 (2) A1
  |/ /     reworded(description) from fa8956746c52 using amend by test (Thu Jan 01 00:00:06 1970 +0000)
  | |
  | x  fe7a7d317e16 (4) B1
  | |    rewritten(description, parent) from d6ed1d624918 using prune by test (Thu Jan 01 00:00:06 1970 +0000)
  | |
  | x  d6ed1d624918 (3) B0
  |
  x  fa8956746c52 (1) A0
  
  $ hg glhf
  @  7:e492d2f9be46 B1 (B)
  |
  | o  6:54b340ce1d87 A0 (A)
  | |
  x |  2:3748b241cad8 A1 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

  $ hg debugobsolete --exclusive -r 'first(head())'
  7f9a5314ef94f5856ee90661268194cc5ce9b332 54b340ce1d87f3593fd9de2a742e7b444e5136ed e492d2f9be46b73c0cfa51709e92db864b8f3ed9 0 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '15', 'operation': 'rewind', 'user': 'test'}
  fa8956746c5294ce3351309133b450c5930f30f5 54b340ce1d87f3593fd9de2a742e7b444e5136ed 4 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}
  $ hg debugobsolete --exclusive -r 'last(head())'
  7f9a5314ef94f5856ee90661268194cc5ce9b332 54b340ce1d87f3593fd9de2a742e7b444e5136ed e492d2f9be46b73c0cfa51709e92db864b8f3ed9 0 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '15', 'operation': 'rewind', 'user': 'test'}
  fe7a7d317e168a15e8aa43131b54d3256443d728 e492d2f9be46b73c0cfa51709e92db864b8f3ed9 4 (Thu Jan 01 00:00:06 1970 +0000) {'ef1': '2', 'operation': 'rewind', 'user': 'test'}

  $ cd ..

simple fold with a missing part
-------------------------------

.. B0 ⇠ (B1) ⇠\
.. |     |     ⇠ AB2
.. A0 ⇠  A1  ⇠/

a stack was rewritten, but then a part of it became unknown locally

  $ hg init extra-fold-case-4
  $ cd extra-fold-case-4

  $ echo R > R
  $ hg ci -qAm R
  $ echo A > A
  $ hg ci -qAm A0
  $ echo B > B
  $ hg ci -qAm B0
  $ hg up 'desc("R")' -q
  $ echo A > A
  $ hg ci -qAm A1
  $ echo B > B
  $ hg ci -qAm B1
  $ hg prune -r 'desc("A0")+desc("B0")' -s 'desc("A1")+desc("B1")' --biject
  2 changesets pruned

  $ hg fold -r 'desc("A1") + desc("B1")' -m AB2 --exact -q

  $ hg glhf --hidden
  @  5:1988e9fe9517 AB2 (A B)
  |
  | x  4:25210d726f52 B1 (B)
  | |
  | x  3:9c76368ab336 A1 (A)
  |/
  | x  2:a07c12c45197 B0 (B)
  | |
  | x  1:fa8956746c52 A0 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

target selection

  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: fa8956746c52 25210d726f52
  $ hg rewind --hidden --to 'desc("A1")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: 9c76368ab336 25210d726f52
  $ hg rewind --hidden --to 'desc("B1")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: 9c76368ab336 25210d726f52

because B0 is a child of A0, we use A0 instead of A1 unless --exact is given

XXX the semantic of --exact might need clarification here,
XXX for example, shouln't --exact make sure we only rewind to the `--to` target ?

  $ hg rewind --hidden --to 'desc("B0")' --dry-run
  rewinding 1988e9fe9517 to 2 changesets: fa8956746c52 a07c12c45197
  $ hg rewind --hidden --to 'desc("B0")' --exact --dry-run
  rewinding 1988e9fe9517 to 2 changesets: a07c12c45197 9c76368ab336

stripping one of the fold parts

  $ hg strip --config extensions.strip= -r 'desc("B1")' --hidden -q

  $ hg glhf --hidden
  @  4:1988e9fe9517 AB2 (A B)
  |
  | x  3:9c76368ab336 A1 (A)
  |/
  | x  2:a07c12c45197 B0 (B)
  | |
  | x  1:fa8956746c52 A0 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

target selection

the obvious challenge here is to somehow work around the missing fold
component, but we can't do much because it is one of the latest predecessors of
AB2 fold

in future we might have a way to allow rewind to skip changesets unknown
locally and still proceed (and lose the least amount of work possible)

  $ hg rewind --hidden --to 'desc("A0")+desc("B0")' --exact --dry-run
  rewinding 1988e9fe9517 to 2 changesets: fa8956746c52 a07c12c45197
  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  abort: not rewinding, some predecessors are unknown locally: 25210d726f52
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]
  $ hg rewind --hidden --to 'desc("A1")' --dry-run
  abort: not rewinding, some predecessors are unknown locally: 25210d726f52
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]

XXX the semantic of --exact might need clarification here,
XXX for example, shouln't --exact make sure we only rewind to the `--to` target ?

  $ hg rewind --hidden --to 'desc("A1")' --exact --dry-run
  abort: not rewinding, some predecessors are unknown locally: 25210d726f52
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]
  $ hg rewind --from 'desc("AB2")' --dry-run
  abort: not rewinding, some predecessors are unknown locally: 25210d726f52
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]
  $ hg rewind --from 'desc("AB2")' --exact --dry-run
  abort: not rewinding, some predecessors are unknown locally: 25210d726f52
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]

  $ cd ..

split and then fold with a missing part
---------------------------------------

..      /⇠ (C1) ⇠\
.. BC0 ⇠    |     \
..  |   \⇠  B1     ⇠ AC2
..  A0 ⇠⇠⇠⇠⇠⇠⇠⇠⇠⇠⇠/

here we have a case when walking successors and then predecessors of target
revisions just once might not be enough, because it's a more complex DAG with a
changeset missing from local repo

  $ hg init extra-fold-case-5
  $ cd extra-fold-case-5

  $ echo R > R
  $ hg ci -qAm R
  $ echo A > A
  $ hg ci -qAm A0
  $ echo B > B
  $ echo C > C
  $ hg ci -qAm BC0
  $ hg up 'desc("A0")' -q
  $ echo B > B
  $ hg ci -qAm B1
  $ echo C > C
  $ hg ci -qAm C1

  $ hg prune -r 'desc("BC0")' -s 'desc("B1")+desc("C1")' --split
  1 changesets pruned

  $ hg up 'desc("R")' -q
  $ echo A > A
  $ echo C > C
  $ hg ci -qAm AC2

  $ hg prune -r 'desc("A0")+desc("C1")' -s 'desc("AC2")' --fold
  2 changesets pruned
  1 new orphan changesets

  $ hg glhf --hidden
  @  5:9ccaac2e5fbb AC2 (A C)
  |
  | x  4:2e4ab803d8ae C1 (C)
  | |
  | *  3:44774eafdc1c B1 (B)
  | |
  | | x  2:883d75400657 BC0 (B C)
  | |/
  | x  1:fa8956746c52 A0 (A)
  |/
  o  0:167e04d3d1b2 R (R)
  

target selection

  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  rewinding 9ccaac2e5fbb to 2 changesets: fa8956746c52 2e4ab803d8ae
  $ hg rewind --hidden --to 'desc("BC0")' --dry-run
  rewinding 44774eafdc1c to 1 changesets: 883d75400657
  rewinding 9ccaac2e5fbb to 2 changesets: fa8956746c52 883d75400657
  $ hg rewind --from 'desc("AC2")' --dry-run
  rewinding 9ccaac2e5fbb to 2 changesets: fa8956746c52 2e4ab803d8ae

stripping a component of AC2 fold

  $ hg strip --config extensions.strip= --hidden -r 'desc("C1")' -q
  warning: ignoring unknown working parent 9ccaac2e5fbb!

target selection

at the moment, there's not much that we can do here because of missing C1

in future we might have a way to allow rewind to skip changesets unknown
locally and still proceed (and lose the least amount of work possible)

XXX the semantic of --exact might need clarification here,
XXX for example, shouln't --exact make sure we only rewind to the `--to` target ?

  $ hg rewind --hidden --to 'desc("A0")' --dry-run
  abort: not rewinding, some predecessors are unknown locally: 2e4ab803d8ae
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]
  $ hg rewind --hidden --to 'desc("BC0")' --dry-run
  rewinding 44774eafdc1c to 1 changesets: 883d75400657
  rewinding 9ccaac2e5fbb to 2 changesets: fa8956746c52 883d75400657
  $ hg rewind --from 'desc("AC2")' --dry-run
  abort: not rewinding, some predecessors are unknown locally: 2e4ab803d8ae
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]
  $ hg rewind --from 'desc("AC2")' --exact --dry-run
  abort: not rewinding, some predecessors are unknown locally: 2e4ab803d8ae
  (try selecting all changesets to rewind to manually, possibly with --exact)
  [255]
