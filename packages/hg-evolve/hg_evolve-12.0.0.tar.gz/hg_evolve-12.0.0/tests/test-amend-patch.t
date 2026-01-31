** Test for the `--patch` flag for `hg amend` command **

Setup

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH << EOF
  > [diff]
  > git = 1
  > [extensions]
  > evolve =
  > EOF

Reposetup

  $ hg init repo
  $ cd repo
  $ echo foo > a
  $ hg ci -Aqm "added a"
  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID f7ad4196431346de3c33c52e75374fba45e04313
  # Parent  0000000000000000000000000000000000000000
  added a
  
  diff --git a/a b/a
  new file mode 100644
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,1 @@
  +foo

Testing of just changing the diff, not the patch metadata
==========================================================

Testing the normal case
-----------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID f7ad4196431346de3c33c52e75374fba45e04313
  > # Parent  0000000000000000000000000000000000000000
  > added a
  > diff --git a/a b/a
  > new file mode 100644
  > --- /dev/null
  > +++ b/a
  > @@ -0,0 +1,1 @@
  > +Gello
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

Making sure the amended commit is correct

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID af624b221c0c0bec5d74e2650180dd3eddcb7c42
  # Parent  0000000000000000000000000000000000000000
  added a
  
  diff --git a/a b/a
  new file mode 100644
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,1 @@
  +Gello

  $ hg glog
  @  1:af624b221c0c added a
      () draft

Obsolsence history is fine

  $ hg debugobsolete
  f7ad4196431346de3c33c52e75374fba45e04313 af624b221c0c0bec5d74e2650180dd3eddcb7c42 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  $ hg obslog -p -r .
  @  af624b221c0c (1) added a
  |    amended(content) from f7ad41964313 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff --git a/a b/a
  |      --- a/a
  |      +++ b/a
  |      @@ -1,1 +1,1 @@
  |      -foo
  |      +Gello
  |
  |
  x  f7ad41964313 (0) added a
  
Diff and status are good too
  $ hg diff
  $ hg status
  ? editor.sh
  $ cat a
  Gello

Dirstate parents should be correctly set
  $ hg parents
  changeset:   1:af624b221c0c
  tag:         tip
  parent:      -1:000000000000
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added a
  
Trying to amend with a wrong patch
----------------------------------

Having context which was is not present

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID c6ba250efbf73e671f2ca24b79db2c178ccbfff9
  > # Parent  0000000000000000000000000000000000000000
  > added a
  > diff --git a/a b/a
  > new file mode 100644
  > --- /dev/null
  > +++ b/a
  > @@ -0,0 +1,1 @@
  > I was not there before!
  > +Gello
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch
  failed to apply edited patch: bad hunk #1 @@ -0,0 +1,1 @@
   (1 0 1 1)
  try to fix the patch (yn)? y
  abort: patch unchanged
  [255]

Having deletions which dont exists

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID af624b221c0c0bec5d74e2650180dd3eddcb7c42
  > # Parent  0000000000000000000000000000000000000000
  > added a
  > diff --git a/a b/a
  > new file mode 100644
  > --- /dev/null
  > +++ b/a
  > @@ -0,0 +1,1 @@
  > -I was not deleted before!
  > +Gello
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch
  failed to apply edited patch: bad hunk #1 @@ -0,0 +1,1 @@
   (1 0 1 1)
  try to fix the patch (yn)? y
  abort: patch unchanged
  [255]

Changing the file mode using amend --patch
------------------------------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID af624b221c0c0bec5d74e2650180dd3eddcb7c42
  > # Parent  0000000000000000000000000000000000000000
  > added a
  > diff --git a/a b/a
  > new file mode 100755
  > --- /dev/null
  > +++ b/a
  > @@ -0,0 +1,1 @@
  > +Gello
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp --git
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 3a99e4b7ac73da799e20ae56914e3dd5b1a22d4d
  # Parent  0000000000000000000000000000000000000000
  added a
  
  diff --git a/a b/a
  new file mode 100755
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,1 @@
  +Gello

Changing the file using amend --patch
-------------------------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 3a99e4b7ac73da799e20ae56914e3dd5b1a22d4d
  > # Parent  0000000000000000000000000000000000000000
  > added a
  > diff --git a/changedfile b/changedfile
  > new file mode 100755
  > --- /dev/null
  > +++ b/changedfile
  > @@ -0,0 +1,1 @@
  > +Gello
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID fc57c20be380f2878f4db139dad66d6cfb42ec62
  # Parent  0000000000000000000000000000000000000000
  added a
  
  diff --git a/changedfile b/changedfile
  new file mode 100755
  --- /dev/null
  +++ b/changedfile
  @@ -0,0 +1,1 @@
  +Gello

  $ hg status -A
  ? editor.sh
  C changedfile

