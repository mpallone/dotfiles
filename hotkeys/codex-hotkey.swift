import AppKit
import Carbon

private let hotkeyID = EventHotKeyID(signature: 0x43445848, id: 1)
private var keyIsDown = false

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

/// Handle only our registered F18 event; a held key creates one session per press.
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
          receivedID.signature == hotkeyID.signature,
          receivedID.id == hotkeyID.id else {
        return OSStatus(eventNotHandledErr)
    }
    switch GetEventKind(event) {
    case UInt32(kEventHotKeyPressed):
        if !keyIsDown {
            keyIsDown = true
            launchCodex()
        }
    case UInt32(kEventHotKeyReleased):
        keyIsDown = false
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
var hotkey: EventHotKeyRef?
let registrationStatus = RegisterEventHotKey(
    UInt32(kVK_F18), 0, hotkeyID, GetEventDispatcherTarget(), 0, &hotkey
)
guard registrationStatus == noErr else {
    log("could not register F18 (status \(registrationStatus)); another app may own it")
    exit(1)
}
log("registered systemwide F18")
application.run()
