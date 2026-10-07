import type { Assessment, StudentProfile } from "./contracts";

export const demoProfile: StudentProfile = {
  branch: "Computer Science & Engineering",
  graduationYear: "2027",
  cgpa: "8.4",
  cgpaScale: "10",
  role: "Frontend Engineer",
  skills: "TypeScript, React, JavaScript, CSS, Git",
  project: "Built a responsive campus events dashboard with React and a REST API.",
};

export const demoAssessment: Assessment = {
  id: "demo-cp-v1-001",
  eligibility: { status: "unknown", reasons: [{ code: "criteria_not_provided", message: "Add an opportunity’s explicit criteria to check eligibility. No requirements were assumed." }] },
  readiness: {
    score: 78,
    confidence: "medium",
    scoring_version: "cp-v1",
    factors: [
      { key: "role_skill_coverage", label: "Role skill coverage", score: 82, weight: 0.3, available: true },
      { key: "project_evidence", label: "Project evidence", score: 86, weight: 0.25, available: true },
      { key: "resume_clarity", label: "Resume clarity", score: 65, weight: 0.2, available: true },
      { key: "technical_evidence", label: "Technical evidence", score: 76, weight: 0.15, available: true },
      { key: "profile_completeness", label: "Profile completeness", score: 80, weight: 0.1, available: true },
    ],
    excluded_factors: [],
  },
  role_match: { score: 78, matched: ["TypeScript", "React", "JavaScript"], missing: ["Testing"], unknown: ["Accessibility"] },
  strengths: [
    { label: "React", evidence: "Listed in profile and supported by a project description", confidence: "medium" },
    { label: "Project delivery", evidence: "Responsive dashboard described with a REST API", confidence: "medium" },
  ],
  gaps: [{ label: "Testing", importance: "required", reason: "Testing appears in the sample role requirements but no evidence was supplied." }],
  next_actions: [
    { title: "Add testing evidence", rationale: "Testing is a role requirement without supporting evidence yet.", completion_evidence: "Link a project test suite or describe a test you wrote." },
    { title: "Upload a resume", rationale: "A resume can provide more context for your experience and skills.", completion_evidence: "Review the extracted details and confirm what is accurate." },
    { title: "Add an opportunity description", rationale: "A specific job description makes role matching more useful.", completion_evidence: "Paste the role requirements you want to assess against." },
  ],
  created_at: new Date().toISOString(),
};
