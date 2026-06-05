import SwiftUI
import SwiftData
import UniformTypeIdentifiers

struct ActivitiesView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \Activity.scheduledDate, order: .reverse) private var activities: [Activity]

    @State private var filterCategory: ActivityCategory? = nil
    @State private var filterStatus: ActivityStatus? = nil
    @State private var editing: Activity? = nil
    @State private var showingAdd = false

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
                                    Button(s.label) { a.status = s; try? context.save() }
                                }
                            } label: { TagPill(text: a.status.label, color: a.status.color) }
                                .menuStyle(.borderlessButton).fixedSize()
                            Button { editing = a } label: { Image(systemName: "pencil") }.buttonStyle(.plain)
                            Button { context.delete(a); try? context.save() } label: {
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
    }

    private func timeRange(_ a: Activity) -> String {
        guard let s = a.startTime else { return "—" }
        return a.endTime == nil ? s.timeLabel() : "\(s.timeLabel())–\(a.endTime!.timeLabel())"
    }

    private func exportCSV() {
        var rows = ["name,category,date,start,end,duration_min,status,notes"]
        let df = DateFormatter(); df.dateFormat = "yyyy-MM-dd"
        for a in filtered {
            let start = a.startTime?.timeLabel() ?? ""
            let end = a.endTime?.timeLabel() ?? ""
            let notes = a.notes.replacingOccurrences(of: ",", with: ";").replacingOccurrences(of: "\n", with: " ")
            rows.append("\(a.name),\(a.category.label),\(df.string(from: a.scheduledDate)),\(start),\(end),\(a.durationMinutes ?? 0),\(a.status.label),\(notes)")
        }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "activities.csv"
        panel.allowedContentTypes = [.commaSeparatedText]
        if panel.runModal() == .OK, let url = panel.url {
            try? rows.joined(separator: "\n").write(to: url, atomically: true, encoding: .utf8)
        }
    }
}

struct ActivityEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
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
        try? context.save()
        dismiss()
    }
}
