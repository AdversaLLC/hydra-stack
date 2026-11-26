# Cheatsheet — Spring for GraphQL 2.0.6

[S] = in the v2.0.6 source; [U] = Boot, spec or unverified. Course-era differences are in brackets.

| Need | Use | Ev. |
|---|---|---|
| Root field | `@QueryMapping` / `@MutationMapping` / `@SubscriptionMapping` (= `@SchemaMapping(typeName="Query"…)`) | S |
| Nested field | `@SchemaMapping(typeName="T")`; parent = the unannotated non-simple parameter, **any position** | S |
| Argument | `@Argument` on every argument; needs `-parameters` or an explicit name. All arguments at once: `@Arguments` | S |
| Omitted vs null | `ArgumentValue<T>` (1.1; `isEmpty`/`ifPresent` 1.4) | S |
| Binder options (names, field access) | `GraphQlArgumentBinder.Options` via `configureBinder` (2.0) | S |
| N+1 | `@BatchMapping`, Map form; four return shapes; `maxBatchSize`; no `@Argument` | S |
| Batched field **with** arguments | `@SchemaMapping` + `DataLoader` param + composite key (P2) | S API / U run |
| Unmapped field check | `SchemaMappingInspector` report at startup (1.2) [course: silent null] | S |
| Which sub-fields were asked | `DataFetchingFieldSelectionSet.contains("a/b")`, `*` one level, `**` any depth; relative to the current field | S param / U glob |
| Slow parent stream | Root fetcher + selection set + `flatMapSequential`; delete the child mappings | S cause |
| Scalars | dependency (GJ-25 line) + `scalar X` in SDL + `RuntimeWiringConfigurer.scalar(...)`; `Date`=`LocalDate`, `DateTime`=`OffsetDateTime` | S wiring / U lib |
| Interface/union type | Default `ClassNameTypeResolver` on all abstract types; `setClassNameExtractor`, `addMapping`, `defaultTypeResolver` | S |
| Document cache | graphql-java `PreparsedDocumentProvider` via `configureGraphQl`; bounded; variables | S hook / U impl |
| Expected outcome | Non-null union result + `__typename` + a fragment per member | S/U |
| Unexpected exception → error | `@GraphQlExceptionHandler` (controller, then `@ControllerAdvice`) → Adapter → raw resolver | S |
| Default unhandled error | `INTERNAL_ERROR for <executionId>`, message hidden, logged | S |
| Error categories | Spring `ErrorType`: BAD_REQUEST, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INTERNAL_ERROR | S |
| Bean Validation | `@Validated`/`@Valid`/constraints → `ConstraintViolationException`; **map it yourself** (P5) | S |
| Headers → handler | `WebGraphQlInterceptor` → `graphQLContext` → `@ContextValue` | S |
| Reject request | `WebFilter`/Security scoped to `/graphql` [U WebFlux] | U |
| Live events | Multicast sink → `asFlux().cache(0)` → `@SubscriptionMapping`; SDL `f: Event` not `[Event]`; handle `EmitResult` | S Spring / U Reactor |
| Subscription transport | WebSocket = graphql-transport-ws (legacy Apollo `graphql-ws` closed); SSE (1.3); keep-alive (1.3); `connection_init` auth (1.3) | S |
| HTTP verbs | **POST only in 2.0.6**; GET/QUERY on main (2.1) | S |
| HTTP status | Field errors 200; invalid document 4xx only with `application/graphql-response+json` (1.4) | S |
| Reactive client | `HttpGraphQlClient` (WebClient); `retrieve(path)` vs `execute()` (table in ch08) | S |
| Blocking client | `HttpSyncGraphQlClient` (RestClient, 1.3); `retrieveSync`/`executeSync`; `configureMessageConverters` | S |
| Field result | `getValue()`, `getErrors()` [course `hasValue()`/`getError()` removed] | S |
| Client documents | `graphql-documents/*.graphql\|.gql`; tester: `graphql-test/` | S |
| Subscription client | `WebSocketGraphQlClient.builder("ws://…", client)`, `retrieveSubscription`, `keepAlive` (1.3) | S |
| Per-request client headers | `GraphQlClientInterceptor` (or `mutate()` off the hot path) | S |
| Engine-only test | `ExecutionGraphQlServiceTester` (`@GraphQlTest` [U Boot]) | S |
| HTTP stack test | `@SpringBootTest @AutoConfigureHttpGraphQlTester` + `HttpGraphQlTester` (no subscriptions) | S/U |
| Socket test | `WebSocketGraphQlTester` on `RANDOM_PORT`; `stop()` after | S |
| Expected errors in tests | `errors().expect(pred).verify()` before `path()`; `satisfy` is weakest | S |
| Null vs absent | `valueIsNull()` vs `pathDoesNotExist()` | S |
| Pagination | `ScrollSubrange` + `ConnectionTypeDefinitionConfigurer` (1.2) | S |
| Federation | `data/federation` (1.3+) | S |

| Query feature | Syntax | Spring touchpoint |
|---|---|---|
| Alias | `a: customerById(id: 1) { name }` | error `path` uses the alias [S] |
| Fragment | `fragment C on Customer { id }` → `...C`; inline `... on Book { author }` | tester `fragment()` 1.3 [S] |
| Operation name | `query ById { … }` + `operationName` | trace tag only (high-cardinality) [S] |
| Variables | `query Q($id: ID! = 1, $f: AgeRangeFilter!)` | `ArgumentValue` for omitted [S] |
| Directives | `@include(if: $x)`, `@skip(if: $x)`; schema `@deprecated(reason:)` | no Spring code [S] |

| GraphQL vs REST | |
|---|---|
| Endpoint | One (`POST /graphql` in 2.0.6) vs many |
| Shape | Client picks fields vs server-fixed |
| Nested data | One round trip, fields resolved lazily; children wait for the whole parent list [S] |
| Status codes | `errors[]`, partial success; 4xx only for request-level failures (1.4, graphql-response media type) |
| Caching | Document cache (graphql-java), not HTTP GET caching (GET arrives in 2.1) |
