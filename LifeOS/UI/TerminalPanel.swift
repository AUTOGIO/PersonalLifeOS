import SwiftUI

struct TerminalPanel<Content: View>: View {
    let title: String
    let accent: Color
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(TerminalTheme.mono(size: 12, weight: .bold))
                    .foregroundStyle(accent)
                Spacer()
            }

            content
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(TerminalTheme.panel)
        .overlay(
            RoundedRectangle(cornerRadius: 4)
                .stroke(TerminalTheme.border, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 4))
    }
}
