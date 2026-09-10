#!/bin/sh
osascript <<'EOF'
tell application "iTerm"
  activate
  if (count of windows) = 0 then
    create window with default profile
  else
    tell current window to create tab with default profile
  end if
end tell
EOF
