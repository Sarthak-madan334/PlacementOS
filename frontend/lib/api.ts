import { demoAssessment } from "./demo-data";
import type { Assessment } from "./contracts";

const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

export async function createAssessment(): Promise<Assessment> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 700));
    return { ...demoAssessment, id: `demo-${Date.now()}`, created_at: new Date().toISOString() };
  }

  throw new Error("Live assessment is not connected yet. Switch to demo mode or try again later.");
}
