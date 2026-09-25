#!/bin/sh
osascript <<'EOF'
tell application "Safari"
  if (count of windows) = 0 then
    make new document
  else
    tell front window
      set current tab to (make new tab)
    end tell
  end if
  activate
end tell
EOF
