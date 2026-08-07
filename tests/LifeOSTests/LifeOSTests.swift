import XCTest
@testable import LifeOS

final class LifeOSTests: XCTestCase {

    func testActivityComputeDuration() {
        let start = timeOfDay("09:00")
        let end = timeOfDay("11:30")
        XCTAssertEqual(Activity.computeDuration(start, end), 150)
        XCTAssertNil(Activity.computeDuration(end, start))
        XCTAssertNil(Activity.computeDuration(start, nil))
    }

    func testCSVEscaping() {
        XCTAssertEqual(CSV.escape("plain"), "plain")
        XCTAssertEqual(CSV.escape("a,b"), "\"a,b\"")
        XCTAssertEqual(CSV.escape("say \"hi\""), "\"say \"\"hi\"\"\"")
        XCTAssertEqual(CSV.row(["a,b", "c"]), "\"a,b\",c")
    }

    func testIsoDayUsesFortalezaFormatter() {
        var comps = DateComponents()
        comps.year = 2026
        comps.month = 7
        comps.day = 29
        comps.hour = 23
        comps.minute = 30
        comps.timeZone = AppCalendar.timeZone
        let date = AppCalendar.calendar.date(from: comps)!
        XCTAssertEqual(date.isoDay, "2026-07-29")
        XCTAssertEqual(date.startOfDay.isoDay, "2026-07-29")
    }

    func testWeekStartIsMondayInFortaleza() {
        // Wednesday 2026-07-29 Fortaleza → week starts Monday 2026-07-27
        var comps = DateComponents()
        comps.year = 2026
        comps.month = 7
        comps.day = 29
        comps.hour = 12
        comps.timeZone = AppCalendar.timeZone
        let wed = AppCalendar.calendar.date(from: comps)!
        XCTAssertEqual(wed.weekStart.isoDay, "2026-07-27")
        XCTAssertEqual(Weekday.from(date: wed), .wed)
    }

    func testHabitStreak() {
        let habit = Habit(name: "Test")
        let today = Date().startOfDay
        habit.completedDates = [today.isoDay, today.adding(days: -1).isoDay]
        habit.recomputeStreak()
        XCTAssertEqual(habit.streakCount, 2)
        habit.toggle(on: today)
        XCTAssertFalse(habit.isDone(on: today))
        habit.recomputeStreak()
        XCTAssertEqual(habit.streakCount, 0)
    }

    func testDecodeBundledTideSample() throws {
        let json = """
        [{"port_name":"Cabedelo","date":"2026-01-01","time":"06:12","height_m":2.1,"tide_type":"HIGH","source":"DHN","timezone":"America/Fortaleza"}]
        """.data(using: .utf8)!
        let seeds = try SeedLoader.decodeTides(from: json)
        XCTAssertEqual(seeds.count, 1)
        XCTAssertEqual(seeds[0].tide_type, "HIGH")
        XCTAssertEqual(AppCalendar.dayFormatter.date(from: seeds[0].date)?.isoDay, "2026-01-01")
    }

    func testDecodeDailyPlans() throws {
        let json = """
        [{"date":"2026-06-01","morning_intention":"Focus","evening_review":"","mood_score":7,"energy_score":null}]
        """.data(using: .utf8)!
        let seeds = try SeedLoader.decodePlans(from: json)
        XCTAssertEqual(seeds.count, 1)
        XCTAssertEqual(seeds[0].mood_score, 7)
        XCTAssertNil(seeds[0].energy_score)
    }
}