Handling both deletions and additions
-------------------------------------

  $ echo foobar > changedfile
  $ hg ci -m "foobar to changedfile"
  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 7969f70ffb81c3a6eee2d4f2f7032b694ce05349
  # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  foobar to changedfile
  
  diff --git a/changedfile b/changedfile
  --- a/changedfile
  +++ b/changedfile
  @@ -1,1 +1,1 @@
  -Gello
  +foobar

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 7969f70ffb81c3a6eee2d4f2f7032b694ce05349
  > # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  > foobar to changedfile
  > diff --git a/changedfile b/changedfile
  > --- a/changedfile
  > +++ b/changedfile
  > @@ -1,1 +1,1 @@
  > -Gello
  > +foobar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch
  abort: nothing changed
  [255]

Cannot change lines which are deleted

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 7969f70ffb81c3a6eee2d4f2f7032b694ce05349
  > # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  > foobar to changedfile
  > diff --git a/changedfile b/changedfile
  > --- a/changedfile
  > +++ b/changedfile
  > @@ -1,1 +1,1 @@
  > -Hello
  > +foobar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch
  patching file changedfile
  Hunk #1 FAILED at 0
  failed to apply edited patch: patch failed to apply
  try to fix the patch (yn)? y
  abort: patch unchanged
  [255]

Add more addition to the patch

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 7969f70ffb81c3a6eee2d4f2f7032b694ce05349
  > # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  > foobar to changedfile
  > diff --git a/changedfile b/changedfile
  > --- a/changedfile
  > +++ b/changedfile
  > @@ -1,1 +1,2 @@
  > -Gello
  > +foobar
  > +babar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 5d54400acb70b88f07128a1df497ed794b0b177b
  # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  foobar to changedfile
  
  diff --git a/changedfile b/changedfile
  --- a/changedfile
  +++ b/changedfile
  @@ -1,1 +1,2 @@
  -Gello
  +foobar
  +babar

  $ cat changedfile
  foobar
  babar

Introduce files which were not there
------------------------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 5d54400acb70b88f07128a1df497ed794b0b177b
  > # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  > foobar to changedfile
  > diff --git a/changedfile b/changedfile
  > --- a/changedfile
  > +++ b/changedfile
  > @@ -1,1 +1,2 @@
  > -Gello
  > +foobar
  > +babar
  > diff --git a/a b/a
  > new file mode 100755
  > --- /dev/null
  > +++ b/a
  > @@ -0,0 +1,1 @@
  > +Gello
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID c3e29c061982c94418ce141d521434d6da76cd46
  # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  foobar to changedfile
  
  diff --git a/a b/a
  new file mode 100755
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,1 @@
  +Gello
  diff --git a/changedfile b/changedfile
  --- a/changedfile
  +++ b/changedfile
  @@ -1,1 +1,2 @@
  -Gello
  +foobar
  +babar

Delete files which were not deleted in the first place
------------------------------------------------------

  $ echo Hello >> a
  $ hg ci -m "hello to a"
  $ hg glog
  @  7:3d62c45a1699 hello to a
  |   () draft
  o  6:c3e29c061982 foobar to changedfile
  |   () draft
  o  3:fc57c20be380 added a
      () draft

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 3d62c45a1699b11c7ecae573f013601712f2cc5f
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,2 @@
  >  Gello
  > +Hello
  > diff --git a/changedfile b/changedfile
  > deleted file mode 100755
  > --- a/changedfile
  > +++ /dev/null
  > @@ -1,2 +0,0 @@
  > -foobar
  > -babar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID c9875799c53fb862c0dbaf01500459c9397373a4
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,2 @@
   Gello
  +Hello
  diff --git a/changedfile b/changedfile
  deleted file mode 100755
  --- a/changedfile
  +++ /dev/null
  @@ -1,2 +0,0 @@
  -foobar
  -babar

  $ hg status
  ? editor.sh

  $ cat changedfile
  cat: changedfile: No such file or directory
  [1]

Testing sercret phase preservation during `hg amend --patch`
------------------------------------------------------------

  $ hg phase -r . --secret --force

  $ hg phase -r .
  8: secret

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID c9875799c53fb862c0dbaf01500459c9397373a4
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Hello
  > +mello
  > diff --git a/changedfile b/changedfile
  > deleted file mode 100755
  > --- a/changedfile
  > +++ /dev/null
  > @@ -1,2 +0,0 @@
  > -foobar
  > -babar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 4414485658e719a1f3d5e58bc8b2412385aa1592
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Hello
  +mello
  diff --git a/changedfile b/changedfile
  deleted file mode 100755
  --- a/changedfile
  +++ /dev/null
  @@ -1,2 +0,0 @@
  -foobar
  -babar

  $ hg phase -r .
  9: secret

