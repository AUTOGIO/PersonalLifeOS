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
    var startOfDay: Date { AppCalendar.calendar.startOfDay(for: self) }

    var isoDay: String { AppCalendar.dayFormatter.string(from: self) }

    func adding(days: Int) -> Date {
        AppCalendar.calendar.date(byAdding: .day, value: days, to: self)!
    }

    var weekStart: Date {
        let cal = AppCalendar.calendar
        let weekday = cal.component(.weekday, from: self) // 1=Sun
        let daysFromMonday = (weekday + 5) % 7
        return cal.date(byAdding: .day, value: -daysFromMonday, to: startOfDay)!
    }

    var monthStart: Date {
        let cal = AppCalendar.calendar
        return cal.date(from: cal.dateComponents([.year, .month], from: self))!
    }

    func timeLabel() -> String {
        let f = DateFormatter()
        f.calendar = AppCalendar.calendar
        f.timeZone = AppCalendar.timeZone
        f.dateFormat = "HH:mm"
        return f.string(from: self)
    }

    func dayLabel() -> String {
        let f = DateFormatter()
        f.calendar = AppCalendar.calendar
        f.timeZone = AppCalendar.timeZone
        f.dateFormat = "EEE dd"
        return f.string(from: self)
    }

    var isAppToday: Bool {
        AppCalendar.calendar.isDateInToday(self)
    }
}

/// Build a Date for a given time-of-day from "HH:mm" or "HH:mm:ss" using AppCalendar.
func timeOfDay(_ s: String, on day: Date = Date()) -> Date {
    let parts = s.split(separator: ":").compactMap { Int($0) }
    let cal = AppCalendar.calendar
    var comps = cal.dateComponents([.year, .month, .day], from: day)
    comps.hour = parts.count > 0 ? parts[0] : 0
    comps.minute = parts.count > 1 ? parts[1] : 0
    comps.second = parts.count > 2 ? parts[2] : 0
    return cal.date(from: comps) ?? day
}

enum CSV {
    /// RFC-style CSV field: quote when needed; escape internal quotes.
    static func escape(_ field: String) -> String {
        if field.contains(",") || field.contains("\"") || field.contains("\n") || field.contains("\r") {
            return "\"" + field.replacingOccurrences(of: "\"", with: "\"\"") + "\""
        }
        return field
    }

    static func row(_ fields: [String]) -> String {
        fields.map(escape).joined(separator: ",")
    }
}

extension Double {
    var trimmedHours: String {
        self == rounded() ? String(format: "%.0f", self) : String(format: "%.1f", self)
    }
}
