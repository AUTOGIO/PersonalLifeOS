import SwiftUI

@main
struct LifeOSApp: App {
    var body: some Scene {
        WindowGroup {
            TerminalRootView()
                .frame(minWidth: 1280, minHeight: 800)
        }
        .windowStyle(.titleBar)
        .windowResizability(.contentSize)
    }
}
