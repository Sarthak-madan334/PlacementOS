export type View = "overview" | "profile" | "resume" | "opportunity" | "results";
export type Eligibility = "eligible" | "not_eligible" | "unknown";

export interface Assessment {
  id: string;
  source?: "fixture" | "live";
  eligibility: { status: Eligibility; reasons: { code: string; message: string }[] };
  readiness: {
    score: number | null;
    confidence: "low" | "medium" | "high";
    scoring_version: "cp-v1";
    factors: { key: string; label: string; score: number | null; weight: number; available: boolean; evidence?: string[]; explanation?: string }[];
    excluded_factors: string[];
  };
  role_match: { score: number | null; matched: string[]; missing: string[]; unknown: string[]; preferred?: string[]; explanation?: string };
  profile_links: {
    github: { status: "not_provided" | "available" | "not_found" | "unavailable"; profile_url: string | null; public_repositories: number | null; recent_public_commits: number | null; activity_window_days: number; languages: { name: string; repositories: number }[]; note: string };
    linkedin: { status: "not_provided" | "provided"; profile_url: string | null; note: string };
  };
  strengths: { label: string; evidence: string; confidence: string }[];
  gaps: { label: string; importance: string; reason: string }[];
  next_actions: { title: string; rationale: string; completion_evidence: string }[];
  created_at: string;
}

export interface AssessmentRequest {
  profile: {
    branch: string;
    graduation_year: number | null;
    cgpa: number | null;
    cgpa_scale: number | null;
    target_role: string;
    skills: string[];
    projects: { title: string; description: string; url?: string }[];
    github_profile_url?: string | null;
    linkedin_profile_url?: string | null;
  };
  opportunity: {
    title?: string;
    description?: string;
    required_skills: string[];
    preferred_skills: string[];
    minimum_cgpa: number | null;
    cgpa_scale: number | null;
    eligible_branches: string[];
    graduation_years: number[];
  };
}

export interface ResumeParseResponse {
  candidate_facts: {
    skills: { display_name: string; normalized_name: string; source_snippet?: string | null }[];
    projects: { title: string; description: string; url?: string | null }[];
  };
  sections_detected: string[];
  quality_signals: { signal: string; category: string; observed_text: string; rule_or_reason: string }[];
  warnings: string[];
}

export interface StudentProfile {
  branch: string;
  graduationYear: string;
  cgpa: string;
  cgpaScale: string;
  role: string;
  skills: string;
  project: string;
  githubUrl: string;
  linkedinUrl: string;
}
