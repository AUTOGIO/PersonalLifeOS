import Foundation
import SwiftData
import SwiftUI

// MARK: - Enums (mirror Django choices)

enum ActivityCategory: String, Codable, CaseIterable, Identifiable {
    case muayThai = "MUAY_THAI"
    case gym = "GYM"
    case dogTraining = "DOG_TRAINING"
    case kitesurfing = "KITESURFING"
    case aiDevCore = "AI_DEV_CORE"
    case aiDevBusiness = "AI_DEV_BUSINESS"
    case aiDevMacos = "AI_DEV_MACOS"
    case aiDevTools = "AI_DEV_TOOLS"
    case sleep = "SLEEP"
    case custom = "CUSTOM"

    var id: String { rawValue }

    var label: String {
        switch self {
        case .muayThai: return "Muay Thai"
        case .gym: return "Gym"
        case .dogTraining: return "Dog Training"
        case .kitesurfing: return "Kitesurfing"
        case .aiDevCore: return "AI Dev Core"
        case .aiDevBusiness: return "AI Dev Business"
        case .aiDevMacos: return "AI Dev macOS"
        case .aiDevTools: return "AI Dev Tools"
        case .sleep: return "Sleep"
        case .custom: return "Custom"
        }
    }

    var color: Color {
        switch self {
        case .muayThai: return Color(hex: 0xdc2626)
        case .gym: return Color(hex: 0xf97316)
        case .dogTraining: return Color(hex: 0x22c55e)
        case .kitesurfing: return Color(hex: 0x22c55e)
        case .aiDevCore: return Color(hex: 0x2563eb)
        case .aiDevBusiness: return Color(hex: 0xeab308)
        case .aiDevMacos: return Color(hex: 0x3b82f6)
        case .aiDevTools: return Color(hex: 0xec4899)
        case .sleep: return Color(hex: 0x1f2937)
        case .custom: return Color(hex: 0xa855f7)
        }
    }

    var isAIDev: Bool { rawValue.hasPrefix("AI_DEV") }
}

enum ActivityStatus: String, Codable, CaseIterable, Identifiable {
    case planned = "PLANNED"
    case inProgress = "IN_PROGRESS"
    case done = "DONE"
    case skipped = "SKIPPED"
    case rescheduled = "RESCHEDULED"

    var id: String { rawValue }
    var label: String {
        switch self {
        case .planned: return "Planned"
        case .inProgress: return "In Progress"
        case .done: return "Done"
        case .skipped: return "Skipped"
        case .rescheduled: return "Rescheduled"
        }
    }
    var color: Color {
        switch self {
        case .planned: return TerminalTheme.textSecondary
        case .inProgress: return TerminalTheme.cyan
        case .done: return Color(hex: 0x22c55e)
        case .skipped: return Color(hex: 0xef4444)
        case .rescheduled: return TerminalTheme.amber
        }
    }
}

enum ProjectCategory: String, Codable, CaseIterable, Identifiable {
    case coreOS = "CORE_OS"
    case businessData = "BUSINESS_DATA"
    case macosNative = "MACOS_NATIVE"
    case toolsScripts = "TOOLS_SCRIPTS"
    var id: String { rawValue }
    var label: String {
        switch self {
        case .coreOS: return "Core OS"
        case .businessData: return "Business Data"
        case .macosNative: return "macOS Native"
        case .toolsScripts: return "Tools & Scripts"
        }
    }
}

enum ProjectPriority: String, Codable, CaseIterable, Identifiable {
    case high = "HIGH", medium = "MEDIUM", low = "LOW"
    var id: String { rawValue }
    var label: String { rawValue.capitalized }
    var sortRank: Int { self == .high ? 0 : (self == .medium ? 1 : 2) }
}

enum ProjectStatus: String, Codable, CaseIterable, Identifiable {
    case active = "ACTIVE", paused = "PAUSED", completed = "COMPLETED"
    var id: String { rawValue }
    var label: String { rawValue.capitalized }
}

enum HabitFrequency: String, Codable, CaseIterable, Identifiable {
    case daily = "DAILY", weekly = "WEEKLY", custom = "CUSTOM"
    var id: String { rawValue }
    var label: String { rawValue.capitalized }
}

enum Weekday: String, Codable, CaseIterable, Identifiable {
    case mon = "MON", tue = "TUE", wed = "WED", thu = "THU", fri = "FRI", sat = "SAT", sun = "SUN"
    var id: String { rawValue }
    var label: String {
        ["MON":"Monday","TUE":"Tuesday","WED":"Wednesday","THU":"Thursday",
         "FRI":"Friday","SAT":"Saturday","SUN":"Sunday"][rawValue] ?? rawValue
    }
    var short: String { String(rawValue.prefix(3)).capitalized }
    /// 1=Mon ... 7=Sun (ISO-ish ordering used for display)
    var order: Int { Self.allCases.firstIndex(of: self).map { $0 + 1 } ?? 0 }

