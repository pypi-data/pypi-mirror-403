  $ . $TESTDIR/testlib/topic_setup.sh

Code logically equivalent to the following is used in Zsh to show the branch
and topic (if set) in the prompt. If the format of the files is changed in a
way that it breaks the test, a mail should be sent to zsh-workers@zsh.org.

  $ get_branch_like_zsh() {
  >     branchfile=".hg/branch"
  >     topicfile=".hg/topic"
  >     if [ -r "${branchfile}" ] ; then
  >         r_branch=$(cat "${branchfile}")
  >     fi
  >     if [ -f "${topicfile}" ] && [ -r "${topicfile}" ] && [ -s "${topicfile}" ] ; then
  >         IFS= read -r REPLY < ${topicfile}
  >         r_branch=${r_branch}:${REPLY}
  >     fi
  >     echo $r_branch
  > }

  $ hg init
  $ hg branch branch -q
  $ get_branch_like_zsh
  branch
  $ hg topic topic -q
  $ get_branch_like_zsh
  branch:topic
  $ hg topic --clear -q
  $ get_branch_like_zsh
  branch
