"use client";

import { useMemo, useState } from "react";
import { createAssessment, parseResume } from "@/lib/api";
import { ResultsView } from "./results-view";
import { demoProfile } from "@/lib/demo-data";
import type { Assessment, AssessmentRequest, ResumeParseResponse, StudentProfile, View } from "@/lib/contracts";

const navItems: { id: View; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Profile" },
  { id: "resume", label: "Resume" },
  { id: "opportunity", label: "Opportunity" },
];

const roleSuggestions = ["Software Engineer", "Software Developer", "Frontend Engineer", "Frontend Developer", "Backend Engineer", "Backend Developer", "Full-Stack Engineer", "Full-Stack Developer", "Web Developer", "Mobile App Developer", "iOS Developer", "Android Developer", "React Native Developer", "Flutter Developer", "Game Developer", "Embedded Systems Engineer", "Firmware Engineer", "DevOps Engineer", "Site Reliability Engineer", "Platform Engineer", "Cloud Engineer", "Cloud Architect", "Cybersecurity Analyst", "Security Engineer", "Penetration Tester", "Network Engineer", "Systems Administrator", "Database Administrator", "Data Engineer", "Analytics Engineer", "Data Analyst", "Business Intelligence Analyst", "Data Scientist", "Machine Learning Engineer", "AI Engineer", "NLP Engineer", "Computer Vision Engineer", "Research Engineer", "QA Engineer", "Software Test Engineer", "Automation Engineer", "Performance Engineer", "Solutions Architect", "Solutions Engineer", "Technical Support Engineer", "IT Support Specialist", "Product Manager", "Technical Product Manager", "Project Manager", "Program Manager", "Business Analyst", "Systems Analyst", "UX Designer", "UI Designer", "Product Designer", "UX Researcher", "Interaction Designer", "Graphic Designer", "Visual Designer", "Motion Designer", "Content Designer", "Technical Writer", "Developer Advocate", "Marketing Analyst", "Digital Marketing Specialist", "Growth Marketer", "Sales Engineer", "Financial Analyst", "Operations Analyst", "Consultant", "Research Analyst", "Mechanical Engineer", "Electrical Engineer", "Civil Engineer", "Electronics Engineer", "Chemical Engineer", "Biomedical Engineer", "Robotics Engineer", "Automation Engineer", "Hardware Engineer", "Other"];

const skillSuggestions = ["JavaScript", "TypeScript", "Python", "Java", "C", "C++", "C#", "Go", "Rust", "Kotlin", "Swift", "Dart", "PHP", "Ruby", "R", "SQL", "HTML", "CSS", "Bash", "React", "Next.js", "Angular", "Vue", "Svelte", "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot", ".NET", "React Native", "Flutter", "Tailwind CSS", "REST APIs", "GraphQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Supabase", "Firebase", "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Git", "GitHub", "GitHub Actions", "Linux", "CI/CD", "Machine Learning", "Data Analysis", "Pandas", "NumPy", "PyTorch", "TensorFlow", "LLMs", "Prompt Engineering", "Data Visualization", "Power BI", "Tableau", "Excel", "Figma", "User Research", "Wireframing", "Prototyping", "Accessibility", "Responsive Design", "UI Design", "UX Design", "Jest", "Playwright", "Pytest", "Selenium", "Unit Testing", "Integration Testing", "Agile", "Scrum", "Communication", "Writing", "Problem Solving", "Teamwork", "Leadership", "Project Management", "Public Speaking", "Critical Thinking", "Research", "Customer Support", "Stakeholder Management", "Product Strategy", "SEO", "Content Writing", "Digital Marketing", "Financial Modeling", "Statistics", "CAD", "AutoCAD", "SolidWorks", "MATLAB", "Embedded C", "Networking", "Cybersecurity", "Incident Response", "Requirements Analysis", "Documentation", "Time Management"];

function Ring({ score }: { score: number | null }) {
  return <div className="score-ring" style={{ "--score": `${score ?? 0}%` } as React.CSSProperties} role="img" aria-label={score === null ? "Readiness score unavailable" : `Readiness score ${score} out of 100`}><div><strong>{score ?? "—"}</strong><span>{score === null ? "unavailable" : "/ 100"}</span></div></div>;
}

