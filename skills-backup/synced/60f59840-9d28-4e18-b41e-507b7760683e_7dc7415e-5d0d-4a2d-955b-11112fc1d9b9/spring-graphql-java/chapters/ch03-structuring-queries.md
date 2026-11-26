# Ch 3 — Structuring GraphQL Queries (10 lessons)

Labels as in ch02. Era: Boot 2.7.2 / SfG 1.0 (lesson 9 banner). This module is GraphQL *language*. The server code is unchanged from ch02, so most claims are spec-level [U]. The value is in knowing where each feature lands in Spring.

## What the course teaches
- **Clients.** Altair and Postman, besides GraphiQL. Point them at `/graphql` (the API), not `/graphiql` (HTML). They load the schema by introspection.
- **Alias.** `newKey: field` renames the response key, at any depth (`balance: amount`). Main use: the same field with different arguments in one request (`a: customerById(id: 1)`, `b: customerById(id: 2)`), and the kids/adults/seniors bucket pattern.
- **Named fragments.** `fragment C on Customer { id name }` used with `...C`. Edit once, change everywhere. Inline fragments come in ch04.
- **Operation name.** `query CustomersByAge { … }`. It labels requests for monitoring and logs. Several operations can share one document; the JSON body carries `operationName` to pick one.
- **Variables.** `query Q($id: ID! = 1)` with values sent as JSON. Declared types must fit the argument's nullability. Defaults apply when the client sends nothing. A variable can carry a whole `input` object.
- **`@include` / `@skip`.** Conditional sections driven by `Boolean!` flags. An empty filter still runs the resolver; a skipped field does not.
- **`@deprecated(reason: …)`.** Belongs in the schema. GraphiQL hides the field in docs and highlights it in queries, but the query still runs. Lifecycle: deprecate, migrate, remove.

## Current in 2.0.6 (where each feature lands)

| Feature | Spring touchpoint | Evidence |
|---|---|---|
| Alias | Error `path` uses the aliased name. Handlers still bind to the schema field name. | [S `ResponseError.java:72-73`] |
| Alias cost | Each alias is a separate field resolution. Spring has no alias or complexity limit; hooks are `GraphQlSource.Builder.instrumentation(...)` / `configureGraphQl(...)` | [U] resolution; hooks [S `execution/GraphQlSource.java:140-150`] |
| Fragment | Whole document passed to graphql-java; handlers see a merged `DataFetchingFieldSelectionSet` | [S `GraphQlRequest.java`]; merge [U] |
| Fragment in tests | `GraphQlTester.RequestSpec.fragment(String)` / `fragmentName(String)` since 1.3.0; `GraphQlClient` has no `fragment()` | [S `spring-graphql-test/…/tester/GraphQlTester.java:150-167`; `client/GraphQlClient.java`] |
| Operation name | `GraphQlRequest.getOperationName()`. Observation key `graphql.operation.name` is **high-cardinality** (traces only). Metrics carry only `graphql.outcome` and `graphql.operation.type`. Unnamed operations are tagged `"query"`. | [S `observation/GraphQlObservationDocumentation.java:115-160`, `DefaultExecutionRequestObservationConvention.java:48,60-113`] |
| Variables | `GraphQlRequest.getVariables()`; client `variable()`/`variables(Map)`. Omitted vs null is visible only via `ArgumentValue<T>.isOmitted()` (1.1.0) | [S `data/ArgumentValue.java:48,90`] |
| `@include`/`@skip` | No Spring code at all; graphql-java evaluates them before fetching | [S: grep over the 2.0.6 tree finds nothing]; ordering [U] |
| `@deprecated` | No special casing in `execution/`. The inspector still expects both old and new fields to be mapped. | [S grep]; inspector inference [U] |
| Transport | POST only. Request bodies `application/json` or `application/graphql`; Accept `application/json` or `application/graphql-response+json` | [S `server/webflux/GraphQlRequestPredicates.java:60-104`] |
| Documents in files | Client: `classpath:graphql-documents/`. Tester: `graphql-test/`. Extensions `.graphql`, `.gql` | [S `client/AbstractGraphQlClientBuilder.java:94`; `spring-graphql-test/…/tester/AbstractGraphQlTesterBuilder.java:86`; `support/ResourceDocumentSource.java:49`] |

## Decision rules
- Keep the document static: name the operation, pass every changing value as a variable, share selections as fragments, and switch sections with `@include`/`@skip`. That stability is what makes files, logs, traces and document caching work.
- Use an alias when client naming differs, or to call one field with several argument sets. If clients do this at scale, add a bulk field or batch on the server.
- Name every operation a real client sends. Keep names stable and unique per use case.
- Type variables with the schema's `input` type, never an output `type`.
- Deprecation checklist: reason names the successor → successor ships **with a handler** → inspector clean → watch traffic by operation name → remove.
- Never build documents by concatenating user input. That is the skill's own rule; the course argues for variables on other grounds.

## Traps
- Code that reads the response (or an error path) must use the alias, not the field name.
- Aliases multiply server work. Three aliases mean three handler calls [U].
- Several operations without `operationName` → no operation to run [U].
- Expecting a handler to distinguish omitted from null without `ArgumentValue`.
- An empty filter is not a skip. The resolver and upstream still run.
- The demo adds a successor field with no handler. It returns null silently, or an error if the field is non-null.
- Expecting operation names on metrics dashboards out of the box. You need a custom `ExecutionRequestObservationConvention`; cap the names, or cardinality explodes.
- Introspection-based tooling fails if introspection is turned off in production [U: Boot property].

## 2.0 delta

| Since | Change |
|---|---|
| 1.1 | `ArgumentValue` (omitted vs null) [S]; `isEmpty`/`ifPresent` since 1.4.0 [S `data/ArgumentValue.java:79,111`] |
| 1.3 | Tester `fragment()`/`fragmentName()` and `variables(Map)` [S] |
| 1.3 | `DgsGraphQlClient` (2.0 adds several queries in one request and `queryAlias`) [S `client/DgsGraphQlClient.java:122-127`; wiki-2.0] |
| 2.0 | Binder options for input field names [S wiki-2.0] |
| 2.0.6 vs 2.1 | 2.0.6 is POST only; GET/QUERY are on main (2.1), so HTTP caching of GraphQL GETs is not current yet [S] |
