import Foundation

/// Single day-boundary policy for LifeOS (Cabedelo / America/Fortaleza).
enum AppCalendar {
    static let timeZoneIdentifier = "America/Fortaleza"

    static var timeZone: TimeZone {
        TimeZone(identifier: timeZoneIdentifier) ?? .gmt
    }

    static var calendar: Calendar {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = timeZone
        cal.firstWeekday = 2 // Monday
        return cal
    }

    static var dayFormatter: DateFormatter {
        let f = DateFormatter()
        f.calendar = calendar
        f.locale = Locale(identifier: "en_US_POSIX")
        f.timeZone = timeZone
        f.dateFormat = "yyyy-MM-dd"
        return f
    }
}
