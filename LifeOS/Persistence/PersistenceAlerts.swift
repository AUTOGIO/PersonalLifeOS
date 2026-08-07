import Foundation
import SwiftData
import SwiftUI

/// Surfaces SwiftData save / seed failures to the UI instead of swallowing them.
@MainActor
final class PersistenceAlerts: ObservableObject {
    @Published var errorMessage: String?
    @Published var seedWarning: String?

    func save(_ context: ModelContext) {
        do {
            try context.save()
        } catch {
            #if DEBUG
            print("SwiftData save failed: \(error)")
            #endif
            errorMessage = "Could not save changes: \(error.localizedDescription)"
        }
    }

    func presentSeedWarnings(_ warnings: [String]) {
        guard !warnings.isEmpty else { return }
        seedWarning = warnings.joined(separator: "\n")
    }
}

extension View {
    func persistenceAlerts(_ alerts: PersistenceAlerts) -> some View {
        self
            .alert("Save Error", isPresented: Binding(
                get: { alerts.errorMessage != nil },
                set: { if !$0 { alerts.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { alerts.errorMessage = nil }
            } message: {
                Text(alerts.errorMessage ?? "")
            }
            .alert("Seed Warning", isPresented: Binding(
                get: { alerts.seedWarning != nil },
                set: { if !$0 { alerts.seedWarning = nil } }
            )) {
                Button("OK", role: .cancel) { alerts.seedWarning = nil }
            } message: {
                Text(alerts.seedWarning ?? "")
            }
    }
}
