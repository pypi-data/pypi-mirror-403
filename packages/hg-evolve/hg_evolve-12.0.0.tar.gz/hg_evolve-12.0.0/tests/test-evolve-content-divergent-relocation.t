======================================================
Tests the resolution of content divergence: relocation
======================================================

This file intend to cover case where changesets need to be moved to different parents

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n ({bookmarks}) [{branch}] {phase}"
  > [phases]
  > publish = False
  > [extensions]
  > rebase =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH


Testing resolution of content-divergent changesets when they are on different
parents and resolution and relocation wont result in conflicts
------------------------------------------------------------------------------

  $ hg init multiparents
  $ cd multiparents
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ for ch in a b c d; do echo foo > $ch; hg add $ch; hg ci -qm "added "$ch; done;

  $ hg glog
  @  4:c41c793e0ef1 added d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo bar > b
  $ hg amend
  2 new orphan changesets

  $ hg rebase -r b1661037fa25 -d 8fa14d15e168 --hidden --config experimental.evolution.allowdivergence=True
  rebasing 2:b1661037fa25 "added b"
  2 new content-divergent changesets

  $ hg glog
  *  6:da4b96f4a8d6 added b
  |   () [default] draft
  | @  5:7ed0642d644b added b
  | |   () [default] draft
  | | *  4:c41c793e0ef1 added d
  | | |   () [default] draft
  | | *  3:ca1b80f7960a added c
  | | |   () [default] draft
  | | x  2:b1661037fa25 added b
  | |/    () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

In this case, we have two divergent changeset:
- one did not changed parent
- the other did changed parent

So we can do a 3 way merges merges. on one side we have changes (the parent
change) and on the other one we don't, we should apply the change.

  $ hg evolve --list --rev 'contentdivergent()'
  7ed0642d644b: added b
    content-divergent: da4b96f4a8d6 (draft) (precursor b1661037fa25)
  
  da4b96f4a8d6: added b
    content-divergent: 7ed0642d644b (draft) (precursor b1661037fa25)
  

  $ hg glog --hidden --rev '::(7ed0642d644b+da4b96f4a8d6+b1661037fa25)'
  *  6:da4b96f4a8d6 added b
  |   () [default] draft
  | @  5:7ed0642d644b added b
  | |   () [default] draft
  | | x  2:b1661037fa25 added b
  | |/    () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent
  merge:[5] added b
  with: [6] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset 7ed0642d644b on 8fa14d15e168
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at bd76a775c527

  $ hg glog
  @  8:bd76a775c527 added b
  |   () [default] draft
  | *  4:c41c793e0ef1 added d
  | |   () [default] draft
  | *  3:ca1b80f7960a added c
  | |   () [default] draft
  | x  2:b1661037fa25 added b
  | |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID bd76a775c52744611afa76b4980e0b46a7a105f5
  # Parent  8fa14d15e1684a9720b1b065aba9d5ea51024cb2
  added b
  
  diff -r 8fa14d15e168 -r bd76a775c527 b
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar

  $ hg debugobsolete
  b1661037fa25511d0b7ccddf405e336f9d7d3424 7ed0642d644bb9ad93d252dd9ffe7b4729febe48 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  b1661037fa25511d0b7ccddf405e336f9d7d3424 da4b96f4a8d610a85b225583138f681d67e275dd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  7ed0642d644bb9ad93d252dd9ffe7b4729febe48 df708ef51071b9b7932664cb88742483ffa6c0af 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  df708ef51071b9b7932664cb88742483ffa6c0af bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  da4b96f4a8d610a85b225583138f681d67e275dd bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    bd76a775c527 (8) added b
  |\     amended(content) from da4b96f4a8d6 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten from df708ef51071 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  da4b96f4a8d6 (6) added b
  | |    rebased(parent) from b1661037fa25 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  df708ef51071 (7) added b
  | |    rebased(parent) from 7ed0642d644b using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  7ed0642d644b (5) added b
  |/     amended(content) from b1661037fa25 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  b1661037fa25 (2) added b
  

Resolving orphans to get back to a normal graph

  $ hg evolve --all
  move:[3] added c
  atop:[8] added b
  move:[4] added d
  $ hg glog
  o  10:44c908a29dde added d
  |   () [default] draft
  o  9:905d3f000de6 added c
  |   () [default] draft
  @  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

