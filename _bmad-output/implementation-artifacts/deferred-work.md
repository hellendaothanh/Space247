- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-project-identity-space247.md`
  summary: Introduce Alembic migration framework for database schema and pgvector lifecycle management.
  evidence: Production schemas require reproducible migrations rather than application startup Base.metadata.create_all.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-project-identity-space247.md`
  summary: Add HNSW index definition to Property.embedding in SQLAlchemy model.
  evidence: docs/architecture/02-data-model-and-vector-search.md specifies HNSW cosine index for production scale.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-project-identity-space247.md`
  summary: Implement Hybrid Search with Full-Text Search and Reciprocal Rank Fusion.
  evidence: Documented in architectural design for advanced Vietnamese property discovery.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-project-identity-space247.md`
  summary: Expand frontend shared API client methods for natural language search and full property filtering.
  evidence: Properties endpoint supports natural language search and range filters that can be surfaced to client apps.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-core-vector-search-api.md`
  summary: Use dedicated COUNT query for total matching records in search endpoints instead of in-memory list length when paginating.
  evidence: When limit or threshold is applied, total count should reflect total eligible matches in database.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-core-vector-search-api.md`
  summary: Sanitize and escape LIKE/ILIKE wildcards (%, _) in address, city, and district filter queries.
  evidence: User input containing % or _ can alter search match semantics in SQLAlchemy ilike expressions.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-core-vector-search-api.md`
  summary: Defer loading large embedding vector column on property listing endpoints (GET /properties).
  evidence: Fetching 768-float vectors for list views increases memory usage and payload size unnecessarily.
