=========================================================
Test the proper behavior of evolve during merge conflict.
=========================================================

Initial setup

  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive=false
  > merge=internal:merge
  > promptecho = True
  > [merge-tools]
  > touch.checkchanged=true
  > touch.gui=true
  > touch.args=babar
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

  $ safesed() {
  >   sed "$1" "$2" > `pwd`/sed.temp
  >   mv `pwd`/sed.temp "$2"
  > }

create a simple repo

  $ hg init repo
  $ cd repo
  $ cat << EOF > babar
  > un
  > deux
  > trois
  > quatre
  > cinq
  > EOF
  $ hg add babar
  $ hg commit -m "babar count up to five"
  $ cat << EOF >> babar
  > six
  > sept
  > huit
  > neuf
  > dix
  > EOF
  $ hg commit -m "babar count up to ten"
  $ cat << EOF >> babar
  > onze
  > douze
  > treize
  > quatorze
  > quinze
  > EOF
  $ hg commit -m "babar count up to fifteen"


proper behavior without conflict
----------------------------------

  $ hg gdown
  gdown have been deprecated in favor of previous
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [1] babar count up to ten
  $ safesed 's/huit/eight/' babar
  $ hg diff
  diff -r 9d5daf8bd956 babar
  --- a/babar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/babar	Thu Jan 01 00:00:00 1970 +0000
  @@ -5,6 +5,6 @@
   cinq
   six
   sept
  -huit
  +eight
   neuf
   dix
  $ hg amend
  1 new orphan changesets
  $ hg evolve --update
  move:[2] babar count up to fifteen
  atop:[3] babar count up to ten
  merging babar
  working directory is now at 71c18f70c34f

  $ hg log -r . -T '{extras % "{key}={value}\n"}'
  branch=default
  rebase_source=694f05b30ab7d4324e469d19af2ee80003a8fb50

  $ hg resolve -l
  $ hg log -G
  @  changeset:   4:71c18f70c34f
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     babar count up to fifteen
  |
  o  changeset:   3:5977072d13c5
  |  parent:      0:29ec1554cfaf
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     babar count up to ten
  |
  o  changeset:   0:29ec1554cfaf
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     babar count up to five
  


proper behavior with conflict using internal:merge
--------------------------------------------------

  $ hg gdown
  gdown have been deprecated in favor of previous
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [3] babar count up to ten
  $ safesed 's/dix/ten/' babar
  $ hg diff
  diff -r 5977072d13c5 babar
  --- a/babar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/babar	Thu Jan 01 00:00:00 1970 +0000
  @@ -7,4 +7,4 @@
   sept
   eight
   neuf
  -dix
  +ten
  $ hg amend
  1 new orphan changesets
  $ hg evolve --update
  move:[4] babar count up to fifteen
  atop:[5] babar count up to ten
  merging babar
  warning: conflicts while merging babar! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg resolve -l
  U babar
  $ hg log -G
  @  changeset:   5:e04690b09bc6
  |  tag:         tip
  |  parent:      0:29ec1554cfaf
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     babar count up to ten
  |
  | %  changeset:   4:71c18f70c34f
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan
  | |  summary:     babar count up to fifteen
  | |
  | x  changeset:   3:5977072d13c5
  |/   parent:      0:29ec1554cfaf
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    amended using amend as 5:e04690b09bc6
  |    summary:     babar count up to ten
  |
  o  changeset:   0:29ec1554cfaf
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     babar count up to five
  
(fix the conflict and continue)

  $ hg revert -r 71c18f70c34f --all
  reverting babar
  $ safesed 's/dix/ten/' babar
  $ hg resolve --all -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 4:71c18f70c34f "babar count up to fifteen"
  working directory is now at 368da14a3c59

  $ hg log -r . -T '{extras % "{key}={value}\n"}'
  branch=default
  rebase_source=71c18f70c34f7a15e293983a89ccd17ae3f444aa

  $ hg resolve -l
  $ hg log -G
  @  changeset:   6:368da14a3c59
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     babar count up to fifteen
  |
  o  changeset:   5:e04690b09bc6
  |  parent:      0:29ec1554cfaf
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     babar count up to ten
  |
  o  changeset:   0:29ec1554cfaf
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     babar count up to five
  
proper behavior with conflict using an external merge tool
----------------------------------------------------------

  $ safesed 's/merge=.*/merge=touch/' $HGRCPATH
  $ safesed 's/touch.gui=.*/touch.gui=false/' $HGRCPATH
  $ hg gdown
  gdown have been deprecated in favor of previous
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [5] babar count up to ten
  $ safesed 's/ten/zehn/' babar
  $ hg diff
  diff -r e04690b09bc6 babar
  --- a/babar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/babar	Thu Jan 01 00:00:00 1970 +0000
  @@ -7,4 +7,4 @@
   sept
   eight
   neuf
  -ten
  +zehn
  $ hg amend
  1 new orphan changesets
  $ safesed 's/interactive=.*/interactive=true/' $HGRCPATH
  $ hg evolve --tool touch <<EOF
  > n
  > EOF
  move:[6] babar count up to fifteen
  atop:[7] babar count up to ten
  merging babar
   output file babar appears unchanged
  was merge successful (yn)? n
  merging babar failed!
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg resolve -l
  U babar
  $ hg log -G
  @  changeset:   7:b20d08eea373
  |  tag:         tip
  |  parent:      0:29ec1554cfaf
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     babar count up to ten
  |
  | %  changeset:   6:368da14a3c59
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan
  | |  summary:     babar count up to fifteen
  | |
  | x  changeset:   5:e04690b09bc6
  |/   parent:      0:29ec1554cfaf
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    amended using amend as 7:b20d08eea373
  |    summary:     babar count up to ten
  |
  o  changeset:   0:29ec1554cfaf
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     babar count up to five
  
  $ cat babar
  un
  deux
  trois
  quatre
  cinq
  six
  sept
  eight
  neuf
  zehn
