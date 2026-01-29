# /tdd:create:story

Interactive story/task creation wizard.
Act as a **Product Owner** to help define a well-structured story with clear acceptance criteria.

## Instructions

### 1. Load context

{{STATE_READ}}

Check:
- Current epic (if any)
- Backend type

### 2. Select or confirm epic

{{LIST_EPICS}}

If a current epic is set, confirm with user:
```
Current epic: {epic_id} - {epic_name}

Creating new story in this epic. Is this correct?
```

If no current epic or user wants different one, let them choose from the list.

### 3. Show existing stories

{{LIST_STORIES}}

Display existing stories in the selected epic for context:
```
### Existing stories in {epic_id}:
- {task_id}: {title} ({status})
- ...
```

### 4. Gather story information

Engage the user with questions to build a comprehensive story definition.

**Ask sequentially, waiting for answers:**

1. **What should this story accomplish?**
   - What specific functionality or change?
   - User perspective: "As a user, I want to..."

2. **What is a good title for this story?**
   - Suggest 2-3 concise options based on their description
   - Good format: Verb + Object (e.g., "Add login validation", "Implement search filters")
   - Let them choose or provide their own

3. **What are the technical details?**
   - What components/files might be involved?
   - Any specific implementation approach?
   - Edge cases to consider?

4. **What are the acceptance criteria?**
   - How do we know when this story is complete?
   - What specific behaviors must be verified?
   - Guide them to write testable criteria

### 5. Refine acceptance criteria

Help the user write SMART acceptance criteria:

**Good acceptance criteria are:**
- **S**pecific - Clear, unambiguous behavior
- **M**easurable - Can be verified as pass/fail
- **A**chievable - Technically feasible
- **R**elevant - Directly related to the story goal
- **T**estable - Can be automated in tests

**Transform vague criteria into specific ones:**

| Vague | Specific |
|-------|----------|
| "Works correctly" | "Returns HTTP 200 with valid JSON on success" |
| "Handles errors" | "Returns HTTP 400 with error message for invalid input" |
| "Fast response" | "Response time < 200ms for 95th percentile" |
| "User friendly" | "Form shows inline validation errors within 100ms" |

Present refined criteria for approval:
```markdown
**Acceptance Criteria:**
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}
```

### 6. Build description

Compose a structured description:

```markdown
## Summary
{What this story accomplishes in 1-2 sentences}

## Details
{Technical context and implementation notes}

## Edge Cases
- {Edge case 1}
- {Edge case 2}
```

### 7. Review and confirm

Present the complete story definition to the user:

---
**STORY PREVIEW**

**Epic:** {epic_id} - {epic_name}
**Title:** {story_title}

**Description:**
{formatted_description}

**Acceptance Criteria:**
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

---

> Review the story definition above.
> Reply "ok" to create it, or suggest changes.

**On changes:** Incorporate feedback and return to step 7.
**On approval:** Proceed to creation.

### 8. Create the story

{{CREATE_STORY}}

### 9. Offer continuation

Display:
```
## Story Created: {task_id} - {title}

Epic: {epic_id} - {epic_name}

What would you like to do next?

1. **Add another story** to this epic
   Run `/tdd:create:story`

2. **Start working** on this story
   Run `/tdd:flow:1-analyze`

3. **Create a new epic**
   Run `/tdd:create:epic`

4. **View epic status**
   Run `/tdd:flow:status`
```

## Tips for Quality Stories

**Good story characteristics:**
- Single, focused purpose
- Completable in 1-3 days
- Independent (can be built/tested alone)
- Valuable (delivers user/business value)
- Testable (clear acceptance criteria)

**Story sizing guide:**
- **Too small:** Single function/bug fix → Maybe just a task
- **Right size:** Feature slice with 2-5 tests
- **Too large:** Multiple features → Split into smaller stories

**Acceptance criteria tips:**
- Start with the happy path
- Add at least one error case
- Consider edge cases (null, empty, max values)
- Include performance criteria if relevant
- Each criterion should map to a test
