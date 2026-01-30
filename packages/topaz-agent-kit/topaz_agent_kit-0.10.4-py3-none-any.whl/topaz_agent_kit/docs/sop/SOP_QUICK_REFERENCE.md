# SOP Quick Reference

A quick reference guide for creating Standard Operating Procedures (SOPs) in Topaz Agent Kit.

## Minimum Requirements

### Absolute Minimum (SOP Works)
```yaml
# manifest.yml
sop_id: my_agent
version: "1.0.0"
description: "SOP description"
sections: []
```

### Recommended Minimum (Actually Useful)
```yaml
# manifest.yml
sop_id: my_agent
version: "1.0.0"
description: "SOP description"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Overview"
    read_at: start
```

```markdown
# overview.md
## Your Role
[What the agent does]

## Key Steps
1. Step 1
2. Step 2

## Tools
- tool_name - [Description]

## Output Format
Return JSON with fields...
```

## Directory Structure

```
config/sop/
└── <pipeline>/
    ├── glossary.md              # Pipeline-level glossary
    └── <agent>/
        ├── manifest.yml         # REQUIRED
        ├── overview.md          # RECOMMENDED
        ├── steps/
        │   └── step_XX_*.md
        ├── scenarios/
        │   └── scenario_*.md
        └── troubleshooting.md
```

## Section Types

| Type | Purpose | read_at | Example |
|------|---------|---------|---------|
| `reference` | Context, overview | `start` or `on_demand` | `overview.md` |
| `procedure` | Step-by-step actions | `on_demand` | `steps/step_01_*.md` |
| `example` | Scenario patterns | `on_demand` | `scenarios/two_way_match.md` |
| `troubleshooting` | Error resolution | `on_demand` | `troubleshooting.md` |

## Manifest Structure

```yaml
sop_id: my_agent
version: "1.0.0"
description: "SOP description"
author: "Team Name"
last_updated: "2026-01-22"

settings:
  require_sop_read_before_step: true
  cache_sections: true

sections:
  # =============================================================================
  # OVERVIEW
  # =============================================================================
  - id: overview
    file: overview.md
    type: reference
    description: "High-level workflow"
    read_at: start

  # =============================================================================
  # PROCEDURAL STEPS
  # =============================================================================
  - id: step_01_do_something
    file: steps/step_01_do_something.md
    type: procedure
    description: "Do something"
    read_at: on_demand
    depends_on: []
    outputs:
      - result_field
    tools_used:
      - my_tool.do_something

  # =============================================================================
  # SCENARIOS / EXAMPLES
  # =============================================================================
  - id: scenario_example
    file: scenarios/example.md
    type: example
    description: "Example scenario"
    read_at: on_demand

  # =============================================================================
  # TROUBLESHOOTING
  # =============================================================================
  - id: troubleshooting
    file: troubleshooting.md
    type: troubleshooting
    description: "Common issues"
    read_at: on_demand
```

## Step File Template

```markdown
# Step N: [Step Name]

## What You Do
[Clear description]

## Steps
1. [Action with exact tool call]
2. **If condition:**
   - [Action]
3. **If other condition:**
   - [Action]

## Why This Matters
[Explanation]

## Save This for Next Step
[Data to accumulate]

## Document in Execution Trace
Record:
- **Input**: [What inputs]
- **Tool calls**: [What tools]
- **Output**: [What outputs]
- **Decision**: [What decision]

## Next
→ Go to Step N+1
```

## Scenario Template

```markdown
# Scenario: [Name]

## Description
[What this scenario represents]

## Pattern
[Visual/text representation]

## Example: [Specific Example]

### Initial State
**Input:**
| Field | Value |
|-------|-------|
| field1 | value1 |

### Process
1. **Step 1**: [What happens]
2. **Step 2**: [What happens]

### Expected Output
```json
{
  "field1": "value1"
}
```

## Key Points
1. [Point 1]
2. [Point 2]
```

## Troubleshooting Template

```markdown
# Troubleshooting Guide

## Common Issues and Solutions

### [Issue Name]

**Symptom**: [What agent sees]

**Possible Causes:**
1. **Cause 1**
   - [Explanation]
   - [How to check]

**Action**: [What to do]

---

### [Another Issue]
...
```

## Glossary Template

```markdown
# [Pipeline] Glossary

## [Term]

**Definition**: [Clear definition]

**Role**: [What role it plays]

**Key Rules**:
- **Rule 1**: [Important rule]
- **Rule 2**: [Important rule]

**Example**: [Concrete example]

---

## [Another Term]
...
```

## Agent Configuration

```yaml
# agent.yml
id: my_agent
sop: "config/sop/<pipeline>/<agent>/manifest.yml"

mcp:
  servers:
    - url: "http://localhost:8050/mcp"
      toolkits: ["sop"]
      tools: ["sop_initialize", "sop_get_section", "sop_get_example", "sop_get_troubleshooting", "sop_get_glossary_term"]

max_turns: 30  # Increase for complex SOPs
```

## Agent Prompt Template

```jinja
You are a [Agent Name] (SOP-Driven) responsible for [task].

Tasks:
1. **Initialize SOP**: Call `sop_initialize` with `project_dir` and `sop_path`.
2. **Read SOP Overview**: Call `sop_get_section(section_id="overview")`.
3. **Follow SOP Steps**:
   - **Step 1**: Call `sop_get_section(section_id="step_01_...")`, then execute.
   - **Step 2**: Call `sop_get_section(section_id="step_02_...")`, then execute.
4. **If Stuck**: Use `sop_get_example(scenario_name="...")` or `sop_get_troubleshooting(issue="...")`.
5. **If Uncertain**: Use `sop_get_glossary_term(term_id="<term>")`.
```

## SOP Tools

| Tool | Purpose |
|------|---------|
| `sop_initialize` | Load SOP manifest |
| `sop_get_section` | Read a section |
| `sop_get_example` | Get scenario example |
| `sop_get_troubleshooting` | Get error help |
| `sop_get_glossary_term` | Look up term |
| `sop_list_glossary_terms` | List all terms |
| `sop_list_sections` | List sections |
| `sop_invalidate_cache` | Clear cache |

## Checklist

### Minimum ✅
- [ ] `manifest.yml` with `sop_id`, `version`, `description`
- [ ] Agent configured with `sop` path

### Recommended ✅
- [ ] `overview.md` with role, workflow, tools
- [ ] At least one procedure step
- [ ] Agent prompt uses SOP tools

### Best Practice ✅
- [ ] All steps with metadata (`depends_on`, `outputs`, `tools_used`)
- [ ] At least one scenario example
- [ ] Troubleshooting guide
- [ ] Pipeline glossary
- [ ] Clear, actionable instructions
- [ ] Examples with tables/calculations

## ReconVoy Reference

**Location**: `config/sop/reconvoy/sop_matcher/`

**Structure**:
- `manifest.yml` - 8 sections (1 overview, 6 steps, 2 scenarios, 1 troubleshooting)
- `overview.md` - Workflow, tools, output format
- `steps/` - 6 procedural steps with full metadata
- `scenarios/` - 2 complete examples (two-way, three-way)
- `troubleshooting.md` - 10+ common issues
- `glossary.md` (pipeline-level) - 12 domain terms

**Best Practices Demonstrated**:
- ✅ Clear section organization
- ✅ Complete metadata for all steps
- ✅ Actionable step instructions
- ✅ Rich scenario examples
- ✅ Comprehensive troubleshooting
- ✅ Domain-specific glossary

---

**See**: `docs/sop/SOP_CREATION_GUIDE.md` for detailed guide
