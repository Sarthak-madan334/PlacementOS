import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CampusProof — Know where you stand",
  description: "An evidence-backed readiness workspace for your next campus opportunity.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
