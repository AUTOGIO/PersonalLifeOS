import SwiftUI
import SwiftData

struct DashboardView: View {
    @Environment(\.modelContext) private var context
    @EnvironmentObject private var persistence: PersistenceAlerts
    @Query private var activities: [Activity]
    @Query private var kiteSessions: [KiteSession]
    @Query private var sessions: [ProjectSession]
    @Query private var tides: [TideEvent]
    @Query(sort: \DailyPlan.date, order: .reverse) private var plans: [DailyPlan]

    @State private var showingPlanEditor = false

    private var today: Date { Date().startOfDay }

    private var todayActivities: [Activity] {
        activities.filter { $0.scheduledDate.startOfDay == today }
            .sorted { ($0.startTime ?? .distantPast) < ($1.startTime ?? .distantPast) }
    }
    private var gymThisWeek: Int {
        let ws = Date().weekStart
        return activities.filter { $0.category == .gym && $0.scheduledDate >= ws && $0.status == .done }.count
    }
    private var muayThaiMonth: Int {
        let ms = Date().monthStart
        return activities.filter { $0.category == .muayThai && $0.scheduledDate >= ms && $0.status == .done }.count
    }
    private var aiHoursToday: Double {
        let mins = sessions.filter { $0.startTime.isAppToday }
            .compactMap { $0.durationMinutes }.reduce(0, +)
        return (Double(mins) / 60 * 10).rounded() / 10
    }
    private var kiteMonth: Int {
        let ms = Date().monthStart
        return kiteSessions.filter { $0.date >= ms }.count
    }
    private var activeSession: ProjectSession? { sessions.first { $0.endTime == nil } }
    private var todayTides: [TideEvent] {
        tides.filter { $0.date.startOfDay == today }.sorted { $0.time < $1.time }
    }
    private var todayPlan: DailyPlan? { plans.first { $0.date.startOfDay == today } }

    private let cols = [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12),
                        GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                LazyVGrid(columns: cols, spacing: 12) {
                    KPITile(label: "Gym this week", value: "\(gymThisWeek)", unit: "done", accent: ActivityCategory.gym.color)
                    KPITile(label: "Muay Thai (month)", value: "\(muayThaiMonth)", unit: "done", accent: ActivityCategory.muayThai.color)
                    KPITile(label: "AI hours today", value: aiHoursToday.trimmedHours, unit: "h", accent: TerminalTheme.cyan)
                    KPITile(label: "Kite (month)", value: "\(kiteMonth)", unit: "sessions", accent: ActivityCategory.kitesurfing.color)
                }

