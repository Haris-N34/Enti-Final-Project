# Limitations And Future Work

## Current Limitations

- The local demo profile is not production authentication.
- The frontend stores the active session locally in the browser.
- Backend model quality depends on optional provider keys.
- Webcam and microphone behavior depends on browser permissions and device availability.
- Teachable Machine gesture evidence is a coaching proxy, not a psychological conclusion.
- Full upload-based video/deck analysis is backend-oriented and not the safest demo path.
- Frontend code is currently concentrated in a large static JavaScript file for MVP speed.
- More real customer discovery should be added before final submission.

## Safety Limitations

Case Mirror should not claim to:

- predict winners
- simulate official judges
- infer emotion
- infer personality
- infer protected traits
- judge employability or leadership ability

Body and gesture outputs should be described only as visible, observable practice signals.

## Future Work

- Add production authentication only if cloud persistence becomes necessary.
- Add a coach dashboard for reviewing team reports.
- Add more frontend automated tests.
- Split frontend JavaScript into modules.
- Add a hosted backend deployment.
- Improve report sharing and export.
- Validate with multiple case teams and coaches.
- Add clearer privacy controls for uploaded presentation materials.
- Improve Teachable Machine classes with more diverse training examples.
