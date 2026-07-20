# Address Enrichment Pipeline

This repository is for a 4-step address enrichment pipeline.

The goal is to take a raw address string, progressively enrich it, and return the best structured result available:

1. Libpostal parse for fast local extraction.
2. LLM extraction to fill gaps in the structured result.
3. LLM web search to resolve any remaining missing fields.
4. Geocoding plus nearby-business lookup, with fallback behavior and regex backfill for incomplete addresses.

## Users

The primary users of this tool are:

- Data/ops users who need messy address strings normalized into structured records.
- Engineers who need a deterministic pipeline they can embed in larger workflows.
- Administrators who need to configure credentials, proxy settings, retries, and fallback behavior.

## Week 1 Goal

Week 1 is about defining the problem clearly before building anything:

- lock the input/output contract
- define what counts as a complete address
- document the step-by-step escalation rules
- document fallbacks, retries, confidence scoring, and cost estimation
- sketch the three main screens or views on paper before implementation

## User Stories

1. As a data/ops user, I want to paste a raw address string and get back structured fields like street, city, state, zip, and country.
2. As a data/ops user, I want the pipeline to stop early when libpostal already found all required fields, so I do not pay for unnecessary LLM calls.
3. As a data/ops user, I want missing fields to be filled by an LLM using the raw input plus the libpostal parse, so partial addresses can still become usable records.
4. As a data/ops user, I want the pipeline to escalate to search-enabled LLMs only when the earlier steps are still incomplete, so the system uses the cheapest reliable path first.
5. As a data/ops user, I want the geocoding step to return latitude, longitude, and nearby businesses, so I can validate and enrich the address context.
6. As a data/ops user, I want the system to backfill missing city, state, or zip data from the first nearby business address when possible, so downstream records are still as complete as possible.
7. As an engineer, I want retry logic and confidence scoring built into the plan, so transient failures and low-quality parses are handled consistently.
8. As an administrator, I want proxy and CA bundle handling documented, so the pipeline can run reliably in enterprise or AKS environments.

## Out of Scope

The following are intentionally out of scope for the whole project unless the scope is later expanded explicitly:

- adding authentication, user management, or role-based access control
- storing customer data beyond the pipeline inputs and outputs needed for testing
- optimizing model prompts beyond the initial extraction and search prompts
- production deployment, cloud infrastructure, or release automation
- large-scale batch processing, queue orchestration, or distributed workers
- advanced analytics, reporting dashboards, or observability platforms
- real customer address data before the pipeline is validated and secured

## Paper Sketches

1. Raw address input and pipeline output view.
2. Step-by-step enrichment trace showing libpostal, LLM extraction, search, and geocoding.
3. Settings and diagnostics view for retries, proxy settings, confidence score, and cost estimates.

## Data Model

The pipeline stores each processing stage explicitly so you can inspect what happened at every step.

### Entity relationship view

```mermaid
erDiagram
		USER ||--o{ RAW_INPUT : submits
		RAW_INPUT ||--o{ PARSE_RESULT : has
		PARSE_RESULT ||--o{ ENRICHMENT_RESULT : has
		ENRICHMENT_RESULT ||--o{ GEOCODE_RESULT : has

		USER {
			uuid id PK
			string email
			string role
			string password_hash
			datetime created_at
		}

		RAW_INPUT {
			uuid id PK
			uuid user_id FK
			string raw_address
			string input_source
			string country_hint
			datetime created_at
		}

		PARSE_RESULT {
			uuid id PK
			uuid raw_input_id FK
			string parser_name
			json parsed_components
			boolean is_complete
			float confidence_score
			datetime created_at
		}

		ENRICHMENT_RESULT {
			uuid id PK
			uuid parse_result_id FK
			json merged_address
			string enrichment_source
			boolean needs_search_fallback
			float confidence_score
			int prompt_tokens
			int completion_tokens
			datetime created_at
		}

		GEOCODE_RESULT {
			uuid id PK
			uuid enrichment_result_id FK
			decimal latitude
			decimal longitude
			json nearby_businesses
			string geocode_source
			boolean backfilled_from_business
			json final_address
			datetime created_at
		}
```

### Table responsibilities

- `user`: identity and access context for who ran a pipeline request.
- `raw_input`: the original address string and submission metadata.
- `parse_result`: libpostal output and completion status.
- `enrichment_result`: LLM-filled fields, source path, confidence, and token usage.
- `geocode_result`: coordinates, nearby businesses, fallback source, and final backfilled address.

### Relationship rules

- One `user` can submit many `raw_input` records.
- One `raw_input` can have many `parse_result` records (useful for retries or parser versioning).
- One `parse_result` can have many `enrichment_result` records (prompt iterations or fallback runs).
- One `enrichment_result` can have many `geocode_result` records (primary/fallback attempts).

### Why this structure

- Keeps each pipeline stage auditable and debuggable.
- Preserves provenance of where each field came from.
- Supports retries and side-by-side model or API comparisons.
- Makes confidence and cost analysis first-class from day one.

## Notes for Week 1

The first week should produce a clear spec, not code. If the pipeline contract is ambiguous, resolve the ambiguity here before implementation starts.
