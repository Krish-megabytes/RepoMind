# PRD — RepoMind: GitHub Repository Intelligence RAG

## 1. Product Overview

**Product Name:** RepoMind  
**Product Type:** AI-powered GitHub Repository Intelligence Assistant  
**Primary Goal:** Allow developers to connect a GitHub repository and ask natural-language questions about its codebase, architecture, dependencies, documentation, and implementation details.

RepoMind uses Retrieval-Augmented Generation (RAG) to retrieve relevant repository context before generating an answer. Answers should include file-level and, where available, line-level citations so users can verify the response.

---

## 2. Problem Statement

Developers often spend significant time understanding unfamiliar codebases. Traditional code search requires knowing filenames, functions, or keywords in advance, while general-purpose LLMs may hallucinate, lack repository context, or provide answers without evidence.

RepoMind addresses this by indexing a repository and combining semantic retrieval, keyword search, reranking, and LLM generation.

---

## 3. Target Users

### Primary Users
- Software developers
- Students learning unfamiliar codebases
- Open-source contributors
- Software engineering interview candidates
- Developers onboarding onto existing projects

### Secondary Users
- Technical leads
- Teaching/mentoring teams
- Small development teams

---

## 4. Goals

### Primary Goals
1. Accept a public GitHub repository URL.
2. Ingest supported source code and documentation.
3. Create searchable vector representations of repository content.
4. Answer repository-specific questions using RAG.
5. Provide source citations for generated answers.
6. Support multi-turn conversations.
7. Provide repository architecture and technology summaries.
8. Evaluate retrieval and answer quality.

### Non-Goals for MVP
- Automatically modifying repository code.
- Deploying repositories.
- Running arbitrary repository code.
- Supporting every programming language initially.
- Replacing IDEs or full static-analysis platforms.

---

## 5. Core User Flow

```text
User
 ↓
Enter GitHub Repository URL
 ↓
Validate Repository
 ↓
Clone / Fetch Repository
 ↓
Filter Relevant Files
 ↓
Parse Source Code + Documentation
 ↓
Code-Aware Chunking
 ↓
Generate Embeddings
 ↓
Store in Vector Database
 ↓
User Asks Question
 ↓
Query Understanding
 ↓
Hybrid Retrieval
 ↓
Reranking
 ↓
Context Construction
 ↓
LLM Generation
 ↓
Answer + Source Citations
```

---

# 6. Functional Requirements

## FR-01: Repository Input

The user must be able to enter a GitHub repository URL.

Example:

`https://github.com/username/project`

The system should:
- Validate the URL.
- Extract repository owner and name.
- Reject unsupported URLs.
- Show repository ingestion status.

---

## FR-02: Repository Ingestion

The backend should fetch the repository and process supported files.

Initially supported:
- Python
- JavaScript
- TypeScript
- Java
- C++
- C
- HTML
- CSS
- Markdown
- JSON
- YAML
- SQL

Files/directories to ignore:

```text
.git/
node_modules/
dist/
build/
__pycache__/
.venv/
venv/
coverage/
*.lock
.env
```

The system must not expose secrets found in environment/configuration files.

---

## FR-03: Code-Aware Parsing

The system should identify logical code units where possible:

- Classes
- Functions
- Methods
- Interfaces
- Modules
- Imports
- Documentation sections

Each chunk should contain metadata.

Example:

```json
{
  "repository": "example-project",
  "file": "src/auth/authService.js",
  "language": "javascript",
  "symbol": "loginUser",
  "start_line": 25,
  "end_line": 67
}
```

---

## FR-04: Chunking

The system should use code-aware chunking rather than blindly splitting text by character count.

Chunk metadata should include:

- Repository
- File path
- Programming language
- Symbol/function/class name
- Start line
- End line
- File type
- Content hash

The system should avoid unnecessary duplicate chunks.

---

## FR-05: Embedding Generation

The system should generate embeddings for indexed chunks.

Recommended initial approach:
- Hugging Face embedding model
- Configurable embedding model
- Batch embedding generation

The system should store embeddings with metadata in the vector database.

---

## FR-06: Vector Database

Use **Qdrant** initially.

The vector database should support:
- Vector similarity search
- Metadata filtering
- Repository-level isolation
- Chunk retrieval
- Collection management

Each indexed repository should be logically isolated.

---

## FR-07: Semantic Retrieval

Given a user query, the system should retrieve semantically relevant chunks.

Example:

User:
> How does authentication work?

The system should retrieve relevant authentication controllers, services, middleware, models, and documentation even when the exact word "authentication" is not present in every chunk.

---

## FR-08: Keyword Retrieval

The system should support keyword-based retrieval for exact identifiers.

Example:

