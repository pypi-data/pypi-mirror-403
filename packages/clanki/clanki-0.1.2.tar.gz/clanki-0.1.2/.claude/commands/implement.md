# Implement Linear Ticket

Implement the Linear ticket provided by the user.

## Arguments
- `$ARGUMENTS` - The Linear ticket ID (e.g., ANKI-123) followed by the implementation plan

## Workflow

### 1. Fetch Ticket Details
First, fetch the Linear ticket using mcp-linear to understand the full scope:
- Get the ticket title, description, and acceptance criteria
- Check if the ticket has sub-issues (child tickets)
- Note the current status

### 2. Review the Implementation Plan
The user will provide an implementation plan along with the ticket ID. Review the plan carefully:
- If there are **open questions**, **ambiguities**, or **concerns** with the plan, raise them immediately for clarification before proceeding
- If the plan references files or code patterns, verify they exist and match expectations
- Only proceed once the plan is clear and actionable

### 3. Git Setup
Before starting implementation:
1. Check the current git status
2. Ensure we're on `main` and up to date (fetch and check for divergence)
3. **Work directly on main** - do NOT create a feature branch

### 4. Implementation
Execute the implementation plan:
- Follow the plan step by step
- Use the TodoWrite tool to track progress through the implementation
- Ensure code follows existing project patterns and conventions
- Test changes where applicable

### 5. Handle Sub-Issues (if present)
If the ticket has sub-issues:
- Work through each sub-issue **one by one** in order
- After completing each sub-issue:
  - Stage the relevant changes
  - Create a commit with a short descriptive message (do NOT include ticket ID)
  - Mark the sub-issue as complete
- Continue until all sub-issues are done

### 6. Normal Issues (no sub-issues)
For tickets without sub-issues:
- Complete the full implementation
- Do **NOT** commit - codex will handle the commit and PR

### 7. Completion
Once implementation is finished:
1. Update the Linear ticket status to indicate implementation is complete
2. Provide a **summary for codex** that includes:
   - What was implemented
   - Files changed
   - Any decisions made during implementation
   - Testing performed
   - Any follow-up items or notes

---

**Remember:** Claude handles implementation only. Codex handles git commits (for non-sub-issue tickets), PRs, and Linear ticket management.
