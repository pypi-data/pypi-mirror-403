# Reference: Human-in-the-Loop (HITL) Gates

This document provides detailed reference for HITL gate types, configuration, placement strategies, and async HITL mode.

---

## HITL Modes Overview

| Mode | Behavior | Use When |
|------|----------|-----------|
| **Sync** (default) | Pipeline blocks until human responds | Simple workflows, single-item processing |
| **Async** | Pipeline continues, requests queued for review | Batch processing, loop patterns, high-throughput |

---

## Gate Types Overview

| Type | Purpose | User Action |
|------|---------|-------------|
| Approval | Review and approve/reject | Click approve or reject |
| Input | Collect information | Fill form fields |
| Selection | Choose between options | Select from list |

---

## 1. Approval Gates

**Use When**: Human needs to review and approve/reject before continuing.

### Basic Approval Gate

```yaml
hitl:
  - id: "{pipeline_id}_approve_{purpose}"
    type: "approval"
    after: "{agent_id}"
    title: "Review {Agent} Output"
    description_template: "config/hitl/{gate_id}.jinja"
    actions:
      on_approve: "continue"
      on_reject: "stop"
```

### Approval with Retry

```yaml
hitl:
  - id: "{pipeline_id}_approve_{purpose}"
    type: "approval"
    after: "{agent_id}"
    title: "Review Analysis"
    description_template: "config/hitl/{gate_id}.jinja"
    actions:
      on_approve: "continue"
      on_reject:
        action: "retry"
        retry_agent: "{agent_to_retry}"
        max_retries: 3
        inject_context: true
```

### Description Template Example

```jinja
## Review Required

The {{ agent_name }} has completed analysis.

**Summary:**
{{ agent_output.summary }}

**Key Findings:**
{% for finding in agent_output.findings %}
- {{ finding }}
{% endfor %}

**Confidence Score:** {{ agent_output.confidence }}%

Please review and approve to continue, or reject to stop the pipeline.
```

---

## 2. Input Gates

**Use When**: Need to collect information from user.

### Basic Input Gate

```yaml
hitl:
  - id: "{pipeline_id}_input_{purpose}"
    type: "input"
    after: "{agent_id}"  # or "start"
    title: "Provide Information"
    description_template: "config/hitl/{gate_id}.jinja"
    fields:
      - name: "field_name"
        type: "text"
        label: "Field Label"
        required: true
        placeholder: "Enter value..."
```

### Input Gate at Start (File Upload)

```yaml
hitl:
  - id: "{pipeline_id}_upload_document"
    type: "input"
    after: "start"
    title: "Upload Document"
    description_template: "config/hitl/{gate_id}.jinja"
    fields:
      - name: "document_file"
        type: "file"
        label: "Document"
        required: true
        accept: ".pdf,.docx,.txt"
      - name: "document_type"
        type: "select"
        label: "Document Type"
        required: true
        options:
          - value: "contract"
            label: "Contract"
          - value: "invoice"
            label: "Invoice"
          - value: "report"
            label: "Report"
```

### Field Types

| Type | Description | Additional Properties |
|------|-------------|----------------------|
| `text` | Single line text | `placeholder`, `pattern` |
| `textarea` | Multi-line text | `rows`, `placeholder` |
| `select` | Dropdown selection | `options` |
| `checkbox` | Boolean toggle | `default` |
| `file` | File upload | `accept`, `multiple` |
| `number` | Numeric input | `min`, `max`, `step` |
| `date` | Date picker | `min`, `max` |
| `email` | Email input | `placeholder` |

### Pre-populated Fields

```yaml
fields:
  - name: "suggested_response"
    type: "textarea"
    label: "Response Draft"
    required: true
    default: "{{ drafter.response }}"  # Pre-fill from agent output
    rows: 10
```

### Conditional Fields

```yaml
fields:
  - name: "needs_escalation"
    type: "checkbox"
    label: "Escalate to Manager"
    default: false
  - name: "escalation_reason"
    type: "textarea"
    label: "Escalation Reason"
    required: true
    condition: "{{ needs_escalation }} == true"
```

---

## 3. Selection Gates

**Use When**: User needs to choose between options.

### Basic Selection Gate

