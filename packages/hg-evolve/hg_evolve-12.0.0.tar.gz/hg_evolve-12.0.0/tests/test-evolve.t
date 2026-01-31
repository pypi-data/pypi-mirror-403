  $ cat >> $HGRCPATH <<EOF
  > [phases]
  > publish = False
  > [alias]
  > qlog = log --template='{rev} - {node|short} {desc} ({phase})\n'
  > [diff]
  > git = 1
  > unified = 0
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

  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1"
  > }

  $ mkstack() {
  >    # Creates a stack of commit based on $1 with messages from $2, $3 ..
  >    hg update $1 -C
  >    shift
  >    mkcommits $*
  > }

  $ glog() {
  >   hg log -G --template '{rev}:{node|short}@{branch}({phase}) {desc|firstline}\n' "$@"
  > }

  $ shaof() {
  >   hg log -T {node} -r "first(desc($1))"
  > }

  $ mkcommits() {
  >   for i in $@; do mkcommit $i ; done
  > }

Test the evolution test topic is installed

  $ hg help evolution
  Safely Rewriting History
  """"""""""""""""""""""""
  
      Obsolescence markers make it possible to mark changesets that have been
      deleted or superseded in a new version of the changeset.
  
      Unlike the previous way of handling such changes, by stripping the old
      changesets from the repository, obsolescence markers can be propagated
      between repositories. This allows for a safe and simple way of exchanging
      mutable history and altering it after the fact. Changeset phases are
      respected, such that only draft and secret changesets can be altered (see
      'hg help phases' for details).
  
      Obsolescence is tracked using "obsolete markers", a piece of metadata
      tracking which changesets have been made obsolete, potential successors
      for a given changeset, the moment the changeset was marked as obsolete,
      and the user who performed the rewriting operation. The markers are stored
      separately from standard changeset data can be exchanged without any of
      the precursor changesets, preventing unnecessary exchange of obsolescence
      data.
  
      The complete set of obsolescence markers describes a history of changeset
      modifications that is orthogonal to the repository history of file
      modifications. This changeset history allows for detection and automatic
      resolution of edge cases arising from multiple users rewriting the same
      part of history concurrently.
  
      Current feature status
      ======================
  
      This feature is still in development.  If you see this help, you have
      enabled an extension that turned this feature on.
  
      Obsolescence markers will be exchanged between repositories that
      explicitly assert support for the obsolescence feature (this can currently
      only be done via an extension).
  
      Instability
      ===========
  
      Rewriting changesets might introduce instability.
  
      There are two main kinds of instability: orphaning and diverging.
  
      Orphans are changesets left behind when their ancestors are rewritten.
      Divergence has two variants:
  
      * Content-divergence occurs when independent rewrites of the same
        changesets lead to different results.
      * Phase-divergence occurs when the old (obsolete) version of a changeset
        becomes public.
  
      It is possible to prevent local creation of orphans by using the following
      config:
  
        [experimental]
        evolution=createmarkers,allnewcommands,exchange
  
      You can also enable that option explicitly:
  
        [experimental]
        evolution=createmarkers,allnewcommands,allowunstable,exchange
  
      or simply:
  
        [experimental]
        evolution=all
  
      To prevent users from creating content divergence, a check is performed by
      default on the revisions being rewritten, and the operation is aborted if
      it creates divergence. If users want to allow creating content divergent
      changesets, this check can be turned off by setting the following config:
  
        [experimental]
        evolution.allowdivergence=True

various init

  $ hg init local
  $ cd local
  $ mkcommit a
  $ mkcommit b
  $ cat >> .hg/hgrc << EOF
  > [phases]
  > publish = True
  > EOF
  $ hg pull -q . # make 1 public
  $ rm .hg/hgrc
  $ mkcommit c
  $ mkcommit d
  $ hg up 1
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ mkcommit e -q
  created new head
  $ mkcommit f
  $ hg qlog
  5 - e44648563c73 add f (draft)
  4 - fbb94e3a0ecf add e (draft)
  3 - 47d2a3944de8 add d (draft)
  2 - 4538525df7e2 add c (draft)
  1 - 7c3bad9141dc add b (public)
  0 - 1f0dee641bb7 add a (public)

test kill and immutable changeset

  $ hg log -r 1 --template '{rev} {phase} {obsolete}\n'
  1 public 
  $ hg prune 1
  abort: cannot prune public changesets: 7c3bad9141dc
  (see 'hg help phases' for details)
  [10]
  $ hg log -r 1 --template '{rev} {phase} {obsolete}\n'
  1 public 

test simple kill

  $ hg id -n
  5
  $ hg prune .
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at fbb94e3a0ecf
  1 changesets pruned
  $ hg qlog
  4 - fbb94e3a0ecf add e (draft)
  3 - 47d2a3944de8 add d (draft)
  2 - 4538525df7e2 add c (draft)
  1 - 7c3bad9141dc add b (public)
  0 - 1f0dee641bb7 add a (public)