```text
JWT_SECRET
generateToken
UserController
MongoDB
```

Recommended approach:
- BM25 or equivalent lexical retrieval.

---

## FR-09: Hybrid Retrieval

Combine semantic and keyword retrieval.

Example:

```text
Vector Search
      +
BM25 Search
      ↓
Candidate Chunks
```

The system should support configurable weighting between retrieval methods.

---

## FR-10: Reranking

Retrieved candidates should optionally pass through a reranking model.

Example:

```text
Top 20 candidates
       ↓
Reranker
       ↓
Top 5–8 relevant chunks
```

The reranking stage should improve context relevance before sending information to the LLM.

---

## FR-11: Answer Generation

The LLM should generate answers using only retrieved repository context where possible.

The system prompt should instruct the model to:
- Prefer repository evidence.
- Avoid unsupported claims.
- Clearly state when evidence is insufficient.
- Cite relevant files.
- Distinguish documented facts from inference.

---

## FR-12: Source Citations

Every repository-specific answer should provide relevant source references.

Example:

```text
Sources:
- src/auth/authController.js
- src/middleware/auth.js
- src/services/authService.js
```

Where line information is available:

```text
src/auth/authController.js:25–67
```

Clicking a source should open the corresponding file view where supported.

---

## FR-13: Conversation History

The user should be able to ask follow-up questions.

Example:

User:
> Explain authentication.

Assistant:
> ...

User:
> Where is the JWT generated?

The system should preserve the relevant conversation context while still retrieving repository evidence for the new question.

---

## FR-14: Repository Overview

After indexing, the system should provide:

- Project purpose
- Detected languages
- Frameworks
- Dependencies
- Major directories
- Entry points
- API structure where detectable
- Database technologies where detectable

---

## FR-15: Architecture Explanation

The system should analyze repository structure and produce an architecture summary.

Example:

```text
Frontend
   ↓
REST API
   ↓
Service Layer
   ↓
Database
```

Where enough evidence exists, the application may generate a Mermaid architecture diagram.

---

## FR-16: Code Explanation

Users should be able to select or reference a function/class and request:

- Explanation
- Inputs/outputs
- Dependencies
- Control flow
- Related files

---

## FR-17: Repository Search

Provide a search interface allowing users to search:
- Files
- Functions
- Classes
- Documentation
- Identifiers

Results should display file paths and relevant snippets.

---

## FR-18: Error Handling

The system should handle:
- Invalid GitHub URLs
- Repository not found
- Repository access restrictions
- Unsupported file types
- Empty repositories
- Embedding failures
- Vector database failures
- LLM/API failures
- Rate limits

Errors should be displayed using actionable messages.

---

# 7. UI Requirements

## Main Dashboard

Components:

```text
------------------------------------------------
RepoMind
GitHub Repository URL
[____________________________] [Analyze]
------------------------------------------------

Repository
Status: Indexed

Languages
Python | JavaScript | TypeScript

Files
342

Chunks
4,821

------------------------------------------------
Ask about this repository
[________________________________________]
[Ask]
------------------------------------------------
```

---

## Chat Interface

Each answer should contain:

1. Answer
2. Relevant code snippets where useful
3. Source citations
4. Confidence/evidence indication where appropriate

---

## Repository Explorer

Sidebar:

```text
Repository
├── src
│   ├── auth
│   ├── users
│   └── database
├── tests
├── README.md
└── package.json
```

---

# 8. Technical Architecture

## Frontend

- React
- Tailwind CSS
- React Router
- Axios/fetch
- Markdown renderer
- Syntax highlighting

## Backend

- Python
- FastAPI
- Pydantic
- GitPython

## RAG

- LangChain
- Hugging Face embeddings
- Qdrant
- BM25
- Reranker
- OpenAI API

## Database

- PostgreSQL for application metadata
- Qdrant for vector data

## Infrastructure

- Docker
- Docker Compose
- Vercel for frontend
- Render/Railway/AWS for backend
- Qdrant Cloud for production vector storage

---

# 9. API Requirements

## POST /api/repositories

Register and start indexing a repository.

Request:

```json
{
  "github_url": "https://github.com/user/repository"
}
```

Response:

```json
{
  "repository_id": "repo_123",
  "status": "processing"
}
```

---

## GET /api/repositories/{id}

Return repository status and metadata.

---

## POST /api/repositories/{id}/chat

Request:

```json
{
  "question": "How does authentication work?",
  "conversation_id": "conv_123"
}
```

Response:

```json
{
  "answer": "Authentication is handled through...",
  "sources": [
    {
      "file": "src/auth/authController.js",
      "start_line": 25,
      "end_line": 67
    }
  ]
}
```

---

## GET /api/repositories/{id}/files

Return indexed repository files.

