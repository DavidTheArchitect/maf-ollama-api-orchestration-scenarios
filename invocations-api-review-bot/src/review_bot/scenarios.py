from __future__ import annotations

from dataclasses import dataclass

from .agents import AgentSpec


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    pattern: str
    title: str
    learning_goal: str
    when_to_use: str
    sample_task: str
    agents: tuple[AgentSpec, ...]


SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec(
        id="sequential-release-readiness",
        pattern="sequential",
        title="Sequential Release Readiness Job",
        learning_goal="Learn how an invocation can accept a structured job and run a deterministic multi-stage review pipeline.",
        when_to_use="Use Invocations plus sequential orchestration for webhook or CI jobs that must pass through fixed processing stages.",
        sample_task="Prepare a release readiness job result for a billing reconciliation change before promotion.",
        agents=(
            AgentSpec("JobIntakeAgent", "Normalizes the incoming job payload.", "Normalize the structured invocation into a concise work order. Preserve supplied fields."),
            AgentSpec("DependencyAuditAgent", "Audits dependencies and rollout sequencing.", "Identify dependencies, rollout ordering, migration concerns, and blocked prerequisites."),
            AgentSpec("RiskClassifierAgent", "Classifies release-blocking risks.", "Classify risks by severity, likelihood, owner, and required mitigation."),
            AgentSpec("EvidenceCheckAgent", "Checks evidence and test sufficiency.", "Assess whether supplied artifacts support the requested release decision."),
            AgentSpec("ActionPlannerAgent", "Produces the final action plan.", "Synthesize the pipeline into next actions, required approvals, and a release recommendation."),
        ),
    ),
    ScenarioSpec(
        id="concurrent-pr-review",
        pattern="concurrent",
        title="Concurrent Pull Request Review Job",
        learning_goal="Learn how an invocation can fan out a structured review payload to multiple independent reviewers.",
        when_to_use="Use Invocations plus concurrent orchestration for CI, webhook, and batch reviews where each expert can run independently.",
        sample_task="Review this PR before it is merged into the release branch.",
        agents=(
            AgentSpec("SecurityReviewerAgent", "Reviews security risk.", "Review auth, data exposure, secrets, privilege boundaries, and abuse cases."),
            AgentSpec("PerformanceReviewerAgent", "Reviews performance risk.", "Review query cost, concurrency, caching, memory, and throughput risk."),
            AgentSpec("TestReviewerAgent", "Reviews test and regression risk.", "Review coverage, edge cases, failure modes, migrations, and rollback tests."),
            AgentSpec("MaintainabilityReviewerAgent", "Reviews maintainability risk.", "Review readability, interfaces, operational debugging, and future change cost."),
            AgentSpec("ReleaseRiskAgent", "Reviews merge and rollout risk.", "Review release gates, feature flags, monitoring, and customer-impact risk."),
        ),
    ),
    ScenarioSpec(
        id="handoff-support-triage",
        pattern="handoff",
        title="Handoff Support Triage Job",
        learning_goal="Learn how an invocation can still manage session-aware routing while owning its own JSON payload.",
        when_to_use="Use Invocations plus handoff for ticket, webhook, or service-desk automation that routes to specialists.",
        sample_task="Route a support ticket about invoice export failures after SSO login.",
        agents=(
            AgentSpec("TicketTriageAgent", "Routes structured support tickets.", "Classify the ticket and hand off to the best specialist. Use the supplied artifacts only."),
            AgentSpec("AuthSpecialistAgent", "Handles SSO and permission issues.", "Assess SSO, login, session, role, and permission failure modes."),
            AgentSpec("BillingSpecialistAgent", "Handles invoice and reconciliation issues.", "Assess invoices, billing state, reconciliation, and finance-close impact."),
            AgentSpec("ExportSpecialistAgent", "Handles export and report failures.", "Assess export queries, formats, dashboard state, and data pipeline issues."),
            AgentSpec("EscalationCoordinatorAgent", "Plans escalation and communications.", "Create escalation actions, owner handoffs, and customer-safe communication."),
        ),
    ),
    ScenarioSpec(
        id="group-chat-launch-council",
        pattern="group-chat",
        title="Group Chat Change Advisory Job",
        learning_goal="Learn how an invocation can return a structured result from a transparent multi-agent advisory conversation.",
        when_to_use="Use Invocations plus group chat when an internal system wants a decision record from several named stakeholders.",
        sample_task="Create a change advisory recommendation for launching dashboard export changes this week.",
        agents=(
            AgentSpec("ChangeManagerAgent", "Facilitates the advisory discussion.", "Evaluate change risk, approval criteria, and decision record quality."),
            AgentSpec("SecurityAdvisorAgent", "Represents security constraints.", "Evaluate security and compliance objections or approvals."),
            AgentSpec("ReliabilityAdvisorAgent", "Represents reliability constraints.", "Evaluate SLO, rollback, observability, and operational readiness."),
            AgentSpec("QaAdvisorAgent", "Represents quality gates.", "Evaluate test evidence, regression risk, and release-blocking gaps."),
            AgentSpec("CustomerReadinessAgent", "Represents customer communications.", "Evaluate customer-facing readiness, known issues, and support enablement."),
        ),
    ),
    ScenarioSpec(
        id="magentic-incident-response",
        pattern="magentic",
        title="Magentic Incident Automation Job",
        learning_goal="Learn how an invocation can carry a custom incident payload into a manager-led dynamic multi-agent workflow.",
        when_to_use="Use Invocations plus magentic orchestration for non-chat jobs that require dynamic planning and specialist coordination.",
        sample_task="Coordinate analysis of export timeouts, delayed reconciliation, and rising support tickets.",
        agents=(
            AgentSpec("IncidentManagerAgent", "Plans and coordinates the workflow.", "Coordinate the team, select specialists, replan when needed, and produce the final incident result."),
            AgentSpec("TelemetryAnalystAgent", "Analyzes supplied telemetry artifacts.", "Analyze metrics, logs, alerts, and timeline clues from supplied artifacts."),
            AgentSpec("DatabaseSpecialistAgent", "Analyzes database and migration risk.", "Assess database locks, query plans, migrations, and reconciliation job interactions."),
            AgentSpec("InfrastructureSpecialistAgent", "Analyzes platform and capacity risk.", "Assess capacity, queues, network, deployments, and service dependencies."),
            AgentSpec("CustomerImpactAgent", "Analyzes customer impact.", "Estimate customer impact, severity, escalation urgency, and external communication needs."),
            AgentSpec("RemediationPlannerAgent", "Plans mitigation and follow-up.", "Create mitigation, validation, owner handoffs, and prevention follow-up."),
        ),
    ),
)

SCENARIOS_BY_ID: dict[str, ScenarioSpec] = {scenario.id: scenario for scenario in SCENARIOS}
SCENARIO_IDS: tuple[str, ...] = tuple(scenario.id for scenario in SCENARIOS)
PATTERNS: tuple[str, ...] = tuple(dict.fromkeys(scenario.pattern for scenario in SCENARIOS))
PATTERN_DEFAULT_SCENARIO: dict[str, str] = {scenario.pattern: scenario.id for scenario in SCENARIOS}


def normalize_scenario_id(value: str | None) -> str:
    normalized = (value or "concurrent-pr-review").strip().lower().replace("_", "-")
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
