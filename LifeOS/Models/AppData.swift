import Foundation

enum AppData {
    static let rockQuotes: [String] = [
        "Don't stop believin'. — Journey",
        "Any way you want it, that's the way you need it. — Journey",
        "The wheel in the sky keeps on turnin'. — Journey",
        "Some will win, some will lose. — Journey",
        "Lights, when you call my name, soft and slow. — Journey",
        "It goes on and on and on. — Journey",
        "Hold on to that feelin'. — Journey",
        "Be good to yourself when nobody else will. — Journey",
    ]

    static func randomQuote() -> String { rockQuotes.randomElement() ?? rockQuotes[0] }
}
