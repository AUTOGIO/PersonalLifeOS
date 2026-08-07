import SwiftUI
import SwiftData
import AppKit
import UniformTypeIdentifiers

struct ActivitiesView: View {
    @Environment(\.modelContext) private var context
    @EnvironmentObject private var persistence: PersistenceAlerts
    @Query(sort: \Activity.scheduledDate, order: .reverse) private var activities: [Activity]

    @State private var filterCategory: ActivityCategory? = nil
    @State private var filterStatus: ActivityStatus? = nil
    @State private var editing: Activity? = nil
    @State private var showingAdd = false
    @State private var pendingDelete: Activity? = nil

    private var filtered: [Activity] {
        activities.filter { a in
            (filterCategory == nil || a.category == filterCategory) &&
            (filterStatus == nil || a.status == filterStatus)
        }
    }

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 10) {
                Text("ACTIVITIES")
                    .font(TerminalTheme.mono(size: 14, weight: .bold))
                    .foregroundStyle(TerminalTheme.amber)
                Spacer()
                Picker("", selection: $filterCategory) {
                    Text("All categories").tag(ActivityCategory?.none)
                    ForEach(ActivityCategory.allCases) { c in Text(c.label).tag(ActivityCategory?.some(c)) }
                }.frame(width: 170)
                Picker("", selection: $filterStatus) {
                    Text("All statuses").tag(ActivityStatus?.none)
                    ForEach(ActivityStatus.allCases) { s in Text(s.label).tag(ActivityStatus?.some(s)) }
                }.frame(width: 150)
                Button { exportCSV() } label: { Label("CSV", systemImage: "square.and.arrow.up") }
                Button { showingAdd = true } label: { Label("Add", systemImage: "plus") }
                    .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal, 16).padding(.top, 14)

            ScrollView {
                VStack(spacing: 6) {
                    if filtered.isEmpty {
                        EmptyHint(text: "No activities match the current filter.")
                    }
                    ForEach(filtered) { a in
                        HStack(spacing: 10) {
                            Rectangle().fill(a.category.color).frame(width: 3, height: 34)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(a.name)
                                    .font(TerminalTheme.mono(size: 13, weight: .medium))
                                    .foregroundStyle(TerminalTheme.textPrimary)
                                Text("\(a.scheduledDate.dayLabel()) · \(timeRange(a)) · \(a.category.label)")
                                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                            Spacer()
                            if let d = a.durationMinutes {
                                Text("\(d)m")
                                    .font(TerminalTheme.mono(size: 11, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                            Menu {
                                ForEach(ActivityStatus.allCases) { s in
                                    Button(s.label) { a.status = s; persistence.save(context) }
                                }
                            } label: { TagPill(text: a.status.label, color: a.status.color) }
                                .menuStyle(.borderlessButton).fixedSize()
                            Button { editing = a } label: { Image(systemName: "pencil") }.buttonStyle(.plain)
                            Button { pendingDelete = a } label: {
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
        .sheet(isPresented: $showingAdd) { ActivityEditor(activity: nil) }
        .sheet(item: $editing) { a in ActivityEditor(activity: a) }
        .confirmationDialog(
            "Delete activity?",
            isPresented: Binding(
                get: { pendingDelete != nil },
                set: { if !$0 { pendingDelete = nil } }
            ),
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                if let a = pendingDelete {
                    context.delete(a)
                    persistence.save(context)
                }
                pendingDelete = nil
            }
            Button("Cancel", role: .cancel) { pendingDelete = nil }
        } message: {
            Text(pendingDelete.map { "Remove \($0.name) permanently." } ?? "")
        }
    }

    private func timeRange(_ a: Activity) -> String {
        guard let s = a.startTime else { return "—" }
        return a.endTime == nil ? s.timeLabel() : "\(s.timeLabel())–\(a.endTime!.timeLabel())"
    }

    private func exportCSV() {
        var rows = [CSV.row(["name", "category", "date", "start", "end", "duration_min", "status", "notes"])]
        let df = AppCalendar.dayFormatter
        for a in filtered {
            let start = a.startTime?.timeLabel() ?? ""
            let end = a.endTime?.timeLabel() ?? ""
            rows.append(CSV.row([
                a.name,
                a.category.label,
                df.string(from: a.scheduledDate),
                start,
                end,
                "\(a.durationMinutes ?? 0)",
                a.status.label,
                a.notes,
            ]))
        }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "activities.csv"
        panel.allowedContentTypes = [.commaSeparatedText]
        if panel.runModal() == .OK, let url = panel.url {
            do {
                try rows.joined(separator: "\n").write(to: url, atomically: true, encoding: .utf8)
            } catch {
                persistence.errorMessage = "Could not write CSV: \(error.localizedDescription)"
            }
        }
    }
}

struct ActivityEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var persistence: PersistenceAlerts
    let activity: Activity?

    @State private var name = ""
    @State private var category: ActivityCategory = .custom
    @State private var date = Date()
    @State private var start = timeOfDay("09:00")
    @State private var end = timeOfDay("10:00")
    @State private var status: ActivityStatus = .planned
    @State private var notes = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(activity == nil ? "NEW ACTIVITY" : "EDIT ACTIVITY")
                .font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)
            Form {
                TextField("Name", text: $name)
                Picker("Category", selection: $category) {
                    ForEach(ActivityCategory.allCases) { c in Text(c.label).tag(c) }
                }
                DatePicker("Date", selection: $date, displayedComponents: .date)
                DatePicker("Start", selection: $start, displayedComponents: .hourAndMinute)
                DatePicker("End", selection: $end, displayedComponents: .hourAndMinute)
                Picker("Status", selection: $status) {
                    ForEach(ActivityStatus.allCases) { s in Text(s.label).tag(s) }
                }
                TextField("Notes", text: $notes, axis: .vertical).lineLimit(2...4)
            }
            .formStyle(.grouped)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") { save() }.buttonStyle(.borderedProminent).disabled(name.isEmpty)
            }
        }
        .padding(18)
        .frame(width: 420)
        .onAppear { load() }
    }

    private func load() {
        guard let a = activity else { return }
        name = a.name; category = a.category; date = a.scheduledDate
        start = a.startTime ?? start; end = a.endTime ?? end
        status = a.status; notes = a.notes
    }
    private func save() {
        if let a = activity {
            a.name = name; a.category = category; a.scheduledDate = date
            a.startTime = start; a.endTime = end; a.status = status; a.notes = notes
            a.refreshDuration()
        } else {
            let a = Activity(name: name, category: category, scheduledDate: date,
                             startTime: start, endTime: end, status: status, notes: notes)
            context.insert(a)
        }
        persistence.save(context)
        if persistence.errorMessage == nil { dismiss() }
    }
}
