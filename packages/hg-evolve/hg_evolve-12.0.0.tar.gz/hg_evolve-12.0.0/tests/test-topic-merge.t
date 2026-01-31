==========================================================
Testing the ability to control merge behavior around topic
==========================================================

Especially, we want to test mode allowing the creation of merge that will
eventually become "oedipus" merge.

  $ . "$TESTDIR/testlib/topic_setup.sh"
  $ . "$TESTDIR/testlib/common.sh"



Setup a test repository
=======================

  $ hg init test-repo
  $ cd test-repo
  $ mkcommit root
  $ mkcommit default-1
  $ mkcommit default-2
  $ hg up 'desc("default-2")'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg topic test-topic
  marked working directory as topic: test-topic
  $ mkcommit topic-1
  active topic 'test-topic' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit topic-2
  $ hg up null
  0 files updated, 0 files merged, 5 files removed, 0 files unresolved
  $ hg log -G
  o  changeset:   4:c3ec1ef2bf00
  |  tag:         tip
  |  topic:       test-topic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     topic-2
  |
  o  changeset:   3:3300cececc85
  |  topic:       test-topic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     topic-1
  |
  o  changeset:   2:b05d997f9ab0
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     default-2
  |
  o  changeset:   1:ccab697ce421
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     default-1
  |
  o  changeset:   0:1e4be0697311
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     root
  

Test that the merge is rejected by default
==========================================

from the topic

  $ hg up test-topic
  switching to topic test-topic
  5 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg merge default
  abort: merging with a working directory ancestor has no effect
  [255]

from the bare branch

  $ hg up default
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg merge test-topic
  abort: nothing to merge
  (use 'hg update' or check 'hg heads')
  [255]

Test that the merge is rejected if set to reject
================================================

Actually, this also work with any invalid value, but:

- the default value might change in the future,
- this make sure we read the config right.

Same result when setting the config to be strict

  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > topic.linear-merge = reject
  > EOF

from the topic

  $ hg up test-topic
  switching to topic test-topic
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg merge default
  abort: merging with a working directory ancestor has no effect
  [255]

from the bare branch

  $ hg up default
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg merge test-topic
  abort: nothing to merge
  (use 'hg update' or check 'hg heads')
  [255]

Test that the merge is accepted if configured to allow them
===========================================================

  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > topic.linear-merge = allow-from-bare-branch
  > EOF

from the topic, this is rejected since the resulting merge would be in the topic itself

  $ hg up test-topic
  switching to topic test-topic
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg merge default
  abort: merging with a working directory ancestor has no effect
  [255]

from the bare branch this is allowed since the resulting merge will be in the branch

  $ hg up default
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg merge test-topic --traceback
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "How dreadful the knowledge of the truth can be when there's no help in truth."
  $ hg log -G
  @    changeset:   5:42ca2e8cb810
  |\   tag:         tip
  | |  parent:      2:b05d997f9ab0
  | |  parent:      4:c3ec1ef2bf00
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     How dreadful the knowledge of the truth can be when there's no help in truth.
  | |
  | o  changeset:   4:c3ec1ef2bf00
  | |  topic:       test-topic
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     topic-2
  | |
  | o  changeset:   3:3300cececc85
  |/   topic:       test-topic
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     topic-1
  |
  o  changeset:   2:b05d997f9ab0
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     default-2
  |
  o  changeset:   1:ccab697ce421
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     default-1
  |
  o  changeset:   0:1e4be0697311
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     root
  
