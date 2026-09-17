#!/bin/sh
osascript <<'EOF'
if application "Google Chrome" is running then
  tell application "Google Chrome"
    if (count of windows) = 0 then
      make new window
    else
      make new tab at end of tabs of front window
      set active tab index of front window to (count of tabs of front window)
    end if
    activate
  end tell
else
  tell application "Google Chrome" to activate
end if
EOF