More testing!

  $ echo x > x
  $ hg ci -Aqm "added x"
  $ hg glog -r .
  @  11:2eea3a452f03 added x
  |   () [default] draft
  ~

  $ echo foo > x
  $ hg branch bar
  marked working directory as branch bar
  (branches are permanent and global, did you want a bookmark?)
  $ hg amend -m "added foo to x"

  $ hg up 'predecessors(.)' --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 2eea3a452f03
  (hidden revision '2eea3a452f03' was rewritten as: f9c46439290c)
  working directory parent is obsolete! (2eea3a452f03)
  (use 'hg evolve' to update to its successor: f9c46439290c)
  $ hg rebase -r . -d 'desc("added d")' --config experimental.evolution.allowdivergence=True
  rebasing 11:2eea3a452f03 "added x"
  2 new content-divergent changesets

  $ hg glog
  @  13:03d7f147ff42 added x
  |   () [default] draft
  | *  12:f9c46439290c added foo to x
  | |   () [bar] draft
  o |  10:44c908a29dde added d
  | |   () [default] draft
  o |  9:905d3f000de6 added c
  |/    () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent
  merge:[12] added foo to x
  with: [13] added x
  base: [11] added x
  rebasing "divergent" content-divergent changeset f9c46439290c on 44c908a29dde
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 60f40a789d85

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch bar
  # Node ID 60f40a789d85a42549e1e10c27779cfb5d5e1e1c
  # Parent  44c908a29dde4b2a7fd1fa5714177b99a2423bbb
  added foo to x
  
  diff -r 44c908a29dde -r 60f40a789d85 x
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/x	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo

The above `hg exp` and the following log call demonstrates that message, content
and branch change is preserved in case of relocation
  $ hg glog
  @  15:60f40a789d85 added foo to x
  |   () [bar] draft
  o  10:44c908a29dde added d
  |   () [default] draft
  o  9:905d3f000de6 added c
  |   () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg debugobsolete
  b1661037fa25511d0b7ccddf405e336f9d7d3424 7ed0642d644bb9ad93d252dd9ffe7b4729febe48 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  b1661037fa25511d0b7ccddf405e336f9d7d3424 da4b96f4a8d610a85b225583138f681d67e275dd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  7ed0642d644bb9ad93d252dd9ffe7b4729febe48 df708ef51071b9b7932664cb88742483ffa6c0af 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  df708ef51071b9b7932664cb88742483ffa6c0af bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  da4b96f4a8d610a85b225583138f681d67e275dd bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  ca1b80f7960aae2306287bab52b4090c59af8c29 905d3f000de6ac0cdca8ed4bd222bf08ddb4b6d4 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  c41c793e0ef1ddb463e85ea9491e377d01127ba2 44c908a29dde4b2a7fd1fa5714177b99a2423bbb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  2eea3a452f0362f367aa8a45ffc2ebec52971c3d f9c46439290cf371c88424caaefc92398d808666 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '73', 'operation': 'amend', 'user': 'test'}
  2eea3a452f0362f367aa8a45ffc2ebec52971c3d 03d7f147ff4243d7ac83eba7047ab8847da35c91 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  f9c46439290cf371c88424caaefc92398d808666 45cdf781a3eac63e762b68047e0beee60a47a805 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  45cdf781a3eac63e762b68047e0beee60a47a805 60f40a789d85a42549e1e10c27779cfb5d5e1e1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  03d7f147ff4243d7ac83eba7047ab8847da35c91 60f40a789d85a42549e1e10c27779cfb5d5e1e1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '73', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    60f40a789d85 (15) added foo to x
  |\     rewritten(description, branch, content) from 03d7f147ff42 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten from 45cdf781a3ea using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  03d7f147ff42 (13) added x
  | |    rebased(parent) from 2eea3a452f03 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  45cdf781a3ea (14) added foo to x
  | |    rebased(parent) from f9c46439290c using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  f9c46439290c (12) added foo to x
  |/     rewritten(description, branch, content) from 2eea3a452f03 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  2eea3a452f03 (11) added x
  

