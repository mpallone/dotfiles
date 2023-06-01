
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

export PATH=$PATH:/opt/homebrew/bin

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

# This function opens github in the browser.
#
# If the current directory is a git repo, then it will open that repo.
# Otherwise, it'll look for a fallback URL on the command line. If that
# fallback URL is present, it will open it. Otherwise, it'll just open
# github.com 
open_github() {
    if git status &>/dev/null; then
        # Current directory is a git repo. Open it in browser.
        # (Piping to xargs just trims whitespace characters)
        open "https://"`git remote show origin | grep "Fetch URL" | xargs | sed -e 's/Fetch URL://' | sed -e 's/git@//' | sed -e 's/com:/com\//' | sed -e 's/.git//' | xargs`
    else
        # We're not in a git repo
        if [ -z "$1" ]; then
            # Fallback URL is not on the command line
            open "https://github.com"
        else
            open $1 
        fi
    fi
}
alias gh="open_github"
alias ghm="open_github https://github.com/mpallone"


# Example usage: 
# 
#     mpallone@MPALL1ML1 ~ $ lpass ls | grep 'discipline.pds sjc val'
#     Shared-PenaltyDetermination/discipline.pds sjc val RSO client id & basic auth [id: 3299371871728735068]
# 
#     mpallone@MPALL1ML1 ~ $ basic_auth_from_lastpass 3299371871728735068
# 
#     <basic auth string is now copied to clipboard> 
# 
basic_auth_from_lastpass() {
    username=$(lpass show $1 --username)
    password=$(lpass show $1 --password)
    echo "Basic $(echo -n $username:$password | base64)" | pbcopy
}

export LPASS_AGENT_TIMEOUT=57600 # 57600 seconds = 16 hours

# Usage:
# 
#     githistory app.yaml
# 
#     <prints git history of file> 
# 
githistory() {
    git lg -p -- $1
}
alias githist="githistory"

decode_base64_url() {
  local len=$((${#1} % 4))
  local result="$1"
  if [ $len -eq 2 ]; then result="$1"'=='
  elif [ $len -eq 3 ]; then result="$1"'=' 
  fi
  echo "$result" | tr '_-' '/+' | openssl enc -d -base64
}

# Example usage: 
# 
#    decode_jwt 2 $pbToken
# 
# if pbToken holds a base-64 encoded JWT, this will pretty print it.
# 
decode_jwt(){
   decode_base64_url $(echo -n $2 | cut -d "." -f $1) | jq .
}

# Decode JWT header
alias jwth="decode_jwt 1"

# Decode JWT Payload
alias jwtp="decode_jwt 2"