---

## GET /api/repositories/{id}/overview

Return generated repository overview.

---

# 10. Data Model

## Repository

```text
id
github_url
owner
name
branch
commit_hash
status
created_at
updated_at
```

## File

```text
id
repository_id
path
language
size
content_hash
```

## Chunk

```text
id
repository_id
file_id
content
symbol
start_line
end_line
embedding_id
```

## Conversation

```text
id
repository_id
created_at
```

## Message

```text
id
conversation_id
role
content
created_at
```

---

# 11. Security Requirements

1. Never index `.env` or secret files.
2. Do not expose API keys to the frontend.
3. Store secrets in environment variables.
4. Validate GitHub URLs.
5. Apply request rate limits.
6. Limit repository size and file count for MVP.
7. Sanitize rendered Markdown/code.
8. Do not execute arbitrary repository code.
9. Isolate repository data between users.
10. Use authentication before production deployment.

---

# 12. Performance Requirements

Target MVP:

- Repository validation: < 3 seconds excluding GitHub/network latency.
- Chat response: target < 10 seconds depending on LLM/provider.
- Retrieval: target < 2 seconds.
- Streaming responses should be supported.
- Indexing should run asynchronously for larger repositories.

The system should show ingestion progress:

```text
Cloning repository       ✓
Scanning files           ✓
Parsing code             ✓
Generating embeddings    ███████░░░ 70%
Indexing vectors         ...
```

---

# 13. RAG Evaluation

Create a benchmark dataset containing repository questions and expected supporting files.

Metrics:

### Retrieval
- Recall@K
- Precision@K
- MRR

### Generation
- Faithfulness
- Context relevance
- Answer relevance

Example evaluation:

```text
Evaluation Results

Recall@5:        X%
MRR:             X
Faithfulness:    X%
Answer Relevance X%
```

Only publish measured results.

---

# 14. MVP Scope

### Must Have

- GitHub URL input
- Repository ingestion
- File filtering
- Code-aware chunking
- Embeddings
- Qdrant
- Semantic retrieval
- LLM answer generation
- Source citations
- React interface
- FastAPI backend

### Should Have

- Hybrid BM25 + vector retrieval
- Reranking
- Conversation history
- Repository overview
- Repository search

### Could Have

- Architecture diagram
- Dependency graph
- Code explanation mode
- RAG evaluation dashboard
- GitHub OAuth
- Private repository support

### Won't Have Initially

- Automatic code modification
- Code execution
- IDE extension
- Automated pull requests
- Full static analysis

---

# 15. Development Milestones

## Milestone 1 — Backend Foundation
- FastAPI setup
- Repository URL validation
- GitHub repository cloning
- File filtering

## Milestone 2 — RAG Pipeline
- Parsing
- Chunking
- Embeddings
- Qdrant
- Basic retrieval
- LLM generation

## Milestone 3 — Web Application
- React UI
- Repository submission
- Chat interface
- Source display

## Milestone 4 — Advanced Retrieval
- BM25
- Hybrid retrieval
- Reranking
- Query rewriting

## Milestone 5 — Intelligence Features
- Repository overview
- Architecture analysis
- Code explanation
- Dependency analysis

## Milestone 6 — Evaluation
- Benchmark dataset
- Retrieval metrics
- Generation metrics
- Evaluation dashboard

## Milestone 7 — Production
- Authentication
- Rate limiting
- Docker
- Deployment
- Monitoring

---

# 16. Success Criteria

The MVP is successful when a user can:

1. Enter a valid public GitHub repository.
2. Successfully index the repository.
3. Ask natural-language questions.
4. Receive answers grounded in repository content.
5. View relevant source files.
6. Ask follow-up questions.
7. Receive useful answers without fabricated repository details.

---

# 17. Future Enhancements

- GitHub OAuth and private repositories
- GitHub Issues integration
- Pull Request analysis
- Commit history analysis
- Code change explanations
- Automated documentation generation
- IDE extension
- Repository comparison
- Multi-repository knowledge base
- Team workspaces
- Agentic code investigation
- Automated test-generation suggestions

---

# 18. Resume Positioning

**RepoMind — GitHub Repository Intelligence RAG**

Built an AI-powered GitHub repository analysis platform using **React, FastAPI, LangChain, Qdrant, and LLMs**, implementing code-aware chunking, hybrid retrieval, reranking, and source-level citations for repository-specific technical queries.

Add quantitative metrics only after measuring the deployed system.

---

# 19. Project Principle

RepoMind should not behave like a generic chatbot.

Its core principle is:

> **Retrieve first. Reason over evidence. Cite the source. Admit uncertainty.**

This principle should guide the RAG pipeline, prompt design, evaluation strategy, and user experience.
