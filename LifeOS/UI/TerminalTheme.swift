import SwiftUI

enum TerminalTheme {
    static let background = Color(red: 0.02, green: 0.03, blue: 0.05)
    static let panel = Color(red: 0.05, green: 0.07, blue: 0.10)
    static let border = Color(red: 0.18, green: 0.20, blue: 0.25)

    static let amber = Color(red: 1.00, green: 0.72, blue: 0.10)
    static let cyan = Color(red: 0.20, green: 0.90, blue: 1.00)

    static let textPrimary = Color.white
    static let textSecondary = Color(red: 0.65, green: 0.70, blue: 0.78)

    /// Global UI text multiplier; kept in sync by `FontScaleStore`.
    static var fontScale: CGFloat = 1.0

    static func mono(size: CGFloat, weight: Font.Weight) -> Font {
        .system(size: size * fontScale, weight: weight, design: .monospaced)
    }

    static func icon(size: CGFloat) -> Font {
        .system(size: size * fontScale)
    }
}

@MainActor
final class FontScaleStore: ObservableObject {
    static let minScale: Double = 0.85
    static let maxScale: Double = 1.30
    static let step: Double = 0.05
    private static let defaultsKey = "lifeOS.fontScale"

    @Published private(set) var scale: Double {
        didSet {
            UserDefaults.standard.set(scale, forKey: Self.defaultsKey)
            TerminalTheme.fontScale = CGFloat(scale)
        }
    }

    init() {
        let stored = UserDefaults.standard.object(forKey: Self.defaultsKey) as? Double ?? 1.0
        let clamped = min(Self.maxScale, max(Self.minScale, stored))
        scale = clamped
        TerminalTheme.fontScale = CGFloat(clamped)
    }

    var percentLabel: String {
        "\(Int((scale * 100).rounded()))%"
    }

    var canDecrease: Bool { scale > Self.minScale + 0.001 }
    var canIncrease: Bool { scale < Self.maxScale - 0.001 }

    func decrease() {
        guard canDecrease else { return }
        scale = rounded(scale - Self.step)
    }

    func increase() {
        guard canIncrease else { return }
        scale = rounded(scale + Self.step)
    }

    private func rounded(_ value: Double) -> Double {
        (value * 100).rounded() / 100
    }
}
