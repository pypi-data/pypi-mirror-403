# AGENTS.md

## Project: Skilz CLI - Universal AI Skills Package Manager

**Status:** Production Ready (v1.7+)

Skilz is the universal package manager for AI skills - think `npm install` but for AI agent skills and tools. It installs and manages skills across 14+ AI coding assistants including Claude Code, OpenCode, Gemini, Codex, and more.

### Quick Links
- 📖 [README.md](README.md) - Project overview
- 📚 [User Manual](docs/USER_MANUAL.md) - Complete usage guide
- 🎯 [Comprehensive Guide](docs/COMPREHENSIVE_USER_GUIDE.md) - All agent-specific instructions
- 🚀 [Gemini Migration](docs/GEMINI_MIGRATION.md) - Gemini CLI support
- 🌐 [Universal Agent Guide](docs/UNIVERSAL_AGENT_GUIDE.md) - Multi-agent setup

### Architecture Overview

**Technology Stack:**
- **Language:** Python 3.10+
- **Package Manager:** Poetry
- **Task Runner:** Task (Go-based)
- **Testing:** pytest (448+ tests, 85%+ coverage)
- **CLI Framework:** Click
- **Config Format:** YAML

**Key Components:**
1. **Registry** - Maps skill IDs to Git repositories and commits
2. **Installer** - Clones repos, checks out commits, copies skills
3. **Agents** - 14+ AI agent adapters (Claude, OpenCode, Gemini, etc.)
4. **Manifest** - Tracks installed skills with `.skilz-manifest.yaml`
5. **Config Sync** - Updates agent config files (AGENTS.md, GEMINI.md, etc.)

**Core Workflows:**
- Install: `registry.yaml` → clone repo → checkout SHA → copy to agent dir → write manifest
- Update: Compare installed SHA vs registry SHA → reinstall if different
- List: Read manifests → check for updates → display status table
- Search: GitHub API → filter repositories → display results

### Build and Development Commands

```bash
# Setup
task install              # Install in development mode
poetry install           # Alternative: direct poetry install

# Testing
task test                # Run all tests (verbose)
task test:fast           # Run tests (fast, no verbose)
task coverage            # Tests with coverage report
task coverage:html       # HTML coverage report

# Quality
task lint                # Ruff linter
task lint:fix            # Auto-fix linting issues
task format              # Format code with ruff
task typecheck           # mypy type checking
task check               # Run all quality checks (lint + type + test)

# Building
task build               # Build distribution packages
task clean               # Remove build artifacts
task ci                  # Full CI pipeline locally

# Shortcuts
task t                   # Alias for test
task c                   # Alias for coverage
task l                   # Alias for lint
task f                   # Alias for format
```

### Code Quality Standards

- **Tests:** 448+ tests, 85%+ coverage, ALL must pass
- **Type Safety:** 100% type hints, mypy strict mode
- **Linting:** Ruff, PEP 8 compliance
- **Documentation:** Docstrings for all public APIs

### Architectural Decisions

**Key Design Principles:**
1. **Registry-Based Resolution** - Skills resolved through YAML registry mapping IDs to Git sources
2. **Reproducible Installs** - Pinned Git SHAs ensure identical installs across environments
3. **Agent Agnostic** - Abstract agent interface supports 14+ different AI tools
4. **Manifest Tracking** - Every install writes `.skilz-manifest.yaml` for auditability
5. **Native vs Universal** - Respects native skill directories, falls back to universal mode

### Project Structure

```
src/skilz/
  ├── cli.py              # Main CLI entry point
  ├── commands/           # Command implementations (install, list, etc.)
  ├── agents.py           # Agent registry and adapters
  ├── installer.py        # Core installation logic
  ├── registry.py         # Registry resolution
  ├── git_ops.py          # Git operations
  ├── config_sync.py      # Config file synchronization
  └── manifest.py         # Manifest file management

tests/
  ├── test_*.py           # Unit tests for each module
  └── conftest.py         # Shared pytest fixtures
```

### Important Notes for Code Changes

1. **Agent Support** - When adding new agent support, update:
   - `src/skilz/agents.py` - Add agent adapter
   - `src/skilz/agent_registry.py` - Register agent
   - Tests for new agent
   - Documentation (README.md, COMPREHENSIVE_USER_GUIDE.md)

2. **Testing** - Always run full test suite before commits:
   ```bash
   task check  # Runs lint + typecheck + test
   ```

3. **Config Sync** - Changes to config sync affect multiple agents:
   - Claude Code: `.claude/skills/` (native, no config sync)
   - OpenCode: `.opencode/skill/` (native, no config sync)
   - Universal: `.skilz/skills/` + AGENTS.md/GEMINI.md (config sync)

