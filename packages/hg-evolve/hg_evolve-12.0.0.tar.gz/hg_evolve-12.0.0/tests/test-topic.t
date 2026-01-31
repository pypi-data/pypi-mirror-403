  $ . "$TESTDIR/testlib/topic_setup.sh"

  $ hg init pinky
  $ cd pinky
  $ cat <<EOF >> .hg/hgrc
  > [phases]
  > publish=false
  > EOF

  $ hg help -e topic
  topic extension - support for topic branches
  
  Topic branches are lightweight branches which fade out when changes are
  finalized (move to the public phase).
  
  Compared to bookmark, topic is reference carried by each changesets of the
  series instead of just the single head revision.  Topic are quite similar to
  the way named branch work, except they eventually fade away when the changeset
  becomes part of the immutable history. Changeset can belong to both a topic
  and a named branch, but as long as it is mutable, its topic identity will
  prevail. As a result, default destination for 'update', 'merge', etc...  will
  take topic into account. When a topic is active these operations will only
  consider other changesets on that topic (and, in some occurrence, bare
  changeset on same branch).  When no topic is active, changeset with topic will
  be ignored and only bare one on the same branch will be taken in account.
  
  There is currently two commands to be used with that extension: 'topics' and
  'stack'.
  
  The 'hg topics' command is used to set the current topic, change and list
  existing one. 'hg topics --verbose' will list various information related to
  each topic.
  
  The 'stack' will show you information about the stack of commit belonging to
  your current topic.
  
  Topic is offering you aliases reference to changeset in your current topic
  stack as 's#'. For example, 's1' refers to the root of your stack, 's2' to the
  second commits, etc. The 'hg stack' command show these number. 's0' can be
  used to refer to the parent of the topic root. Updating using 'hg up s0' will
  keep the topic active.
  
  Push behavior will change a bit with topic. When pushing to a publishing
  repository the changesets will turn public and the topic data on them will
  fade away. The logic regarding pushing new heads will behave has before,
  ignore any topic related data. When pushing to a non-publishing repository
  (supporting topic), the head checking will be done taking topic data into
  account. Push will complain about multiple heads on a branch if you push
  multiple heads with no topic information on them (or multiple public heads).
  But pushing a new topic will not requires any specific flag. However, pushing
  multiple heads on a topic will be met with the usual warning.
  
  The 'evolve' extension takes 'topic' into account. 'hg evolve --all' will
  evolve all changesets in the active topic. In addition, by default. 'hg next'
  and 'hg prev' will stick to the current topic.
  
  Be aware that this extension is still an experiment, commands and other
  features are likely to be change/adjusted/dropped over time as we refine the
  concept.
  
  topic-mode
  ==========
  
  The topic extension can be configured to ensure the user do not forget to add
  a topic when committing a new topic:
  
    [experimental]
    # behavior when commit is made without an active topic
    topic-mode = ignore # do nothing special (default)
    topic-mode = warning # print a warning
    topic-mode = enforce # abort the commit (except for merge)
    topic-mode = enforce-all # abort the commit (even for merge)
    topic-mode = random # use a randomized generated topic (except for merge)
    topic-mode = random-all # use a randomized generated topic (even for merge)
  
  Single head enforcing
  =====================
  
  The extensions come with an option to enforce that there is only one heads for
  each name in the repository at any time.
  
    [experimental]
    enforce-single-head = yes
  
  Publishing behavior
  ===================
  
  Topics vanish when changesets move to the public phase. Moving to the public
  phase usually happens on push, but it is possible to modify this behavior. The
  server needs to have specific config for this.
  
  * everything pushed becomes public (the default):
  
      [phases]
      publish = yes
  
  * nothing pushed turns public:
  
      [phases]
      publish = no
  
  * topic branches are not published, changesets without topic are:
  
      [phases]
      publish = no
      [experimental]
      topic.publish-bare-branch = yes
  
  In addition, 'hg push' command has a "--publish" flag. When used, the pushed
  revisions are published if the push succeeds. It also applies to common
  revisions selected by the push.
  
  One can prevent any publishing from happening in a repository using:
  
    [experimental]
    topic.allow-publish = no
  
  Server side visibility
  ======================
  
  Serving changesets with topics to clients without topic extension can get
  confusing. Such clients will have multiple anonymous heads without a clear way
  to distinguish them. They will also "lose" the canonical heads of the branch.
  
  To avoid this confusion, server can be configured to only serve changesets
  with topics to clients with the topic extension (version 9.3+). This might
  become the default in future:
  
    [experimental]
    topic.server-gate-topic-changesets = yes
  
  Explicitly merging in the target branch
  =======================================
  
  By default, Mercurial will not let your merge a topic into its target branch
  if that topic is already based on the head of that branch. In other word,
  Mercurial will not let your create a merge that will eventually have two
  parents in the same branches, one parent being the ancestors of the other
  parent. This behavior can be lifted using the following config:
  
    [experimental]
    topic.linear-merge = allow-from-bare-branch
  
  When this option is set to 'allow-from-bare-branch', it is possible to merge a
  topic branch from a bare branch (commit an active topic (eg: public one))
  regardless of the topology. The result would typically looks like that:
  
    @    summary: resulting merge commit
    |\   branch:  my-branch
    | |
    | o  summary: some more change in a topic, the merge "target"
    | |  branch:  my-branch
    | |  topic:   my-topic
    | |
    | o  summary: some change in a topic
    |/   branch:  my-branch
    |    topic:   my-topic
    |
    o    summary: previous head of the branch, the merge "source"
    |    branch:  my-branch
  
  list of commands:
  
  Change organization:
  
   topics        View current topic, set current topic, change topic for a set
                 of revisions, or see all topics.
  
  Change navigation:
  
   stack         list all changesets in a topic and other information
  
  (use 'hg help -v topic' to show built-in aliases and global options)

