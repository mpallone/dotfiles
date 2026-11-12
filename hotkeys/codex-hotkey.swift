import AppKit
import Carbon

private let hotkeySignature: OSType = 0x43445848
private enum HotkeyAction: UInt32 {
    case codex = 1
    case missionControl = 2
    case spotlight = 3
}
private var heldKeys = Set<UInt32>()

private func log(_ message: String) {
    FileHandle.standardError.write(Data("Codex Hotkey: \(message)\n".utf8))
}

/// Start the shared launcher asynchronously so its startup wait cannot block key events.
/// For example, pressing F18 in Chrome launches the same command as the Quick Action.
private func launchCodex() {
    let launcher = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent(".local/bin/new-codex-session")
    let process = Process()
    process.executableURL = launcher
    process.standardInput = FileHandle.nullDevice
    process.standardOutput = FileHandle.standardOutput
    process.standardError = FileHandle.standardError
    process.terminationHandler = { process in
        if process.terminationStatus != 0 {
            log("launcher exited with status \(process.terminationStatus)")
        }
    }
    do {
        try process.run()
        log("launched new Codex session")
    } catch {
        log("could not start \(launcher.path): \(error.localizedDescription)")
    }
}

/// Open macOS's window overview, as when pressing Fun+3 from Chrome.
private func openMissionControl() {
    let application = URL(fileURLWithPath: "/System/Applications/Mission Control.app")
    if NSWorkspace.shared.open(application) {
        log("opened Mission Control")
    } else {
        log("could not open \(application.path)")
    }
}

/// Invoke macOS's configured Spotlight shortcut; launching its app alone shows no UI.
private func openSpotlight() {
    guard CGPreflightPostEventAccess() else {
        CGRequestPostEventAccess()
        log("Spotlight needs Codex Hotkey enabled in Privacy & Security > Accessibility")
        return
    }
    let settings = UserDefaults(suiteName: "com.apple.symbolichotkeys")?
        .dictionary(forKey: "AppleSymbolicHotKeys")
    let shortcut = settings?["64"] as? [String: Any]
    if shortcut?["enabled"] as? Bool == false {
        log("Spotlight's keyboard shortcut is disabled in macOS Keyboard Shortcuts")
        return
    }
    let value = shortcut?["value"] as? [String: Any]
    let parameters = value?["parameters"] as? [NSNumber]
    let keyCode = parameters.flatMap { $0.count >= 3 ? $0[1].uint16Value : nil }
        ?? UInt16(kVK_Space)
    let modifiers = parameters.flatMap { $0.count >= 3 ? $0[2].uint64Value : nil }
        ?? CGEventFlags.maskCommand.rawValue
    for pressed in [true, false] {
        guard let event = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: pressed) else {
            log("could not create Spotlight shortcut event")
            return
        }
        event.flags = CGEventFlags(rawValue: modifiers)
        event.post(tap: .cghidEventTap)
    }
    log("invoked Spotlight shortcut")
}

/// Dispatch registered keys once per press; each key tracks its own release.
private func handleHotkey(
    _: EventHandlerCallRef?, event: EventRef?, _: UnsafeMutableRawPointer?
) -> OSStatus {
    guard let event = event else { return OSStatus(eventNotHandledErr) }
    var receivedID = EventHotKeyID()
    let status = GetEventParameter(
        event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID),
        nil, MemoryLayout<EventHotKeyID>.size, nil, &receivedID
    )
    guard status == noErr,
          receivedID.signature == hotkeySignature,
          let action = HotkeyAction(rawValue: receivedID.id) else {
        return OSStatus(eventNotHandledErr)
    }
    switch GetEventKind(event) {
    case UInt32(kEventHotKeyPressed):
        if heldKeys.insert(receivedID.id).inserted {
            switch action {
            case .codex:
                launchCodex()
            case .missionControl:
                openMissionControl()
            case .spotlight:
                openSpotlight()
            }
        }
    case UInt32(kEventHotKeyReleased):
        heldKeys.remove(receivedID.id)
    default:
        return OSStatus(eventNotHandledErr)
    }
    return noErr
}

let application = NSApplication.shared
application.setActivationPolicy(.accessory)
var events = [
    EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed)),
    EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyReleased))
]
var handler: EventHandlerRef?
let handlerStatus = InstallEventHandler(
    GetEventDispatcherTarget(), handleHotkey, events.count, &events, nil, &handler
)
guard handlerStatus == noErr else {
    log("could not install hotkey handler (status \(handlerStatus))")
    exit(1)
}
private let bindings: [(code: UInt32, action: HotkeyAction, name: String)] = [
    (UInt32(kVK_F18), .codex, "F18 (Codex)"),
    (UInt32(kVK_F3), .missionControl, "F3 (Mission Control)"),
    (UInt32(kVK_F4), .spotlight, "F4 (Spotlight)")
]
var hotkeys = [EventHotKeyRef]()
for binding in bindings {
    var hotkey: EventHotKeyRef?
    let identifier = EventHotKeyID(signature: hotkeySignature, id: binding.action.rawValue)
    let status = RegisterEventHotKey(
        binding.code, 0, identifier, GetEventDispatcherTarget(), 0, &hotkey
    )
    guard status == noErr, let hotkey = hotkey else {
        log("could not register \(binding.name) (status \(status)); another app may own it")
        // A conflicting system action must not disable the Codex key.
        if binding.action == .codex { exit(1) }
        continue
    }
    hotkeys.append(hotkey)
    log("registered systemwide \(binding.name)")
}
application.run()