Testing bookmark movement on amend --patch
------------------------------------------

  $ hg bookmark foo
  $ hg glog
  @  9:4414485658e7 hello to a
  |   (foo) secret
  o  6:c3e29c061982 foobar to changedfile
  |   () draft
  o  3:fc57c20be380 added a
      () draft

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 4414485658e719a1f3d5e58bc8b2412385aa1592
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Hello
  > +bello
  > diff --git a/changedfile b/changedfile
  > deleted file mode 100755
  > --- a/changedfile
  > +++ /dev/null
  > @@ -1,2 +0,0 @@
  > -foobar
  > -babar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 36454bda1fdb8e2e4fe07bb084eef378e29cba74
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Hello
  +bello
  diff --git a/changedfile b/changedfile
  deleted file mode 100755
  --- a/changedfile
  +++ /dev/null
  @@ -1,2 +0,0 @@
  -foobar
  -babar

  $ hg glog
  @  10:36454bda1fdb hello to a
  |   (foo) secret
  o  6:c3e29c061982 foobar to changedfile
  |   () draft
  o  3:fc57c20be380 added a
      () draft

Trying to amend --patch a public changeset
------------------------------------------

  $ hg phase -r . --public
  $ hg glog
  @  10:36454bda1fdb hello to a
  |   (foo) public
  o  6:c3e29c061982 foobar to changedfile
  |   () public
  o  3:fc57c20be380 added a
      () public

  $ HGEDITOR=cat hg amend --patch
  abort: cannot amend public changesets: 36454bda1fdb
  (see 'hg help phases' for details)
  [10]

  $ hg phase -r . --draft --force

Trying on a dirty working directory
-------------------------------------

  $ echo bar > bar
  $ hg add bar
  $ HGEDITOR=cat hg amend --patch
  abort: uncommitted changes
  [20]

  $ hg revert --all
  forgetting bar

Trying to pass filenames, only mentioned file names should be popped up in
editor and rest should stay in the commit as they were
--------------------------------------------------------------------------

Checking the we pop-up with the files which were mentioned

  $ HGEDITOR=cat hg amend --patch changedfile
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 36454bda1fdb8e2e4fe07bb084eef378e29cba74
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/changedfile b/changedfile
  deleted file mode 100755
  --- a/changedfile
  +++ /dev/null
  @@ -1,2 +0,0 @@
  -foobar
  -babar
  abort: nothing changed
  [255]

  $ HGEDITOR=cat hg amend --patch a
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 36454bda1fdb8e2e4fe07bb084eef378e29cba74
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Hello
  +bello
  abort: nothing changed
  [255]

  $ HGEDITOR=cat hg amend --patch changedfile a
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 36454bda1fdb8e2e4fe07bb084eef378e29cba74
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Hello
  +bello
  diff --git a/changedfile b/changedfile
  deleted file mode 100755
  --- a/changedfile
  +++ /dev/null
  @@ -1,2 +0,0 @@
  -foobar
  -babar
  abort: patch unchanged
  [255]

  $ HGEDITOR=cat hg amend --patch doesnotexists
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 36454bda1fdb8e2e4fe07bb084eef378e29cba74
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  abort: nothing changed
  [255]

Changing only one file
  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 36454bda1fdb8e2e4fe07bb084eef378e29cba74
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Hello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch a

file 'a' should be amended, rest of them should remain unchanged

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID ea175dcc4ee38c106db157975e006b4092444c65
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Hello
  +betto
  diff --git a/changedfile b/changedfile
  deleted file mode 100755
  --- a/changedfile
  +++ /dev/null
  @@ -1,2 +0,0 @@
  -foobar
  -babar

  $ hg status
  ? bar
  ? editor.sh

  $ hg diff

Testing again with file 'changedfile'

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID ea175dcc4ee38c106db157975e006b4092444c65
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/changedfile b/changedfile
  > --- a/changedfile
  > +++ b/changedfile
  > @@ -1,2 +1,1 @@
  >  foobar
  > -babar
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch changedfile

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 0e64d76c3519308c398a28192cb095d48b29aede
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Hello
  +betto
  diff --git a/changedfile b/changedfile
  --- a/changedfile
  +++ b/changedfile
  @@ -1,2 +1,1 @@
   foobar
  -babar

  $ hg diff
  $ hg status
  ? bar
  ? editor.sh

Dropping a file from commit by removing related hunks
------------------------------------------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 0e64d76c3519308c398a28192cb095d48b29aede
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Kello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 944e9f65fa55fdb2de98577c9d8ab30de0927d8e
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Kello
  +betto

The part which was dropped from the patch will not be there in working directory
too
  $ hg diff

  $ hg status
  ? bar
  ? editor.sh