4. **Git Operations** - Use `git_ops.py` utilities, never direct git commands

5. **Documentation** - Update docs when changing:
   - CLI commands → USER_MANUAL.md
   - Agent support → COMPREHENSIVE_USER_GUIDE.md
   - Workflows → README.md

---

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills
below can help complete the task more effectively.

How to use skills:
- Invoke: Bash("skilz read <skill-name>")
- The skill content will load with detailed instructions
- Base directory provided in output for resolving bundled resources

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
</usage>

<available_skills>

<skill>
<name>architect-agent</name>
<description>Coordinates planning, delegation, and evaluation across architect and code agent workspaces. Use when asked to "write instructions for code agent", "initialize architect workspace", "grade code agent work", "send instructions", or "verify code agent setup".</description>
<location>.opencode/skill/architect-agent/SKILL.md</location>
</skill>

<skill>
<name>design-doc-mermaid</name>
<description>Create Mermaid diagrams (activity, deployment, sequence, architecture) from text descriptions or source code. Use when asked to "create a diagram", "generate mermaid", "document architecture", "code to diagram", "create design doc", or "convert code to diagram". Supports hierarchical on-demand guide loading, Unicode semantic symbols, and Python utilities for diagram extraction and image conversion.</description>
<location>.opencode/skill/design-doc-mermaid/SKILL.md</location>
</skill>

<skill>
<name>developing-with-docker</name>
<description>Debugging-first guidance for professional Docker development across CLI, Compose, Docker Desktop, and Rancher Desktop. Use when asked to "debug Docker", "troubleshoot containers", "fix Docker networking", "resolve volume permissions", or "Docker Compose issues", and when explaining cross-platform runtime behavior (Linux, macOS, Windows/WSL2) or Docker runtime architecture.</description>
<location>.opencode/skill/developing-with-docker/SKILL.md</location>
</skill>

<skill>
<name>documentation-specialist</name>
<description>|</description>
<location>.opencode/skill/documentation-specialist/SKILL.md</location>
</skill>

<skill>
<name>jira</name>
<description>Manages JIRA issues, projects, and workflows using Atlassian MCP. Use when asked to "create JIRA ticket", "search JIRA", "update JIRA issue", "transition issue", "sprint planning", or "epic management".</description>
<location>.opencode/skill/jira/SKILL.md</location>
</skill>

<skill>
<name>mastering-aws-cdk</name>
<description>Guides AWS CDK v2 infrastructure-as-code development in TypeScript with patterns, troubleshooting, and deployment workflows. Use when creating or refactoring CDK stacks, debugging CloudFormation or CDK deploy errors, setting up CI/CD with GitHub Actions OIDC, or integrating AWS services (Lambda, API Gateway, ECS/Fargate, S3, DynamoDB, EventBridge, Aurora, MSK).</description>
<location>.opencode/skill/mastering-aws-cdk/SKILL.md</location>
</skill>

<skill>
<name>mastering-confluence</name>
<description>|</description>
<location>.opencode/skill/mastering-confluence/SKILL.md</location>
</skill>

<skill>
<name>mastering-gcloud-commands</name>
<description>|</description>
<location>.opencode/skill/mastering-gcloud-commands/SKILL.md</location>
</skill>

<skill>
<name>mastering-git-cli</name>
<description>Git CLI operations, workflows, and automation for modern development (2025). Use when working with repositories, commits, branches, merging, rebasing, worktrees, submodules, or multi-repo architectures. Includes parallel agent workflow patterns, merge strategies, conflict resolution, and large repo optimization. Triggers on git commands, version control, merge conflicts, worktree setup, submodule management, repository troubleshooting, branch strategy, rebase operations, cherry-pick decisions, and CI/CD git integration.</description>
<location>.opencode/skill/mastering-git-cli/SKILL.md</location>
</skill>

<skill>
<name>mastering-github-cli</name>
<description>|</description>
<location>.opencode/skill/mastering-github-cli/SKILL.md</location>
</skill>

<skill>
<name>mastering-postgresql</name>
<description>PostgreSQL development for Python with full-text search (tsvector, tsquery, BM25 via pg_search), vector similarity (pgvector with HNSW/IVFFlat), JSONB and array indexing, and production deployment. Use when creating search features, storing AI embeddings, querying vector similarity, optimizing PostgreSQL indexes, or deploying to AWS RDS/Aurora, GCP Cloud SQL/AlloyDB, or Azure. Covers psycopg2, psycopg3, asyncpg, SQLAlchemy integration, Docker development setup, and index selection strategies. Triggers are Use "PostgreSQL search", "pgvector", "BM25 postgres", "JSONB index", "psycopg", "asyncpg", "PostgreSQL Docker", "AlloyDB vector". Does NOT cover - DBA administration (backup, replication, users), MySQL/MongoDB/Redis, schema design theory, stored procedures.</description>
<location>.opencode/skill/mastering-postgresql/SKILL.md</location>
</skill>

