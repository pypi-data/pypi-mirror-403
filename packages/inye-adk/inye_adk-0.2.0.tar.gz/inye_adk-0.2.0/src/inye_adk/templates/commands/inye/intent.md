# Intent Clarification Command

Forces exhaustive high-level questioning until user intent converges to a single unambiguous requirement. Never guess or assume - always ask.

## Essential Files

@.moai/project/product.md
@.moai/project/structure.md
@.moai/project/tech.md

## Core Principle

**NEVER GUESS. ALWAYS ASK.**

AI typically picks the most probable interpretation. This command does the opposite:
- Treat ALL possible interpretations as equally valid
- Ask until only ONE interpretation remains
- Confirm the final understanding with the user

## Execution Flow

### Phase 1: Context Loading

1. Read project context files if they exist:
   - `.moai/project/product.md` - Product definition
   - `.moai/project/structure.md` - Project structure
   - `.moai/project/tech.md` - Tech stack

2. Understand the project domain before asking questions.

### Phase 2: Intent Decomposition

For the user's request, identify ALL ambiguous aspects:

**Scope Ambiguity:**
- What exactly is included?
- What is explicitly excluded?
- Are there related features that might be assumed?

**Implementation Ambiguity:**
- Multiple technical approaches possible?
- Which patterns/libraries to use?
- Where in the codebase should this live?

**Behavior Ambiguity:**
- Edge cases not specified?
- Error handling expectations?
- Success/failure criteria?

**User Ambiguity:**
- Who is the target user?
- What is the user's actual goal?
- What problem are they solving?

### Phase 3: Questioning Strategy

Use AskUserQuestion tool with these principles:

1. **Ask high-level first** - Don't dive into implementation details before understanding the goal
2. **One topic per question** - Don't overwhelm with multiple concerns
3. **Provide options when possible** - Help user think through choices
4. **Continue until convergence** - Stop only when intent is singular and clear

Example question flow:
```
Q1: "What problem is this solving for the user?"
Q2: "Who specifically will use this feature?"
Q3: "What should happen when X occurs?"
Q4: "Should this include Y, or is that out of scope?"
...continue until clear...
```

### Phase 4: Requirement Summary

When intent has converged, present a structured summary:

```
Based on our discussion, here's what we're building:

**Purpose:**
[Clear statement of what this does and why]

**Scope:**
- Included: [list]
- Excluded: [list]

**Success Criteria:**
- [Measurable outcome 1]
- [Measurable outcome 2]

Is this correct?
```

### Phase 5: Confirmation

- **User confirms** -> Intent clarification complete. Proceed with implementation.
- **User requests changes** -> Return to Phase 3, ask clarifying questions about the specific concern.

## Anti-Patterns (NEVER DO)

1. **Never assume the obvious choice**
   - Bad: "I'll use JWT since it's standard"
   - Good: "Should we use JWT, session-based auth, or OAuth?"

2. **Never skip edge cases**
   - Bad: "I'll handle the happy path first"
   - Good: "What should happen if the user tries to X when Y?"

3. **Never infer scope**
   - Bad: "I'll also add the related feature since it makes sense"
   - Good: "Should this include X, or is that a separate task?"

4. **Never proceed with ambiguity**
   - Bad: "I'll make a decision and we can change it later"
   - Good: "I have a question before proceeding..."

## Example Session

**User request:** `/inye:intent Add order cancellation`

**Questions:**
1. "What's the main reason users need to cancel orders? Mistaken purchase, changed mind, found better price, or something else?"
2. "Can all orders be cancelled, or only orders in certain states (before shipping, before payment, etc.)?"
3. "What happens to the payment when cancelled? Auto-refund, store credit, or manual process?"
4. "Should users be able to cancel the entire order only, or also partial items?"
5. "Where should the cancel button appear? Order history, order detail page, or both?"

**Summary:**
```
Based on our discussion:

**Purpose:**
Allow users to self-cancel orders before shipping starts,
so they don't need to contact customer support for simple cancellations.

**Scope:**
- Included: Full order cancellation, auto-refund to original payment method
- Excluded: Partial cancellation, post-shipping cancellation

**Success Criteria:**
- User can cancel from order detail page with one click
- Cancelled orders show "Cancelled" status
- Refund is automatically initiated

Is this correct?
```

## Works Well With

- `/moai:1-plan` - After intent is clear, create a SPEC
- `.moai/project/` files - Provides context for better questions