```yaml
hitl:
  - id: "{pipeline_id}_select_{purpose}"
    type: "selection"
    after: "{agent_id}"
    title: "Select Option"
    description_template: "config/hitl/{gate_id}.jinja"
    options:
      - value: "option_1"
        label: "Option 1"
        description: "Description of option 1"
      - value: "option_2"
        label: "Option 2"
        description: "Description of option 2"
```

### Selection with Branch Routing

```yaml
hitl:
  - id: "{pipeline_id}_select_path"
    type: "selection"
    after: "{agent_id}"
    title: "Choose Processing Path"
    options:
      - value: "fast_track"
        label: "Fast Track"
        description: "Quick processing, less thorough"
        next_agent: "fast_processor"
      - value: "detailed"
        label: "Detailed Analysis"
        description: "Thorough analysis, takes longer"
        next_agent: "detailed_processor"
      - value: "expert_review"
        label: "Expert Review"
        description: "Send to human expert"
        next_agent: "expert_notifier"
```

### Dynamic Options from Agent Output

```yaml
hitl:
  - id: "{pipeline_id}_select_candidate"
    type: "selection"
    after: "ranker"
    title: "Select Best Candidate"
    options_source: "ranker.candidates"
    option_template:
      value: "{{ item.id }}"
      label: "{{ item.name }}"
      description: "Score: {{ item.score }}"
```

---

## Gate Placement Strategies

### At Pipeline Start

```yaml
pattern:
  type: sequential
  steps:
    # HITL gate is first step
    - pattern:
        type: hitl
        gate_id: "{pipeline_id}_upload_document"
    - extractor
    - analyzer
```

Or using `after: "start"`:
```yaml
hitl:
  - id: "{pipeline_id}_upload"
    type: "input"
    after: "start"
```

### Between Agents

```yaml
pattern:
  type: sequential
  steps:
    - analyzer
    # Implicit HITL gate placement via "after"
    - processor
```

With explicit gate:
```yaml
hitl:
  - id: "{pipeline_id}_review_analysis"
    type: "approval"
    after: "analyzer"
```

### Before Critical Actions

```yaml
pattern:
  type: sequential
  steps:
    - drafter
    - pattern:
        type: hitl
        gate_id: "{pipeline_id}_approve_email"
    - email_sender
```

### In Loops

```yaml
pattern:
  type: loop
  iterate_over: "scanner.items"
  steps:
    - processor
    - pattern:
        type: hitl
        gate_id: "{pipeline_id}_approve_item"
        condition: "{{processor.needs_review}} == true"
```

---

## Conditional Gates

Gates can be conditional:

```yaml
hitl:
  - id: "{pipeline_id}_escalate"
    type: "selection"
    after: "analyzer"
    condition: "{{analyzer.risk_score}} > 80"
    title: "High Risk - Manual Review Required"
```

---

## Context Injection

When retry is used, previous context can be injected:

```yaml
actions:
  on_reject:
    action: "retry"
    retry_agent: "drafter"
    inject_context: true
    context_fields:
      - "rejection_reason"
      - "user_feedback"
```

The retry agent's prompt can then use:
```jinja
{% if rejection_reason %}
**Previous Attempt Rejected:**
{{ rejection_reason }}

**User Feedback:**
{{ user_feedback }}

Please address this feedback in your revised output.
{% endif %}
```

---

## Timeout Configuration

```yaml
hitl:
  - id: "{pipeline_id}_approve"
    type: "approval"
    after: "analyzer"
    timeout:
      duration: 3600  # seconds
      action: "auto_approve"  # or "auto_reject" or "stop"
```

---

## HITL Description Templates

### Best Practices

1. **Clear context**: Explain what was done and why review is needed
2. **Key information**: Highlight important data points
3. **Actionable**: Clear instructions on what user should do

### Template Structure

```jinja
## {Gate Title}

### Summary
{Brief description of what happened}

### Key Information

| Field | Value |
|-------|-------|
| {Field 1} | {{ agent.field1 }} |
| {Field 2} | {{ agent.field2 }} |

### Details

{{ agent.detailed_output }}

### Action Required

{Instructions for the user}
```

### Using Markdown Tables

Follow whitespace rules (see `reference_jinja.md`):
```jinja
| Field | Value |
|-------|-------|
{%- for item in items %}
| {{ item.name }} | {{ item.value }} |
{%- endfor %}
```

---

---

## Async HITL Configuration

### When to Use Async HITL

