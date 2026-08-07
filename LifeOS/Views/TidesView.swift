import SwiftUI
import SwiftData

struct TidesView: View {
    @Query private var tides: [TideEvent]
    @State private var selectedDate = Date()

    private var dayTides: [TideEvent] {
        tides.filter { $0.date.startOfDay == selectedDate.startOfDay }
            .sorted { $0.time < $1.time }
    }
    private var weekTides: [(Date, [TideEvent])] {
        (0..<7).map { offset -> (Date, [TideEvent]) in
            let day = selectedDate.adding(days: offset).startOfDay
            let t = tides.filter { $0.date.startOfDay == day }.sorted { $0.time < $1.time }
            return (day, t)
        }
    }
    private var maxHeight: Double { max(tides.map { $0.heightM }.max() ?? 3, 0.1) }

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text("TIDES · PORTO DE CABEDELO").font(TerminalTheme.mono(size: 14, weight: .bold))
                    .foregroundStyle(TerminalTheme.amber)
                Spacer()
                DatePicker("", selection: $selectedDate, displayedComponents: .date)
                    .labelsHidden().frame(width: 130)
            }
            .padding(.horizontal, 16).padding(.top, 14)

            ScrollView {
                VStack(spacing: 12) {
                    SectionPanel(title: "Selected day", accent: TerminalTheme.cyan,
                                 subtitle: selectedDate.dayLabel()) {
                        if dayTides.isEmpty { EmptyHint(text: "No tide data for this day.") }
                        ForEach(dayTides) { t in
                            HStack {
                                Image(systemName: t.tideType.symbol).foregroundStyle(t.tideType.color).frame(width: 18)
                                Text(t.tideType.label)
                                    .font(TerminalTheme.mono(size: 12, weight: .medium))
                                    .foregroundStyle(TerminalTheme.textPrimary)
                                Spacer()
                                Text(t.timeString)
                                    .font(TerminalTheme.mono(size: 12, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary).frame(width: 56, alignment: .trailing)
                                BarRow(label: "", value: t.heightM, maxValue: maxHeight, color: t.tideType.color,
                                       valueText: String(format: "%.2fm", t.heightM))
                                    .frame(width: 220)
                            }
                            .padding(.vertical, 2)
                        }
                    }

                    SectionPanel(title: "Next 7 days", accent: TerminalTheme.amber) {
                        ForEach(weekTides, id: \.0) { (day, ts) in
                            HStack(alignment: .top, spacing: 10) {
                                Text(day.dayLabel())
                                    .font(TerminalTheme.mono(size: 11, weight: .semibold))
                                    .foregroundStyle(TerminalTheme.cyan).frame(width: 64, alignment: .leading)
                                if ts.isEmpty {
                                    Text("—").font(TerminalTheme.mono(size: 11, weight: .regular))
                                        .foregroundStyle(TerminalTheme.textSecondary)
                                } else {
                                    VStack(alignment: .leading, spacing: 2) {
                                        ForEach(ts) { t in
                                            HStack(spacing: 6) {
                                                Image(systemName: t.tideType.symbol)
                                                    .font(TerminalTheme.icon(size: 9)).foregroundStyle(t.tideType.color)
                                                Text("\(t.timeString)  \(String(format: "%.2fm", t.heightM))")
                                                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                                                    .foregroundStyle(TerminalTheme.textPrimary)
                                            }
                                        }
                                    }
                                }
                                Spacer()
                            }
                            .padding(.vertical, 3)
                            Divider().overlay(TerminalTheme.border)
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 16)
            }
        }
    }
}