test multiple kill

  $ hg prune 4 -r 3
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 7c3bad9141dc
  2 changesets pruned
  $ hg qlog
  2 - 4538525df7e2 add c (draft)
  1 - 7c3bad9141dc add b (public)
  0 - 1f0dee641bb7 add a (public)

test kill with dirty changes

  $ hg up 2
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 4 > g
  $ hg add g
  $ hg prune .
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 7c3bad9141dc
  1 changesets pruned
  $ hg st
  A g

Smoketest debugobsrelsethashtree:

  $ hg debugobsrelsethashtree
  1f0dee641bb7258c56bd60e93edfa2405381c41e 0000000000000000000000000000000000000000
  7c3bad9141dcb46ff89abf5f61856facd56e476c * (glob)
  4538525df7e2b9f09423636c61ef63a4cb872a2d * (glob)
  47d2a3944de8b013de3be9578e8e344ea2e6c097 * (glob)
  fbb94e3a0ecf6d20c2cc31152ef162ce45af982f * (glob)
  e44648563c73f75950076031c6fdf06629de95f1 * (glob)

Smoketest stablerange.obshash:

  $ hg debugobshashrange --subranges --rev 'head()'
           rev         node        index         size        depth      obshash
             1 7c3bad9141dc            0            2            2 * (glob)
             0 1f0dee641bb7            0            1            1 000000000000
             1 7c3bad9141dc            1            1            2 * (glob)

  $ cd ..

##########################
importing Parren test
##########################

  $ cat << EOF >> $HGRCPATH
  > [ui]
  > logtemplate = "{rev}\t{bookmarks}: {desc|firstline} - {author|user}\n"
  > EOF

Creating And Updating Changeset
===============================

Setup the Base Repo
-------------------

We start with a plain base repo::

  $ hg init main; cd main
  $ cat >main-file-1 <<-EOF
  > One
  > 
  > Two
  > 
  > Three
  > EOF
  $ echo Two >main-file-2
  $ hg add
  adding main-file-1
  adding main-file-2
  $ hg commit --message base
  $ cd ..

and clone this into a new repo where we do our work::

  $ hg clone main work
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd work


Create First Patch
------------------

To begin with, we just do the changes that will be the initial version of the changeset::

  $ echo One >file-from-A
  $ sed -i'' -e s/One/Eins/ main-file-1
  $ hg add file-from-A

So this is what we would like our changeset to be::

  $ hg diff
  diff --git a/file-from-A b/file-from-A
  new file mode 100644
  --- /dev/null
  +++ b/file-from-A
  @@ -0,0 +1,1 @@
  +One
  diff --git a/main-file-1 b/main-file-1
  --- a/main-file-1
  +++ b/main-file-1
  @@ -1,1 +1,1 @@
  -One
  +Eins

To commit it we just - commit it::

  $ hg commit --message "a nifty feature"

and place a bookmark so we can easily refer to it again (which we could have done before the commit)::

  $ hg book feature-A


Create Second Patch
-------------------

Let's do this again for the second changeset::

  $ echo Two >file-from-B
  $ sed -i'' -e s/Two/Zwie/ main-file-1
  $ hg add file-from-B

Before committing, however, we need to switch to a new bookmark for the second
changeset. Otherwise we would inadvertently move the bookmark for our first changeset.
It is therefore advisable to always set the bookmark before committing::

  $ hg book feature-B
  $ hg commit --message "another feature (child of $(hg log -r . -T '{node|short}'))"

So here we are::

  $ hg book
     feature-A                 1:568a468b60fc
   * feature-B                 2:73296a82292a


Fix The Second Patch
--------------------

There's a typo in feature-B. We spelled *Zwie* instead of *Zwei*::

  $ hg diff --change tip | grep -F Zwie
  +Zwie

Fixing this is very easy. Just change::

  $ sed -i'' -e s/Zwie/Zwei/ main-file-1

and **amend**::

  $ hg amend

This results in a new single changeset for our amended changeset, and the old
changeset plus the updating changeset are hidden from view by default::

  $ hg log
  3	feature-B: another feature (child of 568a468b60fc) - test
  1	feature-A: a nifty feature - test
  0	: base - test

  $ hg up feature-A -q
  $ hg bookmark -i feature-A
  $ sed -i'' -e s/Eins/Un/ main-file-1

(amend of public changeset denied)

  $ hg phase --public 0 -v
  phase changed for 1 changesets


(amend of on ancestors)

  $ hg amend
  1 new orphan changesets
  $ hg log
  4	feature-A: a nifty feature - test
  3	feature-B: another feature (child of 568a468b60fc) - test
  1	: a nifty feature - test
  0	: base - test
  $ hg up -q 0
  $ glog --hidden
  o  4:ba0ec09b1bab@default(draft) a nifty feature
  |
  | *  3:6992c59c6b06@default(draft) another feature (child of 568a468b60fc)
  | |
  | | x  2:73296a82292a@default(draft) another feature (child of 568a468b60fc)
  | |/
  | x  1:568a468b60fc@default(draft) a nifty feature
  |/
  @  0:e55e0562ee93@default(public) base
  
  $ hg debugobsolete
  73296a82292a76fb8a7061969d2489ec0d84cd5e 6992c59c6b06a1b4a92e24ff884829ae026d018b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  568a468b60fc99a42d5d4ddbe181caff1eef308d ba0ec09b1babf3489b567853807f452edd46704f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  $ hg evolve
  move:[3] another feature (child of 568a468b60fc)
  atop:[4] a nifty feature
  merging main-file-1
  $ hg log
  5	feature-B: another feature (child of ba0ec09b1bab) - test
  4	feature-A: a nifty feature - test
  0	: base - test

