from __future__ import annotations

from dataclasses import dataclass

from .agents import AgentSpec

PatternName = str


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    pattern: PatternName
    title: str
    learning_goal: str
    when_to_use: str
    sample_input: str
    agents: tuple[AgentSpec, ...]


SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec(
        id="sequential-release-readiness",
        pattern="sequential",
        title="Sequential Release Readiness Pipeline",
        learning_goal="Learn how Responses API clients can send a normal chat request while the server runs a fixed multi-stage agent pipeline.",
        when_to_use="Use Responses plus sequential orchestration when each turn should produce a conversational answer through a predictable chain of review stages.",
        sample_input="Prepare a release readiness brief for version 2.4.0 with billing reconciliation, dashboard exports, and API bug fixes.",
        agents=(
            AgentSpec("ScopePlannerAgent", "Extracts release scope and readiness questions.", "Turn the user request into a concrete release-scope summary and ordered readiness questions."),
            AgentSpec("DependencyPlannerAgent", "Identifies dependencies and sequencing.", "Identify upstream/downstream teams, rollout dependencies, migration needs, and sequencing constraints."),
            AgentSpec("RiskReviewerAgent", "Reviews operational and customer risk.", "Assess operational risk, rollback risk, security exposure, and customer impact. Return mitigations."),
            AgentSpec("DocsWriterAgent", "Plans release notes and internal docs.", "Create release-note bullets, internal enablement tasks, and support-facing docs needs."),
            AgentSpec("FinalEditorAgent", "Creates the final readiness brief.", "Synthesize the prior outputs into scope, risks, required follow-ups, and a go/no-go recommendation."),
        ),
    ),
    ScenarioSpec(
        id="concurrent-pr-review",
        pattern="concurrent",
        title="Concurrent Pull Request Review",
        learning_goal="Learn how a Responses API endpoint can fan out one conversational request to independent expert agents and aggregate their answers.",
        when_to_use="Use Responses plus concurrent orchestration when the user expects one answer but independent perspectives can run in parallel.",
        sample_input="Review a pull request that changes authentication middleware, export queries, and reconciliation tests before release branch merge.",
        agents=(
            AgentSpec("SecurityReviewerAgent", "Reviews auth, data exposure, and abuse risk.", "Review the change for authentication, authorization, secrets, input validation, and data exposure risk."),
            AgentSpec("PerformanceReviewerAgent", "Reviews latency and scaling risk.", "Review the change for query cost, batching, memory pressure, concurrency, and user-visible latency."),
            AgentSpec("TestReviewerAgent", "Reviews test coverage and regression risk.", "Assess whether tests cover the changed behavior, edge cases, migrations, and rollback behavior."),
            AgentSpec("MaintainabilityReviewerAgent", "Reviews code clarity and future debugging cost.", "Review maintainability, interfaces, naming, error handling, and operational debuggability."),
            AgentSpec("ReleaseRiskAgent", "Reviews release and rollout risk.", "Assess rollout, monitoring, feature flags, customer communications, and release-blocking risk."),
        ),
    ),
    ScenarioSpec(
        id="handoff-support-triage",
        pattern="handoff",
        title="Handoff Support Triage",
        learning_goal="Learn how a conversational Responses API session can route turns between specialists while keeping the public protocol unchanged.",
        when_to_use="Use Responses plus handoff when the user may ask follow-ups and the right specialist depends on the conversation.",
        sample_input="A customer says their invoice export fails after SSO login and they need an answer before finance close.",
        agents=(
            AgentSpec("SupportTriageAgent", "Routes customer issues to the right specialist.", "Classify the issue and hand off to the most relevant specialist. Ask clarifying questions only when needed."),
            AgentSpec("AuthSpecialistAgent", "Handles login, SSO, and permission problems.", "Resolve authentication, SSO, session, permission, and identity-provider concerns."),
            AgentSpec("BillingSpecialistAgent", "Handles invoices and reconciliation problems.", "Resolve invoice, reconciliation, subscription, and finance-close concerns."),
            AgentSpec("DataExportSpecialistAgent", "Handles dashboard and export failures.", "Resolve report export, file format, query, and dashboard data concerns."),
            AgentSpec("EscalationCoordinatorAgent", "Coordinates urgent escalation and next actions.", "Create escalation criteria, next actions, and customer-safe communication for urgent issues."),
        ),
    ),
    ScenarioSpec(
        id="group-chat-launch-council",
        pattern="group-chat",
        title="Group Chat Launch Council",
        learning_goal="Learn how a Responses API chat can expose a collaborative council that iteratively improves an answer.",
        when_to_use="Use Responses plus group chat when transparency, critique, and iterative refinement matter more than a fixed pipeline.",
        sample_input="Should we launch the new dashboard export feature this week or hold for another beta cohort?",
        agents=(
            AgentSpec("ProductManagerAgent", "Represents customer value and launch tradeoffs.", "Argue from customer value, scope clarity, launch goals, and business tradeoffs."),
            AgentSpec("SreAgent", "Represents reliability and operations.", "Argue from reliability, observability, rollback, incident risk, and supportability."),
            AgentSpec("SupportLeadAgent", "Represents customer support readiness.", "Argue from support macros, known issues, customer confusion, and escalation burden."),
            AgentSpec("SalesEnablementAgent", "Represents field readiness.", "Argue from customer-facing messaging, enablement, objections, and account-team readiness."),
            AgentSpec("ReleaseNotesAgent", "Represents docs and release communications.", "Turn the discussion into release notes, caveats, and internal communications."),
        ),
    ),
    ScenarioSpec(
        id="magentic-incident-response",
        pattern="magentic",
        title="Magentic Incident Response Coordination",
        learning_goal="Learn how a manager agent can dynamically coordinate specialists for a less predictable multi-step response.",
        when_to_use="Use Responses plus magentic orchestration for open-ended tasks that need planning, dynamic specialist selection, and replanning.",
        sample_input="Investigate a production incident where exports are timing out, billing reconciliation is delayed, and support tickets are rising.",
        agents=(
            AgentSpec("IncidentManagerAgent", "Plans and coordinates the incident response.", "Coordinate the team, decide who should act next, replan when blocked, and produce the final incident brief."),
            AgentSpec("TelemetryAnalystAgent", "Analyzes logs, metrics, and symptoms.", "Reason about logs, metrics, alerts, error rates, and timelines from the provided incident description."),
            AgentSpec("CustomerImpactAgent", "Estimates customer and business impact.", "Assess affected customers, severity, communication urgency, and business impact."),
            AgentSpec("MitigationPlannerAgent", "Plans rollback and mitigation options.", "Propose mitigation, rollback, feature-flag, and validation options."),
            AgentSpec("CommsLeadAgent", "Drafts stakeholder and customer communications.", "Draft concise internal updates and customer-safe status language."),
            AgentSpec("PostIncidentReviewerAgent", "Identifies follow-up and prevention work.", "Identify post-incident actions, owners, and prevention themes."),
        ),
    ),
)

