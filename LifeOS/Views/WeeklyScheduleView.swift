import SwiftUI
import SwiftData

struct WeeklyScheduleView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: [SortDescriptor(\ScheduleBlock.displayOrder)]) private var blocks: [ScheduleBlock]
    @State private var showingAdd = false

    private func blocks(for day: Weekday) -> [ScheduleBlock] {
        blocks.filter { $0.dayOfWeek == day && $0.isActive }
            .sorted { $0.startTime < $1.startTime }
    }

    private let cols = Array(repeating: GridItem(.flexible(), spacing: 8), count: 7)

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text("WEEKLY SCHEDULE").font(TerminalTheme.mono(size: 14, weight: .bold))
                    .foregroundStyle(TerminalTheme.amber)
                Spacer()
                Button { showingAdd = true } label: { Label("Add block", systemImage: "plus") }
                    .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal, 16).padding(.top, 14)

            ScrollView {
                LazyVGrid(columns: cols, alignment: .leading, spacing: 8) {
                    ForEach(Weekday.allCases) { day in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(day.short.uppercased())
                                .font(TerminalTheme.mono(size: 11, weight: .bold))
                                .foregroundStyle(TerminalTheme.cyan)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.bottom, 2)
                                .overlay(Rectangle().frame(height: 1).foregroundStyle(TerminalTheme.border), alignment: .bottom)
                            ForEach(blocks(for: day)) { b in
                                VStack(alignment: .leading, spacing: 2) {
                                    HStack(spacing: 4) {
                                        Image(systemName: b.category.sfSymbol).font(.system(size: 8))
                                            .foregroundStyle(b.category.color)
                                        if b.isAnchor {
                                            Image(systemName: "pin.fill").font(.system(size: 7))
                                                .foregroundStyle(TerminalTheme.amber)
                                        }
                                    }
                                    Text(b.activity)
                                        .font(TerminalTheme.mono(size: 9, weight: .medium))
                                        .foregroundStyle(TerminalTheme.textPrimary).lineLimit(2)
                                    Text("\(b.startTime.timeLabel())–\(b.endTime.timeLabel())")
                                        .font(TerminalTheme.mono(size: 8, weight: .regular))
                                        .foregroundStyle(TerminalTheme.textSecondary)
                                }
                                .padding(6)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(b.category.color.opacity(0.14))
                                .overlay(RoundedRectangle(cornerRadius: 4).stroke(b.category.color.opacity(0.4), lineWidth: 1))
                                .clipShape(RoundedRectangle(cornerRadius: 4))
                                .contextMenu {
                                    Button("Delete", role: .destructive) { context.delete(b); try? context.save() }
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 8)

                // Legend
                SectionPanel(title: "Legend", accent: TerminalTheme.textSecondary) {
                    let cats = ScheduleCategory.allCases
                    let legendCols = Array(repeating: GridItem(.flexible(), alignment: .leading), count: 4)
                    LazyVGrid(columns: legendCols, alignment: .leading, spacing: 6) {
                        ForEach(cats) { c in
                            HStack(spacing: 6) {
                                Image(systemName: c.sfSymbol).font(.system(size: 10)).foregroundStyle(c.color).frame(width: 16)
                                Text(c.label).font(TerminalTheme.mono(size: 10, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textPrimary).lineLimit(1)
                            }
                        }
                        HStack(spacing: 6) {
                            Image(systemName: "pin.fill").font(.system(size: 9)).foregroundStyle(TerminalTheme.amber).frame(width: 16)
                            Text("Anchor block").font(TerminalTheme.mono(size: 10, weight: .regular))
                                .foregroundStyle(TerminalTheme.textPrimary)
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 16)
            }
        }
        .sheet(isPresented: $showingAdd) { ScheduleBlockEditor() }
    }
}

struct ScheduleBlockEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @State private var day: Weekday = .mon
    @State private var activity = ""
    @State private var start = timeOfDay("09:00")
    @State private var end = timeOfDay("10:00")
    @State private var category: ScheduleCategory = .core
    @State private var isAnchor = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("NEW SCHEDULE BLOCK").font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)
            Form {
                Picker("Day", selection: $day) { ForEach(Weekday.allCases) { Text($0.label).tag($0) } }
                TextField("Activity", text: $activity)
                DatePicker("Start", selection: $start, displayedComponents: .hourAndMinute)
                DatePicker("End", selection: $end, displayedComponents: .hourAndMinute)
                Picker("Category", selection: $category) { ForEach(ScheduleCategory.allCases) { Text($0.label).tag($0) } }
                Toggle("Anchor (immovable)", isOn: $isAnchor)
            }.formStyle(.grouped)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") {
                    context.insert(ScheduleBlock(dayOfWeek: day, activity: activity, startTime: start,
                                                 endTime: end, category: category, isAnchor: isAnchor))
                    try? context.save(); dismiss()
                }.buttonStyle(.borderedProminent).disabled(activity.isEmpty)
            }
        }
        .padding(18).frame(width: 440)
    }
}