#if hg69
  $ hg help topics
  hg topics [OPTION]... [-r REV]... [TOPIC]
  
  View current topic, set current topic, change topic for a set of revisions, or
  see all topics.
  
  Clear topic on existing topiced revisions:
  
    hg topics --rev <related revset> --clear
  
  Change topic on some revisions:
  
    hg topics <newtopicname> --rev <related revset>
  
  Clear current topic:
  
    hg topics --clear
  
  Set current topic:
  
    hg topics <topicname>
  
  List of topics:
  
    hg topics
  
  List of topics sorted according to their last touched time displaying last
  touched time and the user who last touched the topic:
  
    hg topics --age
  
  The active topic (if any) will be prepended with a "*".
  
  The '--current' flag helps to take active topic into account. For example, if
  you want to set the topic on all the draft changesets to the active topic, you
  can do: 'hg topics -r "draft()" --current'
  
  The --verbose version of this command display various information on the state
  of each topic.
  
  options ([+] can be repeated):
  
      --clear             clear active topic if any
   -r --rev REV [+]       revset of existing revisions
   -l --list              show the stack of changeset in the topic
      --age               show when you last touched the topics
      --current           display the current topic only
   -T --template TEMPLATE display with template
  
  (some details hidden, use --verbose to show complete help)
#endif

  $ hg topics

Test topics interaction with evolution:

  $ hg topics --config experimental.evolution= \
  >           --config experimental.evolution.createmarkers=0 \
  >           --config experimental.evolution.exchange=0
  $ hg topics --config experimental.evolution= \
  >           --config experimental.evolution.createmarkers=0 \
  >           --config experimental.evolution.exchange=0 \
  >           --rev . bob
  abort: must have obsolete enabled to change topics
  [255]

Create some changes:

  $ for x in alpha beta gamma delta ; do
  >   echo file $x >> $x
  >   hg addremove
  >   hg ci -m "Add file $x"
  > done
  adding alpha
  adding beta
  adding gamma
  adding delta

