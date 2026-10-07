import { demoAssessment, demoProfile } from "./demo-data";
import type { Assessment, AssessmentRequest, ResumeParseResponse } from "./contracts";

const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export async function createAssessment(input?: AssessmentRequest): Promise<Assessment> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 700));
    return { ...demoAssessment, id: `demo-${Date.now()}`, created_at: new Date().toISOString(), source: "fixture" };
  }

  const request: AssessmentRequest = input ?? {
    profile: {
      branch: demoProfile.branch,
      graduation_year: Number(demoProfile.graduationYear),
      cgpa: Number(demoProfile.cgpa),
      cgpa_scale: Number(demoProfile.cgpaScale),
      target_role: demoProfile.role,
      skills: demoProfile.skills.split(",").map((skill) => skill.trim()).filter(Boolean),
      projects: [{ title: "Campus events dashboard", description: demoProfile.project }],
    },
    opportunity: { title: demoProfile.role, required_skills: ["React", "TypeScript", "Accessibility", "Testing"], preferred_skills: [], minimum_cgpa: null, cgpa_scale: null, eligible_branches: [], graduation_years: [] },
  };
  const response = await fetch(`${apiBase}/api/v1/assessments/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === "string" ? error.detail : "The assessment service could not complete your request.");
  }
  return { ...(await response.json() as Assessment), source: "live" };
}

export async function parseResume(file: File): Promise<ResumeParseResponse> {
  const form = new FormData();
  form.set("file", file);
  const response = await fetch(`${apiBase}/api/v1/resumes/parse`, {
    method: "POST",
    body: form,
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === "string" ? error.detail : "We couldn’t read that resume. You can continue manually.");
  }
  return response.json() as Promise<ResumeParseResponse>;
}