    static func from(date: Date) -> Weekday {
        // Calendar weekday: 1=Sun..7=Sat
        let wd = Calendar.current.component(.weekday, from: date)
        switch wd {
        case 1: return .sun
        case 2: return .mon
        case 3: return .tue
        case 4: return .wed
        case 5: return .thu
        case 6: return .fri
        default: return .sat
        }
    }
}

enum ScheduleCategory: String, Codable, CaseIterable, Identifiable {
    case core = "Core", macos = "macOS", business = "Business",
         tools = "Tools", physical = "Physical", meta = "Meta", recovery = "Recovery"
    var id: String { rawValue }
    var label: String {
        switch self {
        case .core: return "AI Dev — Core OS"
        case .macos: return "AI Dev — macOS Native"
        case .business: return "AI Dev — Business Data"
        case .tools: return "AI Dev — Tools/Scripts"
        case .physical: return "Physical"
        case .meta: return "Meta / Admin"
        case .recovery: return "Recovery"
        }
    }
    var color: Color {
        switch self {
        case .core: return Color(hex: 0x7c3aed)
        case .macos: return Color(hex: 0x3b82f6)
        case .business: return Color(hex: 0xf59e0b)
        case .tools: return Color(hex: 0xec4899)
        case .physical: return Color(hex: 0xdc2626)
        case .meta: return Color(hex: 0x6b7280)
        case .recovery: return Color(hex: 0x22c55e)
        }
    }
    var sfSymbol: String {
        switch self {
        case .core: return "brain"
        case .macos: return "apple.logo"
        case .business: return "chart.line.uptrend.xyaxis"
        case .tools: return "wrench.and.screwdriver"
        case .physical: return "figure.boxing"
        case .meta: return "list.clipboard"
        case .recovery: return "bed.double"
        }
    }
}

enum TideType: String, Codable, CaseIterable, Identifiable {
    case high = "HIGH", low = "LOW", unknown = "UNKNOWN"
    var id: String { rawValue }
    var label: String {
        switch self {
        case .high: return "High Tide"
        case .low: return "Low Tide"
        case .unknown: return "Unknown"
        }
    }
    var symbol: String { self == .high ? "arrow.up" : (self == .low ? "arrow.down" : "minus") }
    var color: Color { self == .high ? TerminalTheme.cyan : TerminalTheme.amber }
}

// MARK: - SwiftData Models

@Model
final class Activity {
    var name: String
    var categoryRaw: String
    var scheduledDate: Date
    var startTime: Date?
    var endTime: Date?
    var durationMinutes: Int?
    var statusRaw: String
    var notes: String
    var createdAt: Date

    init(name: String, category: ActivityCategory, scheduledDate: Date,
         startTime: Date? = nil, endTime: Date? = nil, status: ActivityStatus = .planned,
         notes: String = "") {
        self.name = name
        self.categoryRaw = category.rawValue
        self.scheduledDate = scheduledDate
        self.startTime = startTime
        self.endTime = endTime
        self.statusRaw = status.rawValue
        self.notes = notes
        self.createdAt = Date()
        self.durationMinutes = Activity.computeDuration(startTime, endTime)
    }

    var category: ActivityCategory {
        get { ActivityCategory(rawValue: categoryRaw) ?? .custom }
        set { categoryRaw = newValue.rawValue }
    }
    var status: ActivityStatus {
        get { ActivityStatus(rawValue: statusRaw) ?? .planned }
        set { statusRaw = newValue.rawValue }
    }

    static func computeDuration(_ start: Date?, _ end: Date?) -> Int? {
        guard let s = start, let e = end, e > s else { return nil }
        return Int(e.timeIntervalSince(s) / 60)
    }

    func refreshDuration() { durationMinutes = Activity.computeDuration(startTime, endTime) }
}

@Model
final class AIProject {
    var name: String
    var categoryRaw: String
    var priorityRaw: String
    var statusRaw: String
    var githubRepo: String?
    @Relationship(deleteRule: .cascade, inverse: \ProjectSession.project)
    var sessions: [ProjectSession] = []

    init(name: String, category: ProjectCategory, priority: ProjectPriority = .medium,
         status: ProjectStatus = .active, githubRepo: String? = nil) {
        self.name = name
        self.categoryRaw = category.rawValue
        self.priorityRaw = priority.rawValue
        self.statusRaw = status.rawValue
        self.githubRepo = githubRepo
    }

    var category: ProjectCategory { get { ProjectCategory(rawValue: categoryRaw) ?? .coreOS } set { categoryRaw = newValue.rawValue } }
    var priority: ProjectPriority { get { ProjectPriority(rawValue: priorityRaw) ?? .medium } set { priorityRaw = newValue.rawValue } }
    var status: ProjectStatus { get { ProjectStatus(rawValue: statusRaw) ?? .active } set { statusRaw = newValue.rawValue } }

    var totalHours: Double {
        let mins = sessions.compactMap { $0.durationMinutes }.reduce(0, +)
        return (Double(mins) / 60.0 * 10).rounded() / 10
    }
}

@Model
final class ProjectSession {
    var project: AIProject?
    var startTime: Date
    var endTime: Date?
    var durationMinutes: Int?
    var notes: String

