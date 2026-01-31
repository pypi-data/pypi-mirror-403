Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh

Test simple common cases
========================

Test setup
----------
  $ hg init $TESTTMP/simple
  $ cd $TESTTMP/simple

Actual test
-----------
  $ hg obslog -ap null
  @  000000000000 (-1)
  
  $ hg obslog 'wdir()'
  abort: working directory revision cannot be specified
  [255]

Test output with pushed and pulled obs markers
==============================================

Test setup
----------

  $ hg init $TESTTMP/local-remote-markers-1
  $ cd $TESTTMP/local-remote-markers-1
  $ mkcommit ROOT
  $ mkcommit A0
  $ hg log --hidden -G
  @  changeset:   1:471f378eab4c
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
  $ hg clone $TESTTMP/local-remote-markers-1 $TESTTMP/local-remote-markers-2
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd $TESTTMP/local-remote-markers-2
  $ hg log --hidden -G
  @  changeset:   1:471f378eab4c
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
  $ cd $TESTTMP/local-remote-markers-1
  $ hg amend -m "A1"
  $ hg amend -m "A2"
  $ hg log --hidden -G
  @  changeset:   3:7a230b46bf61
  |  tag:         tip
  |  parent:      0:ea207398892e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A2
  |
  | x  changeset:   2:fdf9bde5129a
  |/   parent:      0:ea207398892e
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    reworded using amend as 3:7a230b46bf61
  |    summary:     A1
  |
  | x  changeset:   1:471f378eab4c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    reworded using amend as 2:fdf9bde5129a
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Actual test
-----------

  $ hg obslog 7a230b46bf61 --patch --no-origin
  @  7a230b46bf61 (3) A2
  |
  x  fdf9bde5129a (2) A1
  |    reworded(description) as 7a230b46bf61 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r fdf9bde5129a -r 7a230b46bf61 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A1
  |      +A2
  |
  |
  x  471f378eab4c (1) A0
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r fdf9bde5129a changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A1
  
  

  $ hg obslog 7a230b46bf61 --patch
  @  7a230b46bf61 (3) A2
  |    reworded(description) from fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r fdf9bde5129a -r 7a230b46bf61 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A1
  |      +A2
  |
  |
  x  fdf9bde5129a (2) A1
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A1
  |
  |
  x  471f378eab4c (1) A0
  

  $ cd $TESTTMP/local-remote-markers-2
  $ hg pull
  pulling from $TESTTMP/local-remote-markers-1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 1 files (+1 heads)
  2 new obsolescence markers
  obsoleted 1 changesets
  new changesets 7a230b46bf61 (1 drafts)
  (run 'hg heads' to see heads)
  working directory parent is obsolete! (471f378eab4c)
  (use 'hg evolve' to update to its successor: 7a230b46bf61)
Check that obslog works with markers pointing to missing local changectx
  $ hg obslog 7a230b46bf61 --patch --no-origin
  o  7a230b46bf61 (2) A2
  |
  x  fdf9bde5129a
  |    reworded(description) as 7a230b46bf61 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      (No patch available, context is not local)
  |
  @  471f378eab4c (1) A0
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, successor is unknown locally)
  

  $ hg obslog 7a230b46bf61 --patch
  o  7a230b46bf61 (2) A2
  |    reworded(description) from fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      (No patch available, predecessor is unknown locally)
  |
  x  fdf9bde5129a
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      (No patch available, context is not local)
  |
  @  471f378eab4c (1) A0
  

  $ hg obslog 7a230b46bf61 --patch -f --no-origin
  o  7a230b46bf61 (2) A2
  |
  @  471f378eab4c (1) A0
       reworded(description) as 7a230b46bf61 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r 7a230b46bf61 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A2
  
  
  $ hg obslog 7a230b46bf61 --patch -f
  o  7a230b46bf61 (2) A2
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r 7a230b46bf61 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A2
  |
  |
  @  471f378eab4c (1) A0
  

  $ hg obslog 7a230b46bf61 --color=debug --patch
  o  [evolve.node|7a230b46bf61] [evolve.rev|(2)] [evolve.short_description|A2]
  |    [evolve.verb|reworded](description) from [evolve.node|fdf9bde5129a] using [evolve.operation|amend] by [evolve.user|test] [evolve.date|(Thu Jan 01 00:00:00 1970 +0000)]
  |      (No patch available, predecessor is unknown locally)
  |
  x  [evolve.node evolve.missing_change_ctx|fdf9bde5129a]
  |    [evolve.verb|reworded](description) from [evolve.node|471f378eab4c] using [evolve.operation|amend] by [evolve.user|test] [evolve.date|(Thu Jan 01 00:00:00 1970 +0000)]
  |      (No patch available, context is not local)
  |
  @  [evolve.node|471f378eab4c] [evolve.rev|(1)] [evolve.short_description|A0]
  

  $ hg obslog 7a230b46bf61 --graph --no-origin \
  > -T '{node|short} {rev} {desc|firstline}\n{markers % "rewritten using {operations}"}\n'
  o  7a230b46bf61 2 A2
  |
  x  fdf9bde5129a
  |  rewritten using amend
  @  471f378eab4c 1 A0
     rewritten using amend

  $ hg obslog 7a230b46bf61 --graph \
  > -T '{node|short} {rev} {desc|firstline}\n{markers % "rewritten using {operations}"}\n'
  o  7a230b46bf61 2 A2
  |  rewritten using amend
  x  fdf9bde5129a
  |  rewritten using amend
  @  471f378eab4c 1 A0
  

