# MCP eRegistrations BPA

**AI-powered Service Design for Government Digital Transformation**

An MCP server that enables AI assistants like Claude to design, configure, and deploy government services on the eRegistrations BPA platform using natural language.

## What It Does

Design and configure BPA services through conversation:

```
You: Create a "Business License" service
Claude: Created service with registration. Service ID: abc-123

You: Add a reviewer role
Claude: Added "Reviewer" role to the service

You: Set a $50 processing fee
Claude: Created fixed cost of $50 attached to the registration
```

Each step uses the right MCP tool. Full audit trail. Rollback if needed.

## Installation

### Desktop Extension (Easiest)

Download a `.mcpb` package from the [latest release](https://github.com/UNCTAD-eRegistrations/mcp-eregistrations-bpa/releases/latest) and double-click to install. No Python required.

- **Pre-configured**: `bpa-nigeria-*.mcpb`, `bpa-elsalvador-*.mcpb`, etc. (just install and login)
- **Generic**: `bpa-mcp-server-*.mcpb` (configure your BPA URL after install)

### One-Line Installer

For users comfortable with the command line. Requires [GitHub CLI](https://cli.github.com/) (`gh auth login` first).

**macOS / Linux:**

```bash
gh api repos/UNCTAD-eRegistrations/mcp-eregistrations-bpa/contents/scripts/install.sh --jq '.content' | base64 -d | bash
```

**Windows (PowerShell):**

```powershell
gh api repos/UNCTAD-eRegistrations/mcp-eregistrations-bpa/contents/scripts/install.ps1 --jq '.content' | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) } | iex
```

The installer provides an **interactive multi-select menu** — use arrow keys to navigate, space to select instances, and enter to confirm.

**With pre-configured instance(s):**

```bash
# macOS/Linux - single instance
gh api repos/UNCTAD-eRegistrations/mcp-eregistrations-bpa/contents/scripts/install.sh --jq '.content' | base64 -d | bash -s -- --instance kenya-test

# macOS/Linux - multiple instances
gh api repos/UNCTAD-eRegistrations/mcp-eregistrations-bpa/contents/scripts/install.sh --jq '.content' | base64 -d | bash -s -- --instance nigeria,kenya-test

# Windows
$script = gh api repos/UNCTAD-eRegistrations/mcp-eregistrations-bpa/contents/scripts/install.ps1 --jq '.content' | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }; Invoke-Expression "$script -Instance nigeria"
```

Available instances: `nigeria`, `elsalvador`, `kenya-test`, `cuba-test`, `cuba`

See [Installation Guide](docs/INSTALLATION.md) for all methods, troubleshooting, and advanced configuration.

## Manual Configuration

The MCP server supports two authentication providers:
- **Keycloak** (modern BPA systems) — OIDC with PKCE
- **CAS** (legacy BPA systems) — OAuth2 with Basic Auth

The provider is auto-detected based on which environment variables you set.

### Keycloak Configuration (Modern Systems)

**For Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "BPA-elsalvador-dev": {
      "command": "uvx",
      "args": ["--refresh", "mcp-eregistrations-bpa"],
      "env": {
        "BPA_INSTANCE_URL": "https://bpa.dev.els.eregistrations.org",
        "KEYCLOAK_URL": "https://login.dev.els.eregistrations.org",
        "KEYCLOAK_REALM": "SV"
      }
    }
  }
}
```

**For Claude Code** — add to `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "BPA-elsalvador-dev": {
      "command": "uvx",
      "args": ["--refresh", "mcp-eregistrations-bpa"],
      "env": {
        "BPA_INSTANCE_URL": "https://bpa.dev.els.eregistrations.org",
        "KEYCLOAK_URL": "https://login.dev.els.eregistrations.org",
        "KEYCLOAK_REALM": "SV"
      }
    }
  }
}
```

**Or via CLI** — install globally with one command:

```bash
claude mcp add --scope user --transport stdio BPA-kenya \
  --env BPA_INSTANCE_URL=https://bpa.test.kenya.eregistrations.org \
  --env KEYCLOAK_URL=https://login.test.kenya.eregistrations.org \
  --env KEYCLOAK_REALM=KE \
  -- uvx --refresh mcp-eregistrations-bpa
