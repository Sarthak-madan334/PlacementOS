# CampusProof — Product and Interface Design

## 1. Experience goal

The interface should quickly answer: **Where do I stand for this role, why, and what useful thing can I do next?** The score is supporting context; the clearest emphasis is eligibility, evidence, the biggest role-specific gap, and the next action.

## 2. Information architecture

### MVP routes/screens

1. **Landing / demo entry:** CampusProof value proposition, privacy note, primary “Check my readiness” action, and clearly labeled synthetic demo option.
2. **Profile setup:** academic details, target role, skills, and projects. Explain CGPA scale. Allow skipping resume.
3. **Resume review:** upload progress, parse warnings, extracted facts grouped by section, editable values, and explicit confirmation.
4. **Opportunity setup:** target role, optional company/JD, explicit eligibility rules when known, and sample opportunity selection for demo.
5. **Readiness results:** eligibility and reason first; readiness score and confidence; factor breakdown; matched/missing skills; evidence strengths; no more than three recommended next actions.
6. **Edit/reassess:** inputs remain editable; show when results are based on an older assessment snapshot.

Do not place an application tracker, social feed, or broad job-board navigation in MVP.

## 3. Visual system

- **Mood:** focused, optimistic, credible, student-first. Avoid corporate ATS density and gamified certainty.
- **Canvas:** deep ink/navy background with subtle violet/blue gradient illumination; ensure the initial dark palette remains legible.
- **Glass surfaces:** translucent panels with restrained backdrop blur, thin low-contrast borders, soft shadows, and layered gradient accents. Use opaque or less transparent surfaces behind dense text and forms so contrast stays strong.
- **Accent:** violet for primary actions and progress; teal for positive evidence; amber for caution/unknown; red for explicit hard-rule failure. Always pair color with label/icon/text.
- **Type:** legible sans-serif; strong page title, concise section labels, readable body size, tabular numerals for score. Avoid oversized decorative text in data views.
- **Shape:** consistent medium-radius cards and controls; use spacing and alignment to group information rather than card-on-card nesting.
- **Motion:** short, purposeful transitions only. Respect `prefers-reduced-motion`; no animated score increase implying an outcome guarantee.

## 4. Results hierarchy

Desktop: main results column with eligibility/readiness summary, factor breakdown and skills/evidence; narrower side column for “Your next step.” Mobile: single column, eligibility and next action near the top, compact labeled bars/lists instead of charts. The score includes `/100`, confidence, assessment context, and a clear “How this is calculated” disclosure with text-equivalent factor labels.

### Required content

- Eligibility badge: Eligible / Not eligible / More information needed, with exact reasons.
- Readiness score: score, confidence, assessment date, and factor contributions.
- Role match: matched, missing, and unknown terms; hide when no usable JD, with an invitation to add one.
- Evidence: distinguish self-reported skills from resume/project evidence.
- Gaps: distinguish “not shown in your evidence” from “you do not know this skill.”
- Actions: up to three concrete actions with a reason and what evidence would demonstrate completion.

## 5. States and copy behavior

- **Initial/empty:** explain why profile data helps; offer manual start and optional resume upload.
- **Loading:** skeletons for known content areas; upload/parse progress text; prevent accidental duplicate submission.
- **Validation:** field-level message, focus first invalid field, preserve entered values.
- **Parse warning/failure:** identify the file issue, retain manual workflow, provide retry and editable fallback.
- **API/network error:** plain-language message, retry action, preserve form. Do not show raw exceptions.
- **Unknown eligibility:** say what information is missing and how to provide it; never style as failure.
- **Not eligible:** state the failed explicit requirement and avoid implying the student lacks overall ability.
- **No JD/role requirements:** present general evidence snapshot and prompt to add a JD for role match.
- **Success:** confirm what was assessed and the saved time; avoid suggesting a hiring result.

## 6. Accessibility and responsive behavior

- Design and verify at 360 px, tablet, and desktop widths; forms and score content must not require horizontal scrolling.
- Use semantic headings, labeled form controls, keyboard-accessible upload and dialogs, visible focus, and meaningful link/button names.
- Provide text status in addition to color, score bars with accessible names/values, and reduced-motion behavior.
- Keep tap targets comfortable on mobile and place the primary action where it remains easy to reach without covering content.
