import SwiftUI

struct HeaderBarView: View {
    @EnvironmentObject private var vm: MainViewModel

    private var dateString: String {
        let f = DateFormatter()
        f.dateFormat = "EEEE, dd MMM yyyy"
        return f.string(from: Date())
    }

    var body: some View {
        HStack(spacing: 12) {
            Text("LIFE_OS")
                .font(TerminalTheme.mono(size: 20, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)

            Text("WORKSPACE")
                .font(TerminalTheme.mono(size: 13, weight: .semibold))
                .foregroundStyle(TerminalTheme.cyan)

            Text(dateString.uppercased())
                .font(TerminalTheme.mono(size: 11, weight: .medium))
                .foregroundStyle(TerminalTheme.textSecondary)

            Spacer()

            Text(vm.quote)
                .font(TerminalTheme.mono(size: 11, weight: .regular))
                .foregroundStyle(TerminalTheme.textSecondary)
                .lineLimit(1)
                .truncationMode(.tail)
                .frame(maxWidth: 360, alignment: .trailing)

            Text("STATUS: LIVE")
                .font(TerminalTheme.mono(size: 11, weight: .semibold))
                .foregroundStyle(TerminalTheme.green)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(TerminalTheme.panel)
        .overlay(
            Rectangle().frame(height: 1).foregroundStyle(TerminalTheme.border),
            alignment: .bottom
        )
    }
}
