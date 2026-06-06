import SwiftUI

enum NavigationSection: String, CaseIterable, Identifiable {
    case dashboard = "Dashboard"
    case schedule = "Weekly Schedule"
    case activities = "Activities"
    case projects = "AI Projects"
    case habits = "Habits"
    case kite = "Kite Sessions"
    case tides = "Tides"
    case analytics = "Analytics"

    var id: String { rawValue }
    var icon: String {
        switch self {
        case .dashboard: return "square.grid.2x2"
        case .schedule: return "calendar"
        case .activities: return "checklist"
        case .projects: return "hammer"
        case .habits: return "flame"
        case .kite: return "wind"
        case .tides: return "water.waves"
        case .analytics: return "chart.bar.xaxis"
        }
    }
}

@MainActor
final class MainViewModel: ObservableObject {
    @Published var selection: NavigationSection = .dashboard
    @Published var quote: String = AppData.randomQuote()

    func refreshQuote() { quote = AppData.randomQuote() }
}
