
#!/bin/bash
#
# Set up my environment, for all of my Unix devices.
#

# All of my unix config files are in the same directory as this script:
DIRNAME_OF_THIS_SCRIPT=`dirname $BASH_SOURCE`

# Git configuration, from Udacity
source ${DIRNAME_OF_THIS_SCRIPT}/bash_profile_udacity_git

# Add my scripts to my path
PATH=${DIRNAME_OF_THIS_SCRIPT}/../scripts:${PATH}

alias emacs='emacs -nw'

alias cdbudg='cd /Users/mpallone/Dropbox/Documents/money/budget-project'
alias budg='cdbudg && python budget.py && python reports.py && git commit -a -m "budget.py update"'
alias rep='cdbudg && python reports.py'
alias evalbudg='cdbudg && ./evaluate-savings.py && cat savings-tracking.csv && git commit -a -m "evaluate-savings.py update" && echo ""'

alias docs='cd ~/Dropbox/Documents'
alias doc='docs'

alias cdpw='cd ~/Documents/src/repos/personal-website/'

alias subl='/Applications/Sublime\ Text.app/Contents/SharedSupport/bin/subl'

# Add nand2tetris to path
export PATH=$PATH:~/Dropbox/documents/nand2tetris/nand2tetris/tools

# Rust, from https://doc.rust-lang.org/book/ch01-01-installation.html
export PATH="$HOME/.cargo/bin:$PATH"

export HISTSIZE=100000
export HISTFILESIZE=100000
export HISTTIMEFORMAT="%d/%m/%y %T "

# mpallone@MPALL1ML1 ~ $ sudo lsof -i :3306 | grep mysqld
# mysqld  122 _mysql   28u  IPv6 0xc4c9ed30b87b1785      0t0  TCP *:mysql (LISTEN)
#         ^^^
#         |
#         Essentially, grab that pid and kill it 
mac_kill_mysqld() {
	mysqld_pid=$(sudo lsof -i :3306 | grep mysqld | tr -s ' ' | cut -d ' ' -f 2)
	sudo kill ${mysqld_pid}
}

alias cpgitbranch="git rev-parse --abbrev-ref HEAD | perl -pe 'chomp' | pbcopy"

# Capture packets between docker containers
alias dockerpcap="docker run --rm --net=host -v $PWD/tcpdump:/tcpdump kaazing/tcpdump"

mcp() {
    open https://markcpallone.atlassian.net/browse/MCP-$1
}