Test output with non-local changesets and various templates
===========================================================

  $ hg init $TESTTMP/obslog-non-local-templates
  $ cd $TESTTMP/obslog-non-local-templates
  $ cat << EOF >> .hg/hgrc
  > [templates]
  > fancy = '{desc|firstline}\n{markers % "{verb} using {operations} by {users} ({join(notes, "; ")})"}'
  > fancier = '{desc|firstline}\n{markers % "{join(users, ", ")} had {verb} this commit using {join(operations, "/")} and said: {join(notes % "\"{note}\"", ", ")})"}'
  > EOF

  $ mkcommit A0
  $ hg metaedit -m 'A1' -n 'note1' -d '42 0' --config devel.default-date='1 0' -q
  $ HGUSER=alice hg amend -m 'A2' -n 'note2'
  $ HGUSER=bob hg amend -m 'A3' -n 'note3'

  $ hg debugobsolete
  6ffd04c870fe2b73e7c885e508c4f1213a75c4d4 e481355d236800802337be3e637bd820870b04d2 0 (Thu Jan 01 00:00:01 1970 +0000) {'ef1': '33', 'note': 'note1', 'operation': 'metaedit', 'user': 'test'}
  e481355d236800802337be3e637bd820870b04d2 65835bf83412a950e6a47f023690d5e6ae09718d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'note': 'note2', 'operation': 'amend', 'user': 'alice'}
  65835bf83412a950e6a47f023690d5e6ae09718d 41985e02b792daac8907f6b30b513bbf6e8e034d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'note': 'note3', 'operation': 'amend', 'user': 'bob'}

  $ hg strip 'desc(A1) + desc(A2)' --hidden --quiet --config extensions.strip=

  $ hg obslog -f --no-origin
  @  41985e02b792 (1) A3
  |
  x  6ffd04c870fe (0) A0
       rewritten(description, date) as 41985e02b792 using amend, metaedit by alice, bob, test (between Thu Jan 01 00:00:00 1970 +0000 and Thu Jan 01 00:00:01 1970 +0000)
         note: note1
         note: note2
         note: note3
  
  $ hg obslog -f
  @  41985e02b792 (1) A3
  |    rewritten(description, date) from 6ffd04c870fe using amend, metaedit by alice, bob, test (between Thu Jan 01 00:00:00 1970 +0000 and Thu Jan 01 00:00:01 1970 +0000)
  |      note: note1
  |      note: note2
  |      note: note3
  |
  x  6ffd04c870fe (0) A0
  
  $ hg obslog -f -T fancy --no-origin
  @  A3
  |
  x  A0
     rewritten using amend, metaedit by alice, bob, test (note1; note2; note3)

  $ hg obslog -f -T fancy
  @  A3
  |  rewritten using amend, metaedit by alice, bob, test (note1; note2; note3)
  x  A0
  

  $ hg obslog -f -T fancier --no-origin
  @  A3
  |
  x  A0
     alice, bob, test had rewritten this commit using amend/metaedit and said: "note1", "note2", "note3")

  $ hg obslog -f -T fancier
  @  A3
  |  alice, bob, test had rewritten this commit using amend/metaedit and said: "note1", "note2", "note3")
  x  A0
  
