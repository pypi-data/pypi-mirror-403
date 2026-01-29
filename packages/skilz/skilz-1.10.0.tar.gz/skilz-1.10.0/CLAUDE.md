# CLAUDE.md


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
<location>.claude/skills/architect-agent/SKILL.md</location>
</skill>

<skill>
<name>design-doc-mermaid</name>
<description>Create Mermaid diagrams (activity, deployment, sequence, architecture) from text descriptions or source code. Use when asked to "create a diagram", "generate mermaid", "document architecture", "code to diagram", "create design doc", or "convert code to diagram". Supports hierarchical on-demand guide loading, Unicode semantic symbols, and Python utilities for diagram extraction and image conversion.</description>
<location>.claude/skills/design-doc-mermaid/SKILL.md</location>
</skill>

<skill>
<name>developing-with-docker</name>
<description>Debugging-first guidance for professional Docker development across CLI, Compose, Docker Desktop, and Rancher Desktop. Use when asked to "debug Docker", "troubleshoot containers", "fix Docker networking", "resolve volume permissions", or "Docker Compose issues", and when explaining cross-platform runtime behavior (Linux, macOS, Windows/WSL2) or Docker runtime architecture.</description>
<location>.claude/skills/developing-with-docker/SKILL.md</location>
</skill>

<skill>
<name>documentation-specialist</name>
<description>|</description>
<location>.claude/skills/documentation-specialist/SKILL.md</location>
</skill>

<skill>
<name>jira</name>
<description>Manages JIRA issues, projects, and workflows using Atlassian MCP. Use when asked to "create JIRA ticket", "search JIRA", "update JIRA issue", "transition issue", "sprint planning", or "epic management".</description>
<location>.claude/skills/jira/SKILL.md</location>
</skill>

<skill>
<name>mastering-aws-cdk</name>
<description>Guides AWS CDK v2 infrastructure-as-code development in TypeScript with patterns, troubleshooting, and deployment workflows. Use when creating or refactoring CDK stacks, debugging CloudFormation or CDK deploy errors, setting up CI/CD with GitHub Actions OIDC, or integrating AWS services (Lambda, API Gateway, ECS/Fargate, S3, DynamoDB, EventBridge, Aurora, MSK).</description>
<location>.claude/skills/mastering-aws-cdk/SKILL.md</location>
</skill>

<skill>
<name>mastering-confluence</name>
<description>|</description>
<location>.claude/skills/mastering-confluence/SKILL.md</location>
</skill>

<skill>
<name>mastering-gcloud-commands</name>
<description>|</description>
<location>.claude/skills/mastering-gcloud-commands/SKILL.md</location>
</skill>

<skill>
<name>mastering-git-cli</name>
<description>Git CLI operations, workflows, and automation for modern development (2025). Use when working with repositories, commits, branches, merging, rebasing, worktrees, submodules, or multi-repo architectures. Includes parallel agent workflow patterns, merge strategies, conflict resolution, and large repo optimization. Triggers on git commands, version control, merge conflicts, worktree setup, submodule management, repository troubleshooting, branch strategy, rebase operations, cherry-pick decisions, and CI/CD git integration.</description>
<location>.claude/skills/mastering-git-cli/SKILL.md</location>
</skill>

<skill>
<name>mastering-github-cli</name>
<description>|</description>
<location>.claude/skills/mastering-github-cli/SKILL.md</location>
</skill>

<skill>
<name>mastering-postgresql</name>
<description>PostgreSQL development for Python with full-text search (tsvector, tsquery, BM25 via pg_search), vector similarity (pgvector with HNSW/IVFFlat), JSONB and array indexing, and production deployment. Use when creating search features, storing AI embeddings, querying vector similarity, optimizing PostgreSQL indexes, or deploying to AWS RDS/Aurora, GCP Cloud SQL/AlloyDB, or Azure. Covers psycopg2, psycopg3, asyncpg, SQLAlchemy integration, Docker development setup, and index selection strategies. Triggers are Use "PostgreSQL search", "pgvector", "BM25 postgres", "JSONB index", "psycopg", "asyncpg", "PostgreSQL Docker", "AlloyDB vector". Does NOT cover - DBA administration (backup, replication, users), MySQL/MongoDB/Redis, schema design theory, stored procedures.</description>
<location>.claude/skills/mastering-postgresql/SKILL.md</location>
</skill>

<skill>
<name>mastering-typescript</name>
<description>|</description>
<location>.claude/skills/mastering-typescript/SKILL.md</location>
</skill>

<skill>
<name>notion-uploader-downloader</name>
<description>Bidirectional sync between Markdown and Notion. Upload .md files with images to Notion pages/databases, append to existing pages, or download Notion content back to markdown. Supports rich formatting, tables, code blocks, GitHub-flavored markdown, and recursive page hierarchy downloads with YAML frontmatter for round-trip sync.</description>
<location>.claude/skills/notion-uploader-downloader/SKILL.md</location>
</skill>

<skill>
<name>plantuml</name>
<description>Generate PlantUML diagrams from text descriptions and convert them to PNG/SVG images. Use when asked to "create a diagram", "generate PlantUML", "convert puml to image", "extract diagrams from markdown", or "prepare markdown for Confluence". Supports all PlantUML diagram types including UML (sequence, class, activity, state, component, deployment, use case, object, timing) and non-UML (ER diagrams, Gantt charts, JSON/YAML visualization, mindmaps, WBS, network diagrams, wireframes, and more).</description>
<location>.claude/skills/plantuml/SKILL.md</location>
</skill>

<skill>
<name>pr-reviewer</name>
<description>></description>
<location>.claude/skills/pr-reviewer/SKILL.md</location>
</skill>

<skill>
<name>project-memory</name>
<description>Set up and maintain a structured project memory system in docs/project_notes/ that tracks bugs with solutions, architectural decisions, key project facts, and work history. Use this skill when asked to "set up project memory", "track our decisions", "log a bug fix", "update project memory", or "initialize memory system". Configures both CLAUDE.md and AGENTS.md to maintain memory awareness across different AI coding tools.</description>
<location>.claude/skills/project-memory/SKILL.md</location>
</skill>

<skill>
<name>sdd</name>
<description>This skill should be used when users want guidance on Spec-Driven Development methodology using GitHub's Spec-Kit. Guide users through executable specification workflows for both new projects (greenfield) and existing codebases (brownfield). After any SDD command generates artifacts, automatically provide structured 10-point summaries with feature status tracking, enabling natural language feature management and keeping users engaged throughout the process.</description>
<location>.claude/skills/sdd/SKILL.md</location>
</skill>

<skill>
<name>using-firebase</name>
<description>Comprehensive Firebase development guidance for GCP-hosted applications. Covers Firestore database operations (CRUD, queries, transactions, data modeling), Cloud Functions (1st and 2nd generation, TypeScript and Python, all trigger types), Firebase CLI operations, emulator setup and data persistence, security rules (Firestore and Storage), authentication integration, hosting configuration, and GCP service integration. Use when working with Firebase projects, deploying Cloud Functions, querying Firestore, setting up triggers (Firestore, Auth, Storage, HTTP, Callable, Scheduled, Pub/Sub), managing security rules, configuring hosting rewrites/headers, managing secrets, or integrating with GCP services like BigQuery and Cloud Tasks. Triggers include firebase, firestore, cloud functions, firebase functions, firebase hosting, firebase auth, firebase storage, firebase emulator, firebase deploy, firebase init, firebase rules, callable function, scheduled function, onDocumentCreated, onRequest, onCall, onSchedule.</description>
<location>.claude/skills/using-firebase/SKILL.md</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