Testing when both the content-divergence are on different parents and resolution
will lead to conflicts
---------------------------------------------------------------------------------

  $ hg up .^^^
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved

  $ echo y > y
  $ hg ci -Aqm "added y"
  $ hg glog -r .
  @  16:6cba24390b74 added y
  |   () [default] draft
  ~

  $ echo bar > y
  $ hg amend

  $ hg up 'predecessors(.)' --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 6cba24390b74
  (hidden revision '6cba24390b74' was rewritten as: 347339f712be)
  working directory parent is obsolete! (6cba24390b74)
  (use 'hg evolve' to update to its successor: 347339f712be)
  $ hg rebase -r . -d 'desc("added foo to x")' --config experimental.evolution.allowdivergence=True
  rebasing 16:6cba24390b74 "added y"
  2 new content-divergent changesets
  $ echo wat > y
  $ hg amend

  $ hg glog
  @  19:7734a6171413 added y
  |   () [bar] draft
  | *  17:347339f712be added y
  | |   () [default] draft
  o |  15:60f40a789d85 added foo to x
  | |   () [bar] draft
  o |  10:44c908a29dde added d
  | |   () [default] draft
  o |  9:905d3f000de6 added c
  |/    () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent
  merge:[17] added y
  with: [19] added y
  base: [16] added y
  rebasing "divergent" content-divergent changeset 347339f712be on 60f40a789d85
  merging y
  warning: conflicts while merging y! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo watbar > y
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  working directory is now at a1a5f649aad4

  $ hg glog
  @  21:a1a5f649aad4 added y
  |   () [bar] draft
  o  15:60f40a789d85 added foo to x
  |   () [bar] draft
  o  10:44c908a29dde added d
  |   () [default] draft
  o  9:905d3f000de6 added c
  |   () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg debugobsolete
  b1661037fa25511d0b7ccddf405e336f9d7d3424 7ed0642d644bb9ad93d252dd9ffe7b4729febe48 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  b1661037fa25511d0b7ccddf405e336f9d7d3424 da4b96f4a8d610a85b225583138f681d67e275dd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  7ed0642d644bb9ad93d252dd9ffe7b4729febe48 df708ef51071b9b7932664cb88742483ffa6c0af 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  df708ef51071b9b7932664cb88742483ffa6c0af bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  da4b96f4a8d610a85b225583138f681d67e275dd bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  ca1b80f7960aae2306287bab52b4090c59af8c29 905d3f000de6ac0cdca8ed4bd222bf08ddb4b6d4 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  c41c793e0ef1ddb463e85ea9491e377d01127ba2 44c908a29dde4b2a7fd1fa5714177b99a2423bbb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  2eea3a452f0362f367aa8a45ffc2ebec52971c3d f9c46439290cf371c88424caaefc92398d808666 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '73', 'operation': 'amend', 'user': 'test'}
  2eea3a452f0362f367aa8a45ffc2ebec52971c3d 03d7f147ff4243d7ac83eba7047ab8847da35c91 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  f9c46439290cf371c88424caaefc92398d808666 45cdf781a3eac63e762b68047e0beee60a47a805 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  45cdf781a3eac63e762b68047e0beee60a47a805 60f40a789d85a42549e1e10c27779cfb5d5e1e1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  03d7f147ff4243d7ac83eba7047ab8847da35c91 60f40a789d85a42549e1e10c27779cfb5d5e1e1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '73', 'operation': 'evolve', 'user': 'test'}
  6cba24390b749067bef92c44e0288e6f554bfb37 347339f712becdde80c9ad13d22a497db6086d90 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  6cba24390b749067bef92c44e0288e6f554bfb37 24f8adc447ef80b160e63ae48688e98cb737166f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '68', 'operation': 'rebase', 'user': 'test'}
  24f8adc447ef80b160e63ae48688e98cb737166f 7734a6171413c2df9c39102accf4bc21cbc5bd9a 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  347339f712becdde80c9ad13d22a497db6086d90 6f720dea6f607e618f51c0cf1b07f8415de5e23e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  6f720dea6f607e618f51c0cf1b07f8415de5e23e a1a5f649aad404acfddaa979465e96581c2ce0fb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '72', 'operation': 'evolve', 'user': 'test'}
  7734a6171413c2df9c39102accf4bc21cbc5bd9a a1a5f649aad404acfddaa979465e96581c2ce0fb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r . --all
  @    a1a5f649aad4 (21) added y
  |\     rewritten(branch, content) from 6f720dea6f60 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    amended(content) from 7734a6171413 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  6f720dea6f60 (20) added y
  | |    rebased(parent) from 347339f712be using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  7734a6171413 (19) added y
  | |    amended(content) from 24f8adc447ef using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  24f8adc447ef (18) added y
  | |    rewritten(branch, parent) from 6cba24390b74 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  347339f712be (17) added y
  |/     amended(content) from 6cba24390b74 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  6cba24390b74 (16) added y
  