Changing metadata of a patch by editing patch content
======================================================

Changing user
-------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User RandomUser
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 944e9f65fa55fdb2de98577c9d8ab30de0927d8e
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Kello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User RandomUser
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 5ded18a8c333a55da4b0e051162457cfe5d85558
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Kello
  +betto

Changing Date
-------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User RandomUser
  > # Date 123456 1200
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Node ID 944e9f65fa55fdb2de98577c9d8ab30de0927d8e
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Kello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User RandomUser
  # Date 123456 1200
  #      Fri Jan 02 09:57:36 1970 -0020
  # Node ID e2312ddcd8756665075a60bd05431ddca3c45050
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Kello
  +betto

Changing branch
---------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User RandomUser
  > # Date 123456 1200
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Branch stable
  > # Node ID 944e9f65fa55fdb2de98577c9d8ab30de0927d8e
  > # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Kello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User RandomUser
  # Date 123456 1200
  #      Fri Jan 02 09:57:36 1970 -0020
  # Branch stable
  # Node ID ddc61a4058687b2dd4a316f4b5fe7d52a35b702a
  # Parent  c3e29c061982c94418ce141d521434d6da76cd46
  hello to a
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,3 @@
   Gello
  +Kello
  +betto

Changing parent (this should be fun)
------------------------------------

  $ hg glog
  @  16:ddc61a405868 hello to a
  |   (foo) draft
  o  6:c3e29c061982 foobar to changedfile
  |   () public
  o  3:fc57c20be380 added a
      () public

  $ hg log -r .^^ -T '{node}'
  fc57c20be380f2878f4db139dad66d6cfb42ec62 (no-eol)

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User RandomUser
  > # Date 123456 1200
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Branch stable
  > # Node ID 944e9f65fa55fdb2de98577c9d8ab30de0927d8e
  > # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  > hello to a
  > diff --git a/a b/a
  > --- a/a
  > +++ b/a
  > @@ -1,1 +1,3 @@
  >  Gello
  > +Kello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User RandomUser
  # Date 123456 1200
  #      Fri Jan 02 09:57:36 1970 -0020
  # Branch stable
  # Node ID b763f7cb2302f2efa1275e2a9202655872c9567f
  # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  hello to a
  
  diff --git a/a b/a
  new file mode 100755
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,3 @@
  +Gello
  +Kello
  +betto

  $ hg glog
  @  17:b763f7cb2302 hello to a
  |   (foo) draft
  | o  6:c3e29c061982 foobar to changedfile
  |/    () public
  o  3:fc57c20be380 added a
      () public

Changing the commit desciption
-------------------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > # HG changeset patch
  > # User RandomUser
  > # Date 123456 1200
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Branch stable
  > # Node ID 944e9f65fa55fdb2de98577c9d8ab30de0927d8e
  > # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  > I am a message which is testing change of message
  > diff --git a/a b/a
  > new file mode 100755
  > --- /dev/null
  > +++ b/a
  > @@ -0,0 +1,3 @@
  > +Gello
  > +Kello
  > +betto
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch

  $ hg exp
  # HG changeset patch
  # User RandomUser
  # Date 123456 1200
  #      Fri Jan 02 09:57:36 1970 -0020
  # Branch stable
  # Node ID f14ecd7121e63915ac93edbad7f60f605e62dd52
  # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  I am a message which is testing change of message
  
  diff --git a/a b/a
  new file mode 100755
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,3 @@
  +Gello
  +Kello
  +betto

Changing the Node ID of the patch
---------------------------------

Nothing happens in that case we dont care about the node ID. Look the above 3-4
tests to realize I was testing that too.

Aborting by passing an empty patch file (issue5925)
---------------------------------------------------

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > cat > \$1 <<ENDOF
  > ENDOF
  > EOF

  $ HGEDITOR="sh ./editor.sh" hg amend --patch
  abort: empty patch file, amend aborted
  [255]

  $ hg exp
  # HG changeset patch
  # User RandomUser
  # Date 123456 1200
  #      Fri Jan 02 09:57:36 1970 -0020
  # Branch stable
  # Node ID f14ecd7121e63915ac93edbad7f60f605e62dd52
  # Parent  fc57c20be380f2878f4db139dad66d6cfb42ec62
  I am a message which is testing change of message
  
  diff --git a/a b/a
  new file mode 100755
  --- /dev/null
  +++ b/a
  @@ -0,0 +1,3 @@
  +Gello
  +Kello
  +betto

  $ hg parents
  changeset:   18:f14ecd7121e6
  branch:      stable
  bookmark:    foo
  tag:         tip
  parent:      3:fc57c20be380
  user:        RandomUser
  date:        Fri Jan 02 09:57:36 1970 -0020
  summary:     I am a message which is testing change of message
  
