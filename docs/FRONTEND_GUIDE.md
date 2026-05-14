# Frontend Guide

## Overview

The frontend lives in `case-mirror/` and is a static app built with plain HTML, CSS, and JavaScript.

Main files:

- [case-mirror/index.html](../case-mirror/index.html)
- [case-mirror/styles.css](../case-mirror/styles.css)
- [case-mirror/app.js](../case-mirror/app.js)

This approach keeps the project lightweight, easy to host, and easy to demo without a frontend build system.

## Frontend Responsibilities

The frontend is responsible for:

- rendering the user journey
- storing the current session locally
- collecting case setup inputs
- showing the generated brief and critique
- handling judge Q&A rehearsal
- showing the final readiness report
- managing browser microphone/webcam affordances when available

## Current Page Flow

### Home

Purpose:

- explain the product value quickly
- establish visual polish and credibility
- give users a fast path into the app

### Setup

Purpose:

- collect the case prompt
- collect judging criteria
- collect the team recommendation
- collect optional context such as company, industry, and slide outline

### Brief

Purpose:

- summarize the case problem
- show likely judge priorities
- critique the recommendation
- surface assumptions, risks, and suggested story arc

### Q&A

Purpose:

- walk the user through five judge-style questions
- generate adaptive follow-up questions
- collect typed or spoken answers
- surface live answer metrics

### Report

Purpose:

- summarize readiness
- present category scores
- highlight strengths and weaknesses
- identify missed criteria and weak assumptions
- suggest next practice steps

## Routing Model

Routing is hash-based and handled in `app.js`.

Current top-level routes:

- `#/`
- `#/setup`
- `#/brief`
- `#/rehearsal`
- `#/report`

This makes the app easy to serve from static hosting without additional routing infrastructure.

## State Model

The frontend uses a single local session object.

Session state includes:

- case setup inputs
- generated case brief
- recommendation critique
- generated questions
- user answers and follow-ups
- generated final report
- timing values for rehearsal metrics

Benefits:

- no login required
- fewer moving parts during demos
- easy restart with the same inputs
- resilience across refreshes

Tradeoff:

- state is device-local and single-session only

## Browser Capability Strategy

### Typed Input

Typed answers are the required baseline. The app should remain fully usable even if microphone or webcam access is denied.

### Microphone

The frontend attempts browser speech recognition when available. If recognition is not supported or fails, the UI keeps typed entry as the fallback path.

### Webcam

The webcam is an optional preview only. It supports presentation rehearsal realism but should never be required for the core flow.

## Styling Notes

`styles.css` contains both the older design system and the newer `cm-` prefixed design layer. The newer layer is the active design language in the current home, report, and flow-specific templates.

Visual direction in the current app:

- deep navy and teal accents
- editorial typography
- premium card layouts
- dashboard-like report sections
- stronger landing-page visuals than the earlier revision

## Frontend Maintenance Notes

- Keep element IDs stable when changing event-driven controls in `app.js`.
- Preserve typed-answer fallback.
- Avoid adding a build step unless the project clearly outgrows static delivery.
- Keep safety wording visible wherever metrics could be misread as judgment.
- Prefer progressive enhancement over hard dependencies on microphone or webcam access.
