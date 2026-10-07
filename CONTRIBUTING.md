# Contributing to PlacementOS

## Member-owned documentation

- Sarthak works in `documentation/sarthak/`.
- Aarush works in `documentation/aarush/`.
- Sejal works in `documentation/sejal/`.
- Shared product and interface contracts live in `documentation/shared/`.

Keep member-specific edits in the assigned folder. If a task requires changing a shared contract, propose the change in the relevant shared document and update affected member docs/fixtures in the same pull request. Avoid editing another member's phase file unless coordinating the change with them.

## Low-conflict Git workflow

1. Start from the latest `main` branch.
2. Create a branch with the owner's name, for example `docs/sarthak/profile-flow`, `docs/aarush/scoring-contract`, or `docs/sejal/release-checklist`.
3. Edit files in the owner's folder; keep changes focused and do not rename another owner's files.
4. Pull/rebase the latest `main` before publishing if another pull request has merged.
5. Push the branch and open a pull request to `main`; ask the relevant owner to review changes to shared contracts.
6. Resolve conflicts in the branch, then merge only after the documentation links and contract examples agree.

GitHub permissions apply to the repository, not individual folders. Each member needs repository write access to push a branch. Folder ownership and review rules reduce overlap but do not technically prevent a writer from changing another folder. Protecting `main` and requiring pull requests must be enabled in repository settings by an administrator. GitHub usernames for all members are needed to configure active `CODEOWNERS` review routing or grant access.

## Documentation checks

- Keep filenames descriptive and inside the assigned directory.
- Use relative Markdown links and verify they resolve before opening a pull request.
- Keep examples synthetic; never commit real resumes, credentials, or student records.
- Update `documentation/shared/PHASES.md` if a phase name, owner, or deliverable changes.