**Use Async HITL when**:
- ✅ Processing many items in a loop (batch processing)
- ✅ Only some items need human review
- ✅ Pipeline should continue processing while reviews are queued
- ✅ Operations center manages review queue separately

**Use Sync HITL when**:
- ✅ Simple workflows with single items
- ✅ Pipeline must wait for human decision before continuing
- ✅ Sequential approval flow required

### Enabling Async HITL

**1. Pipeline Configuration** (`config/pipelines/{pipeline_id}.yml`):

```yaml
# =============================================================================
# EXECUTION SETTINGS - Async HITL Configuration
# =============================================================================
execution_settings:
  hitl_mode: "async"              # "sync" (default) or "async"
  checkpoint_expiry_days: 7       # How long checkpoints remain valid

# =============================================================================
# CASE MANAGEMENT CONFIGURATION
# =============================================================================
case_management:
  config_file: "cases/{pipeline_id}.yml"  # Required for async HITL
  tracking_variables:                    # Optional: customize variable names
    hitl_queued: "hitl_queued_cases"    # Default: "hitl_queued_cases"
    completed: "completed_cases"         # Default: "completed_cases"
```

**2. Case Configuration File** (`config/cases/{pipeline_id}.yml`):

```yaml
# Case type for categorization
case_type: "problem_type"

# Identity configuration - how to identify cases
identity:
  prefix: "CASE"                    # Case ID prefix (e.g., "CASE-ABC12345")
  uniqueness: "uuid_suffix"         # "uuid_suffix" (default), "timestamp", or "none"

# Detail view - what to show in case detail panel
detail_view:
  sections:
    - id: "analysis"
      title: "Analysis Results"
      source_agent: "analyzer"
      fields:
        - source: "analyzer.result"
          label: "Result"
          type: text
        - source: "analyzer.confidence"
          label: "Confidence"
          type: number
```

**Field Types**: `text`, `multiline`, `number`, `boolean`, `list`, `object`

### How Async HITL Works

1. **Pipeline Execution**:
   - Pipeline runs normally until it hits a HITL gate
   - Instead of blocking, creates a checkpoint and queues the request
   - Pipeline continues processing (especially useful in loops)

2. **Checkpoint Creation**:
   - Full execution context saved (all agent outputs up to the gate)
   - Case created with extracted data for display
   - HITL request queued for review

3. **Operations UI**:
   - Review requests appear in Operations Center queue
   - Cases can be reviewed and approved/rejected
   - Pipeline resumes from checkpoint when ready

4. **Resume from Checkpoint**:
   - When case is approved/rejected, pipeline resumes
   - Full context restored from checkpoint
   - Pipeline continues from the gate

### Async HITL in Loop Patterns

When using async HITL in loops, the pipeline continues processing remaining items:

```yaml
pattern:
  type: loop
  iterate_over: "scanner.items"
  body:
    - processor
    - gate: review_item
      condition: "{{processor.needs_review}} == true"
```

**Behavior**:
- Items needing review are queued
- Pipeline continues with remaining items
- Queued cases tracked in `hitl_queued_cases` variable
- Summary reporter can access queued cases list

### Tracking Variables

When async HITL is enabled in loops, these variables are automatically created:

- `hitl_queued_cases`: List of queued cases (customizable via `tracking_variables.hitl_queued`)
- `completed_cases`: List of completed cases (customizable via `tracking_variables.completed`)

These are available to downstream agents (e.g., summary reporters).

---

## Common HITL Patterns

### Review Before Send

```yaml
# After drafter, before sender
hitl:
  - id: "{pipeline_id}_review_draft"
    type: "approval"
    after: "drafter"
    title: "Review Before Sending"
```

### Upload at Start, Review at End

```yaml
hitl:
  - id: "{pipeline_id}_upload"
    type: "input"
    after: "start"
  - id: "{pipeline_id}_final_review"
    type: "approval"
    after: "finalizer"
```

### Conditional Escalation

```yaml
hitl:
  - id: "{pipeline_id}_escalate"
    type: "selection"
    after: "analyzer"
    condition: "{{analyzer.confidence}} < 0.7"
    title: "Low Confidence - Please Review"
    options:
      - value: "proceed"
        label: "Proceed Anyway"
      - value: "escalate"
        label: "Escalate to Expert"
      - value: "reject"
        label: "Reject and Stop"
```

