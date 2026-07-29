import SwiftUI
import SwiftData
import AppKit

struct RootView: View {
    @Environment(\.modelContext) private var context
    @StateObject private var vm = MainViewModel()
    @StateObject private var persistence = PersistenceAlerts()
    @State private var didSeed = false
    @State private var showStoreRecovery = false

    let storeRecoveryMode: Bool

    var body: some View {
        ZStack {
            TerminalTheme.background.ignoresSafeArea()
            VStack(spacing: 0) {
                HeaderBarView()
                NavigationSplitView {
                    SidebarView(selection: $vm.selection)
                        .navigationSplitViewColumnWidth(min: 210, ideal: 220, max: 260)
                } detail: {
                    detailView
                        .background(TerminalTheme.background)
                }
                .navigationSplitViewStyle(.balanced)
            }
        }
        .environmentObject(vm)
        .environmentObject(persistence)
        .persistenceAlerts(persistence)
        .alert("Local Data Store Unavailable", isPresented: $showStoreRecovery) {
            Button("Open Support Folder") { openApplicationSupport() }
            Button("OK", role: .cancel) {}
        } message: {
            Text("The on-disk store could not be opened. LifeOS is using temporary in-memory data that will be lost when you quit.\n\nTo reset: quit the app, delete default.store* in ~/Library/Application Support/, then relaunch.")
        }
        .task {
            if storeRecoveryMode {
                showStoreRecovery = true
            }
            if !didSeed {
                didSeed = true
                let warnings = SeedLoader.seedIfNeeded(context)
                persistence.presentSeedWarnings(warnings)
            }
        }
    }

    private func openApplicationSupport() {
        let url = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Library/Application Support")
        NSWorkspace.shared.open(url)
    }

    @ViewBuilder
    private var detailView: some View {
        switch vm.selection {
        case .dashboard: DashboardView()
        case .schedule: WeeklyScheduleView()
        case .activities: ActivitiesView()
        case .projects: ProjectsView()
        case .habits: HabitsView()
        case .kite: KiteSessionsView()
        case .tides: TidesView()
        case .analytics: AnalyticsView()
        }
    }
}

struct SidebarView: View {
    @Binding var selection: NavigationSection

    var body: some View {
        ZStack {
            TerminalTheme.panel.ignoresSafeArea()
            VStack(alignment: .leading, spacing: 2) {
                Text("MODULES")
                    .font(TerminalTheme.mono(size: 10, weight: .bold))
                    .foregroundStyle(TerminalTheme.textSecondary)
                    .padding(.horizontal, 14).padding(.top, 14).padding(.bottom, 6)
                ForEach(NavigationSection.allCases) { section in
                    Button {
                        selection = section
                    } label: {
                        HStack(spacing: 10) {
                            Image(systemName: section.icon)
                                .frame(width: 18)
                                .foregroundStyle(selection == section ? TerminalTheme.amber : TerminalTheme.textSecondary)
                            Text(section.rawValue)
                                .font(TerminalTheme.mono(size: 12, weight: selection == section ? .bold : .regular))
                                .foregroundStyle(selection == section ? TerminalTheme.textPrimary : TerminalTheme.textSecondary)
                            Spacer()
                        }
                        .padding(.horizontal, 12).padding(.vertical, 8)
                        .background(selection == section ? TerminalTheme.cyan.opacity(0.10) : .clear)
                        .overlay(alignment: .leading) {
                            Rectangle()
                                .fill(selection == section ? TerminalTheme.amber : .clear)
                                .frame(width: 2)
                        }
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                }
                Spacer()
                Text("LIFE_OS · CABEDELO-PB")
                    .font(TerminalTheme.mono(size: 9, weight: .regular))
                    .foregroundStyle(TerminalTheme.textSecondary)
                    .padding(14)
            }
        }
    }
}
