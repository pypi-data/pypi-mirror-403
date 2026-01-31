==========================
Testing `hg fixup` command
==========================

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > rebase =
  > evolve =
  > [diff]
  > git = 1
  > EOF

#if hg69
  $ hg help fixup
  hg fixup [OPTION]... [-r] REV
  
  aliases: fix-up
  
  add working directory changes to an arbitrary revision
  
  A new changeset will be created, superseding the one specified. The new
  changeset will combine working directory changes with the changes in the
  target revision.
  
  This operation requires the working directory changes to be relocated onto the
  target revision, which might result in merge conflicts.
  
  If fixup is interrupted to manually resolve a conflict, it can be continued
  with --continue/-c, or aborted with --abort.
  
  Note that this command is fairly new and its behavior is still experimental.
  For example, the working copy will be left on a temporary, obsolete commit
  containing the fixed-up changes after the operation. This might change in the
  future.
  
  Returns 0 on success, 1 if nothing changed.
  
  options:
  
   -r --rev REV  revision to amend
   -c --continue continue an interrupted fixup
      --abort    abort an interrupted fixup
  
  (some details hidden, use --verbose to show complete help)
#endif

Simple cases
------------

  $ hg init simple
  $ cd simple
  $ mkcommit foo
  $ mkcommit bar
  $ mkcommit baz

amending the middle of the stack
--------------------------------

  $ hg bookmark bm
  $ echo 'hookah bar' > bar
  $ hg fixup -r 'desc(bar)'
  (leaving bookmark bm)
  1 new orphan changesets

  $ hg diff -c tip
  diff --git a/bar b/bar
  new file mode 100644
  --- /dev/null
  +++ b/bar
  @@ -0,0 +1,1 @@
  +hookah bar

  $ hg glog
  o  5:2eec5320cfc7 bar
  |   (bm) draft
  | @  3:fd2f632e47ab temporary fixup commit
  | |   () draft
  | *  2:a425495a8e64 baz
  | |   () draft orphan
  | x  1:c0c7cf58edc5 bar
  |/    () draft
  o  0:e63c23eaa88a foo
      () draft

  $ hg glog --hidden
  o  5:2eec5320cfc7 bar
  |   (bm) draft
  | x  4:4869c1db2884 temporary fixup commit
  | |   () draft
  | | @  3:fd2f632e47ab temporary fixup commit
  | | |   () draft
  | | *  2:a425495a8e64 baz
  | |/    () draft orphan
  | x  1:c0c7cf58edc5 bar
  |/    () draft
  o  0:e63c23eaa88a foo
      () draft

using --dry-run should only print actions (issue6669)

  $ hg evolve --dry-run
  update:[5] bar

  $ hg evolve --dry-run --any
  update:[5] bar
  move:[2] baz
  atop:[5] bar
  hg rebase -r a425495a8e64 -d 2eec5320cfc7

  $ hg evolve
  update:[5] bar
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 2eec5320cfc7

  $ hg evolve
  move:[2] baz
  atop:[5] bar

  $ hg glog
  o  6:eb1755d9f810 baz
  |   () draft
  @  5:2eec5320cfc7 bar
  |   (bm) draft
  o  0:e63c23eaa88a foo
      () draft

amending working directory parent in secret phase
-------------------------------------------------

  $ hg up -r 'desc(baz)'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg phase --secret --force -r .
  $ echo buzz >> baz
  $ hg fix-up -r .

  $ hg evolve
  update:[9] baz
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 12b5e442244f
  $ hg glog
  @  9:12b5e442244f baz
  |   () secret
  o  5:2eec5320cfc7 bar
  |   (bm) draft
  o  0:e63c23eaa88a foo
      () draft

testing --abort/--continue
--------------------------

  $ hg up -r 'desc(foo)'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo 'update foo' > foo
  $ hg ci -m 'update foo'
  created new head
  $ hg up -r 'desc(baz)'
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg glog
  o  10:c90c517f86b3 update foo
  |   () draft
  | @  9:12b5e442244f baz
  | |   () secret
  | o  5:2eec5320cfc7 bar
  |/    (bm) draft
  o  0:e63c23eaa88a foo
      () draft

testing --abort flag

  $ echo 'update foo again' >> foo

  $ hg fixup -r 'desc("update foo")'
  merging foo
  warning: conflicts while merging foo! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -1,1 +1,6 @@
  +<<<<<<< destination: c90c517f86b3 - test: update foo
   update foo
  +=======
  +foo
  +update foo again
  +>>>>>>> evolving:    1c9958e73c2d - test: temporary fixup commit

  $ hg fixup --abort
  fixup aborted
  working directory is now at 12b5e442244f

  $ hg diff
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -1,1 +1,2 @@
   foo
  +update foo again

testing abort command

  $ hg fixup -r 'desc("update foo")'
  merging foo
  warning: conflicts while merging foo! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg abort
  fixup aborted
  working directory is now at 12b5e442244f

testing --continue flag

  $ hg fixup -r 'desc("update foo")'
  merging foo
  warning: conflicts while merging foo! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg status --verbose
  M foo
  ? foo.orig
  # The repository is in an unfinished *fixup* state.
  
  # Unresolved merge conflicts:
  # 
  #     foo
  # 
  # To mark files as resolved:  hg resolve --mark FILE
  
  # To continue:    hg fixup --continue
  # To abort:       hg fixup --abort
  
  $ echo 'finalize foo' > foo

  $ hg resolve -m
  (no more unresolved files)
  continue: hg fixup --continue

  $ hg fixup --continue
  evolving 11:1c9958e73c2d "temporary fixup commit"

  $ hg diff -c tip
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -1,1 +1,1 @@
  -foo
  +finalize foo

  $ hg glog
  o  13:fed7e534b3bb update foo
  |   () draft
  | @  11:1c9958e73c2d temporary fixup commit
  | |   () secret
  | o  9:12b5e442244f baz
  | |   () secret
  | o  5:2eec5320cfc7 bar
  |/    (bm) draft
  o  0:e63c23eaa88a foo
      () draft

  $ hg evolve
  update:[13] update foo
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  working directory is now at fed7e534b3bb