Test commit -o options

  $ hg up -r "desc('a nifty feature')"
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg revert -r "desc('another feature')" --all
  reverting main-file-1
  adding file-from-B
  $ sed -i'' -e s/Zwei/deux/ main-file-1
  $ hg commit -m 'another feature that rox' -o 5
  created new head
  $ hg log
  6	feature-B: another feature that rox - test
  4	feature-A: a nifty feature - test
  0	: base - test

phase change turning obsolete changeset public issues a phase divergence warning

  $ hg phase --hidden --public 5c9c8d9c2e4e
  1 new phase-divergent changesets

all solving phase-divergent

  $ glog
  @  6:47d52a103155@default(draft) another feature that rox
  |
  | o  5:5c9c8d9c2e4e@default(public) another feature (child of ba0ec09b1bab)
  |/
  o  4:ba0ec09b1bab@default(public) a nifty feature
  |
  o  0:e55e0562ee93@default(public) base
  
  $ hg evolve --any --traceback --phase-divergent
  recreate:[6] another feature that rox
  atop:[5] another feature (child of ba0ec09b1bab)
  committed as acecd63a9288
  working directory is now at acecd63a9288
  $ glog
  @  7:acecd63a9288@default(draft) phase-divergent update to 5c9c8d9c2e4e:
  |
  o  5:5c9c8d9c2e4e@default(public) another feature (child of ba0ec09b1bab)
  |
  o  4:ba0ec09b1bab@default(public) a nifty feature
  |
  o  0:e55e0562ee93@default(public) base
  
  $ hg diff --hidden -r acecd63a9288 -r 47d52a103155
  $ hg diff -r acecd63a9288^ -r acecd63a9288
  diff --git a/main-file-1 b/main-file-1
  --- a/main-file-1
  +++ b/main-file-1
  @@ -3,1 +3,1 @@
  -Zwei
  +deux
  $ hg log -r 'phasedivergent()' # no more phase-divergent

test evolve --all
  $ sed -i'' -e s/deux/to/ main-file-1
  $ hg commit -m 'dansk 2!'
  $ sed -i'' -e s/Three/tre/ main-file-1
  $ hg commit -m 'dansk 3!'
  $ hg update acecd63a9288
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ sed -i'' -e s/Un/Én/ main-file-1
  $ hg commit --amend -m 'dansk!'
  2 new orphan changesets

