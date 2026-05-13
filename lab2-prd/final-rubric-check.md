# SecondServe Campus final rubric check

## Assignment constraints from the lab document

- Deliverable is a PRD for a software application.
- Scope and complexity must be realistic for completion by the end of class.
- Submission format can be txt, markdown, or Word document.
- Upload destination is the D2L dropbox, not email or shared drive.
- Instructor will grade strictly with AI assistance and compare deliverables.

## PRD structure research used

- Ian Nuttall's referenced PRD template: product overview, goals, personas, functional requirements, UX, narrative, success metrics, technical considerations, milestones, and user stories. Source: https://gist.github.com/iannuttall/f3d425ad5610923a32397a687758ebf2
- Atlassian/Confluence PRD guidance: goals, background, assumptions, user stories, user interaction/design, open questions, and out-of-scope boundaries. Source: https://www.atlassian.com/agile/requirements
- Aha! PRD guidance: product vision, target personas, use cases, core capabilities, release/feature requirements, assumptions, scope, dependencies, and milestones. Source: https://www.aha.io/roadmapping/guide/templates/create/prd
- Miro PRD guidance: overview, goals, success metrics, target audience, features, UX, assumptions, dependencies, out-of-scope, owner/status/version. Source: https://miro.com/templates/template/prd/
- Dovetail/Cavaro style guidance: problem statement, goals, metrics, user stories, functional requirements, technical requirements, out-of-scope, assumptions, and testable acceptance criteria. Sources: https://dovetail.com/product-management/product-requirements-document/ and https://www.cavaro.io/templates/product-requirements-document

## Grading risk checklist

- [x] No obvious internal inconsistencies: user roles, scope, features, data model, and success metrics refer to the same campus-only MVP. Post-critique fix applied to align no-show handling across FR-019, FR-020, and US-014.
- [x] Architecture is feasible: Next.js, Supabase Postgres, Supabase Auth, Tailwind, Resend, and Vercel are a coherent student-friendly stack.
- [x] Architecture can scale to pilot level: indexes, atomic reservations, Supabase scheduled expiry, role policies, and future `campus_id` are included.
- [x] Business case is concrete: campus food waste, student affordability, organizer coordination, and admin impact reporting are all named.
- [x] Competitive landscape is addressed: the PRD distinguishes the campus-only model from broader surplus-food marketplaces and charity recovery tools.
- [x] Idea is specific and creative: not a generic todo, notes, or budgeting app.
- [x] Important details are included: data model, user flows, edge cases, non-functional requirements, accessibility, privacy compliance, risks, milestones, traceability, and user stories.
- [x] Scope is class-realistic: no native mobile app, payments, delivery, AI prediction, or multi-campus platform in MVP.
- [x] User stories are testable and include acceptance criteria.
- [x] Authentication and authorization are addressed.
- [x] Brand/design direction is included and supported by a separate brand kit and HTML prototype.

## Post-critique fixes applied

- Fixed no-show timing contradiction by allowing organizers to mark no-shows after pickup start, while returning portions only before pickup end.
- Promoted allergen and safety-sensitive edit rules into FR-007.
- Added competitive landscape and differentiation.
- Added Canadian privacy compliance, PIPEDA/Alberta PIPA note, and 12-month retention policy.
- Replaced unnamed scheduled job language with Supabase `pg_cron` scheduled Edge Functions.
- Added a requirements traceability matrix.
- Specified 30-minute organizer reminder timing.
- Specified 6-character hashed pickup code requirements.
- Removed repeated no-show limiting from risk mitigation because it is not implemented in the MVP.
- Added English-only MVP localization stance.
- Patched the prototype pickup code generator to output 6 uppercase alphanumeric characters.
- Added canonical dietary and allergen tag taxonomies to the PRD data model.

## Remaining submission note

The primary file to submit is `secondserve-campus-prd.md`. The brand kit and prototype can be attached as supporting materials if the D2L dropbox allows multiple files.