testing continue command

  $ hg up -r 'desc("baz")'
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'not foo' > foo

  $ hg fixup -r 'desc("update foo")'
  merging foo
  warning: conflicts while merging foo! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ echo 'bonjour fixed' > foo
  $ hg resolve --mark foo
  (no more unresolved files)
  continue: hg fixup --continue

  $ hg continue
  evolving 14:6b0b1270d7dd "temporary fixup commit"

  $ hg glog
  o  16:0dd54868f420 update foo
  |   () draft
  | @  14:6b0b1270d7dd temporary fixup commit
  | |   () secret
  | o  9:12b5e442244f baz
  | |   () secret
  | o  5:2eec5320cfc7 bar
  |/    (bm) draft
  o  0:e63c23eaa88a foo
      () draft

  $ hg evolve
  update:[16] update foo
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  working directory is now at 0dd54868f420

amending a descendant of wdp

  $ hg up 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo foobar > foobar
  $ hg add foobar
  $ hg fixup -r 'desc(baz)'
  $ hg glog
  o  19:b50fd0850076 baz
  |   () secret
  | @  17:4a9c4d14d447 temporary fixup commit
  | |   () draft
  | | o  16:0dd54868f420 update foo
  | |/    () draft
  o |  5:2eec5320cfc7 bar
  |/    (bm) draft
  o  0:e63c23eaa88a foo
      () draft

  $ hg evolve
  update:[19] baz
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at b50fd0850076

  $ hg glog
  @  19:b50fd0850076 baz
  |   () secret
  | o  16:0dd54868f420 update foo
  | |   () draft
  o |  5:2eec5320cfc7 bar
  |/    (bm) draft
  o  0:e63c23eaa88a foo
      () draft
  $ hg diff -c .
  diff --git a/baz b/baz
  new file mode 100644
  --- /dev/null
  +++ b/baz
  @@ -0,0 +1,2 @@
  +baz
  +buzz
  diff --git a/foobar b/foobar
  new file mode 100644
  --- /dev/null
  +++ b/foobar
  @@ -0,0 +1,1 @@
  +foobar

no fixup in progress

  $ hg fixup --continue
  abort: no interrupted fixup to continue
  [20]

  $ hg fixup --abort
  abort: no interrupted fixup to abort
  [20]

testing error cases

  $ hg fixup tip --abort
  abort: cannot specify a revision with --abort
  [10]

  $ hg fixup -r tip --continue
  abort: cannot specify a revision with --continue
  [10]

  $ hg fixup
  abort: please specify a revision to fixup
  [10]

  $ hg fixup tip
  nothing changed
  [1]

  $ hg fixup -r tip
  nothing changed
  [1]

  $ hg fixup 1 2 3
  hg fixup: invalid arguments
  hg fixup [OPTION]... [-r] REV
  
  add working directory changes to an arbitrary revision
  
  options:
  
   -r --rev REV  revision to amend
   -c --continue continue an interrupted fixup
      --abort    abort an interrupted fixup
  
  (use 'hg fixup -h' to show more help)
  [10]

  $ hg fixup :10 -r 5
  abort: please specify just one revision
  [10]

  $ cd ..

Multiple branches
-----------------

  $ hg init branches
  $ cd branches

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > topic =
  > [alias]
  > glog = log -GT '{rev}:{node|short} {desc}\n ({branch}) [{topic}]\n'
  > EOF

  $ mkcommit ROOT
  $ hg topic topic-A -q
  $ mkcommit A -q
  $ hg topic topic-B -q
  $ mkcommit B -q
  $ hg up 'desc(ROOT)' -q
  $ hg branch other-branch -q
  $ hg topic topic-C -q
  $ mkcommit C -q
  $ hg topic topic-D -q
  $ mkcommit D -q
  $ hg up 'desc(A)' -q

  $ hg glog
  o  4:deb0223c611b D
  |   (other-branch) [topic-D]
  o  3:381934d792ab C
  |   (other-branch) [topic-C]
  | o  2:d2dfccd24f25 B
  | |   (default) [topic-B]
  | @  1:0a2783c5c927 A
  |/    (default) [topic-A]
  o  0:ea207398892e ROOT
      (default) []

  $ echo Z > Z
  $ hg add Z
  $ hg fix-up -r 'desc(C)'
  switching to topic topic-C
  1 new orphan changesets

  $ hg evolve
  update:[7] C
  switching to topic topic-C
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 57d19d0ff7ee
  $ hg evolve --any
  move:[4] D
  atop:[7] C
  switching to topic topic-C

C and D keep their original branch and topics

  $ hg glog
  o  8:203e06b553f5 D
  |   (other-branch) [topic-D]
  @  7:57d19d0ff7ee C
  |   (other-branch) [topic-C]
  | o  2:d2dfccd24f25 B
  | |   (default) [topic-B]
  | o  1:0a2783c5c927 A
  |/    (default) [topic-A]
  o  0:ea207398892e ROOT
      (default) []

  $ cd ..
