# Restore the Fun-layer system actions

The Model 100's Fun key selects a keyboard layer. It originally sent F1,
F2, and so on; Karabiner translated those keys into Mac system actions.
This setup stores the native media/system signals in the keyboard itself.
The existing [hotkey helper](../hotkeys/README.md) handles F3, F4, and F18.

| Combination | Action | Implementation |
|---|---|---|
| Fun+1 | Brightness down | Native consumer key |
| Fun+2 | Brightness up | Native consumer key |
| Fun+3 | Mission Control | F3 → helper |
| Fun+4 | Spotlight | F4 → helper |
| Fun+5 | Dictation | Native voice-command key, matching Karabiner's dictation alias |
| Fun+6 | Do Not Disturb | Native system-control key |
| Fun+7 | Rewind/previous | Native consumer key |
| Fun+8 | Play/pause | Native consumer key |
| Fun+9 | Fast-forward/next | Native consumer key |
| Fun+0 | Mute | Native consumer key |
| Fun+top-right key (F11) | Volume down | Native consumer key |
| Fun+N | Volume down | Existing native binding, preserved |
| Fun+M | Volume up | Existing native binding, preserved |

Media apps determine the rewind/fast-forward behavior. Dictation follows
the Mac's existing Dictation configuration and microphone permissions.
These are the same HID (Human Interface Device) usages used by
[Karabiner's default function-key mapping](https://github.com/pqrs-org/Karabiner-Elements/blob/main/src/share/core_configuration/details/profile.hpp#L94).

## Inspect, apply, or reverse the keyboard patch

Connect the Model 100 and close Chrysalis so its configuration port is free.
From this repository's root:

```sh
python3 keyboardio/function_keys.py
python3 keyboardio/function_keys.py --apply
bash hotkeys/install.sh
```

The first command only prints the proposed patch. The second updates the
stored Fun layer and reads back the entire keymap to verify it. No firmware
flash is needed. The settings remain on the keyboard after unplugging it
or changing computers. The Python script uses only the standard library.

This keyboard uses its stored custom map (`keymap.onlyCustom = 1`); the
script stops if that mode or the compiled Model 100 layout differs.
The patch touches only layer 2 slots whose compiled defaults are F keys
and whose current values are still that F key or the expected native
action. Existing custom mappings are preserved. On this keyboard, nine
slots changed and all other 503 entries stayed identical. In particular,
the compiled F12 slot is currently Home (Fun+=), so it is left as Home.
The butterfly and Fun+3/Fun+4 mappings remain F18, F3, and F4.

To put these native-action slots back on their original F keys:

```sh
python3 keyboardio/function_keys.py --restore-fkeys
```

If several USB serial devices are connected, pass the Model 100 port with
`--port /dev/cu.usbmodem...`. A failed write/readback triggers an attempt
to restore the map read before the write. Both the update and rollback
are verified against the complete map.

## Verify the restored actions

Play music, press Fun+8 to pause it, then press it again to resume. Check
Fun+1/Fun+2 for brightness and Fun+0 for mute. Fun+7/Fun+9 should control
the active media player. Fun+N lowers volume and Fun+M raises it. The patch
preserves the custom Home key instead of replacing it with F12.

Check Fun+3 for Mission Control, Fun+4 for Spotlight, and butterfly for a
fresh Codex session. For Spotlight, enable **Codex Hotkey** in **System
Settings → Privacy & Security → Accessibility** when requested; the helper
sends the Spotlight keyboard shortcut configured in macOS. Restart the
helper after granting that permission, following the
[permission and restart steps](../hotkeys/README.md#install-and-verify-the-helper).

## Encoding and configuration protocol

Consumer usages are encoded as `0x4800 | usage`; system-control usages use
`0x4100 | usage`. For example, play/pause is consumer usage `0xCD`, so Fun+8
stores `0x48CD`. The keyboard then sends a native play/pause signal instead
of F8, allowing macOS to handle the media control and key holding normally.

The read/write protocol is implemented by Keyboardio's
[EEPROM keymap plugin](https://github.com/keyboardio/Kaleidoscope/blob/master/plugins/Kaleidoscope-EEPROM-Keymap/src/kaleidoscope/plugin/EEPROM-Keymap.cpp#L108).
The [consumer](https://github.com/keyboardio/KeyboardioHID/blob/master/src/MultiReport/ConsumerControl.cpp)
and [system-control](https://github.com/keyboardio/KeyboardioHID/blob/master/src/MultiReport/SystemControl.cpp)
USB reports support the restored usages.
