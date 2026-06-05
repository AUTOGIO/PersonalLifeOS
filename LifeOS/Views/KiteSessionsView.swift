import SwiftUI
import SwiftData

struct KiteSessionsView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \KiteSession.date, order: .reverse) private var sessions: [KiteSession]
    @Query private var tides: [TideEvent]
    @State private var showingAdd = false

    private var monthCount: Int { sessions.filter { $0.date >= Date().monthStart }.count }
    private var totalHours: Double {
        Double(sessions.map { $0.durationMinutes }.reduce(0, +)) / 60
    }
    private var avgWind: Double {
        let winds = sessions.compactMap { $0.windSpeedKnots }
        return winds.isEmpty ? 0 : winds.reduce(0, +) / Double(winds.count)
    }

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text("KITE SESSIONS · CABEDELO").font(TerminalTheme.mono(size: 14, weight: .bold))
                    .foregroundStyle(TerminalTheme.amber)
                Spacer()
                Button { showingAdd = true } label: { Label("Log session", systemImage: "plus") }
                    .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal, 16).padding(.top, 14)

            HStack(spacing: 12) {
                KPITile(label: "This month", value: "\(monthCount)", unit: "sessions", accent: ActivityCategory.kitesurfing.color)
                KPITile(label: "Total time", value: totalHours.trimmedHours, unit: "h", accent: TerminalTheme.cyan)
                KPITile(label: "Avg wind", value: String(format: "%.0f", avgWind), unit: "kn", accent: TerminalTheme.amber)
            }
            .padding(.horizontal, 16)

            ScrollView {
                VStack(spacing: 6) {
                    if sessions.isEmpty { EmptyHint(text: "No kite sessions logged yet.") }
                    ForEach(sessions) { s in
                        HStack(spacing: 10) {
                            Image(systemName: "wind").foregroundStyle(ActivityCategory.kitesurfing.color).frame(width: 18)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(s.date.dayLabel())
                                    .font(TerminalTheme.mono(size: 12, weight: .medium))
                                    .foregroundStyle(TerminalTheme.textPrimary)
                                Text(s.location)
                                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                            Spacer()
                            if let w = s.windSpeedKnots {
                                Text("\(Int(w)) kn")
                                    .font(TerminalTheme.mono(size: 12, weight: .semibold))
                                    .foregroundStyle(TerminalTheme.cyan)
                            }
                            Text("\(s.durationMinutes)m")
                                .font(TerminalTheme.mono(size: 12, weight: .regular))
                                .foregroundStyle(TerminalTheme.textSecondary)
                            Button { context.delete(s); try? context.save() } label: {
                                Image(systemName: "trash").foregroundStyle(TerminalTheme.red)
                            }.buttonStyle(.plain)
                        }
                        .padding(10)
                        .background(TerminalTheme.panel)
                        .overlay(RoundedRectangle(cornerRadius: 5).stroke(TerminalTheme.border, lineWidth: 1))
                        .clipShape(RoundedRectangle(cornerRadius: 5))
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 16)
            }
        }
        .sheet(isPresented: $showingAdd) { KiteEditor() }
    }
}

struct KiteEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @State private var date = Date()
    @State private var location = "Cabedelo, PB"
    @State private var wind = 18.0
    @State private var duration = 90
    @State private var notes = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("LOG KITE SESSION").font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)
            Form {
                DatePicker("Date", selection: $date, displayedComponents: .date)
                TextField("Location", text: $location)
                HStack { Text("Wind (kn)"); Slider(value: $wind, in: 0...45, step: 1); Text("\(Int(wind))") }
                Stepper("Duration: \(duration) min", value: $duration, in: 15...480, step: 15)
                TextField("Notes", text: $notes, axis: .vertical).lineLimit(2...3)
            }.formStyle(.grouped)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") {
                    context.insert(KiteSession(date: date, location: location,
                                               windSpeedKnots: wind, durationMinutes: duration, notes: notes))
                    try? context.save(); dismiss()
                }.buttonStyle(.borderedProminent)
            }
        }
        .padding(18).frame(width: 420)
    }
}
