import SwiftUI
import SwiftData

struct HabitsView: View {
    @Environment(\.modelContext) private var context
    @EnvironmentObject private var persistence: PersistenceAlerts
    @Query private var habits: [Habit]
    @State private var showingAdd = false
    @State private var pendingDelete: Habit? = nil

    private let last7: [Date] = (0..<7).reversed().map { Date().adding(days: -$0).startOfDay }

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text("HABITS").font(TerminalTheme.mono(size: 14, weight: .bold))
                    .foregroundStyle(TerminalTheme.amber)
                Spacer()
                Button { showingAdd = true } label: { Label("Add", systemImage: "plus") }
                    .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal, 16).padding(.top, 14)

            ScrollView {
                VStack(spacing: 8) {
                    if habits.isEmpty { EmptyHint(text: "No habits yet.") }
                    ForEach(habits) { h in
                        SectionPanel(title: h.name, accent: TerminalTheme.green,
                                     subtitle: h.frequency.label) {
                            HStack(spacing: 14) {
                                HStack(spacing: 4) {
                                    Image(systemName: "flame.fill").foregroundStyle(TerminalTheme.amber)
                                    Text("\(h.streakCount) day streak")
                                        .font(TerminalTheme.mono(size: 12, weight: .bold))
                                        .foregroundStyle(TerminalTheme.amber)
                                }
                                Spacer()
                                ForEach(last7, id: \.self) { day in
                                    Button { h.toggle(on: day); persistence.save(context) } label: {
                                        VStack(spacing: 2) {
                                            Circle()
                                                .fill(h.isDone(on: day) ? TerminalTheme.green : TerminalTheme.panelAlt)
                                                .overlay(Circle().stroke(TerminalTheme.border, lineWidth: 1))
                                                .frame(width: 18, height: 18)
                                            Text(shortDay(day))
                                                .font(TerminalTheme.mono(size: 8, weight: .regular))
                                                .foregroundStyle(TerminalTheme.textSecondary)
                                        }
                                    }.buttonStyle(.plain)
                                }
                                Button { pendingDelete = h } label: {
                                    Image(systemName: "trash").foregroundStyle(TerminalTheme.red)
                                }.buttonStyle(.plain).padding(.leading, 6)
                            }
                            if !h.detail.isEmpty {
                                Text(h.detail)
                                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                            if !h.targetDays.isEmpty {
                                Text("Target: \(h.targetDays.joined(separator: " "))")
                                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 16)
            }
        }
        .sheet(isPresented: $showingAdd) { HabitEditor() }
        .confirmationDialog(
            "Delete habit?",
            isPresented: Binding(
                get: { pendingDelete != nil },
                set: { if !$0 { pendingDelete = nil } }
            ),
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                if let h = pendingDelete {
                    context.delete(h)
                    persistence.save(context)
                }
                pendingDelete = nil
            }
            Button("Cancel", role: .cancel) { pendingDelete = nil }
        } message: {
            Text(pendingDelete.map { "Remove \($0.name) and its completion history." } ?? "")
        }
    }

    private func shortDay(_ d: Date) -> String {
        let f = DateFormatter()
        f.calendar = AppCalendar.calendar
        f.timeZone = AppCalendar.timeZone
        f.dateFormat = "EEEEE"
        return f.string(from: d)
    }
}

struct HabitEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var persistence: PersistenceAlerts
    @State private var name = ""
    @State private var detail = ""
    @State private var frequency: HabitFrequency = .daily
    @State private var days: Set<Weekday> = []

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("NEW HABIT").font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)
            Form {
                TextField("Name", text: $name)
                TextField("Description", text: $detail)
                Picker("Frequency", selection: $frequency) { ForEach(HabitFrequency.allCases) { Text($0.label).tag($0) } }
                if frequency != .daily {
                    HStack {
                        ForEach(Weekday.allCases) { d in
                            Button(d.short) {
                                if days.contains(d) { days.remove(d) } else { days.insert(d) }
                            }
                            .buttonStyle(.bordered)
                            .tint(days.contains(d) ? TerminalTheme.green : nil)
                        }
                    }
                }
            }.formStyle(.grouped)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") {
                    let td = Weekday.allCases.filter { days.contains($0) }.map { $0.rawValue }
                    context.insert(Habit(name: name, detail: detail, frequency: frequency, targetDays: td))
                    persistence.save(context)
                    if persistence.errorMessage == nil { dismiss() }
                }.buttonStyle(.borderedProminent).disabled(name.isEmpty)
            }
        }
        .padding(18).frame(width: 460)
    }
}
