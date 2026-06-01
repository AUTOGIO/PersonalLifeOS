import SwiftUI

struct HeaderBarView: View {
    var body: some View {
        HStack(spacing: 12) {
            Text("LIFE_OS")
                .font(TerminalTheme.mono(size: 20, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)

            Text("WORKSPACE")
                .font(TerminalTheme.mono(size: 13, weight: .semibold))
                .foregroundStyle(TerminalTheme.cyan)

            Spacer()

            Text("MACOS 26.6")
                .font(TerminalTheme.mono(size: 12, weight: .medium))
                .foregroundStyle(TerminalTheme.textSecondary)

            Text("STATUS: LIVE")
                .font(TerminalTheme.mono(size: 12, weight: .semibold))
                .foregroundStyle(.green)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(TerminalTheme.panel)
        .overlay(
            Rectangle()
                .frame(height: 1)
                .foregroundStyle(TerminalTheme.border),
            alignment: .bottom
        )
    }
}
