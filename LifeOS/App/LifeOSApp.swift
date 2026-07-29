import SwiftUI
import SwiftData

@main
struct LifeOSApp: App {
    let container: ModelContainer
    /// True when the on-disk store failed and the app fell back to an in-memory container.
    let storeRecoveryMode: Bool

    init() {
        let schema = Schema([
            Activity.self, AIProject.self, ProjectSession.self, DailyPlan.self,
            Habit.self, KiteSession.self, ScheduleBlock.self, TideEvent.self,
        ])
        do {
            let config = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)
            container = try ModelContainer(for: schema, configurations: [config])
            storeRecoveryMode = false
        } catch {
            #if DEBUG
            print("Could not create on-disk ModelContainer: \(error). Using in-memory store.")
            #endif
            do {
                let config = ModelConfiguration(schema: schema, isStoredInMemoryOnly: true)
                container = try ModelContainer(for: schema, configurations: [config])
                storeRecoveryMode = true
            } catch {
                // Last resort — should be extremely rare for an in-memory container.
                fatalError("Could not create ModelContainer (in-memory fallback also failed): \(error)")
            }
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView(storeRecoveryMode: storeRecoveryMode)
                .frame(minWidth: 1180, minHeight: 760)
                .preferredColorScheme(.dark)
        }
        .modelContainer(container)
        .windowStyle(.titleBar)
        .windowResizability(.contentSize)
    }
}