SCENARIOS_BY_ID: dict[str, ScenarioSpec] = {scenario.id: scenario for scenario in SCENARIOS}
SCENARIO_IDS: tuple[str, ...] = tuple(scenario.id for scenario in SCENARIOS)
PATTERNS: tuple[str, ...] = tuple(dict.fromkeys(scenario.pattern for scenario in SCENARIOS))

PATTERN_DEFAULT_SCENARIO: dict[str, str] = {
    scenario.pattern: scenario.id for scenario in SCENARIOS
}


def normalize_scenario_id(value: str | None) -> str:
    normalized = (value or "sequential-release-readiness").strip().lower().replace("_", "-")
    aliases = {
        "sequential": "sequential-release-readiness",
        "concurrent": "concurrent-pr-review",
        "handoff": "handoff-support-triage",
        "group": "group-chat-launch-council",
        "groupchat": "group-chat-launch-council",
        "group-chat": "group-chat-launch-council",
        "magentic": "magentic-incident-response",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in SCENARIOS_BY_ID:
        raise ValueError(f"Unknown scenario '{value}'. Expected one of: {', '.join(SCENARIO_IDS)}")
    return normalized


def get_scenario(value: str | None) -> ScenarioSpec:
    return SCENARIOS_BY_ID[normalize_scenario_id(value)]