                HStack(alignment: .top, spacing: 12) {
                    SectionPanel(title: "Today's Timeline", accent: TerminalTheme.amber,
                                 subtitle: "\(todayActivities.count) blocks") {
                        if todayActivities.isEmpty {
                            EmptyHint(text: "No activities scheduled for today.")
                        } else {
                            VStack(spacing: 6) {
                                ForEach(todayActivities) { a in
                                    HStack(spacing: 10) {
                                        Rectangle().fill(a.category.color).frame(width: 3, height: 26)
                                        VStack(alignment: .leading, spacing: 1) {
                                            Text(a.name)
                                                .font(TerminalTheme.mono(size: 12, weight: .medium))
                                                .foregroundStyle(TerminalTheme.textPrimary)
                                            Text(timeRange(a))
                                                .font(TerminalTheme.mono(size: 10, weight: .regular))
                                                .foregroundStyle(TerminalTheme.textSecondary)
                                        }
                                        Spacer()
                                        TagPill(text: a.status.label, color: a.status.color)
                                    }
                                    .padding(.vertical, 3)
                                }
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)

                    SectionPanel(title: "Tide · Porto de Cabedelo", accent: TerminalTheme.cyan,
                                 subtitle: today.dayLabel()) {
                        if todayTides.isEmpty {
                            EmptyHint(text: "No tide data for today.")
                        } else {
                            VStack(spacing: 6) {
                                ForEach(todayTides) { t in
                                    HStack {
                                        Image(systemName: t.tideType.symbol)
                                            .foregroundStyle(t.tideType.color)
                                            .frame(width: 16)
                                        Text(t.tideType.label)
                                            .font(TerminalTheme.mono(size: 12, weight: .medium))
                                            .foregroundStyle(TerminalTheme.textPrimary)
                                        Spacer()
                                        Text(t.timeString)
                                            .font(TerminalTheme.mono(size: 12, weight: .regular))
                                            .foregroundStyle(TerminalTheme.textSecondary)
                                        Text(String(format: "%.2f m", t.heightM))
                                            .font(TerminalTheme.mono(size: 12, weight: .semibold))
                                            .foregroundStyle(t.tideType.color)
                                            .frame(width: 64, alignment: .trailing)
                                    }
                                    .padding(.vertical, 2)
                                }
                            }
                        }
                    }
                    .frame(width: 360)
                }

                HStack(alignment: .top, spacing: 12) {
                    SectionPanel(title: "Focus Session", accent: TerminalTheme.green) {
                        if let s = activeSession {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(s.project?.name ?? "Untitled")
                                    .font(TerminalTheme.mono(size: 14, weight: .bold))
                                    .foregroundStyle(TerminalTheme.green)
                                Text("Running since \(s.startTime.timeLabel())")
                                    .font(TerminalTheme.mono(size: 11, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                        } else {
                            EmptyHint(text: "No active focus session. Start one in AI Projects.")
                        }
                    }
                    .frame(maxWidth: .infinity)

                    SectionPanel(title: "Daily Plan", accent: TerminalTheme.amber) {
                        VStack(alignment: .leading, spacing: 6) {
                            labeled("Intention", todayPlan?.morningIntention)
                            labeled("Review", todayPlan?.eveningReview)
                            HStack(spacing: 18) {
                                scoreView("Mood", todayPlan?.moodScore)
                                scoreView("Energy", todayPlan?.energyScore)
                            }
                            Button {
                                showingPlanEditor = true
                            } label: {
                                Label(todayPlan == nil ? "Create today's plan" : "Edit today's plan",
                                      systemImage: "square.and.pencil")
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                            .padding(.top, 4)
                        }
                    }
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(16)
        }
        .sheet(isPresented: $showingPlanEditor) {
            DailyPlanEditor(existing: todayPlan, day: today)
        }
    }

    private func timeRange(_ a: Activity) -> String {
        guard let s = a.startTime else { return "—" }
        let e = a.endTime
        return e == nil ? s.timeLabel() : "\(s.timeLabel())–\(e!.timeLabel())"
    }

    private func labeled(_ label: String, _ value: String?) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label.uppercased())
                .font(TerminalTheme.mono(size: 9, weight: .semibold))
                .foregroundStyle(TerminalTheme.textSecondary)
            Text((value?.isEmpty == false ? value! : "—"))
                .font(TerminalTheme.mono(size: 11, weight: .regular))
                .foregroundStyle(TerminalTheme.textPrimary)
                .lineLimit(2)
        }
    }
    private func scoreView(_ label: String, _ value: Int?) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label.uppercased())
                .font(TerminalTheme.mono(size: 9, weight: .semibold))
                .foregroundStyle(TerminalTheme.textSecondary)
            Text(value != nil ? "\(value!) / 10" : "—")
                .font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.cyan)
        }
    }
}

struct DailyPlanEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var persistence: PersistenceAlerts

    let existing: DailyPlan?
    let day: Date

    @State private var intention = ""
    @State private var review = ""
    @State private var mood: Double = 5
    @State private var energy: Double = 5
    @State private var hasMood = false
    @State private var hasEnergy = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("TODAY'S PLAN")
                .font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)
            Text(day.dayLabel())
                .font(TerminalTheme.mono(size: 11, weight: .regular))
                .foregroundStyle(TerminalTheme.textSecondary)
            Form {
                TextField("Morning intention", text: $intention, axis: .vertical).lineLimit(2...4)
                TextField("Evening review", text: $review, axis: .vertical).lineLimit(2...4)
                Toggle("Set mood score", isOn: $hasMood)
                if hasMood {
                    HStack {
                        Text("Mood")
                        Slider(value: $mood, in: 1...10, step: 1)
                        Text("\(Int(mood))")
                    }
                }
                Toggle("Set energy score", isOn: $hasEnergy)
                if hasEnergy {
                    HStack {
                        Text("Energy")
                        Slider(value: $energy, in: 1...10, step: 1)
                        Text("\(Int(energy))")
                    }
                }
            }
            .formStyle(.grouped)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") { save() }.buttonStyle(.borderedProminent)
            }
        }
        .padding(18)
        .frame(width: 440)
        .onAppear { load() }
    }

    private func load() {
        guard let p = existing else { return }
        intention = p.morningIntention
        review = p.eveningReview
        if let m = p.moodScore { mood = Double(m); hasMood = true }
        if let e = p.energyScore { energy = Double(e); hasEnergy = true }
    }

    private func save() {
        let moodScore = hasMood ? Int(mood) : nil
        let energyScore = hasEnergy ? Int(energy) : nil
        if let p = existing {
            p.morningIntention = intention
            p.eveningReview = review
            p.moodScore = moodScore
            p.energyScore = energyScore
        } else {
            context.insert(DailyPlan(date: day, morningIntention: intention, eveningReview: review,
                                     moodScore: moodScore, energyScore: energyScore))
        }
        persistence.save(context)
        if persistence.errorMessage == nil { dismiss() }
    }
}