(ninja test for the {trouble} template:

  $ hg log -G --template '{rev} {instabilities}\n'
  @  10
  |
  | *  9 orphan
  | |
  | *  8 orphan
  | |
  | x  7
  |/
  o  5
  |
  o  4
  |
  o  0
  


(/ninja)

command-templates.oneline-summary is respected when evolving orphan

  $ hg evolve -n --config 'command-templates.oneline-summary = custom {rev} {desc}'
  move:custom 8 dansk 2!
  atop:custom 10 dansk!
  hg rebase -r bdb9adf2959a -d 74d61108f94b
  skipping 3db99d6b500c, consider including orphan ancestors

command-templates.oneline-summary is respected when evolving/updating working copy

  $ hg co -q 7
  working directory parent is obsolete! (acecd63a9288)
  $ hg evolve --no-all --config 'command-templates.oneline-summary = custom {rev} {desc}'
  update:custom 10 dansk!
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 74d61108f94b

  $ hg evolve --all --traceback
  move:[8] dansk 2!
  atop:[10] dansk!
  merging main-file-1
  move:[9] dansk 3!
  merging main-file-1
  $ hg log -G
  o  12	: dansk 3! - test
  |
  o  11	: dansk 2! - test
  |
  @  10	feature-B: dansk! - test
  |
  o  5	: another feature (child of ba0ec09b1bab) - test
  |
  o  4	feature-A: a nifty feature - test
  |
  o  0	: base - test
  

  $ cd ..

enable general delta

  $ cat << EOF >> $HGRCPATH
  > [format]
  > generaldelta=1
  > EOF



  $ hg init alpha
  $ cd alpha
  $ echo 'base' > firstfile
  $ hg add firstfile
  $ hg ci -m 'base'

  $ cd ..
  $ hg clone -Ur 0 alpha beta
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 702e4d0a6d86 (1 drafts)
  $ cd alpha

  $ cat << EOF > A
  > We
  > need
  > some
  > kind
  > of 
  > file
  > big
  > enough
  > to
  > prevent
  > snapshot
  > .
  > yes
  > new
  > lines
  > are
  > useless
  > .
  > EOF
  $ hg add A
  $ hg commit -m 'adding A'
  $ hg mv A B
  $ echo '.' >> B
  $ hg amend -m 'add B'
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  checking dirstate (?)
  checked 3 changesets with 3 changes to 3 files
  $ hg --config extensions.mq= strip 'extinct()'
  abort: empty revision set
  [255]
(do some garbare collection)
  $ hg --config extensions.mq= strip --hidden 'extinct()'  --config devel.strip-obsmarkers=no
  saved backup bundle to $TESTTMP/alpha/.hg/strip-backup/e87767087a57-a365b072-backup.hg (glob)
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  checking dirstate (?)
  checked 2 changesets with 2 changes to 2 files
  $ cd ..

Clone just this branch

  $ cd beta
  $ hg pull -r tip ../alpha
  pulling from ../alpha
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  1 new obsolescence markers
  new changesets c6dda801837c (1 drafts)
  (run 'hg update' to get a working copy)
  $ hg up
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd ..

Normal testing

  $ hg init test-graft
  $ cd test-graft
  $ mkcommit 0
  $ mkcommit 1
  $ mkcommit 2
  $ mkcommit 3
  $ hg up -qC 0
  $ mkcommit 4
  created new head
  $ glog --hidden
  @  4:ce341209337f@default(draft) add 4
  |
  | o  3:0e84df4912da@default(draft) add 3
  | |
  | o  2:db038628b9e5@default(draft) add 2
  | |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(draft) add 0
  
  $ hg pick -r3
  picking 3:0e84df4912da "add 3"
  $ hg graft -r1
  grafting 1:73d38bb17fd7 "add 1"
  $ hg prune -r2 --successor .
  1 changesets pruned
  $ glog --hidden
  @  6:417185465d2c@default(draft) add 1
  |
  o  5:fa455b5098e0@default(draft) add 3
  |
  o  4:ce341209337f@default(draft) add 4
  |
  | x  3:0e84df4912da@default(draft) add 3
  | |
  | x  2:db038628b9e5@default(draft) add 2
  | |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(draft) add 0
  
  $ hg debugobsolete
  0e84df4912da4c7cad22a3b4fcfd58ddfb7c8ae9 fa455b5098e0ce8c1871edf6369f32be7d8b4d1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'pick', 'user': 'test'}
  db038628b9e56f51a454c0da0c508df247b41748 417185465d2c68e575cff4cd6ed8a4047505ef24 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'prune', 'user': 'test'}

Test grab --continue

  $ hg up -qC 0
  $ echo 2 > 1
  $ hg ci -Am conflict 1
  created new head
  $ hg up -qC 6
  $ hg pick -r 7
  picking 7:a5bfd90a2f29 "conflict"
  merging 1
  warning: conflicts while merging 1! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts (see hg help resolve)
  [240]
  $ hg log -r7 --template '{rev}:{node|short} {obsolete}\n'
  7:a5bfd90a2f29 
  $ echo 3 > 1
  $ hg resolve -m 1
  (no more unresolved files)
  continue: hg pick --continue
  $ hg pick --continue
  $ glog --hidden
  @  8:fb2c0f0a0c54@default(draft) conflict
  |
  | x  7:a5bfd90a2f29@default(draft) conflict
  | |
  o |  6:417185465d2c@default(draft) add 1
  | |
  o |  5:fa455b5098e0@default(draft) add 3
  | |
  o |  4:ce341209337f@default(draft) add 4
  |/
  | x  3:0e84df4912da@default(draft) add 3
  | |
  | x  2:db038628b9e5@default(draft) add 2
  | |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(draft) add 0
  
  $ hg debugobsolete
  0e84df4912da4c7cad22a3b4fcfd58ddfb7c8ae9 fa455b5098e0ce8c1871edf6369f32be7d8b4d1c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'pick', 'user': 'test'}
  db038628b9e56f51a454c0da0c508df247b41748 417185465d2c68e575cff4cd6ed8a4047505ef24 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'prune', 'user': 'test'}
  a5bfd90a2f29c7ccb8f917ff4e5013a9053d0a04 fb2c0f0a0c54be4367988521bad2cbd33a540969 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '12', 'operation': 'pick', 'user': 'test'}

Test touch

  $ glog
  @  8:fb2c0f0a0c54@default(draft) conflict
  |
  o  6:417185465d2c@default(draft) add 1
  |
  o  5:fa455b5098e0@default(draft) add 3
  |
  o  4:ce341209337f@default(draft) add 4
  |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(draft) add 0
  
  $ hg touch
  $ glog
  @  9:*@default(draft) conflict (glob)
  |
  o  6:417185465d2c@default(draft) add 1
  |
  o  5:fa455b5098e0@default(draft) add 3
  |
  o  4:ce341209337f@default(draft) add 4
  |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(draft) add 0
  
  $ hg touch .
  $ glog
  @  10:*@default(draft) conflict (glob)
  |
  o  6:417185465d2c@default(draft) add 1
  |
  o  5:fa455b5098e0@default(draft) add 3
  |
  o  4:ce341209337f@default(draft) add 4
  |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(draft) add 0
  

