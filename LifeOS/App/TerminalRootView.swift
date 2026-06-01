import SwiftUI

struct TerminalRootView: View {
    private let columns: [GridItem] = [
        GridItem(.flexible(minimum: 240), spacing: 10),
        GridItem(.flexible(minimum: 240), spacing: 10),
        GridItem(.flexible(minimum: 240), spacing: 10),
        GridItem(.flexible(minimum: 240), spacing: 10)
    ]

    var body: some View {
        ZStack {
            TerminalTheme.background.ignoresSafeArea()

            VStack(spacing: 10) {
                HeaderBarView()

                ScrollView {
                    LazyVGrid(columns: columns, spacing: 10) {
                        TerminalPanel(title: "WATCHLIST", accent: .cyan) {
                            panelRow("AAPL", "+1.21%", .green)
                            panelRow("TSLA", "-0.47%", .orange)
                            panelRow("NVDA", "+2.63%", .green)
                            panelRow("MSFT", "+0.28%", .green)
                        }

                        TerminalPanel(title: "PORTFOLIO P/L", accent: .orange) {
                            panelRow("Daily", "+$2,340", .green)
                            panelRow("Weekly", "+$8,120", .green)
                            panelRow("Monthly", "-$1,090", .orange)
                            panelRow("YTD", "+$24,410", .green)
                        }

                        TerminalPanel(title: "SYSTEM", accent: .cyan) {
                            panelRow("Focus Session", "42:18", .white)
                            panelRow("Tasks Closed", "14", .white)
                            panelRow("Energy", "7.8 / 10", .white)
                            panelRow("Latency", "8 ms", .green)
                        }

                        TerminalPanel(title: "CALENDAR", accent: .orange) {
                            panelRow("09:00", "Deep Work", .white)
                            panelRow("11:00", "Review", .white)
                            panelRow("14:00", "Execution Block", .white)
                            panelRow("17:00", "Wind-down", .white)
                        }
                    }
                    .padding(12)
                }
            }
        }
    }

    private func panelRow(_ key: String, _ value: String, _ color: Color) -> some View {
        HStack {
            Text(key)
                .foregroundStyle(TerminalTheme.textPrimary)
            Spacer()
            Text(value)
                .foregroundStyle(color)
        }
        .font(TerminalTheme.mono(size: 13, weight: .medium))
    }
}

#Preview {
    TerminalRootView()
}