checking that relocated commit is there
  $ hg exp 20 --hidden
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 6f720dea6f607e618f51c0cf1b07f8415de5e23e
  # Parent  60f40a789d85a42549e1e10c27779cfb5d5e1e1c
  added y
  
  diff -r 60f40a789d85 -r 6f720dea6f60 y
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/y	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar

Testing when the relocation will result in conflicts and merging also:
----------------------------------------------------------------------

  $ hg glog
  @  21:a1a5f649aad4 added y
  |   () [bar] draft
  o  15:60f40a789d85 added foo to x
  |   () [bar] draft
  o  10:44c908a29dde added d
  |   () [default] draft
  o  9:905d3f000de6 added c
  |   () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg up .^^^^
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved

  $ echo z > z
  $ hg ci -Aqm "added z"
  $ hg glog -r .
  @  22:e308b18e59ab added z
  |   () [default] draft
  ~

  $ echo foo > y
  $ hg add y
  $ hg amend

  $ hg up 'predecessors(.)' --hidden
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset e308b18e59ab
  (hidden revision 'e308b18e59ab' was rewritten as: 20885f9c4458)
  working directory parent is obsolete! (e308b18e59ab)
  (use 'hg evolve' to update to its successor: 20885f9c4458)
  $ hg rebase -r . -d 'desc("added y")' --config experimental.evolution.allowdivergence=True
  rebasing 22:e308b18e59ab "added z"
  2 new content-divergent changesets
  $ echo bar > z
  $ hg amend

  $ hg glog
  @  25:85cb29df3b9e added z
  |   () [bar] draft
  | *  23:20885f9c4458 added z
  | |   () [default] draft
  o |  21:a1a5f649aad4 added y
  | |   () [bar] draft
  o |  15:60f40a789d85 added foo to x
  | |   () [bar] draft
  o |  10:44c908a29dde added d
  | |   () [default] draft
  o |  9:905d3f000de6 added c
  |/    () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent --any
  merge:[23] added z
  with: [25] added z
  base: [22] added z
  rebasing "divergent" content-divergent changeset 20885f9c4458 on a1a5f649aad4
  merging y
  warning: conflicts while merging y! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff -r a1a5f649aad4 y
  --- a/y	Thu Jan 01 00:00:00 1970 +0000
  +++ b/y	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< destination: a1a5f649aad4 bar - test: added y
   watbar
  +=======
  +foo
  +>>>>>>> evolving:    20885f9c4458 - test: added z
  diff -r a1a5f649aad4 z
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/z	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +z

  $ echo foo > y
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  evolving 23:20885f9c4458 "added z"
  merging y
  warning: conflicts while merging y! (edit, then use 'hg resolve --mark')
  1 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff -r 3ad61e93b7b0 y
  --- a/y	Thu Jan 01 00:00:00 1970 +0000
  +++ b/y	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< local: 3ad61e93b7b0 - test: added z
   foo
  +=======
  +watbar
  +>>>>>>> other: 85cb29df3b9e bar - test: added z
  diff -r 3ad61e93b7b0 z
  --- a/z	Thu Jan 01 00:00:00 1970 +0000
  +++ b/z	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -z
  +bar

  $ echo foo > y
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  working directory is now at 9fe0112b059e

  $ hg glog
  @  27:9fe0112b059e added z
  |   () [bar] draft
  o  21:a1a5f649aad4 added y
  |   () [bar] draft
  o  15:60f40a789d85 added foo to x
  |   () [bar] draft
  o  10:44c908a29dde added d
  |   () [default] draft
  o  9:905d3f000de6 added c
  |   () [default] draft
  o  8:bd76a775c527 added b
  |   () [default] draft
  | o  1:c7586e2a9264 added a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch bar
  # Node ID 9fe0112b059ea3e9b1213e4f07839b957125ffca
  # Parent  a1a5f649aad404acfddaa979465e96581c2ce0fb
  added z
  
  diff -r a1a5f649aad4 -r 9fe0112b059e y
  --- a/y	Thu Jan 01 00:00:00 1970 +0000
  +++ b/y	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -watbar
  +foo
  diff -r a1a5f649aad4 -r 9fe0112b059e z
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/z	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar

  $ hg debugobsolete
  b1661037fa25511d0b7ccddf405e336f9d7d3424 7ed0642d644bb9ad93d252dd9ffe7b4729febe48 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  b1661037fa25511d0b7ccddf405e336f9d7d3424 da4b96f4a8d610a85b225583138f681d67e275dd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  7ed0642d644bb9ad93d252dd9ffe7b4729febe48 df708ef51071b9b7932664cb88742483ffa6c0af 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  df708ef51071b9b7932664cb88742483ffa6c0af bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  da4b96f4a8d610a85b225583138f681d67e275dd bd76a775c52744611afa76b4980e0b46a7a105f5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  ca1b80f7960aae2306287bab52b4090c59af8c29 905d3f000de6ac0cdca8ed4bd222bf08ddb4b6d4 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  c41c793e0ef1ddb463e85ea9491e377d01127ba2 44c908a29dde4b2a7fd1fa5714177b99a2423bbb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  2eea3a452f0362f367aa8a45ffc2ebec52971c3d f9c46439290cf371c88424caaefc92398d808666 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '73', 'operation': 'amend', 'user': 'test'}
  2eea3a452f0362f367aa8a45ffc2ebec52971c3d 03d7f147ff4243d7ac83eba7047ab8847da35c91 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  f9c46439290cf371c88424caaefc92398d808666 45cdf781a3eac63e762b68047e0beee60a47a805 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  45cdf781a3eac63e762b68047e0beee60a47a805 60f40a789d85a42549e1e10c27779cfb5d5e1e1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  03d7f147ff4243d7ac83eba7047ab8847da35c91 60f40a789d85a42549e1e10c27779cfb5d5e1e1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '73', 'operation': 'evolve', 'user': 'test'}
  6cba24390b749067bef92c44e0288e6f554bfb37 347339f712becdde80c9ad13d22a497db6086d90 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  6cba24390b749067bef92c44e0288e6f554bfb37 24f8adc447ef80b160e63ae48688e98cb737166f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '68', 'operation': 'rebase', 'user': 'test'}
  24f8adc447ef80b160e63ae48688e98cb737166f 7734a6171413c2df9c39102accf4bc21cbc5bd9a 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  347339f712becdde80c9ad13d22a497db6086d90 6f720dea6f607e618f51c0cf1b07f8415de5e23e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  6f720dea6f607e618f51c0cf1b07f8415de5e23e a1a5f649aad404acfddaa979465e96581c2ce0fb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '72', 'operation': 'evolve', 'user': 'test'}
  7734a6171413c2df9c39102accf4bc21cbc5bd9a a1a5f649aad404acfddaa979465e96581c2ce0fb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  e308b18e59abf67245f1d9e19d26578bab7cd9c1 20885f9c44581ef505edf72a1de7c939ed3eb794 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  e308b18e59abf67245f1d9e19d26578bab7cd9c1 29d63ec6339e534af5eff2c8f3f47cfac2f2c863 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '68', 'operation': 'rebase', 'user': 'test'}
  29d63ec6339e534af5eff2c8f3f47cfac2f2c863 85cb29df3b9e7c6d08ffa7d546639c5360acc92d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  20885f9c44581ef505edf72a1de7c939ed3eb794 3ad61e93b7b0eb94c634e61fe0570cc016cf2d1b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '12', 'operation': 'evolve', 'user': 'test'}
  3ad61e93b7b0eb94c634e61fe0570cc016cf2d1b 9fe0112b059ea3e9b1213e4f07839b957125ffca 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '72', 'operation': 'evolve', 'user': 'test'}
  85cb29df3b9e7c6d08ffa7d546639c5360acc92d 9fe0112b059ea3e9b1213e4f07839b957125ffca 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    9fe0112b059e (27) added z
  |\     rewritten(branch, content) from 3ad61e93b7b0 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    amended(content) from 85cb29df3b9e using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  3ad61e93b7b0 (26) added z
  | |    rewritten(parent, content) from 20885f9c4458 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  85cb29df3b9e (25) added z
  | |    amended(content) from 29d63ec6339e using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  20885f9c4458 (23) added z
  | |    amended(content) from e308b18e59ab using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  29d63ec6339e (24) added z
  |/     rewritten(branch, parent) from e308b18e59ab using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  e308b18e59ab (22) added z
  

  $ cd ..