export default function Home() {
  const [view, setView] = useState<View>("overview");
  const [profile, setProfile] = useState<StudentProfile>(demoProfile);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [fileName, setFileName] = useState("");
  const [parsedResume, setParsedResume] = useState<ResumeParseResponse | null>(null);
  const [parsing, setParsing] = useState(false);
  const [company, setCompany] = useState("Northstar Labs");
  const [jobDescription, setJobDescription] = useState("We’re looking for a frontend engineer comfortable with React, TypeScript, accessibility, and testing.");
  const [requiredSkills, setRequiredSkills] = useState("React, TypeScript, Accessibility, Testing");
  const [preferredSkills, setPreferredSkills] = useState("");
  const [minimumCgpa, setMinimumCgpa] = useState("");
  const [minimumCgpaScale, setMinimumCgpaScale] = useState("10");
  const [eligibleBranches, setEligibleBranches] = useState("");
  const [eligibleYears, setEligibleYears] = useState("");
  const skills = useMemo(() => profile.skills.split(",").map((skill) => skill.trim()).filter(Boolean), [profile.skills]);

  function buildAssessmentRequest(currentProfile: StudentProfile = profile, resume: ResumeParseResponse | null = parsedResume): AssessmentRequest {
    const list = (value: string) => value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
    const optionalNumber = (value: string) => value.trim() ? Number(value) : null;
    return {
      profile: {
        branch: currentProfile.branch,
        graduation_year: optionalNumber(currentProfile.graduationYear),
        cgpa: optionalNumber(currentProfile.cgpa),
        cgpa_scale: optionalNumber(currentProfile.cgpaScale),
        target_role: currentProfile.role,
        skills: currentProfile.skills.split(",").map((skill) => skill.trim()).filter(Boolean),
        github_profile_url: currentProfile.githubUrl || null,
        linkedin_profile_url: currentProfile.linkedinUrl || null,
        projects: currentProfile.project.trim() ? [{ title: "Project experience", description: currentProfile.project }] : [],
        ...(resume ? { resume_sections: resume.sections_detected } : {}),
      },
      opportunity: {
        title: currentProfile.role || company,
        description: jobDescription,
        required_skills: list(requiredSkills),
        preferred_skills: list(preferredSkills),
        minimum_cgpa: optionalNumber(minimumCgpa),
        cgpa_scale: optionalNumber(minimumCgpa) === null ? null : optionalNumber(minimumCgpaScale),
        eligible_branches: list(eligibleBranches),
        graduation_years: list(eligibleYears).map(Number).filter(Number.isInteger),
      },
    };
  }

  function updateProfile(key: keyof StudentProfile, value: string) {
    setProfile((current) => ({ ...current, [key]: value }));
    if (assessment) setNotice("Your profile changed. These results reflect the previous version.");
  }

  function useDemo() {
    setProfile(demoProfile);
    setAssessment(null);
    setParsedResume(null);
    setFileName("");
    setNotice("Synthetic demo profile loaded. No personal data is saved.");
    setError("");
  }

  async function assess() {
    if (!profile.branch || !profile.graduationYear || !profile.role || !profile.skills.trim()) {
      setError("Add your branch, graduation year, target role and at least one skill to continue.");
      setView("profile");
      return;
    }
    setError(""); setNotice(""); setBusy(true);
    try { setAssessment(await createAssessment(buildAssessmentRequest())); setView("results"); }
    catch (assessmentError) { setError(assessmentError instanceof Error ? `${assessmentError.message} Your entries remain in this session; you can retry or continue in fixture mode.` : "We couldn’t reach the assessment service. Your entries remain in this session; please retry."); }
    finally { setBusy(false); }
  }

  async function tryDemoAssessment() {
    setProfile(demoProfile);
    setParsedResume(null);
    setFileName("");
    setError("");
    setNotice("Synthetic sample data loaded. No profile or assessment is saved.");
    setBusy(true);
    try {
      setAssessment(await createAssessment(buildAssessmentRequest(demoProfile, null)));
    } catch (assessmentError) {
      setError(assessmentError instanceof Error ? assessmentError.message : "The sample assessment could not load.");
    } finally {
      setBusy(false);
    }
  }

  async function handleFile(file?: File) {
    if (!file) return;
    setError(""); setNotice("");
    const accepted = /\.(pdf|docx|txt)$/i.test(file.name);
    if (!accepted) { setError("Choose a PDF, DOCX or TXT file. You can still continue without a resume."); return; }
    if (file.size > 5 * 1024 * 1024) { setError("That file is over 5 MB. Choose a smaller file or continue manually."); return; }
    setFileName(file.name);
    setParsedResume(null);
    if (process.env.NEXT_PUBLIC_DEMO_MODE !== "false") {
      setNotice("Fixture mode does not upload or parse files. You can continue with your profile details.");
      return;
    }
    setParsing(true);
    try {
      const result = await parseResume(file);
      setParsedResume(result);
      setNotice("Resume suggestions are ready for review. Nothing has been added to your profile yet.");
    } catch (parseError) {
      setError(parseError instanceof Error ? `${parseError.message} You can still continue manually.` : "We couldn’t parse that file. You can still continue manually.");
    } finally {
      setParsing(false);
    }
  }

  function applyResumeSuggestions() {
    if (!parsedResume) return;
    const extractedSkills = parsedResume.candidate_facts.skills.map((skill) => skill.display_name);
    const combinedSkills = [...new Set([...skills, ...extractedSkills])].join(", ");
    const extractedProjects = parsedResume.candidate_facts.projects.map((project) => `${project.title}: ${project.description}`).join("\n\n");
    updateProfile("skills", combinedSkills);
    if (extractedProjects) updateProfile("project", [profile.project, extractedProjects].filter(Boolean).join("\n\n"));
    setNotice("Suggestions copied into editable fields. Review them before assessing.");
  }

  const headline = view === "profile" ? "Build your profile." : view === "resume" ? "Review your resume." : view === "opportunity" ? "Choose a role to explore." : "Your readiness snapshot.";
  const subhead = view === "overview" ? "See how your skills and project experience align with the roles you want." : view === "profile" ? "Add the details that help us understand your experience." : view === "resume" ? "Resume upload is optional. You stay in control of every detail." : view === "opportunity" ? "Use a role description to make your match more specific." : "A summary of the evidence you shared—not a hiring prediction.";

  return <main className="app-shell">
    <header className="site-nav glass">
      <a className="site-brand" href="#home" onClick={(event) => { event.preventDefault(); setView("overview"); }} aria-label="CampusProof home">campusproof<span>.</span></a>
      <nav aria-label="Main navigation">{navItems.map((item) => <button key={item.id} className={`site-nav-link ${view === item.id ? "active" : ""}`} onClick={() => setView(item.id)}>{item.label}</button>)}<button className={`site-nav-link ${view === "results" ? "active" : ""}`} onClick={() => setView("results")}>Readiness</button></nav>
      <div className="nav-actions"><button className="nav-cta" onClick={() => setView("profile")}>Get started</button></div>
    </header>

    <section className="main-area">
      <div className="content-wrap">
        {view !== "overview" && <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line"/>YOUR CAREER, IN FOCUS</div><h1>{headline}</h1><p>{subhead}</p></div>{view !== "results" && <span className="step-pill">{view === "profile" ? "01" : view === "resume" ? "02" : "03"}<span> / 03</span></span>}</div>}
        {notice && <div className="notice" role="status"><span>ⓘ</span>{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
        {error && <div className="alert" role="alert"><span>!</span>{error}</div>}
        {view === "results" && assessment?.source === "fixture" && <div className="fixture-disclosure" role="status">Sample result for demonstration only. Fixture mode does not calculate a personal score from edited details.</div>}

        {view === "overview" && <>
          <section className="landing-hero">
            <div className="landing-copy">
              <div className="landing-eyebrow"><span/>YOUR CAREER, IN FOCUS</div>
              <h1>Know where<br/>you <em>stand.</em></h1>
              <p>See which skills and experience match the role you want, and what to work on next.</p>
              <div className="landing-actions"><button className="landing-primary" onClick={() => setView("profile")}>Build my profile <span aria-hidden="true">→</span></button><button className="landing-secondary" onClick={() => { useDemo(); setView("profile"); }}>Try the demo</button></div>
              <div className="landing-note">Resume is optional. Start with your profile details.</div>
            </div>
            <aside className="evidence-panel match-preview" aria-label="Example role match preview">
              <div className="evidence-top"><span>EXAMPLE SNAPSHOT</span><span>Sample data</span></div>
              <div className="match-title"><div><span className="card-overline">ROLE MATCH</span><h2>Frontend engineer</h2></div><span className="match-score">78<span>%</span></span></div>
              <div className="match-meter" role="img" aria-label="Example role match: 78 percent"><span/></div>
              <p className="match-caption">A useful starting point—not a hiring prediction.</p>
              <div className="evidence-row"><span>React projects</span><span className="evidence-status supported"><i/>In profile</span></div>
              <div className="evidence-row"><span>Testing experience</span><span className="evidence-status gap"><i/>To explore</span></div>
              <button className="preview-link" onClick={() => { useDemo(); setView("profile"); }}>Explore the example <span aria-hidden="true">→</span></button>
            </aside>
          </section>
          <section className="landing-workspace">
            <div className="workspace-heading"><div><span className="card-overline">YOUR WORKSPACE · START ANYWHERE</span><h2>A few details<br/><em>make it yours.</em></h2></div><span>Resume is optional</span></div>
            <div className="workspace-rows">
              <button className="workspace-row" onClick={() => setView("profile")}><span className="row-number">01</span><span className="row-copy"><strong>Tell us about yourself</strong><small>Add your target role, skills and projects.</small></span><span className="row-arrow" aria-hidden="true">→</span></button>
              <button className="workspace-row" onClick={() => setView("resume")}><span className="row-number">02</span><span className="row-copy"><strong>Add resume details</strong><small>Optional. You can continue without uploading.</small></span><span className="row-arrow" aria-hidden="true">→</span></button>
              <button className="workspace-row" onClick={() => setView("opportunity")}><span className="row-number">03</span><span className="row-copy"><strong>Explore a role</strong><small>Compare your experience with an opportunity.</small></span><span className="row-arrow" aria-hidden="true">→</span></button>
            </div>
          </section>
          <section className="how-section" id="how-it-works" aria-labelledby="how-heading">
            <div className="how-intro"><span className="card-overline">A SIMPLE PLACE TO BEGIN</span><h2 id="how-heading">From “where do I stand?”<br/><em>to a clear next step.</em></h2><p>No perfect resume required. Start with what you know, then build a more specific picture at your own pace.</p></div>
            <div className="how-steps">
              <button className="how-step" onClick={() => setView("profile")}><span className="how-step-top"><span>01</span><span aria-hidden="true">↗</span></span><span className="how-step-icon profile-icon" aria-hidden="true"><i/><i/><i/></span><strong>Share your starting point</strong><small>Add your studies, skills and projects. Skip anything you’re not ready to share.</small></button>
              <button className="how-step" onClick={() => setView("opportunity")}><span className="how-step-top"><span>02</span><span aria-hidden="true">↗</span></span><span className="how-step-icon role-icon" aria-hidden="true"><i/><i/></span><strong>Choose a role to explore</strong><small>Compare your experience with a role description—or begin with a general snapshot.</small></button>
              <button className="how-step" onClick={() => setView("results")}><span className="how-step-top"><span>03</span><span aria-hidden="true">↗</span></span><span className="how-step-icon next-icon" aria-hidden="true"><i/><i/><i/></span><strong>See what to do next</strong><small>Understand what’s supported, what’s missing and which small step could help.</small></button>
            </div>
            <div className="how-footnote"><span aria-hidden="true">ⓘ</span> Your snapshot is a coaching aid, not a hiring decision. Missing evidence is never treated as proof that you lack a skill.</div>
          </section>
        </>}

        {view === "profile" && <div className="form-layout">
          <section className="form-card glass">
            <div className="form-section-title"><span className="number">01</span><div><h2>Start with the basics</h2><p>Required details help frame your readiness snapshot.</p></div></div>
            <div className="form-grid">
              <label className="field full">Target role <span className="required">*</span><input list="role-suggestions" autoComplete="off" value={profile.role} onChange={(e) => updateProfile("role", e.target.value)} placeholder="Type a role, e.g. Data analyst"/><datalist id="role-suggestions">{roleSuggestions.map((role) => <option key={role} value={role}/>)}</datalist><small>Start typing for role suggestions, or enter any title.</small></label>
              <label className="field">Branch / degree <span className="required">*</span><input value={profile.branch} onChange={(e) => updateProfile("branch", e.target.value)} placeholder="e.g. Computer Science"/></label>
              <label className="field">Graduation year <span className="required">*</span><select value={profile.graduationYear} onChange={(e) => updateProfile("graduationYear", e.target.value)}><option value="">Select year</option>{[2025,2026,2027,2028,2029,2030].map((year) => <option key={year}>{year}</option>)}</select></label>
              <label className="field">CGPA <span className="optional">OPTIONAL</span><input type="number" min="0" max={profile.cgpaScale} step="0.01" value={profile.cgpa} onChange={(e) => updateProfile("cgpa", e.target.value)} placeholder="e.g. 8.2"/></label>
              <label className="field">Scale<select value={profile.cgpaScale} onChange={(e) => updateProfile("cgpaScale", e.target.value)}><option value="10">Out of 10</option><option value="4">Out of 4</option><option value="100">Out of 100</option></select></label>
              <label className="field full">Skills <span className="required">*</span><input list="skill-suggestions" value={profile.skills} onChange={(e) => updateProfile("skills", e.target.value)} placeholder="Type or enter skills separated by commas"/><datalist id="skill-suggestions">{skillSuggestions.map((skill) => <option key={skill} value={skill}/>)}</datalist><small>Broad suggestions across engineering, data, design, business and transferable skills. Add any skill you want.</small><div className="skill-pills">{skills.slice(0, 6).map((skill) => <span key={skill}>{skill}<button onClick={() => updateProfile("skills", skills.filter((item) => item !== skill).join(", "))} aria-label={`Remove ${skill}`}>×</button></span>)}</div></label>
              <label className="field full">Project or experience <span className="optional">OPTIONAL</span><textarea rows={4} value={profile.project} onChange={(e) => updateProfile("project", e.target.value)} placeholder="What did you make, contribute to, or learn?"/><small>Specific contributions help describe your evidence more clearly.</small></label>
              <label className="field">GitHub profile <span className="optional">OPTIONAL</span><input type="url" value={profile.githubUrl} onChange={(e) => updateProfile("githubUrl", e.target.value)} placeholder="https://github.com/username"/><small>We check public repositories, primary languages and a limited sample of recent public commits.</small></label>
              <label className="field">LinkedIn profile <span className="optional">OPTIONAL</span><input type="url" value={profile.linkedinUrl} onChange={(e) => updateProfile("linkedinUrl", e.target.value)} placeholder="https://linkedin.com/in/your-name"/><small>We detect the link only; LinkedIn content and activity are not accessed.</small></label>
              <p className="field full profile-lookup-note">Links are checked only when you build a snapshot. Results are temporary and not saved.</p>
            </div>
            <div className="form-actions"><button className="text-button" onClick={() => setView("overview")}>← Back</button><button className="primary-button" onClick={() => { if (!profile.branch || !profile.graduationYear || !profile.role || !profile.skills.trim()) { setError("Fill the required fields before continuing."); return; } setError(""); setView("resume"); }}>Continue to resume <span>→</span></button></div>
          </section>
          <aside className="tip-card glass"><span className="tip-icon">✳</span><span className="card-overline">A QUICK NOTE</span><h3>Evidence over assumptions.</h3><p>Only requirements stated by an opportunity can determine eligibility. Missing information stays unknown—it isn’t treated as a failure.</p><div className="tip-divider"/><small>YOUR INFORMATION ISN’T SAVED IN THIS DEMO</small></aside>
        </div>}

        {view === "resume" && <div className="form-layout"><section className="form-card glass"><div className="form-section-title"><span className="number">02</span><div><h2>Add resume evidence</h2><p>Optional. Review every suggestion before adding it to your profile.</p></div></div><label className="upload-zone" htmlFor="resume-file"><span className="upload-symbol">↑</span><strong>{parsing ? "Reading your resume…" : fileName || "Choose a resume to review"}</strong><span>or <u>browse files</u></span><small>PDF, DOCX or TXT · Up to 5 MB</small><input id="resume-file" type="file" accept=".pdf,.docx,.txt,application/pdf" disabled={parsing} onChange={(event) => void handleFile(event.target.files?.[0])}/></label>{fileName && <div className="review-panel"><div className="review-heading"><span>▤</span><div><strong>{parsedResume ? "Review extracted suggestions" : parsing ? "Parsing resume" : "Manual review"}</strong><small>{parsedResume ? `${parsedResume.sections_detected.length} sections detected · nothing added yet` : "No resume text is stored by this preview."}</small></div><span className="unknown-pill">{parsedResume ? "REVIEW" : process.env.NEXT_PUBLIC_DEMO_MODE === "false" ? "PENDING" : "DEMO ONLY"}</span></div>{parsedResume ? <><p className="resume-review-copy">The parser found these skills and projects. Choose which suggestions to copy, then review them in your editable profile fields.</p><div className="parsed-suggestions"><strong>Skills found</strong><div className="skill-preview">{parsedResume.candidate_facts.skills.length ? parsedResume.candidate_facts.skills.map((skill) => <span key={skill.normalized_name}>{skill.display_name}</span>) : <small>No skills from the supported vocabulary were detected.</small>}</div>{parsedResume.candidate_facts.projects.map((project) => <div className="parsed-project" key={project.title}><strong>{project.title}</strong><small>{project.description}</small></div>)}{parsedResume.warnings.map((warning) => <small className="parse-warning" key={warning}>{warning}</small>)}</div><button className="inline-link" onClick={applyResumeSuggestions}>Add suggestions to editable profile fields <span>→</span></button></> : <p>{process.env.NEXT_PUBLIC_DEMO_MODE === "false" ? "The file is processed in memory for this preview only. If parsing fails, continue with manual entry." : "Fixture mode doesn’t send files to the parser. You can continue with profile details instead."}</p>}</div>}<div className="manual-note"><span>↗</span><p><strong>Prefer not to upload?</strong><br/>Your profile details and project description are enough to continue.</p></div><div className="form-actions"><button className="text-button" onClick={() => setView("profile")}>← Back to profile</button><button className="primary-button" onClick={() => setView("opportunity")}>Continue to role <span>→</span></button></div></section><aside className="tip-card glass"><span className="tip-icon">⌁</span><span className="card-overline">YOU’RE IN CONTROL</span><h3>Your resume stays yours.</h3><p>Resume text is used only for this preview parse and is not stored. Extracted details remain suggestions until you review them.</p><div className="tip-divider"/><small>UPLOAD IS OPTIONAL · 5 MB MAXIMUM</small></aside></div>}

        {view === "opportunity" && <div className="form-layout"><section className="form-card glass"><div className="form-section-title"><span className="number">03</span><div><h2>Set your direction</h2><p>Use an opportunity to make your snapshot more specific. Eligibility is checked only against criteria you enter explicitly.</p></div></div><div className="form-grid">
          <label className="field full">Target role <input value={profile.role} onChange={(event) => updateProfile("role", event.target.value)} placeholder="e.g. Frontend engineer"/></label>
          <label className="field full">Company <span className="optional">OPTIONAL</span><input value={company} onChange={(event) => setCompany(event.target.value)} placeholder="Company name"/></label>
          <label className="field full">Role description <span className="optional">OPTIONAL</span><textarea rows={5} value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} placeholder="Paste role requirements here"/><small>Role description is used to find familiar skills; it cannot establish hard eligibility rules by itself.</small></label>
          <label className="field full">Required skills <span className="optional">OPTIONAL</span><input value={requiredSkills} onChange={(event) => setRequiredSkills(event.target.value)} placeholder="React, SQL, testing"/><small>Separate explicit requirements with commas. Unrecognized terms are shown for review, not scored as a fail.</small></label>
          <label className="field full">Preferred skills <span className="optional">OPTIONAL</span><input value={preferredSkills} onChange={(event) => setPreferredSkills(event.target.value)} placeholder="Docker, accessibility"/></label>
          <div className="criteria-divider field full"><span>Explicit eligibility rules</span><small>Leave blank when the opportunity doesn’t state a rule.</small></div>
          <label className="field">Minimum CGPA <span className="optional">OPTIONAL</span><input type="number" min="0" max={minimumCgpaScale} step="0.01" value={minimumCgpa} onChange={(event) => setMinimumCgpa(event.target.value)} placeholder="No minimum stated"/></label>
          <label className="field">CGPA scale<select value={minimumCgpaScale} onChange={(event) => setMinimumCgpaScale(event.target.value)}><option value="10">Out of 10</option><option value="4">Out of 4</option><option value="100">Out of 100</option></select></label>
          <label className="field full">Eligible branches <span className="optional">OPTIONAL</span><input value={eligibleBranches} onChange={(event) => setEligibleBranches(event.target.value)} placeholder="e.g. Computer Science, Information Technology"/><small>Comma-separated; compare against your profile branch.</small></label>
          <label className="field full">Eligible graduation years <span className="optional">OPTIONAL</span><input value={eligibleYears} onChange={(event) => setEligibleYears(event.target.value)} placeholder="e.g. 2026, 2027"/></label>
          <div className="field full eligibility-callout"><span>ⓘ</span><p><strong>Missing criteria stay unknown.</strong><br/>No minimum GPA, branch, or graduation rule is inferred from the job-description text.</p></div>
        </div><div className="form-actions"><button className="text-button" onClick={() => setView("resume")}>← Back</button><button className="primary-button" onClick={assess} disabled={busy}>{busy ? <><span className="spinner"/> Building your snapshot…</> : <>See my readiness <span>↗</span></>}</button></div></section><aside className="tip-card glass"><span className="tip-icon">◎</span><span className="card-overline">YOUR PROFILE</span><h3>{profile.role || "Your target role"}</h3><p>{profile.branch || "Add your degree"} · Class of {profile.graduationYear || "—"}</p><div className="skill-preview">{skills.slice(0, 5).map((skill) => <span key={skill}>{skill}</span>)}</div><div className="tip-divider"/><button className="inline-link" onClick={() => setView("profile")}>Edit profile details <span>↗</span></button></aside></div>}

        {view === "results" && <ResultsView assessment={assessment} role={profile.role} busy={busy} onBuildProfile={() => setView("profile")} onTryDemo={tryDemoAssessment} onUpdateProfile={() => setView("profile")} onReassess={assess}/>}
      </div>
    </section>
    <footer className="site-footer">
      <div className="footer-inner"><div className="footer-links"><a href="#how-it-works">About / How it works</a><a href="https://github.com/Sarthak-madan334/PlacementOS" target="_blank" rel="noreferrer">GitHub <span aria-hidden="true">↗</span></a><button onClick={() => setView("profile")}>Get started <span aria-hidden="true">→</span></button></div><div className="footer-bottom"><a className="footer-mark" href="#home" onClick={(event) => { event.preventDefault(); setView("overview"); window.scrollTo({ top: 0, behavior: "smooth" }); }} aria-label="CampusProof, back to top">C</a><span>© {new Date().getFullYear()} CampusProof. Built for clearer next steps.</span><span className="footer-disclaimer">Student-first · Evidence-led · You stay in control</span></div></div>
    </footer>
  </main>;
}
