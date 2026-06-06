import SwiftUI
import SwiftData

struct ProjectsView: View {
    @Environment(\.modelContext) private var context
    @Query private var projects: [AIProject]
    @Query private var sessions: [ProjectSession]
    @State private var showingAdd = false

    private var sortedProjects: [AIProject] {
        projects.sorted { ($0.priority.sortRank, $0.name) < ($1.priority.sortRank, $1.name) }
    }
    private var activeSession: ProjectSession? { sessions.first { $0.endTime == nil } }

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text("AI PROJECTS")
                    .font(TerminalTheme.mono(size: 14, weight: .bold))
                    .foregroundStyle(TerminalTheme.amber)
                Spacer()
                if let s = activeSession {
                    HStack(spacing: 6) {
                        Circle().fill(TerminalTheme.green).frame(width: 8, height: 8)
                        Text("\(s.project?.name ?? "") · since \(s.startTime.timeLabel())")
                            .font(TerminalTheme.mono(size: 11, weight: .medium))
                            .foregroundStyle(TerminalTheme.green)
                        Button("Stop") { stop(s) }.buttonStyle(.bordered).controlSize(.small)
                    }
                }
                Button { showingAdd = true } label: { Label("Add", systemImage: "plus") }
                    .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal, 16).padding(.top, 14)

            ScrollView {
                VStack(spacing: 8) {
                    if sortedProjects.isEmpty { EmptyHint(text: "No projects yet.") }
                    ForEach(sortedProjects) { p in
                        SectionPanel(title: p.name, accent: priorityColor(p.priority)) {
                            HStack(spacing: 10) {
                                TagPill(text: p.category.label, color: TerminalTheme.cyan)
                                TagPill(text: p.priority.label, color: priorityColor(p.priority))
                                TagPill(text: p.status.label, color: statusColor(p.status))
                                Spacer()
                                Text("\(p.totalHours.trimmedHours) h logged")
                                    .font(TerminalTheme.mono(size: 11, weight: .semibold))
                                    .foregroundStyle(TerminalTheme.textPrimary)
                                if activeSession?.project == p {
                                    Button("Stop") { stop(activeSession!) }
                                        .buttonStyle(.bordered).controlSize(.small)
                                } else {
                                    Button("Start") { start(p) }
                                        .buttonStyle(.borderedProminent).controlSize(.small)
                                        .disabled(activeSession != nil)
                                }
                                Button { context.delete(p); try? context.save() } label: {
                                    Image(systemName: "trash").foregroundStyle(TerminalTheme.red)
                                }.buttonStyle(.plain)
                            }
                            if let repo = p.githubRepo, !repo.isEmpty {
                                Text(repo)
                                    .font(TerminalTheme.mono(size: 10, weight: .regular))
                                    .foregroundStyle(TerminalTheme.textSecondary)
                            }
                            let recent = p.sessions.sorted { $0.startTime > $1.startTime }.prefix(3)
                            if !recent.isEmpty {
                                ForEach(Array(recent)) { s in
                                    HStack {
                                        Text(s.startTime.dayLabel())
                                            .font(TerminalTheme.mono(size: 10, weight: .regular))
                                            .foregroundStyle(TerminalTheme.textSecondary)
                                        Spacer()
                                        Text(s.durationMinutes != nil ? "\(s.durationMinutes!)m" : "running")
                                            .font(TerminalTheme.mono(size: 10, weight: .regular))
                                            .foregroundStyle(s.endTime == nil ? TerminalTheme.green : TerminalTheme.textSecondary)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 16)
            }
        }
        .sheet(isPresented: $showingAdd) { ProjectEditor() }
    }

    private func start(_ p: AIProject) {
        let s = ProjectSession(project: p, startTime: Date())
        context.insert(s); try? context.save()
    }
    private func stop(_ s: ProjectSession) { s.stop(); try? context.save() }

    private func priorityColor(_ p: ProjectPriority) -> Color {
        switch p { case .high: return TerminalTheme.red; case .medium: return TerminalTheme.amber; case .low: return TerminalTheme.textSecondary }
    }
    private func statusColor(_ s: ProjectStatus) -> Color {
        switch s { case .active: return TerminalTheme.green; case .paused: return TerminalTheme.amber; case .completed: return TerminalTheme.cyan }
    }
}

struct ProjectEditor: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var category: ProjectCategory = .coreOS
    @State private var priority: ProjectPriority = .medium
    @State private var status: ProjectStatus = .active
    @State private var repo = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("NEW PROJECT").font(TerminalTheme.mono(size: 14, weight: .bold))
                .foregroundStyle(TerminalTheme.amber)
            Form {
                TextField("Name", text: $name)
                Picker("Category", selection: $category) { ForEach(ProjectCategory.allCases) { Text($0.label).tag($0) } }
                Picker("Priority", selection: $priority) { ForEach(ProjectPriority.allCases) { Text($0.label).tag($0) } }
                Picker("Status", selection: $status) { ForEach(ProjectStatus.allCases) { Text($0.label).tag($0) } }
                TextField("GitHub repo (optional)", text: $repo)
            }.formStyle(.grouped)
            HStack {
                Spacer()
                Button("Cancel") { dismiss() }
                Button("Save") {
                    context.insert(AIProject(name: name, category: category, priority: priority,
                                             status: status, githubRepo: repo.isEmpty ? nil : repo))
                    try? context.save(); dismiss()
                }.buttonStyle(.borderedProminent).disabled(name.isEmpty)
            }
        }
        .padding(18).frame(width: 420)
    }
}