Testing when relocation results in nothing to commit
----------------------------------------------------

Set up a repo where relocation results in no changes to commit because the
changes from the relocated node are already in the destination.

  $ hg init nothing-to-commit
  $ cd nothing-to-commit
  $ echo 0 > a
  $ hg ci -Aqm initial
  $ echo 1 > a
  $ hg ci -Aqm upstream
  $ hg prev -q

Create the source of divergence.
  $ echo 0 > b
  $ hg ci -Aqm divergent

The first side of the divergence get rebased on top of upstream.
  $ hg rebase -r . -d 'desc("upstream")'
  rebasing 2:898ddd4443b3 tip "divergent"
  $ hg --hidden co 2 -q
  updated to hidden changeset 898ddd4443b3
  (hidden revision '898ddd4443b3' was rewritten as: befae6138569)
  working directory parent is obsolete! (898ddd4443b3)

The other side of the divergence gets amended so it matches upstream.
Relocation (onto upstream) will therefore result in no changes to commit.
  $ hg revert -r 'desc("upstream")' --all
  removing b
  reverting a
  $ hg amend --config experimental.evolution.allowdivergence=True
  2 new content-divergent changesets

Add a commit on top. This one should become an orphan. Evolving it later
should put it on top of the other divergent side (the one that's on top of
upstream)
  $ echo 0 > c
  $ hg ci -Aqm child
  $ hg co -q null
  $ hg glog
  o  5:88473f9137d1 child
  |   () [default] draft
  *  4:4cc21313ecee divergent
  |   () [default] draft
  | *  3:befae6138569 divergent
  | |   () [default] draft
  | o  1:33c576d20069 upstream
  |/    () [default] draft
  o  0:98a3f8f02ba7 initial
      () [default] draft
  $ hg evolve --content-divergent
  merge:[3] divergent
  with: [4] divergent
  base: [2] divergent
  rebasing "other" content-divergent changeset 4cc21313ecee on 33c576d20069
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  1 new orphan changesets
  $ hg glog
  o  7:412e351c2892 divergent
  |   () [default] draft
  | *  5:88473f9137d1 child
  | |   () [default] draft
  | x  4:4cc21313ecee divergent
  | |   () [default] draft
  o |  1:33c576d20069 upstream
  |/    () [default] draft
  o  0:98a3f8f02ba7 initial
      () [default] draft

  $ hg evolve --any
  move:[5] child
  atop:[7] divergent
  $ hg glog
  o  8:b361c3801668 child
  |   () [default] draft
  o  7:412e351c2892 divergent
  |   () [default] draft
  o  1:33c576d20069 upstream
  |   () [default] draft
  o  0:98a3f8f02ba7 initial
      () [default] draft
  $ hg debugobsolete
  898ddd4443b3d5520bf48f22f9411d5a0751cf2e befae61385695f1ae4b78b030ad91075b2b523ef 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  898ddd4443b3d5520bf48f22f9411d5a0751cf2e 4cc21313ecee97ce33265514a0596a192bfa6b3f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  4cc21313ecee97ce33265514a0596a192bfa6b3f 76fca1cf64e34efb00748a6cc50d2d0b411e3039 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '12', 'operation': 'evolve', 'user': 'test'}
  befae61385695f1ae4b78b030ad91075b2b523ef 412e351c28921f27c0f3ac678e209a9e99d9b76c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  76fca1cf64e34efb00748a6cc50d2d0b411e3039 412e351c28921f27c0f3ac678e209a9e99d9b76c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  88473f9137d12e90055d30bbb9b78dd786520870 b361c3801668c8ba867a32ecc2a38cfdfb582a7e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r 'desc("divergent")' --all
  o    412e351c2892 (7) divergent
  |\     rewritten from 76fca1cf64e3 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    amended(content) from befae6138569 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  76fca1cf64e3 (6) divergent
  | |    rewritten(parent, content) from 4cc21313ecee using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  befae6138569 (3) divergent
  | |    rebased(parent) from 898ddd4443b3 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  4cc21313ecee (4) divergent
  |/     amended(content) from 898ddd4443b3 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  898ddd4443b3 (2) divergent
  
  $ cd ..
