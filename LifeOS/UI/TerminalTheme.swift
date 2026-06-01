import SwiftUI

enum TerminalTheme {
    static let background = Color(red: 0.02, green: 0.03, blue: 0.05)
    static let panel = Color(red: 0.05, green: 0.07, blue: 0.10)
    static let border = Color(red: 0.18, green: 0.20, blue: 0.25)

    static let amber = Color(red: 1.00, green: 0.72, blue: 0.10)
    static let cyan = Color(red: 0.20, green: 0.90, blue: 1.00)

    static let textPrimary = Color.white
    static let textSecondary = Color(red: 0.65, green: 0.70, blue: 0.78)

    static func mono(size: CGFloat, weight: Font.Weight) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }
}
