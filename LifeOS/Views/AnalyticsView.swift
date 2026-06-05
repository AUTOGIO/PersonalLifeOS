import SwiftUI
import SwiftData
import Charts

struct AnalyticsView: View {
    @Query private var activities: [Activity]
    @Query private var sessions: [ProjectSession]
    @Query private var kiteSessions: [KiteSession]
    @Query private var habits: [Habit]
    @Query(sort: \DailyPlan.date) private var plans: [DailyPlan]

    // AI hours by sub-category (DONE activities)
    private var aiByCategory: [(String, Double)] {
        let cats: [ActivityCategory] = [.aiDevCore, .aiDevBusiness, .aiDevMacos, .aiDevTools]
        return cats.map { c in
            let mins = activities.filter { $0.category == c && $0.status == .done }
                .compactMap { $0.durationMinutes }.reduce(0, +)
            return (c.label, (Double(mins) / 60 * 10).rounded() / 10)
        }
    }
    // Monthly counts by category
    private var monthlyByCategory: [(String, Int, Color)] {
        let ms = Date().monthStart
        var dict: [ActivityCategory: Int] = [:]
        for a in activities where a.scheduledDate >= ms { dict[a.category, default: 0] += 1 }
        return dict.sorted { $0.value > $1.value }.map { ($0.key.label, $0.value, $0.key.color) }
    }
    // AI dev hours last 7 days
    private var weeklyAI: [(String, Double)] {
        (0..<7).reversed().map { i in
            let d = Date().adding(days: -i).startOfDay
            let mins = activities.filter { $0.category.isAIDev && $0.scheduledDate.startOfDay == d && $0.status == .done }
                .compactMap { $0.durationMinutes }.reduce(0, +)
            return (d.dayLabel(), (Double(mins) / 60 * 10).rounded() / 10)
        }
    }
    private var moodSeries: [(Date, Int, Int)] {
        let cutoff = Date().adding(days: -29).startOfDay
        return plans.filter { $0.date >= cutoff }.map { ($0.date, $0.moodScore ?? 0, $0.energyScore ?? 0) }
    }

    private let twoCol = [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)]

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                LazyVGrid(columns: twoCol, spacing: 12) {
                    SectionPanel(title: "AI Dev hours by area", accent: TerminalTheme.cyan) {
                        let maxV = aiByCategory.map { $0.1 }.max() ?? 1
                        VStack(spacing: 8) {
                            ForEach(aiByCategory, id: \.0) { item in
                                BarRow(label: item.0, value: item.1, maxValue: maxV,
                                       color: TerminalTheme.cyan, valueText: "\(item.1.trimmedHours)h")
                            }
                        }
                    }

                    SectionPanel(title: "AI Dev hours · last 7 days", accent: TerminalTheme.amber) {
                        Chart(weeklyAI, id: \.0) { item in
                            BarMark(x: .value("Day", item.0), y: .value("Hours", item.1))
                                .foregroundStyle(TerminalTheme.amber)
                        }
                        .frame(height: 160)
                        .chartForegroundStyleScale(range: [TerminalTheme.amber])
                    }
                }

                LazyVGrid(columns: twoCol, spacing: 12) {
                    SectionPanel(title: "This month by category", accent: TerminalTheme.green) {
                        if monthlyByCategory.isEmpty {
                            EmptyHint(text: "No activities this month.")
                        } else {
                            let maxV = Double(monthlyByCategory.map { $0.1 }.max() ?? 1)
                            VStack(spacing: 8) {
                                ForEach(monthlyByCategory, id: \.0) { item in
                                    BarRow(label: item.0, value: Double(item.1), maxValue: maxV,
                                           color: item.2, valueText: "\(item.1)")
                                }
                            }
                        }
                    }

                    SectionPanel(title: "Mood & Energy · 30 days", accent: TerminalTheme.cyan) {
                        if moodSeries.isEmpty {
                            EmptyHint(text: "No daily plans logged yet.")
                        } else {
                            Chart {
                                ForEach(moodSeries, id: \.0) { item in
                                    LineMark(x: .value("Date", item.0), y: .value("Mood", item.1),
                                             series: .value("Series", "Mood"))
                                        .foregroundStyle(TerminalTheme.cyan)
                                    LineMark(x: .value("Date", item.0), y: .value("Energy", item.2),
                                             series: .value("Series", "Energy"))
                                        .foregroundStyle(TerminalTheme.amber)
                                }
                            }
                            .chartYScale(domain: 0...10)
                            .frame(height: 160)
                            HStack(spacing: 16) {
                                legendDot(TerminalTheme.cyan, "Mood")
                                legendDot(TerminalTheme.amber, "Energy")
                            }
                        }
                    }
                }

                LazyVGrid(columns: twoCol, spacing: 12) {
                    SectionPanel(title: "Habit streaks", accent: TerminalTheme.amber) {
                        if habits.isEmpty { EmptyHint(text: "No habits yet.") }
                        let maxV = Double(habits.map { $0.streakCount }.max() ?? 1)
                        VStack(spacing: 8) {
                            ForEach(habits) { h in
                                BarRow(label: h.name, value: Double(h.streakCount), maxValue: max(maxV, 1),
                                       color: TerminalTheme.green, valueText: "\(h.streakCount)d")
                            }
                        }
                    }

                    SectionPanel(title: "Kite wind distribution", accent: ActivityCategory.kitesurfing.color) {
                        if kiteSessions.isEmpty {
                            EmptyHint(text: "No kite sessions logged.")
                        } else {
                            Chart(kiteSessions) { s in
                                PointMark(x: .value("Date", s.date),
                                          y: .value("Wind", s.windSpeedKnots ?? 0))
                                    .foregroundStyle(ActivityCategory.kitesurfing.color)
                            }
                            .frame(height: 160)
                        }
                    }
                }
            }
            .padding(16)
        }
    }

    private func legendDot(_ color: Color, _ label: String) -> some View {
        HStack(spacing: 5) {
            Circle().fill(color).frame(width: 9, height: 9)
            Text(label).font(TerminalTheme.mono(size: 10, weight: .regular)).foregroundStyle(TerminalTheme.textSecondary)
        }
    }
}
