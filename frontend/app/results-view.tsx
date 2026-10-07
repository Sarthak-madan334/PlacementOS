import type { Assessment } from "@/lib/contracts";

interface ResultsViewProps {
  assessment: Assessment | null;
  role: string;
  busy: boolean;
  onBuildProfile: () => void;
  onTryDemo: () => void;
  onUpdateProfile: () => void;
  onReassess: () => void;
}

export function ResultsView({ assessment, role, busy, onBuildProfile, onTryDemo, onUpdateProfile, onReassess }: ResultsViewProps) {
  if (!assessment) {
    return <section className="empty-card glass"><div className="empty-icon">◌</div><h2>Your snapshot is one step away.</h2><p>Add a few details about your profile and the role you have in mind. You can also open a synthetic example.</p><button className="primary-button" onClick={onBuildProfile}>Build my profile <span>→</span></button><button className="text-button" onClick={onTryDemo} disabled={busy}>{busy ? "Building sample…" : "Try the demo profile ↗"}</button></section>;
  }

  const eligibilityLabel = assessment.eligibility.status === "eligible" ? "Meets the provided criteria" : assessment.eligibility.status === "not_eligible" ? "Does not meet a stated requirement" : "More information needed";

  return <div className="results-layout">
    <div className="results-main">
      <section className="result-hero glass">
        <div className="result-title"><div><span className="card-overline">YOUR READINESS SNAPSHOT</span><h2>{role || "Role readiness"}</h2><p>Based on the information you shared · {new Date(assessment.created_at).toLocaleDateString()}</p></div><span className="version-pill">{assessment.readiness.scoring_version}</span></div>
        <div className="result-score-row"><div className="score-ring" style={{ "--score": `${assessment.readiness.score ?? 0}%` } as React.CSSProperties} role="img" aria-label={assessment.readiness.score === null ? "Readiness score unavailable" : `Readiness score ${assessment.readiness.score} out of 100`}><div><strong>{assessment.readiness.score ?? "—"}</strong><span>{assessment.readiness.score === null ? "unavailable" : "/ 100"}</span></div></div><div className="score-copy"><span className="card-overline">READINESS SCORE</span><h3>A useful starting point.</h3><p>This transparent coaching heuristic is not a hiring prediction or a measure of your potential.</p><span className="confidence-tag"><i/> {assessment.readiness.confidence} confidence</span></div></div>
        <div className={`eligibility-box eligibility-${assessment.eligibility.status}`}><span className="status-symbol" aria-hidden="true">{assessment.eligibility.status === "eligible" ? "✓" : assessment.eligibility.status === "not_eligible" ? "!" : "?"}</span><div><span className="card-overline">ELIGIBILITY</span><strong>{eligibilityLabel}</strong>{assessment.eligibility.reasons.map((reason) => <p key={reason.code}>{reason.message}</p>)}</div></div>
      </section>

      <section className="factor-card glass"><div className="section-title"><div><span className="card-overline">HOW IT BREAKS DOWN</span><h3>Evidence behind the snapshot</h3></div><span className="muted">CP-V1 FRAMEWORK</span></div>
        {assessment.readiness.factors.map((factor) => <div className="factor-row" key={factor.key}><div className="factor-name"><span>{factor.label}</span><small>{Math.round(factor.weight * 100)}% weight</small></div>{factor.available && factor.score !== null ? <><div className="factor-track" role="img" aria-label={`${factor.label}: ${factor.score} out of 100`}><span style={{ width: `${factor.score}%` }}/></div><strong>{factor.score}</strong></> : <span className="factor-unavailable">Not enough evidence yet</span>}<p className="factor-explanation">{factor.explanation || "Illustrative sample factor; fixture mode does not calculate from your edits."}</p></div>)}
        <details className="method-details"><summary>How is this calculated?</summary><p>Available cp-v1 factors are combined using their published weights and renormalized when a factor cannot be assessed. These coaching heuristics have not been validated as hiring predictors. Eligibility is separate from readiness.</p></details>
      </section>

      <section className="factor-card glass"><div className="section-title"><div><span className="card-overline">ROLE MATCH</span><h3>{assessment.role_match.score === null ? "No supported requirements to compare" : `${assessment.role_match.score}% match to assessable required skills`}</h3></div></div><p className="fine-print">{assessment.role_match.explanation || "A missing mention is not proof that you lack a skill."}</p>{assessment.role_match.score !== null && <div className="match-pills">{assessment.role_match.matched.map((skill) => <span className="match-pill" key={`matched-${skill}`}>✓ {skill} · shown</span>)}{assessment.role_match.missing.map((skill) => <span className="gap-pill" key={`missing-${skill}`}>＋ {skill} · not shown</span>)}</div>}{assessment.role_match.unknown.length > 0 && <div className="match-pills">{assessment.role_match.unknown.map((skill) => <span className="unknown-pill" key={`unknown-${skill}`}>? {skill} · needs review</span>)}</div>}{assessment.role_match.preferred && assessment.role_match.preferred.length > 0 && <p className="fine-print">Preferred: {assessment.role_match.preferred.join(", ")}. Preferred skills are not included in the required-skills score.</p>}</section>
    </div>

    <aside className="results-side"><section className="next-card glass"><span className="card-overline">YOUR NEXT SMALL WINS</span><h3>Make the next step count.</h3>{assessment.next_actions.length ? assessment.next_actions.slice(0, 3).map((action, index) => <div className="action-row" key={action.title}><span className="action-number">0{index + 1}</span><div><strong>{action.title}</strong><p>{action.rationale}</p><small>Evidence: {action.completion_evidence}</small></div></div>) : <p className="fine-print">No specific action was identified from the information provided.</p>}<button className="primary-button full-button" onClick={onUpdateProfile}>Update my profile <span>↗</span></button></section>
      <section className="evidence-card glass"><span className="card-overline">WHAT’S WORKING</span>{assessment.strengths.length ? assessment.strengths.map((strength) => <div className="strength-row" key={strength.label}><span aria-hidden="true">✓</span><div><strong>{strength.label}</strong><p>{strength.evidence}</p><small>{strength.confidence} confidence · student-provided evidence</small></div></div>) : <p className="fine-print">Add a skill or project to see supporting evidence here.</p>}</section>
      <section className="profile-links-card glass"><span className="card-overline">PUBLIC PROFILE SIGNALS</span><h3>More context, not a score.</h3>
        <div className="social-evidence-row"><div><strong>GitHub</strong><p>{assessment.profile_links.github.note}</p>{assessment.profile_links.github.profile_url && <a href={assessment.profile_links.github.profile_url} target="_blank" rel="noreferrer">Open profile ↗</a>}</div>
          {assessment.profile_links.github.status === "available" ? <div className="social-metrics"><span><strong>{assessment.profile_links.github.public_repositories ?? "—"}</strong><small>public repos</small></span><span><strong>{assessment.profile_links.github.recent_public_commits ?? "—"}</strong><small>commits observed</small></span></div> : <span className="social-status">{assessment.profile_links.github.status === "not_provided" ? "Not added" : assessment.profile_links.github.status === "not_found" ? "Not found" : "Unavailable"}</span>}
        </div>
        {assessment.profile_links.github.languages.length > 0 && <div className="social-languages"><small>PRIMARY LANGUAGES ACROSS PUBLIC REPOSITORIES</small><div className="match-pills">{assessment.profile_links.github.languages.map((language) => <span className="match-pill" key={language.name}>{language.name} · {language.repositories} {language.repositories === 1 ? "repo" : "repos"}</span>)}</div></div>}
        <div className="social-evidence-row linkedin-evidence"><div><strong>LinkedIn</strong><p>{assessment.profile_links.linkedin.note}</p>{assessment.profile_links.linkedin.profile_url && <a href={assessment.profile_links.linkedin.profile_url} target="_blank" rel="noreferrer">Open profile ↗</a>}</div><span className="social-status">{assessment.profile_links.linkedin.status === "provided" ? "Link detected" : "Not added"}</span></div>
        <p className="fine-print">These public signals are informational only, not proof of skill or hiring potential. GitHub commit counts are a limited recent public-event sample, not total commits; private activity is excluded.</p>
      </section>
      <button className="text-button rerun-button" onClick={onReassess} disabled={busy}>{busy ? "Refreshing…" : "↻  Reassess with current details"}</button></aside>
  </div>;
}