Still no topics
  $ hg topics
  $ hg topics --current
  no active topic
  [1]
  $ hg topics --current somerandomtopic
  abort: cannot use --current when setting a topic
  [10]
  $ hg topics --current --clear
  abort: cannot use --current and --clear
  [10]
  $ hg topics --clear somerandomtopic
  abort: cannot use --clear when setting a topic
  [10]
  $ hg topics --list --clear
  abort: cannot specify both --list and --clear
  [10]

Trying some invalid topicnames

  $ hg topic '.'
  abort: the name '.' is reserved
  [10]
  $ hg topic null
  abort: the name 'null' is reserved
  [10]
  $ hg topic tip
  abort: the name 'tip' is reserved
  [10]
  $ hg topic 12345
  abort: cannot use an integer as a name
  [10]
  $ hg topic '   '
  abort: topic names cannot consist entirely of whitespace
  [10]

  $ hg topic 'a12#45'
  abort: invalid topic name: 'a12#45'
  (topic names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

  $ hg topic 'foo bar'
  abort: invalid topic name: 'foo bar'
  (topic names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

this is trying to list topic names
  $ hg topic ''

  $ hg topic '*12 B23'
  abort: invalid topic name: '*12 B23'
  (topic names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

Test commit flag and help text

  $ echo stuff >> alpha
  $ HGEDITOR=cat hg ci -t topicflag
  
  
  HG: Enter commit message.  Lines beginning with 'HG:' are removed.
  HG: Leave message empty to abort commit.
  HG: --
  HG: user: test
  HG: topic 'topicflag'
  HG: branch 'default'
  HG: changed alpha
  abort: empty commit message
  [10]
  $ hg revert alpha
  $ hg topic
   * topicflag (0 changesets)

Non-ascii topic name

  $ hg topic --clear
  clearing empty topic "topicflag"
  $ hg --encoding utf-8 topic æ
  marked working directory as topic: \xc3\xa6 (esc)
  $ hg --encoding utf-8 topics
   * æ (0 changesets) (esc)
  $ hg --encoding ascii topics
   * ? (0 changesets) (esc)
  $ hg --encoding latin1 topics
   * \xe6 (0 changesets) (esc)

  $ hg --encoding utf-8 topic ©
  abort: invalid topic name: '\xc2\xa9' (esc)
  (topic names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

  $ hg --encoding latin1 topic æ
  abort: invalid topic name: '\xc3\xa6' (esc)
  (topic names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

Make a topic

  $ hg topic narf
  $ hg topics
   * narf (0 changesets)
  $ hg topics -v
   * narf (on branch: default, 0 changesets)
  $ hg stack
  ### topic: narf
  ### target: default (branch)
  (stack is empty)
  s0^ Add file delta (base current)

Add commits to topic

  $ echo topic work >> alpha
  $ hg ci -m 'start on narf'
  active topic 'narf' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg co .^
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg topic fran
  marked working directory as topic: fran
  $ hg topics
   * fran (0 changesets)
     narf (1 changesets)
  $ hg topics --current
  fran
  $ echo >> fran work >> beta
  $ hg ci -m 'start on fran'
  active topic 'fran' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg co narf
  switching to topic narf
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg topic
     fran (1 changesets)
   * narf (1 changesets)
  $ hg log -r . -T '{topics}\n'
  narf
  $ echo 'narf!!!' >> alpha
  $ hg ci -m 'narf!'
  $ hg log -G
  @  changeset:   6:7c34953036d6
  |  tag:         tip
  |  topic:       narf
  |  parent:      4:fb147b0b417c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     narf!
  |
  | o  changeset:   5:0469d521db49
  | |  topic:       fran
  | |  parent:      3:a53952faf762
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     start on fran
  | |
  o |  changeset:   4:fb147b0b417c
  |/   topic:       narf
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     start on narf
  |
  o  changeset:   3:a53952faf762
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file delta
  |
  o  changeset:   2:15d1eb11d2fa
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file gamma
  |
  o  changeset:   1:c692ea2c9224
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file beta
  |
  o  changeset:   0:c2b7d2f7d14b
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add file alpha
  

Exchanging of topics:
  $ cd ..
  $ hg init brain
  $ hg -R pinky push -r 4 brain
  pushing to brain
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 5 changes to 4 files

Export

  $ hg -R pinky export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 7c34953036d6a36eae468c550d0592b89ee8bffc
  # Parent  fb147b0b417c25ca15547cd945acf51cf8dcaf02
  # EXP-Topic narf
  narf!
  
  diff -r fb147b0b417c -r 7c34953036d6 alpha
  --- a/alpha	Thu Jan 01 00:00:00 1970 +0000
  +++ b/alpha	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,2 +1,3 @@
   file alpha
   topic work
  +narf!!!

Import

  $ hg -R pinky export > narf.diff
  $ hg -R pinky --config extensions.strip= strip .
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/pinky/.hg/strip-backup/7c34953036d6-1ff3bae2-backup.hg (glob)
  $ hg -R pinky import narf.diff
  applying narf.diff
  $ hg -R pinky log -r .
  changeset:   6:7c34953036d6
  tag:         tip
  topic:       narf
  parent:      4:fb147b0b417c
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     narf!
  
Now that we've pushed to brain, the work done on narf is no longer a
draft, so we won't see that topic name anymore:

  $ hg log -R pinky -G
  @  changeset:   6:7c34953036d6
  |  tag:         tip
  |  topic:       narf
  |  parent:      4:fb147b0b417c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     narf!
  |
  | o  changeset:   5:0469d521db49
  | |  topic:       fran
  | |  parent:      3:a53952faf762
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     start on fran
  | |
  o |  changeset:   4:fb147b0b417c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     start on narf
  |
  o  changeset:   3:a53952faf762
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file delta
  |
  o  changeset:   2:15d1eb11d2fa
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file gamma
  |
  o  changeset:   1:c692ea2c9224
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file beta
  |
  o  changeset:   0:c2b7d2f7d14b
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add file alpha
  
  $ cd brain
  $ hg co tip
  4 files updated, 0 files merged, 0 files removed, 0 files unresolved

Because the change is public, we won't inherit the topic from narf.

  $ hg topic
  $ echo what >> alpha
  $ hg topic query
  marked working directory as topic: query
  $ hg ci -m 'what is narf, pinky?'
  active topic 'query' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg log -Gl2
  @  changeset:   5:c01515cfc331
  |  tag:         tip
  |  topic:       query
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     what is narf, pinky?
  |
  o  changeset:   4:fb147b0b417c
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on narf
  

  $ hg push -f ../pinky -r query
  pushing to ../pinky
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)

  $ hg -R ../pinky log -Gl 4
  o  changeset:   7:c01515cfc331
  |  tag:         tip
  |  topic:       query
  |  parent:      4:fb147b0b417c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     what is narf, pinky?
  |
  | @  changeset:   6:7c34953036d6
  |/   topic:       narf
  |    parent:      4:fb147b0b417c
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     narf!
  |
  | o  changeset:   5:0469d521db49
  | |  topic:       fran
  | ~  parent:      3:a53952faf762
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     start on fran
  |
  o  changeset:   4:fb147b0b417c
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on narf
  

  $ hg topics
   * query (1 changesets)
  $ cd ../pinky
  $ hg co query
  switching to topic query
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo answer >> alpha
  $ hg ci -m 'Narf is like `zort` or `poit`!'
  $ hg merge narf
  merging alpha
  warning: conflicts while merging alpha! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  use 'hg resolve' to retry unresolved file merges or 'hg merge --abort' to abandon
  [1]
  $ hg revert -r narf alpha
  $ hg resolve -m alpha
  (no more unresolved files)
  $ hg topic narf
  $ hg ci -m 'Finish narf'
  $ hg topics
     fran  (1 changesets)
   * narf  (2 changesets)
     query (2 changesets)
  $ hg debugnamecomplete
  default
  default//fran
  default//narf
  default//query
  fran
  narf
  query
  tip
  $ hg phase --public narf
  active topic 'narf' is now empty
  (use 'hg topic --clear' to clear it if needed)

POSSIBLE BUG: narf topic stays alive even though we just made all
narf commits public:

  $ hg topics
     fran (1 changesets)
   * narf (0 changesets)
  $ hg log -Gl 6
  @    changeset:   9:ae074045b7a7
  |\   tag:         tip
  | |  parent:      8:54c943c1c167
  | |  parent:      6:7c34953036d6
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     Finish narf
  | |
  | o  changeset:   8:54c943c1c167
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     Narf is like `zort` or `poit`!
  | |
  | o  changeset:   7:c01515cfc331
  | |  parent:      4:fb147b0b417c
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     what is narf, pinky?
  | |
  o |  changeset:   6:7c34953036d6
  |/   parent:      4:fb147b0b417c
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     narf!
  |
  | o  changeset:   5:0469d521db49
  | |  topic:       fran
  | ~  parent:      3:a53952faf762
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     start on fran
  |
  o  changeset:   4:fb147b0b417c
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on narf
  

  $ cd ../brain
  $ hg topics
   * query (1 changesets)
  $ hg pull ../pinky -r narf
  pulling from ../pinky
  abort: unknown revision 'narf'
  [10]
  $ hg pull ../pinky -r default
  pulling from ../pinky
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  new changesets 7c34953036d6:ae074045b7a7
  1 local changesets published
  active topic 'query' is now empty
  (run 'hg update' to get a working copy)
  $ hg topics
   * query (0 changesets)

We can pull in the draft-phase change and we get the new topic

  $ hg pull ../pinky
  pulling from ../pinky
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  new changesets 0469d521db49 (1 drafts)
  (run 'hg heads' to see heads)
  $ hg topics
     fran  (1 changesets)
   * query (0 changesets)
  $ hg log -Gr 'draft()'
  o  changeset:   9:0469d521db49
  |  tag:         tip
  ~  topic:       fran
     parent:      3:a53952faf762
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on fran
  

query is not an open topic, so when we clear the current topic it'll
fade out:

  $ hg topics --clear
  clearing empty topic "query"
  $ hg topics
     fran (1 changesets)

Topic revset
  $ hg log -r 'topic()' -G
  o  changeset:   9:0469d521db49
  |  tag:         tip
  ~  topic:       fran
     parent:      3:a53952faf762
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on fran
  
  $ hg log -r 'not topic()' -G
  o    changeset:   8:ae074045b7a7
  |\   parent:      7:54c943c1c167
  | |  parent:      6:7c34953036d6
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     Finish narf
  | |
  | o  changeset:   7:54c943c1c167
  | |  parent:      5:c01515cfc331
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     Narf is like `zort` or `poit`!
  | |
  o |  changeset:   6:7c34953036d6
  | |  parent:      4:fb147b0b417c
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     narf!
  | |
  | @  changeset:   5:c01515cfc331
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     what is narf, pinky?
  |
  o  changeset:   4:fb147b0b417c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     start on narf
  |
  o  changeset:   3:a53952faf762
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file delta
  |
  o  changeset:   2:15d1eb11d2fa
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file gamma
  |
  o  changeset:   1:c692ea2c9224
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add file beta
  |
  o  changeset:   0:c2b7d2f7d14b
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add file alpha
  
No matches because narf is already closed:
  $ hg log -r 'topic("narf")' -G
This regexp should match the topic `fran`:
  $ hg log -r 'topic("re:.ra.")' -G
  o  changeset:   9:0469d521db49
  |  tag:         tip
  ~  topic:       fran
     parent:      3:a53952faf762
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on fran
  
Exact match on fran:
  $ hg log -r 'topic(fran)' -G
  o  changeset:   9:0469d521db49
  |  tag:         tip
  ~  topic:       fran
     parent:      3:a53952faf762
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on fran
  

Match current topic:
  $ hg topic
     fran (1 changesets)
  $ hg log -r 'topic(.)'
(no output is expected)

  $ hg up 8
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo test > gamma
  $ hg ci -m non-topic
  $ hg log -r 'topic(.)'

  $ hg co fran
  switching to topic fran
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log -r 'topic(.)'
  changeset:   9:0469d521db49
  topic:       fran
  parent:      3:a53952faf762
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     start on fran
  

Using revsets in topic()
  $ tlog() {
  >   hg log -T '{rev}: {topic}\n' -r "$1"
  > }

  $ tlog 'topic(9)'
  9: fran
  $ tlog 'topic(8)'
  $ tlog 'topic(head())'
  9: fran
  $ tlog 'topic(:)'
  9: fran
  $ tlog 'topic(all())'
  9: fran
  $ tlog 'topic(topic(fran))'
  9: fran
  $ tlog 'topic(wdir())'
  9: fran
  $ tlog 'topic(nonsense)'
  abort: unknown revision 'nonsense'
  [10]

Pattern matching in topic() revset
  $ tlog 'topic("re:nonsense")'
  $ tlog 'topic("literal:nonsense")'
  abort: topic 'nonsense' does not exist
  [10]

Sanity checks for topicnamespace() revset

  $ tlog 'topicnamespace()'

Deactivate the topic.
  $ hg topics
   * fran (1 changesets)
  $ hg topics --clear
  $ hg log -r 'topic(wdir())'
  $ echo fran? >> beta
  $ hg ci -m 'fran?'
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ hg log -Gr 'draft()'
  @  changeset:   11:4073470c35e1
  |  tag:         tip
  |  parent:      9:0469d521db49
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     fran?
  |
  | o  changeset:   10:de75ec1bdbe8
  | |  parent:      8:ae074045b7a7
  | ~  user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     non-topic
  |
  o  changeset:   9:0469d521db49
  |  topic:       fran
  ~  parent:      3:a53952faf762
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     start on fran
  

  $ hg topics
     fran (1 changesets)

Testing for updating to s0
==========================

  $ hg up fran
  switching to topic fran
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg stack
  ### topic: fran
  ### target: default (branch), ambiguous rebase destination - branch 'default' has 2 heads
  s1@ start on fran (current)
  s0^ Add file delta (base)

  $ hg up s0
  preserving the current topic 'fran'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg topic
   * fran (1 changesets)
  $ hg stack
  ### topic: fran
  ### target: default (branch), ambiguous rebase destination - branch 'default' has 2 heads
  s1: start on fran
  s0^ Add file delta (base current)

  $ hg topics --age
   * fran (1970-01-01 by test, 1 changesets)

  $ cd ..

Relation subscript in revsets
=============================

  $ hg init more-than-one-commit-per-topic
  $ cd more-than-one-commit-per-topic
  $ cat > .hg/hgrc << EOF
  > [phases]
  > publish=false
  > EOF

  $ echo 0 > foo
  $ hg ci -qAm 0
  $ hg topic featureA
  marked working directory as topic: featureA
  $ echo 1 > foo
  $ hg ci -qm 1
  $ echo 2 > foo
  $ hg ci -qm 2
  $ echo 3 > foo
  $ hg ci -qm 3
  $ hg topic --clear
  $ echo 4 > foo
  $ hg ci -qm 4

  $ tlog 'all()'
  0: 
  1: featureA
  2: featureA
  3: featureA
  4: 

topic subscript relation

  $ tlog 'featureA'
  3: featureA
  $ tlog 'featureA#topic[0]'
  3: featureA
  $ tlog 'featureA#topic[:]'
  1: featureA
  2: featureA
  3: featureA

  $ tlog '2#t[-2]'
  $ tlog '2#t[-1]'
  1: featureA
  $ tlog '2#t[0]'
  2: featureA
  $ tlog '2#t[1]'
  3: featureA
  $ tlog '2#t[2]'
  $ tlog '2#t[-1:1]'
  1: featureA
  2: featureA
  3: featureA

stack subscript relation

  $ hg stack
  ### target: default (branch)
  s2@ 4 (current)
    ^ 3
  s1: 0

  $ tlog 'tip#s'
  0: 
  4: 

  $ tlog 'tip#stack[0]'
  $ tlog 'tip#stack[1]'
  0: 
  $ tlog 'tip#stack[2]'
  4: 
  $ tlog 'tip#stack[-1]'
  4: 
  $ tlog 'tip#stack[-2]'
  0: 

  $ hg stack featureA
  ### topic: featureA
  ### target: default (branch), 3 behind
  s3: 3
  s2: 2
  s1: 1
  s0^ 0 (base)

  $ tlog 'featureA#s'
  1: featureA
  2: featureA
  3: featureA

  $ tlog 'featureA#s[0]'
  0: 
  $ tlog 'featureA#s[0:0]'
  0: 
  $ tlog 'featureA#s[:]'
  1: featureA
  2: featureA
  3: featureA
  $ tlog 'featureA#s[2:]'
  2: featureA
  3: featureA
  $ tlog 'featureA#s[:2]'
  1: featureA
  2: featureA
  $ tlog 'featureA#s[0:1]'
  0: 
  1: featureA
  $ tlog 'featureA#s[-1:0]'
  0: 
  3: featureA
  $ tlog 'featureA#s[-3:3]'
  1: featureA
  2: featureA
  3: featureA
  $ tlog 'featureA#s[1] and featureA#s[-3]'
  1: featureA
  $ tlog 'featureA#s[2] and featureA#s[-2]'
  2: featureA
  $ tlog 'featureA#s[3] and featureA#s[-1]'
  3: featureA
  $ tlog 'featureA#s[-4]'

  $ tlog 'all()#s[-1]'
  3: featureA
  4: 
  $ tlog 'all()#s[0]'
  0: 
  $ tlog 'all()#s[1]'
  0: 
  1: featureA
  $ tlog 'all()#s[9999]'
  $ tlog 'all()#s[-9999]'

  $ hg topic featureB
  marked working directory as topic: featureB
  $ hg stack
  ### topic: featureB
  ### target: default (branch)
  (stack is empty)
  s0^ 4 (base current)
  $ tlog 'wdir()#s'
  $ tlog 'wdir()#s[0]'
  4: 

  $ cd ..

Testing the new config knob to forbid untopiced commit
======================================================

  $ hg init ponky
  $ cd ponky
  $ cat <<EOF >> .hg/hgrc
  > [phases]
  > publish=false
  > EOF
  $ cat <<EOF >> $HGRCPATH
  > [experimental]
  > topic-mode = enforce
  > EOF
  $ touch a b c d
  $ hg add a
  $ hg ci -m "Added a"
  abort: no active topic
  (see 'hg help -e topic.topic-mode' for details)
  [255]

(same test, checking we abort before the editor)

  $ EDITOR=cat hg ci -m "Added a" --edit
  abort: no active topic
  (see 'hg help -e topic.topic-mode' for details)
  [255]
  $ hg ci -m "added a" --config experimental.topic-mode=off
  $ hg log
  changeset:   0:a154386e50d1
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added a
  

Testing the --age flag for `hg topics`
======================================

  $ hg topic topic1970 --rev 0
  switching to topic topic1970
  changed topic on 1 changesets to "topic1970"

  $ hg add b
  $ hg topic topic1990
  $ hg ci -m "Added b" --config devel.default-date="631152000 0" --user "foo"
  active topic 'topic1990' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg add c
  $ hg topic topic2010
  $ hg ci -m "Added c" --config devel.default-date="1262304000 0" --user "bar"
  active topic 'topic2010' grew its first changeset
  (see 'hg help topics' for more information)

  $ hg log -G
  @  changeset:   3:76b16af75125
  |  tag:         tip
  |  topic:       topic2010
  |  user:        bar
  |  date:        Fri Jan 01 00:00:00 2010 +0000
  |  summary:     Added c
  |
  o  changeset:   2:bba5bde53608
  |  topic:       topic1990
  |  user:        foo
  |  date:        Mon Jan 01 00:00:00 1990 +0000
  |  summary:     Added b
  |
  o  changeset:   1:e5a30a141954
     topic:       topic1970
     parent:      -1:000000000000
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     added a
  
  $ hg topics
     topic1970 (1 changesets)
     topic1990 (1 changesets)
   * topic2010 (1 changesets)

  $ hg topics --age
   * topic2010 (2010-01-01 by bar, 1 changesets)
     topic1990 (1990-01-01 by foo, 1 changesets)
     topic1970 (1970-01-01 by test, 1 changesets)

  $ hg topics --age --verbose
   * topic2010 (2010-01-01 by bar, on branch: default, 1 changesets)
     topic1990 (1990-01-01 by foo, on branch: default, 1 changesets)
     topic1970 (1970-01-01 by test, on branch: default, 1 changesets)

  $ hg up topic1970
  switching to topic topic1970
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved

  $ hg topics --age
     topic2010 (2010-01-01 by bar, 1 changesets)
     topic1990 (1990-01-01 by foo, 1 changesets)
   * topic1970 (1970-01-01 by test, 1 changesets)

  $ hg topics --age random
  abort: cannot use --age while setting a topic
  [10]
  $ cd ..

Test that topics doesn't confuse branchheads checking logic
-----------------------------------------------------------

  $ hg init hgtags
  $ cd hgtags
  $ echo a > a
  $ hg ci -Am "added a" --config experimental.topic-mode=default
  adding a
  $ echo b > b
  $ hg ci -Am "added b" --config experimental.topic-mode=default
  adding b

  $ hg topic foo -r .
  switching to topic foo
  changed topic on 1 changesets to "foo"

Try to put a tag on current rev which also has an active topic:
  $ hg tag 1.0
  $ hg tags
  tip                                3:9efc5c3ac635
  1.0                                2:3bbb3fdb2546

test that being on active topic does not change output of `hg heads`

  $ hg up 0
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo c > c
  $ hg ci -Am "added c" --config experimental.topic-mode=default
  adding c
  $ hg log -G -T '{rev} {branch}{if("{topic}", "/{topic}")}\n' --rev 'all()'
  @  4 default
  |
  | o  3 default/foo
  | |
  | o  2 default/foo
  |/
  o  0 default
  
  $ hg heads
  changeset:   4:29edef26570b
  tag:         tip
  parent:      0:9092f1db7931
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
  changeset:   3:9efc5c3ac635
  topic:       foo
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag 1.0 for changeset 3bbb3fdb2546
  
  $ hg topic foo
  marked working directory as topic: foo
  $ hg heads
  changeset:   4:29edef26570b
  tag:         tip
  parent:      0:9092f1db7931
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
  changeset:   3:9efc5c3ac635
  topic:       foo
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag 1.0 for changeset 3bbb3fdb2546
  

  $ hg up foo
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg heads
  changeset:   4:29edef26570b
  tag:         tip
  parent:      0:9092f1db7931
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
  changeset:   3:9efc5c3ac635
  topic:       foo
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag 1.0 for changeset 3bbb3fdb2546
  
  $ cd ..

Check that we don't break `hg backout`
--------------------------------------

hg backout use codepath we wrap and it broke during the 7.2rc cycle

  $ cd brain
  $ hg backout --rev .~2 --quiet
