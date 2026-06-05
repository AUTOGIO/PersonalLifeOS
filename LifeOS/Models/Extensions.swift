import SwiftUI
import Foundation

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xff) / 255.0,
            green: Double((hex >> 8) & 0xff) / 255.0,
            blue: Double(hex & 0xff) / 255.0,
            opacity: alpha
        )
    }
}

extension Date {
    var startOfDay: Date { Calendar.current.startOfDay(for: self) }

    var isoDay: String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.timeZone = TimeZone(identifier: "America/Fortaleza")
        return f.string(from: self)
    }

    func adding(days: Int) -> Date {
        Calendar.current.date(byAdding: .day, value: days, to: self)!
    }

    var weekStart: Date {
        let cal = Calendar.current
        // Force Monday-based week
        let weekday = cal.component(.weekday, from: self) // 1=Sun
        let daysFromMonday = (weekday + 5) % 7
        return cal.date(byAdding: .day, value: -daysFromMonday, to: startOfDay)!
    }

    var monthStart: Date {
        let cal = Calendar.current
        return cal.date(from: cal.dateComponents([.year, .month], from: self))!
    }

    func timeLabel() -> String {
        let f = DateFormatter(); f.dateFormat = "HH:mm"; return f.string(from: self)
    }

    func dayLabel() -> String {
        let f = DateFormatter(); f.dateFormat = "EEE dd"; return f.string(from: self)
    }
}

/// Build a Date for a given time-of-day (today's date) from "HH:mm" or "HH:mm:ss".
func timeOfDay(_ s: String, on day: Date = Date()) -> Date {
    let parts = s.split(separator: ":").compactMap { Int($0) }
    var comps = Calendar.current.dateComponents([.year, .month, .day], from: day)
    comps.hour = parts.count > 0 ? parts[0] : 0
    comps.minute = parts.count > 1 ? parts[1] : 0
    comps.second = parts.count > 2 ? parts[2] : 0
    return Calendar.current.date(from: comps) ?? day
}

extension Double {
    var trimmedHours: String {
        self == rounded() ? String(format: "%.0f", self) : String(format: "%.1f", self)
    }
}
