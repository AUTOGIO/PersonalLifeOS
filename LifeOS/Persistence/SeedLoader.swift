import Foundation
import SwiftData

/// Loads bundled real data (tide table, daily plans) and a sensible default
/// weekly schedule + sample content on first launch. Idempotent: guarded by counts.
enum SeedLoader {

    struct TideSeed: Codable {
        let port_name: String
        let date: String
        let time: String
        let height_m: Double
        let tide_type: String
        let source: String
        let timezone: String
    }

    struct PlanSeed: Codable {
        let date: String
        let morning_intention: String
        let evening_review: String
        let mood_score: Int?
        let energy_score: Int?
    }

    @MainActor
    static func seedIfNeeded(_ context: ModelContext) {
        seedTides(context)
        seedDailyPlans(context)
        seedWeeklySchedule(context)
        seedSampleContent(context)
        try? context.save()
    }

    private static func dayFormatter() -> DateFormatter {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.timeZone = TimeZone(identifier: "America/Fortaleza")
        return f
    }

    @MainActor
    private static func seedTides(_ context: ModelContext) {
        let existing = (try? context.fetchCount(FetchDescriptor<TideEvent>())) ?? 0
        guard existing == 0 else { return }
        guard let url = Bundle.main.url(forResource: "tides", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let seeds = try? JSONDecoder().decode([TideSeed].self, from: data) else { return }
        let df = dayFormatter()
        for s in seeds {
            guard let day = df.date(from: s.date) else { continue }
            let t = timeOfDay(s.time, on: day)
            let ev = TideEvent(portName: s.port_name, date: day, time: t, heightM: s.height_m,
                               tideType: TideType(rawValue: s.tide_type) ?? .unknown,
                               source: s.source, timezone: s.timezone)
            context.insert(ev)
        }
    }

    @MainActor
    private static func seedDailyPlans(_ context: ModelContext) {
        let existing = (try? context.fetchCount(FetchDescriptor<DailyPlan>())) ?? 0
        guard existing == 0 else { return }
        guard let url = Bundle.main.url(forResource: "daily_plans", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let seeds = try? JSONDecoder().decode([PlanSeed].self, from: data) else { return }
        let df = dayFormatter()
        for s in seeds {
            guard let day = df.date(from: s.date) else { continue }
            let p = DailyPlan(date: day, morningIntention: s.morning_intention,
                              eveningReview: s.evening_review,
                              moodScore: s.mood_score, energyScore: s.energy_score)
            context.insert(p)
        }
    }

    @MainActor
    private static func seedWeeklySchedule(_ context: ModelContext) {
        let existing = (try? context.fetchCount(FetchDescriptor<ScheduleBlock>())) ?? 0
        guard existing == 0 else { return }
        // Default weekly template derived from the Life OS planner blocks.
        // (day, activity, start, end, category, isAnchor)
        let template: [(Weekday, String, String, String, ScheduleCategory, Bool)] = [
            (.mon, "Deep Work — Core OS", "09:00", "11:00", .core, false),
            (.mon, "Gym", "12:00", "13:00", .physical, false),
            (.mon, "AI Dev — macOS Native", "14:00", "16:30", .macos, false),
            (.mon, "Muay Thai", "18:30", "20:00", .physical, true),
            (.tue, "Business Data", "09:00", "11:30", .business, false),
            (.tue, "Tools & Scripts", "14:00", "16:00", .tools, false),
            (.tue, "Muay Thai", "18:30", "20:00", .physical, true),
            (.wed, "Deep Work — Core OS", "09:00", "11:00", .core, false),
            (.wed, "Gym", "12:00", "13:00", .physical, false),
            (.wed, "AI Dev — macOS Native", "14:00", "16:30", .macos, false),
            (.thu, "Business Data", "09:00", "11:30", .business, false),
            (.thu, "Muay Thai", "18:30", "20:00", .physical, true),
            (.fri, "Tools & Scripts", "09:00", "11:00", .tools, false),
            (.fri, "Review & Admin", "15:00", "16:30", .meta, false),
            (.sat, "Kitesurf (wind permitting)", "10:00", "12:00", .physical, false),
            (.sat, "Recovery / Rest", "16:00", "18:00", .recovery, false),
            (.sun, "Planning & Review", "10:00", "11:30", .meta, false),
            (.sun, "Recovery / Rest", "16:00", "18:00", .recovery, false),
        ]
        for (i, row) in template.enumerated() {
            let b = ScheduleBlock(dayOfWeek: row.0, activity: row.1,
                                  startTime: timeOfDay(row.2), endTime: timeOfDay(row.3),
                                  category: row.4, isAnchor: row.5, displayOrder: i)
            context.insert(b)
        }
    }

    @MainActor
    private static func seedSampleContent(_ context: ModelContext) {
        // Only seed sample projects/activities/habits if entirely empty so the
        // dashboard isn't blank on first run. User data is never overwritten.
        let projCount = (try? context.fetchCount(FetchDescriptor<AIProject>())) ?? 0
        if projCount == 0 {
            let projects: [(String, ProjectCategory, ProjectPriority, String?)] = [
                ("FOKS Terminal", .macosNative, .high, "https://github.com/AUTOGIO/FOKS_BLOOMBERG"),
                ("FulôFiló Analytics", .businessData, .high, "https://github.com/AUTOGIO/fulofilo-analytics"),
                ("System Organizer", .macosNative, .medium, "https://github.com/AUTOGIO/System_Org"),
                ("Life OS", .coreOS, .high, "https://github.com/AUTOGIO/PersonalLifeOS"),
                ("Claude Skills OS", .toolsScripts, .medium, "https://github.com/AUTOGIO/claude-skills-os"),
            ]
            for p in projects {
                context.insert(AIProject(name: p.0, category: p.1, priority: p.2, githubRepo: p.3))
            }
        }

        let habitCount = (try? context.fetchCount(FetchDescriptor<Habit>())) ?? 0
        if habitCount == 0 {
            context.insert(Habit(name: "Muay Thai", detail: "Train discipline", frequency: .weekly,
                                  targetDays: ["MON","TUE","THU"]))
            context.insert(Habit(name: "Gym", detail: "Strength", frequency: .weekly,
                                  targetDays: ["MON","WED"]))
            context.insert(Habit(name: "Morning Intention", detail: "Set the day", frequency: .daily))
            context.insert(Habit(name: "Evening Review", detail: "Close the day", frequency: .daily))
        }

        let actCount = (try? context.fetchCount(FetchDescriptor<Activity>())) ?? 0
        if actCount == 0 {
            let today = Date()
            context.insert(Activity(name: "Deep Work — Core OS", category: .aiDevCore,
                                    scheduledDate: today, startTime: timeOfDay("09:00"),
                                    endTime: timeOfDay("11:00"), status: .done))
            context.insert(Activity(name: "Gym", category: .gym, scheduledDate: today,
                                    startTime: timeOfDay("12:00"), endTime: timeOfDay("13:00"),
                                    status: .done))
            context.insert(Activity(name: "AI Dev — macOS Native", category: .aiDevMacos,
                                    scheduledDate: today, startTime: timeOfDay("14:00"),
                                    endTime: timeOfDay("16:30"), status: .inProgress))
            context.insert(Activity(name: "Muay Thai", category: .muayThai, scheduledDate: today,
                                    startTime: timeOfDay("18:30"), endTime: timeOfDay("20:00"),
                                    status: .planned))
        }
    }
}
