import SwiftUI

struct HeaderBarView: View {
    @EnvironmentObject private var vm: MainViewModel
    @EnvironmentObject private var fontScale: FontScaleStore

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

            fontScaleControls

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

    private var fontScaleControls: some View {
        HStack(spacing: 2) {
            Button {
                fontScale.decrease()
            } label: {
                Text("−")
                    .font(TerminalTheme.mono(size: 13, weight: .bold))
                    .frame(width: 22, height: 22)
            }
            .buttonStyle(.plain)
            .foregroundStyle(fontScale.canDecrease ? TerminalTheme.cyan : TerminalTheme.textSecondary.opacity(0.4))
            .disabled(!fontScale.canDecrease)
            .help("Decrease font size")

            Text(fontScale.percentLabel)
                .font(TerminalTheme.mono(size: 11, weight: .semibold))
                .foregroundStyle(TerminalTheme.textSecondary)
                .frame(minWidth: 36)

            Button {
                fontScale.increase()
            } label: {
                Text("+")
                    .font(TerminalTheme.mono(size: 13, weight: .bold))
                    .frame(width: 22, height: 22)
            }
            .buttonStyle(.plain)
            .foregroundStyle(fontScale.canIncrease ? TerminalTheme.cyan : TerminalTheme.textSecondary.opacity(0.4))
            .disabled(!fontScale.canIncrease)
            .help("Increase font size")
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .overlay(
            RoundedRectangle(cornerRadius: 4)
                .stroke(TerminalTheme.border, lineWidth: 1)
        )
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Font size")
        .accessibilityValue(fontScale.percentLabel)
    }
}
