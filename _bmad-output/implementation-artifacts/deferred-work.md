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

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-hybrid-search-hnsw.md`
  summary: Add ward and num_bathrooms filters to PropertySearchQuery and SemanticSearchQuery schemas.
  evidence: Property model stores ward and num_bathrooms but search schemas and filter builders currently omit them.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-hybrid-search-hnsw.md`
  summary: Migrate tsquery parsing from manual regex splitting to PostgreSQL websearch_to_tsquery or plainto_tsquery.
  evidence: PostgreSQL native websearch_to_tsquery safely parses user boolean queries, quotes, and punctuation without custom regex.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-alembic-migrations.md`
  summary: Add domain-level database check constraints (positive price/area, coordinate bounds).
  evidence: Reviewer identified absence of check constraints allowing potentially invalid raw values to bypass ORM.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-alembic-migrations.md`
  summary: Add composite index for geospatial coordinates (latitude, longitude).
  evidence: Map-based bounding-box queries benefit from composite B-tree or GiST spatial indexing.

- source_spec: `C:\Devsecops\Space247/_bmad-output/implementation-artifacts/spec-space247-seed-properties.md`
  summary: Implement batched title lookups and batched embedding generation for bulk property seed/import jobs.
  evidence: Reviewer noted sequential queries and embedding inference create unnecessary round trips for large datasets.