Test fold
(most of the testing have been moved to test-fold

  $ rm *.orig
  $ hg phase --public 0
  $ hg fold --from -r 5
  3 changesets folded
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log -r 11 --template '{desc}\n'
  add 3
  
  
  add 1
  
  
  conflict
  $ hg debugrebuildstate
  $ hg st

Test fold with wc parent is not the head of the folded revision

  $ hg up 4
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg fold --rev 4::11 --user victor --exact
  2 changesets folded
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ glog
  @  12:d26d339c513f@default(draft) add 4
  |
  | o  1:73d38bb17fd7@default(draft) add 1
  |/
  o  0:8685c6d34325@default(public) add 0
  
  $ hg log --template '{rev}: {author}\n'
  12: victor
  1: test
  0: test
  $ hg log -r 12 --template '{desc}\n'
  add 4
  
  
  add 3
  
  
  add 1
  
  
  conflict
  $ hg debugrebuildstate
  $ hg st

Test olog

  $ hg olog --no-origin | head -n 10 # hg touch makes the output unstable (fix it with devel option for more stable touch)
  @    d26d339c513f (12) add 4
  |\
  x |  ce341209337f (4) add 4
   /     folded(description, user, content) as d26d339c513f using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x    cf0c3904643c (11) add 3
  |\     folded(description, user, parent, content) as d26d339c513f using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | \
  | |\

Test obsstore stat

  $ hg debugobsstorestat
  markers total:                     10
      for known precursors:          10 (10/13 obsolete changesets)
      with parents data:              0
  markers with no successors:         0
                1 successors:        10
                2 successors:         0
      more than 2 successors:         0
      available  keys:
                  ef1:               10
              fold-id:                5
             fold-idx:                5
            fold-size:                5
            operation:               10
                 user:               10
  marker size:
      format v1:
          smallest length:           90
          longer length:            131
          median length:            130
          mean length:              110
      format v0:
          smallest length:          * (glob)
          longer length:            * (glob)
          median length:            * (glob)
          mean length:              * (glob)
  disconnected clusters:              1
          any known node:             1
          smallest length:           10
          longer length:             10
          median length:             10
          mean length:               10
      using parents data:             1
          any known node:             1
          smallest length:           10
          longer length:             10
          median length:             10
          mean length:               10


Test evolving renames

  $ hg up null
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ echo a > a
  $ hg ci -Am a
  adding a
  created new head
  $ echo b > b
  $ hg ci -Am b
  adding b
  $ hg mv a c
  $ hg ci -m c
  $ hg prune .^
  1 changesets pruned
  1 new orphan changesets
  $ hg stab --any
  move:[15] c
  atop:[13] a
  working directory is now at 3742bde73477
  $ hg st -C --change=tip
  A c
    a
  R a

Test fold with commit messages

  $ cd ../work
  $ hg up
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg fold --from .^ --message "Folding with custom commit message"
  2 changesets folded
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ glog
  @  13:90308a3a84bd@default(draft) Folding with custom commit message
  |
  o  10:74d61108f94b@default(draft) dansk!
  |
  o  5:5c9c8d9c2e4e@default(public) another feature (child of ba0ec09b1bab)
  |
  o  4:ba0ec09b1bab@default(public) a nifty feature
  |
  o  0:e55e0562ee93@default(public) base
  
  $ cat > commit-message <<EOF
  > A longer
  >                   commit message
  > EOF

  $ hg fold --from .^ --logfile commit-message
  2 changesets folded
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg qlog
  14 - c07a8bc54a51 A longer
                    commit message (draft)
  5 - 5c9c8d9c2e4e another feature (child of ba0ec09b1bab) (public)
  4 - ba0ec09b1bab a nifty feature (public)
  0 - e55e0562ee93 base (public)

  $ cd ..

Test branch preservation:
===========================

  $ hg init evolving-branch
  $ cd evolving-branch
  $ touch a
  $ hg add a
  $ hg ci -m 'a0'
  $ echo 1 > a
  $ hg ci -m 'a1'
  $ echo 2 > a
  $ hg ci -m 'a2'
  $ echo 3 > a
  $ hg ci -m 'a3'

  $ hg log -G --template '{rev} [{branch}] {desc|firstline}\n'
  @  3 [default] a3
  |
  o  2 [default] a2
  |
  o  1 [default] a1
  |
  o  0 [default] a0
  

branch change propagated

  $ hg up 'desc(a2)'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg branch mybranch
  marked working directory as branch mybranch
  (branches are permanent and global, did you want a bookmark?)
  $ hg amend
  1 new orphan changesets

  $ hg evolve
  move:[3] a3
  atop:[4] a2

  $ hg log -G --template '{rev} [{branch}] {desc|firstline}\n'
  o  5 [mybranch] a3
  |
  @  4 [mybranch] a2
  |
  o  1 [default] a1
  |
  o  0 [default] a0
  

branch change preserved

  $ hg up 'desc(a1)'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg amend -m 'a1_'
  2 new orphan changesets
  $ hg evolve --rev 'first(orphan())'
  move:[4] a2
  atop:[6] a1_
  $ hg evolve
  move:[5] a3
  atop:[7] a2
  $ hg log -G --template '{rev} [{branch}] {desc|firstline}\n'
  o  8 [mybranch] a3
  |
  o  7 [mybranch] a2
  |
  @  6 [default] a1_
  |
  o  0 [default] a0
  

Evolve from the middle of a stack pick the right changesets.

  $ hg ci --amend -m 'a1__'
  2 new orphan changesets

  $ hg up -r "desc('a2')"
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log -G --template '{rev} [{branch}] {desc|firstline}\n'
  o  9 [default] a1__
  |
  | *  8 [mybranch] a3
  | |
  | @  7 [mybranch] a2
  | |
  | x  6 [default] a1_
  |/
  o  0 [default] a0
  
  $ hg evolve
  nothing to evolve on current working copy parent
  (2 other orphan in the repository, do you want --any or --rev)
  [2]


Evolve disables active bookmarks.

  $ hg up -r "desc('a1__')"
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg bookmark testbookmark
  $ ls .hg/bookmarks*
  .hg/bookmarks
  .hg/bookmarks.* (glob)
  $ hg evolve --rev 'first(orphan())'
  move:[7] a2
  atop:[9] a1__
  (leaving bookmark testbookmark)
  $ ls .hg/bookmarks*
  .hg/bookmarks
  $ glog
  o  10:f37ed7a60f43@mybranch(draft) a2
  |
  @  9:9f8b83c2e7f3@default(draft) a1__
  |
  | *  8:c7661e655801@mybranch(draft) a3
  | |
  | x  7:5406c5cfee42@mybranch(draft) a2
  | |
  | x  6:faafc6cea0ba@default(draft) a1_
  |/
  o  0:07c1c36d9ef0@default(draft) a0
  

Possibility to select what instability to solve first, asking for
phase-divergent before content-divergent
  $ hg revert -r f37ed7a60f43 --all
  reverting a
  $ hg log -G --template '{rev} [{branch}] {desc|firstline}\n'
  o  10 [mybranch] a2
  |
  @  9 [default] a1__
  |
  | *  8 [mybranch] a3
  | |
  | x  7 [mybranch] a2
  | |
  | x  6 [default] a1_
  |/
  o  0 [default] a0
  
  $ echo "hello world" > newfile
  $ hg add newfile
  $ hg commit -m "add new file bumped" -o 10
  $ hg phase --public --hidden f37ed7a60f43
  1 new phase-divergent changesets
  $ hg log -G
  @  11	: add new file bumped - test
  |
  | o  10	: a2 - test
  |/
  o  9	testbookmark: a1__ - test
  |
  | *  8	: a3 - test
  | |
  | x  7	: a2 - test
  | |
  | x  6	: a1_ - test
  |/
  o  0	: a0 - test
  

Now we have a phase-divergent and an orphan changeset, we solve the
phase-divergent first. Normally the orphan changeset would be solved first

  $ hg log -G
  @  11	: add new file bumped - test
  |
  | o  10	: a2 - test
  |/
  o  9	testbookmark: a1__ - test
  |
  | *  8	: a3 - test
  | |
  | x  7	: a2 - test
  | |
  | x  6	: a1_ - test
  |/
  o  0	: a0 - test
  
  $ hg evolve -r "desc('add new file bumped')" --phase-divergent
  recreate:[11] add new file bumped
  atop:[10] a2
  committed as db294883bd68
  working directory is now at db294883bd68
  $ hg evolve --any
  move:[8] a3
  atop:[12] phase-divergent update to f37ed7a60f43:
  $ glog
  o  13:0210bf7b6518@default(draft) a3
  |
  @  12:db294883bd68@default(draft) phase-divergent update to f37ed7a60f43:
  |
  o  10:f37ed7a60f43@mybranch(public) a2
  |
  o  9:9f8b83c2e7f3@default(public) a1__
  |
  o  0:07c1c36d9ef0@default(public) a0
  

Check that we can resolve instabilities in a revset with more than one commit
  $ hg up 0210bf7b6518 -C
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ mkcommit gg
  $ hg up 0210bf7b6518
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit gh
  created new head
  $ hg up 0210bf7b6518
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ printf "newline\nnewline\n" >> a
  $ hg log -G
  o  15	: add gh - test
  |
  | o  14	: add gg - test
  |/
  @  13	: a3 - test
  |
  o  12	: phase-divergent update to f37ed7a60f43: - test
  |
  o  10	: a2 - test
  |
  o  9	testbookmark: a1__ - test
  |
  o  0	: a0 - test
  
  $ hg amend
  2 new orphan changesets
  $ glog
  @  16:5478ae0ce2d9@default(draft) a3
  |
  | *  15:fb5702c4d3e6@default(draft) add gh
  | |
  | | *  14:148850890f43@default(draft) add gg
  | |/
  | x  13:0210bf7b6518@default(draft) a3
  |/
  o  12:db294883bd68@default(draft) phase-divergent update to f37ed7a60f43:
  |
  o  10:f37ed7a60f43@mybranch(public) a2
  |
  o  9:9f8b83c2e7f3@default(public) a1__
  |
  o  0:07c1c36d9ef0@default(public) a0
  

Evolving an empty revset should do nothing
  $ hg evolve --rev "fb5702c4d3e6 and 148850890f43"
  set of specified revisions is empty
  [1]

  $ hg evolve --rev "0210bf7b6518::" --phase-divergent
  no phasedivergent changesets in specified revisions
  (do you want to use --orphan)
  [2]
  $ hg evolve --rev "0210bf7b6518::" --orphan
  move:[14] add gg
  atop:[16] a3
  move:[15] add gh
  atop:[16] a3
  $ glog
  o  18:5f8a4fc86068@default(draft) add gh
  |
  | o  17:a38ac764661b@default(draft) add gg
  |/
  @  16:5478ae0ce2d9@default(draft) a3
  |
  o  12:db294883bd68@default(draft) phase-divergent update to f37ed7a60f43:
  |
  o  10:f37ed7a60f43@mybranch(public) a2
  |
  o  9:9f8b83c2e7f3@default(public) a1__
  |
  o  0:07c1c36d9ef0@default(public) a0
  
Enabling commands selectively, no command enabled, next and fold and unknown
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=createmarkers
  > EOF
  $ hg next
  hg: unknown command 'next'
  (use 'hg help' for a list of commands)
  [10]
  $ hg fold
  hg: unknown command 'fold'
  (use 'hg help' for a list of commands)
  [10]
Enabling commands selectively, only fold enabled, next is still unknown
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=createmarkers
  > evolutioncommands=fold
  > EOF
  $ hg fold
  abort: no revisions specified
  [255]
  $ hg next
  hg: unknown command 'next'
  (use 'hg help' for a list of commands)
  [10]

Shows "use 'hg evolve' to..." hints iff the evolve command is enabled

  $ hg --hidden up 14
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 148850890f43
  (hidden revision '148850890f43' was rewritten as: a38ac764661b)
  working directory parent is obsolete! (148850890f43)
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolutioncommands=evolve
  > EOF
  $ hg --hidden up 15
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset fb5702c4d3e6
  (hidden revision 'fb5702c4d3e6' was rewritten as: 5f8a4fc86068)
  working directory parent is obsolete! (fb5702c4d3e6)
  (use 'hg evolve' to update to its successor: 5f8a4fc86068)

Restore all of the evolution features

  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=all
  > EOF

Check hg evolve --rev on singled out commit
  $ hg up a38ac764661b -C
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit j1
  $ mkcommit j2
  $ mkcommit j3
  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo "hello" > j4
  $ hg add j4
  $ hg amend
  2 new orphan changesets
  $ glog -r "5478ae0ce2d9::"
  @  22:cc75952078c6@default(draft) add j1
  |
  | *  21:677a629bd09c@default(draft) add j3
  | |
  | *  20:0208ef487f3a@default(draft) add j2
  | |
  | x  19:30d3ac01aa58@default(draft) add j1
  |/
  | o  18:5f8a4fc86068@default(draft) add gh
  | |
  o |  17:a38ac764661b@default(draft) add gg
  |/
  o  16:5478ae0ce2d9@default(draft) a3
  |
  ~

  $ hg evolve --rev 677a629bd09c --any
  abort: cannot specify both "--rev" and "--any"
  [255]
  $ hg evolve --rev 677a629bd09c
  skipping 677a629bd09c, consider including orphan ancestors

Check that uncommit respects the allowunstable option
With only createmarkers we can only uncommit on a head
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=createmarkers, allnewcommands
  > EOF
  $ hg up cc75952078c6^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg uncommit --all
  abort: cannot uncommit changeset, as that will orphan 4 descendants
  (see 'hg help evolution.instability')
  [10]
  $ hg up cc75952078c6
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg uncommit --all
  new changeset is empty
  (use 'hg prune .' to remove it)
  $ glog -r "5478ae0ce2d9::"
  @  23:4086309bffa5@default(draft) add j1
  |
  | *  21:677a629bd09c@default(draft) add j3
  | |
  | *  20:0208ef487f3a@default(draft) add j2
  | |
  | x  19:30d3ac01aa58@default(draft) add j1
  |/
  | o  18:5f8a4fc86068@default(draft) add gh
  | |
  o |  17:a38ac764661b@default(draft) add gg
  |/
  o  16:5478ae0ce2d9@default(draft) a3
  |
  ~

Check that prune respects the allowunstable option
  $ hg up -C .
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg up 5f8a4fc86068
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg evolve --all
  nothing to evolve on current working copy parent
  (2 other orphan in the repository, do you want --any or --rev)
  [2]
  $ hg evolve --all --any
  move:[20] add j2
  atop:[23] add j1
  move:[21] add j3
  $ glog -r "5478ae0ce2d9::"
  o  25:bc61f0de3ab8@default(draft) add j3
  |
  o  24:57c9733eb876@default(draft) add j2
  |
  o  23:4086309bffa5@default(draft) add j1
  |
  | @  18:5f8a4fc86068@default(draft) add gh
  | |
  o |  17:a38ac764661b@default(draft) add gg
  |/
  o  16:5478ae0ce2d9@default(draft) a3
  |
  ~
  $ hg up a38ac764661b
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit c5_
  created new head
  $ hg prune '4086309bffa5 + 57c9733eb876'
  abort: cannot prune changeset, as that will orphan 1 descendants
  (see 'hg help evolution.instability')
  [10]
  $ hg prune 'a38ac764661b::bc61f0de3ab8'
  abort: cannot prune changeset, as that will orphan 1 descendants
  (see 'hg help evolution.instability')
  [10]
  $ hg prune '4086309bffa5::'
  3 changesets pruned
  $ glog -r "5478ae0ce2d9::"
  @  26:0ea0aab97a68@default(draft) add c5_
  |
  | o  18:5f8a4fc86068@default(draft) add gh
  | |
  o |  17:a38ac764661b@default(draft) add gg
  |/
  o  16:5478ae0ce2d9@default(draft) a3
  |
  ~

Check that fold respects the allowunstable option

(most of this has been moved to test-fold.t)

  $ hg up 5478ae0ce2d9
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ mkcommit unstableifparentisfolded
  created new head
  $ glog -r "5478ae0ce2d9::"
  @  27:a590ee1f960d@default(draft) add unstableifparentisfolded
  |
  | o  26:0ea0aab97a68@default(draft) add c5_
  | |
  +---o  18:5f8a4fc86068@default(draft) add gh
  | |
  | o  17:a38ac764661b@default(draft) add gg
  |/
  o  16:5478ae0ce2d9@default(draft) a3
  |
  ~

  $ hg fold --exact "a38ac764661b::"
  2 changesets folded

Check that dirstate changes are kept at failure for conflicts (issue4966)
----------------------------------------

  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=all
  > EOF

  $ echo "will be amended" > newfile
  $ hg commit -m "will be amended"
  $ hg parents
  29	: will be amended - test

  $ echo "will be evolved safely" >> a
  $ hg commit -m "will be evolved safely"

  $ echo "will cause conflict at evolve" > newfile
  $ echo "newly added" > newlyadded
  $ hg add newlyadded
  $ hg commit -m "will cause conflict at evolve"

  $ glog -r "5478ae0ce2d9::"
  @  31:835945a2b5c1@default(draft) will cause conflict at evolve
  |
  o  30:c4fb0d23465b@default(draft) will be evolved safely
  |
  o  29:45e2cc1499ee@default(draft) will be amended
  |
  | o  28:7992c4aad71c@default(draft) add gg
  | |
  o |  27:a590ee1f960d@default(draft) add unstableifparentisfolded
  |/
  | o  18:5f8a4fc86068@default(draft) add gh
  |/
  o  16:5478ae0ce2d9@default(draft) a3
  |
  ~

  $ hg update -q -r "desc('will be amended')"
  $ echo "amended" > newfile
  $ hg amend -m "amended"
  2 new orphan changesets

  $ hg evolve --rev "desc('will be amended')::"
  move:[30] will be evolved safely
  atop:[32] amended
  move:[31] will cause conflict at evolve
  merging newfile (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging newfile
  warning: conflicts while merging newfile! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ glog -r "desc('add unstableifparentisfolded')::" --hidden
  @  33:bdb2d79645eb@default(draft) will be evolved safely
  |
  o  32:d788a38aecda@default(draft) amended
  |
  | %  31:835945a2b5c1@default(draft) will cause conflict at evolve
  | |
  | x  30:c4fb0d23465b@default(draft) will be evolved safely
  | |
  | x  29:45e2cc1499ee@default(draft) will be amended
  |/
  o  27:a590ee1f960d@default(draft) add unstableifparentisfolded
  |
  ~

  $ hg status newlyadded
  A newlyadded

  $ cd ..

Testing bookmark movement when `hg evolve` updates to successor (issue5923)

  $ hg init issue5923
  $ cd issue5923
  $ echo foo > a
  $ hg ci -Aqm "added a"

  $ hg log -GT "{rev}:{node|short} {desc} {bookmarks}\n"
  @  0:f7ad41964313 added a
  
  $ echo bar >> a
  $ hg amend

  $ hg log -GT "{rev}:{node|short} {desc} {bookmarks}\n"
  @  1:ab832e43dd5a added a
  
  $ hg up f7ad41964313 --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset f7ad41964313
  (hidden revision 'f7ad41964313' was rewritten as: ab832e43dd5a)
  working directory parent is obsolete! (f7ad41964313)
  (use 'hg evolve' to update to its successor: ab832e43dd5a)

  $ hg bookmark book

  $ hg evolve
  update:[1] added a
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at ab832e43dd5a

  $ hg log -GT "{rev}:{node|short} {desc} ({bookmarks})\n" --hidden
  @  1:ab832e43dd5a added a (book)
  
  x  0:f7ad41964313 added a ()
  
  $ cd ..
