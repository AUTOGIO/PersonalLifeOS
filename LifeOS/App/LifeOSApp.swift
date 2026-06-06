import SwiftUI
import SwiftData

@main
struct LifeOSApp: App {
    let container: ModelContainer

    init() {
        do {
            let schema = Schema([
                Activity.self, AIProject.self, ProjectSession.self, DailyPlan.self,
                Habit.self, KiteSession.self, ScheduleBlock.self, TideEvent.self,
            ])
            let config = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)
            container = try ModelContainer(for: schema, configurations: [config])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .frame(minWidth: 1180, minHeight: 760)
                .preferredColorScheme(.dark)
        }
        .modelContainer(container)
        .windowStyle(.titleBar)
        .windowResizability(.contentSize)
    }
}