```

### CAS Configuration (Legacy Systems)

For older BPA deployments using CAS (e.g., Cuba test environment):

#### Step 1: Register OAuth Client in CAS

Before configuring the MCP server, you must register an OAuth client in CAS with:

| Setting | Value |
|---------|-------|
| Client ID | Your chosen ID (e.g., `mcp-bpa`) |
| Client Secret | Generated secret |
| Redirect URI | `http://127.0.0.1:8914/callback` |

> **Important:** The redirect URI must be exactly `http://127.0.0.1:8914/callback`. The MCP server uses a fixed port (8914) because CAS requires exact redirect URI matching.

#### Step 2: Configure MCP Server

**For Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "BPA-cuba-test": {
      "command": "uvx",
      "args": ["--refresh", "mcp-eregistrations-bpa"],
      "env": {
        "BPA_INSTANCE_URL": "https://bpa.test.cuba.eregistrations.org",
        "CAS_URL": "https://eid.test.cuba.eregistrations.org/cback/v1.0",
        "CAS_CLIENT_ID": "mcp-bpa",
        "CAS_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

**For Claude Code** — add to `~/.claude.json` (global) or `.mcp.json` (project):

```json
{
  "mcpServers": {
    "BPA-cuba-test": {
      "command": "uvx",
      "args": ["--refresh", "mcp-eregistrations-bpa"],
      "env": {
        "BPA_INSTANCE_URL": "https://bpa.test.cuba.eregistrations.org",
        "CAS_URL": "https://eid.test.cuba.eregistrations.org/cback/v1.0",
        "CAS_CLIENT_ID": "mcp-bpa",
        "CAS_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

**Or via CLI** — install globally with one command:

```bash
claude mcp add --scope user --transport stdio BPA-cuba-test \
  --env BPA_INSTANCE_URL=https://bpa.test.cuba.eregistrations.org \
  --env CAS_URL=https://eid.test.cuba.eregistrations.org/cback/v1.0 \
  --env CAS_CLIENT_ID=mcp-bpa \
  --env CAS_CLIENT_SECRET=your-client-secret \
  -- uvx --refresh mcp-eregistrations-bpa
```

> **Note:** CAS requires `CAS_CLIENT_SECRET` (unlike Keycloak which uses PKCE). Get this from your BPA administrator.

> **Troubleshooting:** If you get "command not found: uvx", you installed via curl which puts uvx in `~/.local/bin` (not in GUI app PATH). Fix: either `brew install uv`, or use `"command": "/bin/zsh", "args": ["-c", "$HOME/.local/bin/uvx mcp-eregistrations-bpa"]`

On first use, a browser opens for login. Your BPA permissions apply automatically.

> **Tip:** Name each MCP after its instance (e.g., `BPA-elsalvador-dev`, `BPA-cuba-test`) to manage multiple environments.

## 119 MCP Tools

| Category          | Capabilities                                                    |
| ----------------- | --------------------------------------------------------------- |
| **Services**      | Create, read, update, copy, export, transform to YAML           |
| **Registrations** | Full CRUD with parent service linking                           |
| **Institutions**  | Assign/unassign institutions to registrations                   |
| **Forms**         | Read/write Form.io components with container support            |
| **Roles**         | Create reviewer/approver/processor roles                        |
| **Bots**          | Configure workflow automation                                   |
| **Determinants**  | Text, select, numeric, boolean, date, classification, grid      |
| **Behaviours**    | Component visibility/validation effects with JSONLogic          |
| **Costs**         | Fixed fees and formula-based pricing                            |
| **Documents**     | Link document requirements to registrations                     |
| **Workflows**     | Arazzo-driven intent-based natural language service design      |
| **Debugging**     | Scan, investigate, and fix service configuration issues         |
| **Audit**         | Complete operation history with rollback                        |
| **Analysis**      | Service inspection and dependency mapping                       |

## Natural Language Workflows

Ask Claude to design services using plain English:

| What you say                            | What happens                                         |
| --------------------------------------- | ---------------------------------------------------- |
| "Create a permit service"               | Creates service + registration with proper structure |
| "Add a reviewer role to this service"   | Adds UserRole with 'processing' assignment           |
| "Set a $75 application fee"             | Creates fixed cost attached to registration          |
| "Add document requirement for ID proof" | Links requirement to the registration                |

The workflow system uses [Arazzo](https://spec.openapis.org/arazzo/latest.html) specifications to orchestrate multi-step operations. It extracts your intent, validates inputs, and executes with full audit trail.

### Workflow Tools

| Tool | Purpose |
|------|---------|
| `workflow_list` | List available workflows by category |
| `workflow_search` | Find workflows matching natural language intent |
| `workflow_describe` | Get workflow details, inputs, and steps |
| `workflow_execute` | Run workflow with provided inputs |
| `workflow_start_interactive` | Begin guided step-by-step execution |
| `workflow_status` | Check execution progress |
| `workflow_rollback` | Undo a completed workflow |

## Service Debugger Tools

AI-assisted debugging for BPA service configuration issues. Scan, investigate, and fix problems collaboratively.

### Available Tools

| Tool | Purpose |
|------|---------|
| `debug_scan` | Scan service for configuration issues |
| `debug_investigate` | Analyze root cause of a specific issue |
| `debug_fix` | Execute fix for a single issue |
| `debug_fix_batch` | Fix multiple issues of the same type |
| `debug_group_issues` | Group issues by type, severity, or fix strategy |
| `debug_plan` | Generate phased fix plan with dependencies |
| `debug_verify` | Verify fixes were applied successfully |

### Issue Types Detected

| Type | Severity | Auto-Fixable |
|------|----------|--------------|
| `effects_determinant` | High | Yes |
| `determinant` | High | Yes |
| `translation_moustache` | Medium | Yes |
| `catalog` | Medium | Yes |
| `missing_determinants_in_component_behaviours` | Medium | Yes |
| Component moustache issues | Low | Manual |
| Role/registration issues | Low | Manual |

### Usage Example

```
You: Scan this service for issues

Claude: Found 144 issues across 5 categories:
        - 67 effects referencing deleted determinants (HIGH)
        - 18 orphaned determinants (HIGH)
        - 33 translation issues (MEDIUM)
        [shows summary]

You: Fix all the high severity issues

Claude: I'll fix these in two phases:
        Phase 1: Delete 67 orphaned effects
        Phase 2: Delete 18 orphaned determinants

        Proceed? [waits for approval]

You: Yes, proceed

Claude: Fixed 85 issues. Audit IDs saved for rollback.
        Verification scan shows 0 high-severity issues remaining.
```

## Key Features

**Audit Trail** — Every operation logged (who, what, when). Query history with `audit_list`.

**Rollback** — Undo any write operation. Restore previous state with `rollback`.

**Export** — Get complete service definitions as clean YAML (~25x smaller than raw JSON) for review or version control.

**Copy** — Clone existing services with selective component inclusion.

**Pagination** — All list endpoints support `limit` and `offset` for large datasets. Responses include `total` and `has_more` for navigation.

## Form MCP Tools

BPA uses Form.io for dynamic forms. These tools provide full CRUD operations on form components.

### Available Tools

| Tool | Purpose |
|------|---------|
| `form_get` | Get form structure with simplified component list |
| `form_component_get` | Get full details of a specific component |
| `form_component_add` | Add new component to form |
| `form_component_update` | Update component properties |
| `form_component_remove` | Remove component from form |
| `form_component_move` | Move component to new position/parent |
| `form_update` | Replace entire form schema |

### Form Types

- `applicant` (default) - Main application form
- `guide` - Guidance/help form
- `send_file` - File submission form
- `payment` - Payment form

### Property Availability

Properties vary by tool. Use `form_get` for overview, `form_component_get` for full details:

| Property | `form_get` | `form_component_get` |
|----------|------------|----------------------|
| key | Yes | Yes |
| type | Yes | Yes |
| label | Yes | Yes |
| path | Yes | Yes |
| is_container | Yes | No |
| children_count | For containers | No |
| required | When present | Yes (in validate) |
| validate | No | Yes |
| registrations | No | Yes |
| determinant_ids | No | Yes (in raw) |
| data | No | Yes |
| default_value | No | Yes |
| raw | No | Yes (complete object) |

### Container Types

Form.io uses containers to organize components. Each has different child accessors:

```
Container Type    Children Accessor
--------------    -----------------
tabs              components[] (tab panes)
panel             components[]
columns           columns[].components[] (2-level)
fieldset          components[]
editgrid          components[] (repeatable)
datagrid          components[]
table             rows[][] (HTML table)
well              components[]
container         components[]
```

### Usage Examples

**Get form overview:**
```
form_get(service_id="abc-123", form_type="applicant")
# Returns: component_count, component_keys, simplified components list
```

**Get specific component details:**
```
form_component_get(service_id="abc-123", component_key="firstName")
# Returns: full component with validate, data, determinant_ids, raw object
```

**Add component to form:**
```
form_component_add(
    service_id="abc-123",
    component={"key": "email", "type": "email", "label": "Email Address"},
    parent_key="personalInfo",  # Optional: nest under panel
    position=0                   # Optional: insert at position
)
```

**Update component:**
```
form_component_update(
    service_id="abc-123",
    component_key="firstName",
    updates={"validate": {"required": True}, "label": "First Name *"}
)
```

**Move component:**
```
form_component_move(
    service_id="abc-123",
    component_key="phoneNumber",
    new_parent_key="contactPanel",
    new_position=1
)
```

All write operations include `audit_id` for rollback capability.

## Determinant & Conditional Logic Tools

Create conditional logic that controls form behavior based on user input.

### Determinant Types

| Type | Use Case | Example |
|------|----------|---------|
| `textdeterminant` | Text field conditions | Show panel if country = "USA" |
| `selectdeterminant` | Dropdown selection | Different fees by business type |
| `numericdeterminant` | Numeric comparisons | Require docs if amount > 10000 |
| `booleandeterminant` | Checkbox conditions | Show section if newsletter = true |
| `datedeterminant` | Date comparisons | Validate expiry > today |
| `classificationdeterminant` | Catalog selections | Requirements by industry code |
| `griddeterminant` | Grid/table row conditions | Validate line items |

### Behaviour Effects

Apply determinants to components to control visibility and validation:

```
effect_create(
    service_id="abc-123",
    determinant_id="det-456",
    component_key="additionalDocs",
    effect_type="visibility"  # or "required", "disabled"
)
```

Use `componentbehaviour_list` and `componentbehaviour_get` to inspect existing effects.

## Example Session

```
You: List all services

Claude: Found 12 services. [displays table with IDs, names, status]

You: Analyze the "Business Registration" service

Claude: [shows registrations, roles, determinants, documents, costs]
        Found 3 potential issues: orphaned determinant, missing cost...

You: Create a copy called "Business Registration v2"

Claude: Created service with ID abc-123. Copied 2 registrations,
        4 roles, 8 determinants. Audit ID: xyz-789
```

## Authentication

The MCP server supports two authentication providers, auto-detected based on configuration:

### Keycloak (Modern Systems)

Uses OIDC with Authorization Code + PKCE:

1. Browser opens automatically on first connection
2. Login with your Keycloak/BPA credentials
3. Tokens managed automatically with refresh
4. Your BPA permissions apply to all operations

**No client secret required** — Keycloak uses PKCE for secure public clients.

### CAS (Legacy Systems)

Uses OAuth2 with Basic Auth (client credentials):

1. Browser opens to CAS login page (`/cas/spa.html`)
2. Login with your eRegistrations credentials
3. Tokens exchanged using HTTP Basic Auth
4. User roles fetched from PARTC service (if configured)

**Client secret required** — CAS doesn't support PKCE, so `CAS_CLIENT_SECRET` must be provided.

### Provider Detection

The provider is automatically detected based on which environment variables are set:

| Configuration | Provider Used |
|---------------|---------------|
| `CAS_URL` set | CAS |
| `KEYCLOAK_URL` set (no `CAS_URL`) | Keycloak |

If both are set, CAS takes precedence.

## Configuration

### Common Variables

| Variable           | Description                 | Required |
| ------------------ | --------------------------- | -------- |
| `BPA_INSTANCE_URL` | BPA server URL              | Yes      |
| `LOG_LEVEL`        | DEBUG, INFO, WARNING, ERROR | No       |

### Keycloak Variables

| Variable           | Description                 | Required |
| ------------------ | --------------------------- | -------- |
| `KEYCLOAK_URL`     | Keycloak server URL         | Yes      |
| `KEYCLOAK_REALM`   | Keycloak realm name         | Yes      |

### CAS Variables

| Variable            | Description                          | Required | Default |
| ------------------- | ------------------------------------ | -------- | ------- |
| `CAS_URL`           | CAS OAuth2 server URL                | Yes      | —       |
| `CAS_CLIENT_ID`     | OAuth2 client ID                     | Yes      | —       |
| `CAS_CLIENT_SECRET` | OAuth2 client secret                 | Yes      | —       |
| `CAS_CALLBACK_PORT` | Local callback port for redirect URI | No       | 8914    |

> **Note:** The callback port must match the redirect URI registered in CAS. Default is 8914 (`http://127.0.0.1:8914/callback`).

> **Note:** The PARTC URL for fetching user roles is automatically derived from `CAS_URL` by replacing `/cback/` with `/partc/`.

Logs: `~/.config/mcp-eregistrations-bpa/instances/{instance-slug}/server.log`

## Development

```bash
# Clone and install
git clone https://github.com/UNCTAD-eRegistrations/mcp-eregistrations-bpa.git
cd mcp-eregistrations-bpa
uv sync

# Run tests (1200+ tests)
uv run pytest

# Lint and format
uv run ruff check . && uv run ruff format .

# Type checking
uv run mypy src/
```

## Complete Tool Reference

### Authentication (2 tools)

| Tool | Description |
|------|-------------|
| `auth_login` | Browser-based Keycloak OIDC login |
| `connection_status` | Check current authentication state |

### Services (6 tools)

| Tool | Description |
|------|-------------|
| `service_list` | List all services with pagination |
| `service_get` | Get service details by ID |
| `service_create` | Create new service |
| `service_update` | Update service properties |
| `service_publish` | Publish service for frontend |
| `service_activate` | Activate/deactivate service |

### Registrations (6 tools)

| Tool | Description |
|------|-------------|
| `registration_list` | List registrations with service filter |
| `registration_get` | Get registration details |
| `registration_create` | Create registration in service |
| `registration_delete` | Delete registration |
| `registration_activate` | Activate/deactivate registration |
| `serviceregistration_link` | Link registration to service |

### Institutions (7 tools)

| Tool | Description |
|------|-------------|
| `registrationinstitution_list` | List institution assignments |
| `registrationinstitution_get` | Get assignment details |
| `registrationinstitution_create` | Assign institution to registration |
| `registrationinstitution_delete` | Remove institution assignment |
| `registrationinstitution_list_by_institution` | List registrations by institution |
| `institution_discover` | Discover institution IDs |
| `institution_create` | Create institution in Keycloak |

### Fields (2 tools)

| Tool | Description |
|------|-------------|
| `field_list` | List fields for a service |
| `field_get` | Get field details |

### Forms (7 tools)

| Tool | Description |
|------|-------------|
| `form_get` | Get form structure |
| `form_component_get` | Get component details |
| `form_component_add` | Add component to form |
| `form_component_update` | Update component properties |
| `form_component_remove` | Remove component |
| `form_component_move` | Move component |
| `form_update` | Replace entire form schema |

### Determinants (12 tools)

| Tool | Description |
|------|-------------|
| `determinant_list` | List determinants for service |
| `determinant_get` | Get determinant details |
| `determinant_search` | Search determinants by criteria |
| `determinant_delete` | Delete determinant |
| `textdeterminant_create` | Create text comparison |
| `textdeterminant_update` | Update text determinant |
| `selectdeterminant_create` | Create dropdown selection |
| `numericdeterminant_create` | Create numeric comparison |
| `booleandeterminant_create` | Create checkbox condition |
| `datedeterminant_create` | Create date comparison |
| `classificationdeterminant_create` | Create catalog selection |
| `griddeterminant_create` | Create grid row condition |

### Behaviours (5 tools)

| Tool | Description |
|------|-------------|
| `componentbehaviour_list` | List behaviours for service |
| `componentbehaviour_get` | Get behaviour by ID |
| `componentbehaviour_get_by_component` | Get behaviour for component |
| `effect_create` | Create visibility/validation effect |
| `effect_delete` | Delete behaviour/effect |

### Actions (2 tools)

| Tool | Description |
|------|-------------|
| `componentaction_get` | Get component actions by ID |
| `componentaction_get_by_component` | Get actions for component |

### Bots (5 tools)

| Tool | Description |
|------|-------------|
| `bot_list` | List bots for service |
| `bot_get` | Get bot details |
| `bot_create` | Create workflow bot |
| `bot_update` | Update bot properties |
| `bot_delete` | Delete bot |

### Classifications (5 tools)

| Tool | Description |
|------|-------------|
| `classification_list` | List catalog classifications |
| `classification_get` | Get classification with entries |
| `classification_create` | Create classification catalog |
| `classification_update` | Update classification |
| `classification_export_csv` | Export as CSV |

### Notifications (2 tools)

| Tool | Description |
|------|-------------|
| `notification_list` | List service notifications |
| `notification_create` | Create notification trigger |

### Messages (5 tools)

| Tool | Description |
|------|-------------|
| `message_list` | List global message templates |
| `message_get` | Get message details |
| `message_create` | Create message template |
| `message_update` | Update message |
| `message_delete` | Delete message |

### Roles (8 tools)

| Tool | Description |
|------|-------------|
| `role_list` | List roles for service |
| `role_get` | Get role with statuses |
| `role_create` | Create UserRole or BotRole |
| `role_update` | Update role properties |
| `role_delete` | Delete role |
| `roleinstitution_create` | Assign institution to role |
| `roleregistration_create` | Assign registration to role |

### Role Status (4 tools)

| Tool | Description |
|------|-------------|
| `rolestatus_get` | Get status transition details |
| `rolestatus_create` | Create workflow transition |
| `rolestatus_update` | Update status |
| `rolestatus_delete` | Delete status |

### Role Units (4 tools)

| Tool | Description |
|------|-------------|
| `roleunit_list` | List units for role |
| `roleunit_get` | Get unit assignment |
| `roleunit_create` | Assign unit to role |
| `roleunit_delete` | Remove unit assignment |

### Documents (5 tools)

| Tool | Description |
|------|-------------|
| `requirement_list` | List global requirements |
| `documentrequirement_list` | List requirements for registration |
| `documentrequirement_create` | Link requirement to registration |
| `documentrequirement_update` | Update requirement |
| `documentrequirement_delete` | Remove requirement |

### Costs (4 tools)

| Tool | Description |
|------|-------------|
| `cost_create_fixed` | Create fixed fee |
| `cost_create_formula` | Create formula-based cost |
| `cost_update` | Update cost |
| `cost_delete` | Delete cost |

### Export (3 tools)

| Tool | Description |
|------|-------------|
| `service_export_raw` | Export service as JSON |
| `service_to_yaml` | Transform to AI-optimized YAML |
| `service_copy` | Clone service with new name |

### Analysis (1 tool)

| Tool | Description |
|------|-------------|
| `analyze_service` | AI-optimized service analysis |

### Audit (2 tools)

| Tool | Description |
|------|-------------|
| `audit_list` | List audit log entries |
| `audit_get` | Get audit entry details |

### Rollback (3 tools)

| Tool | Description |
|------|-------------|
| `rollback` | Undo write operation |
| `rollback_history` | Get object state history |
| `rollback_cleanup` | Clean old rollback states |

### Workflows (13 tools)

| Tool | Description |
|------|-------------|
| `workflow_list` | List available workflows |
| `workflow_describe` | Get workflow details |
| `workflow_search` | Search by intent |
| `workflow_execute` | Run workflow |
| `workflow_status` | Check execution status |
| `workflow_cancel` | Cancel running workflow |
| `workflow_retry` | Retry failed workflow |
| `workflow_rollback` | Undo completed workflow |
| `workflow_chain` | Execute workflow sequence |
| `workflow_start_interactive` | Begin guided mode |
| `workflow_continue` | Continue interactive session |
| `workflow_confirm` | Confirm and execute |
| `workflow_validate` | Validate workflow definitions |

### Debugging (7 tools)

| Tool | Description |
|------|-------------|
| `debug_scan` | Scan for configuration issues |
| `debug_investigate` | Analyze issue root cause |
| `debug_fix` | Fix single issue |
| `debug_fix_batch` | Fix multiple issues |
| `debug_group_issues` | Group issues by criteria |
| `debug_plan` | Generate fix plan |
| `debug_verify` | Verify fixes applied |

## Arazzo Workflow Reference (96 workflows)

### Service Creation

| Workflow | Description |
|----------|-------------|
| `createMinimalService` | Create service with registration |
| `createCompleteService` | Full service with roles and costs |
| `createQuickService` | Minimal service setup |

### Service Publishing

| Workflow | Description |
|----------|-------------|
| `fullPublish` | Complete publish workflow |
| `publishServiceChanges` | Publish pending changes |
| `activateService` | Activate service |
| `deactivateService` | Deactivate service |

### Roles & Workflow

| Workflow | Description |
|----------|-------------|
| `addRole` | Add role to service |
| `updateRole` | Update role properties |
| `configureStandardWorkflow` | Setup standard approval flow |
| `createCustomStatus` | Create workflow status |
| `updateCustomStatus` | Update status |
| `deleteRoleStatus` | Remove status |
| `createUserDefinedStatusWithMessage` | Status with notification |
| `updateUserDefinedStatusMessage` | Update status message |
| `getRoleFull` | Get complete role details |
| `getRoleStatus` | Get status details |
| `getRoleBots` | Get role bots |
| `getRoleUnits` | Get role units |
| `getRoleInstitutions` | Get role institutions |
| `getRoleHistory` | Get role version history |
| `listRolesWithDetails` | List all roles with details |
| `addUnitToRole` | Assign unit to role |
| `assignRoleInstitution` | Assign institution |
| `assignRegistrationToRole` | Assign single registration |
| `assignRegistrationsToRole` | Assign multiple registrations |
| `revertRoleVersion` | Rollback role version |

### Forms

| Workflow | Description |
|----------|-------------|
| `getApplicantForm` | Get applicant form |
| `getGuideForm` | Get guide form |
| `getDocumentForm` | Get document form |
| `updateApplicantForm` | Update applicant form |
| `updateGuideForm` | Update guide form |
| `toggleApplicantForm` | Enable/disable form |
| `deleteComponent` | Remove form component |
| `getField` | Get field details |
| `listFields` | List all fields |
| `getComponentActions` | Get component actions |
| `getComponentValidation` | Get validation rules |
| `getComponentFormula` | Get calculation formula |
| `updateComponentActions` | Update actions |
| `updateComponentValidation` | Update validation |
| `updateComponentFormula` | Update formula |
| `getFormHistory` | Get form version history |
| `revertFormVersion` | Rollback form version |
| `linkFieldToDeterminant` | Link field to condition |

### Determinants

| Workflow | Description |
|----------|-------------|
| `addTextDeterminant` | Create text condition |
| `addSelectDeterminant` | Create dropdown condition |
| `addRadioDeterminant` | Create radio condition |
| `addNumericDeterminant` | Create numeric condition |
| `addClassificationDeterminant` | Create catalog condition |
| `addGridDeterminant` | Create grid row condition |
| `updateTextDeterminant` | Update text determinant |

### Classifications

| Workflow | Description |
|----------|-------------|
| `listClassifications` | List all classifications |
| `searchClassifications` | Search classifications |
| `getClassificationType` | Get classification type |
| `createClassificationType` | Create classification type |
| `updateClassificationType` | Update type |
| `deleteClassificationType` | Delete type |
| `createClassificationGroup` | Create group |
| `deleteClassificationGroup` | Delete group |
| `listClassificationGroups` | List groups |
| `addClassificationField` | Add field to classification |
| `addClassificationFields` | Add multiple fields |
| `updateClassificationField` | Update field |
| `deleteClassificationField` | Delete field |
| `listClassificationFields` | List fields |
| `generateClassificationKeys` | Generate unique keys |
| `addSubcatalogs` | Add subcatalogs |
| `copyClassification` | Copy classification |
| `getServiceClassifications` | Get service classifications |

### Institutions

| Workflow | Description |
|----------|-------------|
| `completeInstitutionSetup` | Full institution setup |
| `assignRegistrationInstitution` | Assign to registration |
| `getRegistrationInstitution` | Get assignment |
| `removeRegistrationInstitution` | Remove assignment |
| `listRegistrationsByInstitution` | List by institution |

### Payments & Costs

| Workflow | Description |
|----------|-------------|
| `addFixedCost` | Add fixed fee |
| `addFormulaCost` | Add formula cost |
| `configureCompletePayments` | Full payment setup |
| `configureTieredPricing` | Tiered pricing rules |

### Documents

| Workflow | Description |
|----------|-------------|
| `addDocumentRequirement` | Add required document |

### Bots

| Workflow | Description |
|----------|-------------|
| `addBot` | Add automation bot |
| `updateBot` | Update bot |

### Notifications & Messages

| Workflow | Description |
|----------|-------------|
| `createServiceNotification` | Create notification |
| `updateNotification` | Update notification |
| `getNotification` | Get notification details |
| `listServiceNotifications` | List notifications |
| `sortServiceNotifications` | Reorder notifications |
| `createMessage` | Create message template |
| `getMessage` | Get message |
| `updateMessage` | Update message |
| `deleteMessage` | Delete message |
| `listMessages` | List messages |
| `updateFileStatus` | Update file status message |
| `updateFileValidatedStatusMessage` | Update validated message |
| `updateFileDeclineStatusMessage` | Update decline message |
| `updateFilePendingStatusMessage` | Update pending message |
| `updateFileRejectStatusMessage` | Update reject message |

### Debugging

| Workflow | Description |
|----------|-------------|
| `scanService` | Scan for issues |
| `planFixes` | Generate fix plan |
| `verifyFixes` | Verify fixes applied |

## License

Copyright (c) 2025-2026
UN for Trade & Development (UNCTAD)
Division on Investment and Enterprise (DIAE)
Business Facilitation Section

All rights reserved. See [LICENSE](LICENSE).

---

Part of [eRegistrations](https://businessfacilitation.org)
