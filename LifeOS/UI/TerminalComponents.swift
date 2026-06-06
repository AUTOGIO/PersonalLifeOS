import SwiftUI

// Extra semantic colors layered on the existing TerminalTheme.
extension TerminalTheme {
    static let green = Color(hex: 0x22c55e)
    static let red = Color(hex: 0xef4444)
    static let panelAlt = Color(red: 0.07, green: 0.09, blue: 0.13)
}

/// Reusable section panel with a titled header and accent bar.
struct SectionPanel<Content: View>: View {
    let title: String
    var accent: Color = TerminalTheme.cyan
    var subtitle: String? = nil
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Rectangle().fill(accent).frame(width: 3, height: 14)
                Text(title.uppercased())
                    .font(TerminalTheme.mono(size: 12, weight: .bold))
                    .foregroundStyle(accent)
                if let subtitle {
                    Text(subtitle)
                        .font(TerminalTheme.mono(size: 11, weight: .regular))
                        .foregroundStyle(TerminalTheme.textSecondary)
                }
                Spacer()
            }
            content
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(TerminalTheme.panel)
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(TerminalTheme.border, lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

/// KPI tile: big value, label, optional delta-style accent.
struct KPITile: View {
    let label: String
    let value: String
    var unit: String? = nil
    var accent: Color = TerminalTheme.cyan
    var hint: String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label.uppercased())
                .font(TerminalTheme.mono(size: 10, weight: .semibold))
                .foregroundStyle(TerminalTheme.textSecondary)
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text(value)
                    .font(TerminalTheme.mono(size: 26, weight: .bold))
                    .foregroundStyle(accent)
                if let unit {
                    Text(unit)
                        .font(TerminalTheme.mono(size: 12, weight: .medium))
                        .foregroundStyle(TerminalTheme.textSecondary)
                }
            }
            if let hint {
                Text(hint)
                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                    .foregroundStyle(TerminalTheme.textSecondary)
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(TerminalTheme.panelAlt)
        .overlay(RoundedRectangle(cornerRadius: 5).stroke(TerminalTheme.border, lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 5))
    }
}

/// Small pill / tag.
struct TagPill: View {
    let text: String
    var color: Color = TerminalTheme.cyan
    var body: some View {
        Text(text.uppercased())
            .font(TerminalTheme.mono(size: 9, weight: .bold))
            .foregroundStyle(color)
            .padding(.horizontal, 7).padding(.vertical, 3)
            .background(color.opacity(0.15))
            .overlay(RoundedRectangle(cornerRadius: 20).stroke(color.opacity(0.4), lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: 20))
    }
}

/// A simple horizontal bar (for analytics) drawn with monospaced labels.
struct BarRow: View {
    let label: String
    let value: Double
    let maxValue: Double
    var color: Color = TerminalTheme.cyan
    var valueText: String? = nil

    var body: some View {
        HStack(spacing: 10) {
            Text(label)
                .font(TerminalTheme.mono(size: 11, weight: .medium))
                .foregroundStyle(TerminalTheme.textPrimary)
                .frame(width: 120, alignment: .leading)
                .lineLimit(1)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3).fill(TerminalTheme.panelAlt)
                    RoundedRectangle(cornerRadius: 3).fill(color)
                        .frame(width: maxValue > 0 ? geo.size.width * CGFloat(value / maxValue) : 0)
                }
            }
            .frame(height: 14)
            Text(valueText ?? String(format: "%.0f", value))
                .font(TerminalTheme.mono(size: 11, weight: .semibold))
                .foregroundStyle(color)
                .frame(width: 52, alignment: .trailing)
        }
    }
}

/// Empty-state hint.
struct EmptyHint: View {
    let text: String
    var body: some View {
        Text(text)
            .font(TerminalTheme.mono(size: 11, weight: .regular))
            .foregroundStyle(TerminalTheme.textSecondary)
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.vertical, 18)
    }
}