    init(project: AIProject?, startTime: Date = Date(), endTime: Date? = nil, notes: String = "") {
        self.project = project
        self.startTime = startTime
        self.endTime = endTime
        self.notes = notes
        self.durationMinutes = Activity.computeDuration(startTime, endTime)
    }
    func stop(at date: Date = Date()) {
        endTime = date
        durationMinutes = Activity.computeDuration(startTime, date)
    }
}

@Model
final class DailyPlan {
    @Attribute(.unique) var date: Date
    var morningIntention: String
    var eveningReview: String
    var moodScore: Int?
    var energyScore: Int?
    var createdAt: Date

    init(date: Date, morningIntention: String = "", eveningReview: String = "",
         moodScore: Int? = nil, energyScore: Int? = nil) {
        self.date = date.startOfDay
        self.morningIntention = morningIntention
        self.eveningReview = eveningReview
        self.moodScore = moodScore
        self.energyScore = energyScore
        self.createdAt = Date()
    }
}

@Model
final class Habit {
    var name: String
    var detail: String
    var frequencyRaw: String
    var targetDays: [String]
    var streakCount: Int
    var isActive: Bool
    /// ISO date strings the habit was completed (yyyy-MM-dd)
    var completedDates: [String]

    init(name: String, detail: String = "", frequency: HabitFrequency = .daily,
         targetDays: [String] = [], streakCount: Int = 0, isActive: Bool = true) {
        self.name = name
        self.detail = detail
        self.frequencyRaw = frequency.rawValue
        self.targetDays = targetDays
        self.streakCount = streakCount
        self.isActive = isActive
        self.completedDates = []
    }
    var frequency: HabitFrequency { get { HabitFrequency(rawValue: frequencyRaw) ?? .daily } set { frequencyRaw = newValue.rawValue } }

    func isDone(on date: Date) -> Bool { completedDates.contains(date.isoDay) }
    func toggle(on date: Date) {
        let key = date.isoDay
        if let idx = completedDates.firstIndex(of: key) { completedDates.remove(at: idx) }
        else { completedDates.append(key) }
        recomputeStreak()
    }
    func recomputeStreak() {
        var streak = 0
        var day = Date().startOfDay
        let set = Set(completedDates)
        while set.contains(day.isoDay) {
            streak += 1
            day = Calendar.current.date(byAdding: .day, value: -1, to: day)!
        }
        streakCount = streak
    }
}

@Model
final class KiteSession {
    var date: Date
    var location: String
    var windSpeedKnots: Double?
    var durationMinutes: Int
    var notes: String

    init(date: Date, location: String = "Cabedelo, PB", windSpeedKnots: Double? = nil,
         durationMinutes: Int, notes: String = "") {
        self.date = date.startOfDay
        self.location = location
        self.windSpeedKnots = windSpeedKnots
        self.durationMinutes = durationMinutes
        self.notes = notes
    }
}

@Model
final class ScheduleBlock {
    var dayOfWeekRaw: String
    var activity: String
    var startTime: Date
    var endTime: Date
    var durationMin: Int
    var categoryRaw: String
    var isAnchor: Bool
    var isActive: Bool
    var notes: String
    var displayOrder: Int

    init(dayOfWeek: Weekday, activity: String, startTime: Date, endTime: Date,
         category: ScheduleCategory, isAnchor: Bool = false, isActive: Bool = true,
         notes: String = "", displayOrder: Int = 0) {
        self.dayOfWeekRaw = dayOfWeek.rawValue
        self.activity = activity
        self.startTime = startTime
        self.endTime = endTime
        self.durationMin = max(0, Int(endTime.timeIntervalSince(startTime) / 60))
        self.categoryRaw = category.rawValue
        self.isAnchor = isAnchor
        self.isActive = isActive
        self.notes = notes
        self.displayOrder = displayOrder
    }
    var dayOfWeek: Weekday { get { Weekday(rawValue: dayOfWeekRaw) ?? .mon } set { dayOfWeekRaw = newValue.rawValue } }
    var category: ScheduleCategory { get { ScheduleCategory(rawValue: categoryRaw) ?? .meta } set { categoryRaw = newValue.rawValue } }
    var durationDisplay: String {
        let h = durationMin / 60, m = durationMin % 60
        if h > 0 && m > 0 { return "\(h)h \(m)min" }
        if h > 0 { return "\(h)h" }
        return "\(m)min"
    }
}

@Model
final class TideEvent {
    var portName: String
    var date: Date
    var time: Date
    var heightM: Double
    var tideTypeRaw: String
    var source: String
    var timezone: String

    init(portName: String, date: Date, time: Date, heightM: Double,
         tideType: TideType, source: String, timezone: String) {
        self.portName = portName
        self.date = date.startOfDay
        self.time = time
        self.heightM = heightM
        self.tideTypeRaw = tideType.rawValue
        self.source = source
        self.timezone = timezone
    }
    var tideType: TideType { get { TideType(rawValue: tideTypeRaw) ?? .unknown } set { tideTypeRaw = newValue.rawValue } }
    var timeString: String {
        let f = DateFormatter(); f.dateFormat = "HH:mm"; return f.string(from: time)
    }
}
