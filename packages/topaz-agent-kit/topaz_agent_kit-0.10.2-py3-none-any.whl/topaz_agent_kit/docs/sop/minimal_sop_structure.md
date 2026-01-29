# Minimal SOP Structure

## Required Files (Absolute Minimum)

For a simple SOP to work, you only need **ONE file**:

### 1. `manifest.yml` - **REQUIRED**

This is the only file that the SOP toolkit requires. It defines the SOP structure and metadata.

**Minimal manifest.yml:**
```yaml
sop_id: my_simple_agent
version: "1.0.0"
description: "Simple SOP for my agent"

sections: []  # Empty sections list is valid
```

**What happens:**
- `sop_initialize` loads the manifest successfully
- Returns empty `overview`, `available_sections`, and `workflow_steps`
- Agent can still call `sop_get_section` for any section it defines later

---

## Recommended Files (For a Useful SOP)

### 2. `overview.md` - **RECOMMENDED**

Provides context and high-level guidance. Loaded automatically during `sop_initialize`.

**Minimal manifest.yml with overview:**
```yaml
sop_id: my_simple_agent
version: "1.0.0"
description: "Simple SOP for my agent"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Overview of the agent's role and workflow"
    read_at: start
```

**Minimal overview.md:**
```markdown
# My Simple Agent - Overview

## Your Role

You are responsible for [brief description].

## Key Steps

1. Step 1
2. Step 2
3. Step 3
```

---

## Optional Files (Only Loaded On-Demand)

These files are **NOT required** for the SOP to work. They're only loaded when the agent explicitly calls:
- `sop_get_section(section_id="...")`
- `sop_get_example(scenario_name="...")`
- `sop_get_troubleshooting(issue="...")`

### 3. `steps/step_*.md` - **OPTIONAL**

Procedural steps. Only needed if the agent needs detailed step-by-step instructions.

**When to include:**
- Complex multi-step procedures
- Steps that need to be followed in order
- Steps with dependencies

**When to skip:**
- Simple single-step operations
- Operations that can be described in overview.md

### 4. `scenarios/*.md` - **OPTIONAL**

Example scenarios. Only needed if the agent benefits from concrete examples.

**When to include:**
- Multiple different scenarios/patterns
- Complex cases that need examples
- Edge cases that need illustration

**When to skip:**
- Simple, straightforward operations
- Single pattern/scenario

### 5. `troubleshooting.md` - **OPTIONAL**

Error handling guidance. Only needed if the agent encounters common errors.

**When to include:**
- Known error conditions
- Common mistakes
- Recovery procedures

**When to skip:**
- Simple operations with no known issues
- Operations that fail fast with clear errors

---

## Examples

### Example 1: Simplest Possible SOP

```
config/sop/my_pipeline/my_agent/
└── manifest.yml
```

**manifest.yml:**
```yaml
sop_id: my_agent
version: "1.0.0"
description: "Simple agent SOP"

sections: []
```

**Usage:**
- Agent calls `sop_initialize` → Success (empty sections)
- Agent doesn't need to call any other SOP tools
- SOP structure is ready for future expansion

---

### Example 2: Minimal Useful SOP

```
config/sop/my_pipeline/my_agent/
├── manifest.yml
└── overview.md
```

**manifest.yml:**
```yaml
sop_id: my_agent
version: "1.0.0"
description: "Simple agent SOP"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Agent overview"
    read_at: start
```

**overview.md:**
```markdown
# My Agent - Overview

## Your Role

Process incoming data and generate output.

## Instructions

1. Read input data
2. Process it
3. Return result
```

**Usage:**
- Agent calls `sop_initialize` → Gets overview automatically
- Agent follows instructions in overview
- No need for additional sections

---

### Example 3: SOP with One Step

```
config/sop/my_pipeline/my_agent/
├── manifest.yml
├── overview.md
└── steps/
    └── step_01_process.md
```

**manifest.yml:**
```yaml
sop_id: my_agent
version: "1.0.0"
description: "Agent with one step"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Agent overview"
    read_at: start
  
  - id: step_01_process
    file: steps/step_01_process.md
    type: procedure
    description: "Main processing step"
    read_at: on_demand
```

**Usage:**
- Agent calls `sop_initialize` → Gets overview
- Agent calls `sop_get_section(section_id="step_01_process")` when needed
- Step file is loaded on-demand

---

## Key Principles

1. **Start Simple**: Begin with just `manifest.yml` and `overview.md`
2. **Add On-Demand**: Only add steps/scenarios/troubleshooting when actually needed
3. **Lazy Loading**: Files are only loaded when the agent requests them
4. **No Validation**: The toolkit doesn't validate that referenced files exist until they're requested

---

## File Loading Behavior

| File Type | When Loaded | Required? |
|-----------|-------------|-----------|
| `manifest.yml` | During `sop_initialize` | ✅ **YES** |
| `overview.md` | During `sop_initialize` (if in manifest) | ⚠️ Recommended |
| `steps/*.md` | On `sop_get_section()` call | ❌ Optional |
| `scenarios/*.md` | On `sop_get_example()` call | ❌ Optional |
| `troubleshooting.md` | On `sop_get_troubleshooting()` call | ❌ Optional |

---

## Best Practices

1. **Always include `manifest.yml`** - It's the entry point
2. **Always include `overview.md`** - Provides essential context
3. **Add steps only when needed** - Don't create steps for simple operations
4. **Use scenarios sparingly** - Only for complex patterns
5. **Add troubleshooting last** - Only after encountering real issues

---

## Migration Path

You can start with a minimal SOP and expand it:

```
Phase 1: manifest.yml only
  ↓
Phase 2: + overview.md
  ↓
Phase 3: + steps/ (as needed)
  ↓
Phase 4: + scenarios/ (if examples help)
  ↓
Phase 5: + troubleshooting.md (if errors occur)
```
