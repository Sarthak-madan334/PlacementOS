export type View = "overview" | "profile" | "resume" | "opportunity" | "results";
export type Eligibility = "eligible" | "not_eligible" | "unknown";

export interface Assessment {
  id: string;
  eligibility: { status: Eligibility; reasons: { code: string; message: string }[] };
  readiness: {
    score: number;
    confidence: "low" | "medium" | "high";
    scoring_version: "cp-v1";
    factors: { key: string; label: string; score: number; weight: number; available: boolean }[];
    excluded_factors: string[];
  };
  role_match: { score: number | null; matched: string[]; missing: string[]; unknown: string[] };
  strengths: { label: string; evidence: string; confidence: string }[];
  gaps: { label: string; importance: string; reason: string }[];
  next_actions: { title: string; rationale: string; completion_evidence: string }[];
  created_at: string;
}

export interface StudentProfile {
  branch: string;
  graduationYear: string;
  cgpa: string;
  cgpaScale: string;
  role: string;
  skills: string;
  project: string;
}
