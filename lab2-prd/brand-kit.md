# SecondServe Campus brand kit

## Brand concept

SecondServe Campus is a practical, warm, campus-trust utility for recovering edible surplus food from events. The brand should avoid shame, charity framing, or over-playful visuals. It should feel like a reliable campus service that happens to make food rescue easier.

## Three visual directions considered

### Option A: Fresh utility

- Palette: sprout green, harvest gold, tomato coral, warm paper, deep ink.
- Feel: quick, credible, food-aware, optimistic.
- Best for: a campus tool that must be trusted by both students and administrators.

### Option B: Campus bulletin

- Palette: navy, sky blue, chalk white, safety orange, charcoal.
- Feel: institutional, notice-board inspired, structured.
- Best for: a university-owned deployment with formal branding.

### Option C: Night market

- Palette: plum, mint, neon lime, black, off-white.
- Feel: social, energetic, student-led.
- Best for: a student club launch, but less appropriate for administrators.

Chosen direction: Option A, Fresh utility.

## Color palette

| Token | Hex | Usage |
| --- | --- | --- |
| Sprout green | `#2F7D57` | Primary buttons, links, success states, active navigation |
| Deep sprout | `#1F5E42` | Hover states, headings on light surfaces |
| Harvest gold | `#F2B84B` | Pickup urgency, highlighted metrics, badges |
| Tomato coral | `#E85D4F` | Expiring soon, warnings, destructive actions |
| Warm paper | `#F8F6F0` | App background |
| Rice white | `#FFFFFF` | Cards, inputs, modals |
| Ink | `#25312B` | Primary text |
| Soft gray | `#D8DDD5` | Borders and dividers |
| Leaf mist | `#E8F3EC` | Success backgrounds and selected filters |

## Typography

- Primary typeface: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif.
- Heading weight: 700 for screen titles, 650 for card titles.
- Body weight: 400 to 500.
- Numeric metrics: tabular numbers where available.
- Avoid decorative food fonts; the interface should feel operational and accessible.

## Layout principles

- Mobile-first because students and organizers will use the app at events.
- Keep drop cards compact and scannable.
- Use 8px radius for cards, buttons, inputs, and chips.
- Use white cards over warm paper backgrounds for contrast.
- Do not nest cards inside cards.
- Prioritize pickup time, portions left, allergen information, and location.

## Component guidance

### Buttons

- Primary: sprout green background, white text, 44px minimum height.
- Secondary: rice white background, ink text, soft gray border.
- Warning/destructive: tomato coral background, white text.
- Disabled: soft gray background, muted text, no shadow.

### Food drop cards

- Required visible fields:
  - Drop title
  - Pickup window
  - Location
  - Portions left
  - Dietary tags
  - Allergen tags or "allergens unknown"
- Use harvest gold chip for "ending soon."
- Use tomato coral chip for "allergens unknown" or flagged risk.

### Tags

- Dietary tags: leaf mist background, deep sprout text.
- Allergen tags: warm paper background, ink text, visible border.
- Warning tags: light coral background, tomato coral text.
- Tags must include readable text and cannot rely on color alone.

### Forms

- Labels always visible above fields.
- Use helper text for food safety and allergen fields.
- Use constrained controls for common values: category menu, location menu, tag checkboxes.
- Show validation messages directly under the affected field.

### Data views

- Admin tables should be dense but readable.
- Use status chips for active, paused, closed, expired, cancelled, flagged.
- CSV export should be a clear icon/text action near date filters.

## Voice and content style

- Plain, calm, and specific.
- Say "Reserve a portion" instead of "Grab it."
- Say "Pickup ends at 4:30 PM" instead of "Hurry."
- Say "Allergens unknown" rather than leaving the field blank.
- Avoid shame-based copy like "Help hungry students."
- Keep warnings direct and practical.

## Example microcopy

- Empty state: "No active drops match these filters."
- Reservation success: "Reserved. Show this code at pickup."
- Sold out state: "All portions are currently reserved."
- Expired state: "Pickup window has ended."
- Safety helper: "Only post food that has been handled according to campus event guidelines."

## Accessibility rules

- Text contrast must meet WCAG 2.2 AA.
- Touch targets must be at least 44 by 44 CSS pixels.
- Focus rings must be visible on all controls.
- Forms must be usable without placeholder text.
- All status chips need text labels.
- Warnings must use icon/text or label/text, not color alone.