<skill>
<name>mastering-typescript</name>
<description>|</description>
<location>.opencode/skill/mastering-typescript/SKILL.md</location>
</skill>

<skill>
<name>notion-uploader-downloader</name>
<description>Bidirectional sync between Markdown and Notion. Upload .md files with images to Notion pages/databases, append to existing pages, or download Notion content back to markdown. Supports rich formatting, tables, code blocks, GitHub-flavored markdown, and recursive page hierarchy downloads with YAML frontmatter for round-trip sync.</description>
<location>.opencode/skill/notion-uploader-downloader/SKILL.md</location>
</skill>

<skill>
<name>plantuml</name>
<description>Generate PlantUML diagrams from text descriptions and convert them to PNG/SVG images. Use when asked to "create a diagram", "generate PlantUML", "convert puml to image", "extract diagrams from markdown", or "prepare markdown for Confluence". Supports all PlantUML diagram types including UML (sequence, class, activity, state, component, deployment, use case, object, timing) and non-UML (ER diagrams, Gantt charts, JSON/YAML visualization, mindmaps, WBS, network diagrams, wireframes, and more).</description>
<location>.opencode/skill/plantuml/SKILL.md</location>
</skill>

<skill>
<name>pr-reviewer</name>
<description>></description>
<location>.opencode/skill/pr-reviewer/SKILL.md</location>
</skill>

<skill>
<name>project-memory</name>
<description>Set up and maintain a structured project memory system in docs/project_notes/ that tracks bugs with solutions, architectural decisions, key project facts, and work history. Use this skill when asked to "set up project memory", "track our decisions", "log a bug fix", "update project memory", or "initialize memory system". Configures both CLAUDE.md and AGENTS.md to maintain memory awareness across different AI coding tools.</description>
<location>.opencode/skill/project-memory/SKILL.md</location>
</skill>

<skill>
<name>sdd</name>
<description>This skill should be used when users want guidance on Spec-Driven Development methodology using GitHub's Spec-Kit. Guide users through executable specification workflows for both new projects (greenfield) and existing codebases (brownfield). After any SDD command generates artifacts, automatically provide structured 10-point summaries with feature status tracking, enabling natural language feature management and keeping users engaged throughout the process.</description>
<location>.opencode/skill/sdd/SKILL.md</location>
</skill>

<skill>
<name>using-firebase</name>
<description>Comprehensive Firebase development guidance for GCP-hosted applications. Covers Firestore database operations (CRUD, queries, transactions, data modeling), Cloud Functions (1st and 2nd generation, TypeScript and Python, all trigger types), Firebase CLI operations, emulator setup and data persistence, security rules (Firestore and Storage), authentication integration, hosting configuration, and GCP service integration. Use when working with Firebase projects, deploying Cloud Functions, querying Firestore, setting up triggers (Firestore, Auth, Storage, HTTP, Callable, Scheduled, Pub/Sub), managing security rules, configuring hosting rewrites/headers, managing secrets, or integrating with GCP services like BigQuery and Cloud Tasks. Triggers include firebase, firestore, cloud functions, firebase functions, firebase hosting, firebase auth, firebase storage, firebase emulator, firebase deploy, firebase init, firebase rules, callable function, scheduled function, onDocumentCreated, onRequest, onCall, onSchedule.</description>
<location>.opencode/skill/using-firebase/SKILL.md</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>

---

## Quality Assurance Protocol

**IMPORTANT**: After ANY code changes, you MUST:

1. Use the `qa-enforcer` agent (if available) to enforce test coverage and quality standards
2. Run the full quality check pipeline:
   ```bash
   task check  # Runs lint + typecheck + test with coverage
   ```
3. Only consider the task complete after both steps pass successfully

This is a mandatory workflow that should be followed automatically without prompting.

---

## Development Workflow

1. **Make Changes** - Edit code following PEP 8 and type hints
2. **Run Tests** - `task test` or `task coverage`
3. **Check Quality** - `task check` (lint + typecheck + test)
4. **Build** - `task build` (creates wheel and sdist)
5. **Manual Test** - Install locally: `pip install -e .`

---

## Notes for AI Agents

- This is a Python CLI tool using Click framework
- Poetry manages dependencies (pyproject.toml)
- Task manages automation (Taskfile.yml)
- All commands use `skilz` prefix: `skilz install`, `skilz list`, etc.
- Registry format: `owner_repo/skill-name` → Git repo + SHA
- Supports both user-level (`~/.skilz/`) and project-level (`.skilz/`) installs
