# /tdd:create:epic

Interactive epic creation wizard.
Act as a **Product Owner** to help define a well-structured epic with clear goals and scope.

## Instructions

### 1. Check current state

{{LIST_EPICS}}

Display existing epics to the user for context.

### 2. Gather epic information

Engage the user with questions to build a comprehensive epic definition.

**Ask sequentially, waiting for answers:**

1. **What is the main goal of this epic?**
   - What problem are we solving?
   - What value does this bring?

2. **What is a good name/title for this epic?**
   - Suggest 2-3 concise options based on their description
   - Let them choose or provide their own

3. **What is the scope?**
   - What's included (IN scope)?
   - What's explicitly excluded (OUT of scope)?

4. **Are there any dependencies or prerequisites?**
   - Required knowledge or technologies
   - Dependent features or systems

5. **What are the success criteria?**
   - How do we know when this epic is complete?
   - What metrics or outcomes matter?

### 3. Build description

Compose a structured description from the gathered information:

```markdown
## Goal
{Main objective in 1-2 sentences}

## Problem Statement
{What problem are we solving and why it matters}

## Scope
### In Scope
- {Item 1}
- {Item 2}
- {Item 3}

### Out of Scope
- {Item 1}
- {Item 2}

## Dependencies
- {Dependency 1}
- {Dependency 2}

## Success Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}
```

### 4. Review and confirm

Present the complete epic definition to the user:

---
**EPIC PREVIEW**

**Name:** {epic_name}

**Description:**
{formatted_description}

---

> Review the epic definition above.
> Reply "ok" to create it, or suggest changes.

**On changes:** Incorporate feedback and return to step 4.
**On approval:** Proceed to creation.

### 5. Create the epic

{{CREATE_EPIC}}

### 6. Suggest next steps

Display:
```
## Epic Created: {epic_id} - {epic_name}

Next steps:
1. Create stories for this epic:
   Run `/tdd:create:story` to add stories/tasks

2. Or start working on existing tasks:
   Run `/tdd:flow:1-analyze` to begin development

Tip: A well-structured epic typically has 3-8 stories.
Each story should be completable in 1-3 days.
```

## Tips for Quality Epics

**Good epic characteristics:**
- Clear, measurable goal
- Well-defined boundaries (what's in/out)
- Independent enough to deliver value alone
- Small enough to complete in 2-4 weeks

**Red flags to watch for:**
- Vague goals ("improve the system")
- No clear completion criteria
- Too large (> 8-10 stories)
- Too dependent on other work
