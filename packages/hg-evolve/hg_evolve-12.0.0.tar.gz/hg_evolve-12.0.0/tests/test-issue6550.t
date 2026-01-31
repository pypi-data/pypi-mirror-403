histedit should preserve topics (issue6550)
https://bz.mercurial-scm.org/show_bug.cgi?id=6550

  $ . "$TESTDIR/testlib/topic_setup.sh"

  $ cat << EOF >> "$HGRCPATH"
  > [extensions]
  > histedit =
  > [alias]
  > glog = log -G --template "{rev}:{node|short} [{topic}] {desc}\n"
  > EOF

Editing commits with one topic on top of a commit with a different topic:

  $ hg init repo1
  $ cd repo1
  $ hg topic topic1
  marked working directory as topic: topic1
  $ echo 1 > A
  $ hg ci -Aqm A
  $ hg topic topic2
  $ echo 1 > B
  $ hg ci -Aqm B
  $ echo 1 > C
  $ hg ci -Aqm C
  $ hg glog
  @  2:392a64d00726 [topic2] C
  |
  o  1:8a25a1549e46 [topic2] B
  |
  o  0:c051488dac25 [topic1] A
  
Swap the order of commits B and C

  $ hg histedit s1 -q --commands - 2>&1 << EOF
  > pick 392a64d00726 C
  > pick 8a25a1549e46 B
  > EOF

Topic of B and C is preserved

  $ hg glog
  @  4:065a99df807b [topic2] B
  |
  o  3:43dddca3e1d1 [topic2] C
  |
  o  0:c051488dac25 [topic1] A
  
  $ cd ..

Editing commits without a topic on top of a commit with a topic:

  $ hg init repo2
  $ cd repo2
  $ hg topic topic1
  marked working directory as topic: topic1
  $ echo 1 > A
  $ hg ci -Aqm A
  $ hg topic --clear
  $ echo 1 > B
  $ hg ci -Aqm B
  $ echo 1 > C
  $ hg ci -Aqm C
  $ hg glog
  @  2:c47acbb860b3 [] C
  |
  o  1:e2e2ca96a6bb [] B
  |
  o  0:c051488dac25 [topic1] A
  
Swap the order of commits B and C

  $ hg histedit s1 -q --commands - 2>&1 << EOF
  > pick c47acbb860b3 C
  > pick e2e2ca96a6bb B
  > EOF

B and C still don't have a topic

  $ hg glog
  @  4:ff3439fe6f3d [] B
  |
  o  3:bb6fab1a29c6 [] C
  |
  o  0:c051488dac25 [topic1] A
  
  $ cd ..

Editing commits with a topic on top of a commit without a topic:

  $ hg init repo3
  $ cd repo3
  $ echo 1 > A
  $ hg ci -Aqm A
  $ hg topic topic1
  marked working directory as topic: topic1
  $ echo 1 > B
  $ hg ci -Aqm B
  $ echo 1 > C
  $ hg ci -Aqm C
  $ hg glog
  @  2:c3dae6eda73b [topic1] C
  |
  o  1:db3a7c9052ac [topic1] B
  |
  o  0:a18fe624bf77 [] A
  
Swap the order of commits B and C

  $ hg histedit s1 -q --commands - 2>&1 << EOF
  > pick c3dae6eda73b C
  > pick db3a7c9052ac B
  > EOF

Topic of B and C is preserved

  $ hg glog
  @  4:aa7af5cc1567 [topic1] B
  |
  o  3:4bf8cf7b2c73 [topic1] C
  |
  o  0:a18fe624bf77 [] A
  
  $ cd ..
