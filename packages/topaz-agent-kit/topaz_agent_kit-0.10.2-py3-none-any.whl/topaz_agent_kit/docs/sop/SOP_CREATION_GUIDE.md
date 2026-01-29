# SOP Creation Guide

A comprehensive guide for creating Standard Operating Procedures (SOPs) for agents in Topaz Agent Kit, based on the ReconVoy implementation.

## Table of Contents

1. [Overview](#overview)
2. [Bare Minimum Requirements](#bare-minimum-requirements)
3. [Complete SOP Structure](#complete-sop-structure)
4. [Best Practices](#best-practices)
5. [ReconVoy Example Analysis](#reconvoy-example-analysis)
6. [Step-by-Step Creation Process](#step-by-step-creation-process)

---

## Overview

SOPs enable agents to follow structured, documented procedures stored as markdown files. This allows you to:
- **Update agent behavior without code changes** - Modify SOP files to change how agents work
- **Maintain consistency** - All agents follow the same documented procedures
- **Enable domain expertise** - Include business rules, terminology, and examples
- **Support troubleshooting** - Built-in error resolution guidance

### How Agents Use SOPs

1. **Initialize**: Agent calls `sop_initialize(project_dir, sop_path)` to load the manifest
2. **Read Overview**: Agent automatically reads the overview section
3. **Follow Steps**: Agent calls `sop_get_section(section_id="step_XX")` before each step
4. **Reference Examples**: Agent calls `sop_get_example(scenario_name="...")` when needed
5. **Handle Errors**: Agent calls `sop_get_troubleshooting(issue="...")` for guidance
6. **Look Up Terms**: Agent calls `sop_get_glossary_term(term_id="...")` for definitions

---

## Bare Minimum Requirements

### Absolute Minimum (SOP Will Work)

**You only need ONE file:**

#### 1. `manifest.yml` - **REQUIRED**

```yaml
sop_id: my_agent
version: "1.0.0"
description: "Simple SOP for my agent"

sections: []  # Empty sections list is valid
```

**What happens:**
- `sop_initialize` loads successfully
- Returns empty `overview`, `available_sections`, and `workflow_steps`
- Agent can still call `sop_get_section` for any section it defines later

**Location**: `config/sop/<pipeline>/<agent>/manifest.yml`

---

### Recommended Minimum (Actually Useful)

#### 1. `manifest.yml` with Overview

```yaml
sop_id: my_agent
version: "1.0.0"
description: "Simple SOP for my agent"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Overview of the agent's role and workflow"
    read_at: start
```

#### 2. `overview.md` - **RECOMMENDED**

```markdown
# My Agent - Overview

## Your Role

You are responsible for [brief description of what the agent does].

## Key Steps

1. Step 1: [Description]
2. Step 2: [Description]
3. Step 3: [Description]

## Tools Available

- `tool_name_1` - [What it does]
- `tool_name_2` - [What it does]

## Output Format

Return JSON with:
- `field1`: [Description]
- `field2`: [Description]
```

**Location**: `config/sop/<pipeline>/<agent>/overview.md`

---

## Complete SOP Structure

### Directory Layout

```
config/sop/
└── <pipeline>/                    # Pipeline-specific SOPs
    ├── glossary.md               # Pipeline glossary (shared across agents)
    └── <agent>/                  # Agent-specific SOP
        ├── manifest.yml          # REQUIRED: SOP structure definition
        ├── overview.md           # RECOMMENDED: High-level guidance
        ├── steps/                # OPTIONAL: Procedural steps
        │   ├── step_01_*.md
        │   ├── step_02_*.md
        │   └── step_NN_*.md
        ├── scenarios/            # OPTIONAL: Example scenarios
        │   ├── scenario_1.md
        │   └── scenario_2.md
        └── troubleshooting.md    # OPTIONAL: Error resolution guide
```

---

## Best Practices

### 1. Manifest Structure

#### ✅ DO: Use Clear Section Organization

```yaml
sections:
  # =============================================================================
  # OVERVIEW
  # =============================================================================
  - id: overview
    file: overview.md
    type: reference
    description: "High-level workflow and your role"
    read_at: start

  # =============================================================================
  # PROCEDURAL STEPS
  # =============================================================================
  - id: step_01_identify_target
    file: steps/step_01_identify_target.md
    type: procedure
    description: "Identify the target system or entity"
    read_at: on_demand
    depends_on: []
    outputs:
      - target_id
      - target_type
    tools_used:
      - my_tool.get_target_by_id
```

#### ❌ DON'T: Mix Types Without Organization

```yaml
sections:
  - id: step_01
  - id: overview
  - id: step_02
  - id: troubleshooting
```

### 2. Section Types

| Type | Purpose | When to Use | read_at |
|------|---------|-------------|---------|
| **`reference`** | Contextual information | Overview, background, rules | `start` or `on_demand` |
| **`procedure`** | Step-by-step instructions | Actions to execute in order | `on_demand` |
| **`example`** | Scenario examples | Pattern matching, use cases | `on_demand` |
| **`troubleshooting`** | Error resolution | Common issues and fixes | `on_demand` |

### 3. Procedure Steps

#### ✅ DO: Include All Metadata

```yaml
- id: step_02_find_match
  file: steps/step_02_find_match.md
  type: procedure
  description: "Find matching entry using reference correlation"
  read_at: on_demand
  depends_on:
    - step_01_identify_foreign_book
  outputs:
    - matched_entry
    - document_number
    - match_status
  tools_used:
    - reconvoy.find_foreign_book_match
    - reconvoy.update_blackline_match_status
```

**Why each field matters:**
- **`depends_on`**: Shows step dependencies (agent can check prerequisites)
- **`outputs`**: Documents what this step produces (agent knows what to expect)
- **`tools_used`**: Lists required tools (agent can verify availability)

#### ❌ DON'T: Skip Metadata

```yaml
- id: step_02
  file: steps/step_02.md
  type: procedure
```

### 4. Step Documentation Format

#### ✅ DO: Use Clear, Actionable Format

```markdown
# Step 2: Find Match

## What You Do

Find the matching entry in the foreign book using the reference description.

## Steps

1. Call the match tool:
   ```
   reconvoy.find_foreign_book_match(
     db_file="<database_path>",
     currency="<item.currency>",
     reference_description="<item.reference_description>",
     amount_foreign=<item.amount_foreign>
   )
   ```

2. **If match found:**
   - Extract `document_number` from the matched entry
   - Mark item as "processing"
   - Continue to Step 3

3. **If no match:**
   - Return early with `matched_entry: null`
   - Do NOT mark as rejected

## Why Mark as "processing"?

If you don't mark it, the loop will process it again.

## Save This for Next Step

You'll need to add this to `item_discovery_results`:
```python
{
  "blackline_item_id": "<item.item_id>",
  "foreign_book_type": "<us_books|fr_books>",
  "matched_entry": <matched_entry_object>,
  "document_number": "<document_number>"
}
```

## Document in Execution Trace

For this step, record:
- **Input**: Item details
- **Tool calls**: Exact parameters
- **Output**: Results
- **Decision**: What to do next

## Next

→ If match found: Go to Step 3
→ If no match: Return early
```

#### ❌ DON'T: Write Vague Instructions

```markdown
# Step 2

Find a match. Use the tool. If it works, continue.
```

### 5. Scenario Examples

#### ✅ DO: Provide Concrete Examples

```markdown
# Scenario: Two-Way Match

## Description

A two-way match is the simplest reconciliation scenario where a UK BlackLine item matches directly to a single foreign book entry.

## Pattern

```
UK Entity ←────────────────→ Foreign Entity (US or FR)
   │                              │
   │  Invoice / Payment           │
   │  (one-to-one match)          │
   └──────────────────────────────┘
```

## Example: UK Sells to US (Direct Payment)

### Initial State

**BlackLine Item (UK):**
| Field | Value |
|-------|-------|
| item_id | BL-001 |
| currency | USD |
| amount_foreign | 625,000.00 |
| reference_description | INV US_OCT_99/US_SUB |

**US Books Entry:**
| Field | Value |
|-------|-------|
| entry_id | US-001 |
| document_number | 150000881 |
| reference | INV US_OCT_99/US_SUB |
| amount_document_currency | 625,000.00 |

### Matching Process

1. **Step 1**: Currency is USD → Target `us_books`
2. **Step 2**: `find_foreign_book_match` by reference → Match found (US-001)
3. **Step 3**: Calculate FX variance
4. **Step 4**: Generate journals

### Key Points

1. Two-way matches involve exactly TWO parties
2. Only ONE foreign book is involved
3. Match status is `two_way_match`
```

#### ❌ DON'T: Write Abstract Examples

```markdown
# Scenario: Simple Match

Sometimes items match. Do the steps.
```

### 6. Troubleshooting Guide

#### ✅ DO: Organize by Symptom

```markdown
# Troubleshooting Guide

## Common Issues and Solutions

### No Match Found

**Symptom**: `find_foreign_book_match` returns `matched_entry: null`

**Possible Causes:**

1. **Reference Mismatch**
   - Check for typos in `reference_description`
   - Compare exact characters (spaces, case, special chars)

2. **Wrong Foreign Book**
   - GBP items should check BOTH books
   - USD → `us_books`, EUR → `fr_books`

**Action**: Do NOT mark as rejected. Leave unchanged for future investigation.

---

### Item Already Being Processed

**Symptom**: Item has `processing_status = 'processing'`

**Cause**: This item is already part of another case.

**Action**: Skip this item (return early). This is expected behavior, not an error.
```

#### ❌ DON'T: Write Generic Troubleshooting

```markdown
# Troubleshooting

If something goes wrong, try again or check the logs.
```

### 7. Glossary Terms

#### ✅ DO: Define Domain-Specific Terms

```markdown
## GBP items

**Definition**: BlackLine items where `currency = "GBP"`.

**Role**: UK-side endpoint items (bank receipts, IC accounts in GBP).

**Key Rules**:
- **Never marked as `need_to_process`**: GBP items are terminal
- **May be marked as `processing`**: When included in a case
- **Status handling**: GBP items remain `UNMATCHED` until journals are posted

**Example**: A bank receipt in GBP (`BL-S3-003-001`, currency: GBP, amount_local_gbp: 101070.38) is a GBP item.
```

#### ❌ DON'T: Use Jargon Without Definition

```markdown
## GBP items

GBP items are special. Handle them differently.
```

---

## ReconVoy Example Analysis

### Structure Overview

The ReconVoy SOP demonstrates a **production-ready, comprehensive SOP**:

```
config/sop/reconvoy/
├── glossary.md                    # 12 domain terms defined
└── sop_matcher/
    ├── manifest.yml              # 8 sections (1 overview, 6 steps, 2 scenarios, 1 troubleshooting)
    ├── overview.md               # High-level workflow, tools, output format
    ├── steps/
    │   ├── step_01_identify_foreign_book.md
    │   ├── step_02_find_match.md
    │   ├── step_03_find_initial_related_items.md
    │   ├── step_04_recursive_discovery.md
    │   ├── step_05_fx_analysis.md
    │   └── step_06_journal_proposal.md
    ├── scenarios/
    │   ├── two_way_match.md      # Complete example with tables, calculations
    │   └── three_way_match.md     # Complex triangular scenario
    └── troubleshooting.md        # 10+ common issues with solutions
```

### Key Strengths

1. **Clear Dependencies**: Each step lists `depends_on` to show execution order
2. **Complete Metadata**: Every step includes `outputs` and `tools_used`
3. **Actionable Instructions**: Steps include exact tool calls with parameters
4. **Rich Examples**: Scenarios include tables, calculations, and expected outputs
5. **Comprehensive Troubleshooting**: Covers edge cases and error handling
6. **Domain Glossary**: 12 terms defined with examples and rules

### How It's Used

**Agent Configuration** (`reconvoy_sop_matcher.yml`):
```yaml
sop: "config/sop/reconvoy/sop_matcher/manifest.yml"
mcp:
  servers:
    - url: "http://localhost:8050/mcp"
      toolkits: ["sop"]
      tools: ["sop_initialize", "sop_get_section", "sop_get_example", "sop_get_troubleshooting", "sop_get_glossary_term"]
max_turns: 50  # Increased for SOP-driven workflow
```

**Agent Prompt** (`reconvoy_sop_matcher.jinja`):
- Instructs agent to call `sop_initialize` at start
- Tells agent to read each step before executing
- Provides guidance on using examples and troubleshooting

---

## Step-by-Step Creation Process

### Step 1: Plan Your SOP

1. **Identify the agent** that needs an SOP
2. **List the steps** the agent must follow
3. **Identify scenarios** the agent might encounter
4. **List domain terms** that need definition
5. **Think about errors** that might occur

### Step 2: Create Directory Structure

```bash
mkdir -p config/sop/<pipeline>/<agent>/steps
mkdir -p config/sop/<pipeline>/<agent>/scenarios
```

### Step 3: Write manifest.yml

Start with the minimum, then add sections:

```yaml
sop_id: my_agent
version: "1.0.0"
description: "SOP for my agent"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Overview of the agent's role"
    read_at: start

  # Add procedure steps
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
```

### Step 4: Write overview.md

```markdown
# My Agent - Overview

## Your Job

[Clear description of what the agent does]

## Simple Workflow

```
Step 1: [Description]
   ↓
Step 2: [Description]
   ↓
Step 3: [Description]
```

## Key Rules

- **Rule 1**: [Important rule]
- **Rule 2**: [Important rule]

## Tools You Have

**SOP Tools** (read instructions):
- `sop_initialize` - Load SOP
- `sop_get_section` - Read a step
- `sop_get_example` - See examples

**Business Tools** (do work):
- `my_tool.action_1` - [What it does]
- `my_tool.action_2` - [What it does]

## Output Format

Return JSON with these fields:
- `field1` - [Description]
- `field2` - [Description]
```

### Step 5: Write Step Files

For each procedure step:

```markdown
# Step N: [Step Name]

## What You Do

[Clear description of the step's purpose]

## Steps

1. [Action 1 with exact tool call]
2. **If condition:**
   - [Action]
   - [Action]
3. **If other condition:**
   - [Action]

## Why This Matters

[Explanation of why this step is important]

## Save This for Next Step

[What data to accumulate for next step]

## Document in Execution Trace

For this step, record:
- **Input**: [What inputs are used]
- **Tool calls**: [What tools are called]
- **Output**: [What outputs are produced]
- **Decision**: [What decision was made]

## Next

→ Go to Step N+1
```

### Step 6: Write Scenario Examples

```markdown
# Scenario: [Scenario Name]

## Description

[What this scenario represents]

## Pattern

[Visual or text representation of the pattern]

## Example: [Specific Example Name]

### Initial State

**Input Data:**
| Field | Value |
|-------|-------|
| field1 | value1 |

### Process

1. **Step 1**: [What happens]
2. **Step 2**: [What happens]

### Expected Output

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

## Key Points

1. [Key point 1]
2. [Key point 2]
```

### Step 7: Write Troubleshooting Guide

```markdown
# Troubleshooting Guide

## Common Issues and Solutions

### [Issue Name]

**Symptom**: [What the agent will see]

**Possible Causes:**

1. **Cause 1**
   - [Explanation]
   - [How to check]

2. **Cause 2**
   - [Explanation]
   - [How to check]

**Action**: [What the agent should do]

---

### [Another Issue]

...
```

### Step 8: Write Glossary (Pipeline-Level)

```markdown
# [Pipeline] Glossary

This glossary defines key terms used in the [pipeline] pipeline.

---

## [Term 1]

**Definition**: [Clear definition]

**Role**: [What role it plays in the workflow]

**Key Rules**:
- **Rule 1**: [Important rule]
- **Rule 2**: [Important rule]

**Example**: [Concrete example]

---

## [Term 2]

...
```

### Step 9: Configure Agent

Add to agent YAML:

```yaml
id: my_agent
sop: "config/sop/<pipeline>/<agent>/manifest.yml"

mcp:
  servers:
    - url: "http://localhost:8050/mcp"
      toolkits: ["sop"]
      tools: ["sop_initialize", "sop_get_section", "sop_get_example", "sop_get_troubleshooting", "sop_get_glossary_term"]

max_turns: 30  # Increase if SOP has many steps
```

### Step 10: Update Agent Prompt

Add to agent prompt template:

```jinja
You are a [Agent Name] (SOP-Driven) responsible for [task].

Tasks:
1. **Initialize SOP**: Call `sop_initialize` with `project_dir` and `sop_path` from inputs.
2. **Read SOP Overview**: Call `sop_get_section(section_id="overview")`.
3. **Follow SOP Steps in Order**:
   - **Step 1**: Call `sop_get_section(section_id="step_01_...")`, then execute.
   - **Step 2**: Call `sop_get_section(section_id="step_02_...")`, then execute.
4. **If Stuck**: Use `sop_get_example(scenario_name="...")` or `sop_get_troubleshooting(issue="...")`.
5. **If Uncertain About Terms**: Use `sop_get_glossary_term(term_id="<term>")`.
```

---

## Checklist for SOP Creation

### Minimum Requirements ✅
- [ ] `manifest.yml` exists with at least `sop_id`, `version`, `description`
- [ ] Agent configured with `sop` path and SOP toolkit enabled

### Recommended ✅
- [ ] `overview.md` with role, workflow, tools, output format
- [ ] At least one procedure step documented
- [ ] Agent prompt instructs to use SOP tools

### Best Practice ✅
- [ ] All procedure steps documented with metadata (`depends_on`, `outputs`, `tools_used`)
- [ ] At least one scenario example provided
- [ ] Troubleshooting guide with common issues
- [ ] Pipeline glossary with domain terms
- [ ] Clear, actionable step instructions
- [ ] Examples include tables, calculations, expected outputs
- [ ] Steps document execution trace requirements

---

## Quick Reference

### Section Types

| Type | File Location | When Agent Reads | Purpose |
|------|--------------|------------------|---------|
| `reference` | `overview.md` | `start` | Context, role, workflow |
| `procedure` | `steps/step_XX_*.md` | `on_demand` | Step-by-step actions |
| `example` | `scenarios/*.md` | `on_demand` | Pattern examples |
| `troubleshooting` | `troubleshooting.md` | `on_demand` | Error resolution |

### SOP Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `sop_initialize` | Load SOP manifest | At agent start |
| `sop_get_section` | Read a section | Before each step |
| `sop_get_example` | Get scenario example | When encountering pattern |
| `sop_get_troubleshooting` | Get error help | When encountering error |
| `sop_get_glossary_term` | Look up term | When term is unclear |
| `sop_list_glossary_terms` | List all terms | To see available terms |
| `sop_list_sections` | List sections | To see available sections |
| `sop_invalidate_cache` | Clear cache | After SOP updates |

---

## Example: Minimal Working SOP

### manifest.yml
```yaml
sop_id: simple_processor
version: "1.0.0"
description: "Simple data processor agent"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Overview of processing workflow"
    read_at: start

  - id: step_01_process
    file: steps/step_01_process.md
    type: procedure
    description: "Process the input data"
    read_at: on_demand
    depends_on: []
    outputs:
      - processed_data
    tools_used:
      - my_tool.process_data
```

### overview.md
```markdown
# Simple Processor - Overview

## Your Job

Process input data and return structured output.

## Workflow

1. Read input data
2. Process using tools
3. Return result

## Tools

- `my_tool.process_data` - Processes the data

## Output

Return JSON with `processed_data` field.
```

### steps/step_01_process.md
```markdown
# Step 1: Process Data

## What You Do

Process the input data using the processing tool.

## Steps

1. Call `my_tool.process_data(input_data="<data>")`
2. Extract the result
3. Return in `processed_data` field

## Next

→ Return result
```

---

## Summary

**Bare Minimum**: Just `manifest.yml` with `sop_id`, `version`, `description`

**Recommended Minimum**: Add `overview.md` with role and workflow

**Best Practice**: Complete structure with:
- Organized manifest with all metadata
- Clear, actionable step instructions
- Concrete scenario examples
- Comprehensive troubleshooting
- Domain-specific glossary
- Proper agent configuration

The ReconVoy SOP is an excellent reference implementation showing all best practices in action.
