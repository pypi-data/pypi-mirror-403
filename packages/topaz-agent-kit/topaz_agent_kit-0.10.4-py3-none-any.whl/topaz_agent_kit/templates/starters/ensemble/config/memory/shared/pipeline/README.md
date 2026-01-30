# Pipeline-Specific Shared Memory Templates

This directory contains shared memory templates organized by pipeline ID.

## Structure

```
config/memory/shared/pipeline/
├── reply_wizard/
│   ├── email_templates/
│   │   ├── greetings/
│   │   │   ├── formal.md
│   │   │   ├── casual.md
│   │   │   ├── professional.md
│   │   │   └── friendly.md
│   │   ├── closings/
│   │   │   ├── formal.md
│   │   │   ├── casual.md
│   │   │   ├── professional.md
│   │   │   └── friendly.md
│   │   ├── structures/
│   │   │   ├── inquiry_response.md
│   │   │   ├── complaint_response.md
│   │   │   └── follow_up.md
│   │   └── acknowledgments.md
│   └── company_info/
│       ├── standard_responses.md
│       ├── policies.md
│       └── tone_guidelines.md
└── invoice_processor/
    └── email_templates/
        └── greetings/
            └── formal.md
```

## How It Works

1. **Template Files**: Stored in `config/memory/shared/pipeline/{pipeline_id}/`
2. **Runtime Initialization**: On first pipeline run, files are copied to:
   - `data/agentos/{pipeline_id}/shared/`
3. **Agent Access**: Agents access via `/shared/email_templates/` (virtual path)

## Runtime Structure

```
data/agentos/
├── reply_wizard/
│   ├── shared/              ← From config/memory/shared/pipeline/reply_wizard/
│   │   └── email_templates/
│   └── agents/
│       └── {agent_id}/
│           ├── memory/
│           └── workspace/
└── invoice_processor/
    ├── shared/              ← From config/memory/shared/pipeline/invoice_processor/
    └── agents/
```

## Adding New Pipeline Templates

1. Create folder: `config/memory/shared/pipeline/{pipeline_id}/`
2. Add your template files
3. Files will be automatically initialized on first pipeline run
