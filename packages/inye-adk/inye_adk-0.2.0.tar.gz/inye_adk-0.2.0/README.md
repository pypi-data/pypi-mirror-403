# Inye-ADK

**Inye Agentic Development Kit** - Intent clarification command for Claude Code.

## What is this?

Inye-ADK provides the `/inye:intent` command for Claude Code that forces exhaustive questioning until user intent converges to a single unambiguous requirement.

**The problem:** AI typically picks the most probable interpretation and runs with it.

**The solution:** `/inye:intent` makes AI ask questions until there's only ONE possible interpretation.

## Installation

```bash
# Using pipx (recommended)
pipx install inye-adk

# Using uv
uv tool install inye-adk

# Using pip
pip install inye-adk
```

## Usage

### Initialize in your project

```bash
cd your-project
inye init
```

This installs the `/inye:intent` command to `.claude/commands/inye/`.

### Use in Claude Code

```
/inye:intent Add order cancellation feature
```

Claude will then ask high-level questions until your intent is 100% clear:

1. "What's the main reason users need to cancel orders?"
2. "Can all orders be cancelled, or only before shipping?"
3. "What happens to payment when cancelled?"
4. ...continues until clear...

Then presents a summary for your confirmation:

```
Based on our discussion:

**Purpose:**
Allow users to self-cancel orders before shipping...

**Scope:**
- Included: Full order cancellation, auto-refund
- Excluded: Partial cancellation

**Success Criteria:**
- User can cancel from order detail page
- Refund is automatically initiated

Is this correct?
```

## MoAI Compatibility

Inye-ADK is compatible with [MoAI-ADK](https://github.com/modu-ai/moai-adk). When `.moai/project/` files exist:

- `product.md` - Product definition
- `structure.md` - Project structure
- `tech.md` - Tech stack

The `/inye:intent` command reads these files to ask more contextual questions.

## Commands

| Command | Description |
|---------|-------------|
| `inye init` | Install /inye:intent command in current project |
| `inye status` | Check if /inye:intent command is installed |

## License

MIT
