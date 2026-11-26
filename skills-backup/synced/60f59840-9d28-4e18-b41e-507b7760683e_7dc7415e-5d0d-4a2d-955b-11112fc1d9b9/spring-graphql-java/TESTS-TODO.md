# TESTS-TODO — runnable suites proposed by the notes (not written yet)

A Claude Code session can implement these later. Each suite turns [U] claims in this skill into checked facts. **Until a suite passes, the claims it covers stay [U].**

Shared ground rules:
- Target Spring for GraphQL **2.0.6** with the matching Spring Boot 4 line. Starter and test-module names under Boot 4 are [U]: compile offline first and fix coordinates before writing assertions.
- Local only, with no course jar: stub upstreams (WireMock files or tiny REST controllers) live in the test tree.
- Make every new assertion fail once before trusting it (the course habit).
- No hard-coded generated ids. Reset data per test, or assert relative to what the test created.
- Subscriptions: subscribe first, trigger in `StepVerifier.then(...)`, `take(n)`, `verify(Duration.ofSeconds(5))`, `stop()` the WebSocket tester.

Proposed layout:
```
spring-graphql-java-tests/
  pom.xml
  src/main/java/…/app/         # customer CRUD + events + movie BFF sample (schema with Float!/Genre! fixes)
  src/main/resources/graphql/  # schemas
  src/test/java/…/             # suites T1–T11
  src/test/resources/graphql-test/
  upstream-stub/               # WireMock mappings for customer/movie/review
```

## T1 — BatchMapping contract (ch02, P1) — from m01-02 proposal 1
- [ ] Map form: missing key → what does the client see for `[T]!` vs `[T]`? (pins java-dataloader 5 behaviour)
- [ ] Flux form with `Mono.justOrEmpty` per key → DataLoader size assertion → `INTERNAL_ERROR` (record the 2.0.6 message text)
- [ ] Flux form with `flatMap` + random delay → misassignment detected; `flatMapSequential` → correct (repeat 20 runs)
- [ ] `@Argument` on a `@BatchMapping` method → startup/first-call failure "Unexpected argument type"
- [ ] `maxBatchSize = 2` with 5 parents → 3 loader calls (counter)
- [ ] Composite-key `DataLoader` with `limit` argument (P2) returns per-limit results

## T2 — Parameter binding (ch02, P2) — m01-02 proposal 2
- [ ] Unannotated `Integer limit` → "no source/parent either"
- [ ] Unannotated `String name` → treated as source → failure
- [ ] Compile without `-parameters`, `@Argument` without a name → "parameter name information not found"
- [ ] Parent parameter in second position still binds

## T3 — Schema inspection gate (ch02, ch03) — m01-02 proposal 3, m03 proposal 4
- [ ] Boot the app with one unmapped schema field; read the inspection report (log or `SchemaMappingInspector.inspect`) and fail the build
- [ ] Deprecated field + successor without a handler → successor reported unmapped; deprecated field still required
- [ ] `Flux<Object>` union handler → "No class information" vs naming-convention discovery

## T4 — Query features (ch03) — m03 proposal 2
- [ ] Two aliased `customerById` → two keys, two handler calls (counter)
- [ ] `@skip(if: true)` section → zero handler calls; skipped `@BatchMapping` field adds no keys
- [ ] Default-valued variable used when omitted
- [ ] `operationName` picks one of two operations; missing `operationName` → error text recorded
- [ ] Tester `.fragment(...)` appends a shared fragment
- [ ] Error `path` uses the alias
- [ ] Custom `ExecutionRequestObservationConvention` puts an allow-listed operation name on metrics (m03 proposal 3)

## T5 — Subscription event bus (ch06, P6) — m05-06 proposal 1, m09 proposal 3
- [ ] Late subscriber receives no history
- [ ] All subscribers cancel → a new subscriber still receives later events (with vs without `cache(0)`)
- [ ] Events emitted before the first subscriber: delivered or dropped? Then repeat in the same context after one subscriber has come and gone (the course's trigger-first order)
- [ ] 8 threads × 1000 concurrent `publish` → no lost events with the failure handler; count losses with bare `tryEmitNext`
- [ ] Event carrying errors fails `toFlux` stream (tester semantics)

## T6 — CRUD semantics (ch05, P3) — m05-06 proposals 2 and 4
- [ ] Two mutations in one operation (create then update same id) run in order
- [ ] Missing id on `customerById` / `updateCustomer` → null, no error
- [ ] Delete of a missing id → document the answer (SUCCESS?) and whether a DELETED event is emitted
- [ ] Full-replace update nulls the omitted fields (course behaviour); `ArgumentValue` patch leaves them untouched and explicit null clears
- [ ] Second mutation field throws → first remains committed

## T7 — Errors, validation, interceptors, security (ch07, P4, P5, P13) — m07 proposals 2–4
- [ ] Partial data + error; aliased failures give two errors with distinct paths
- [ ] Default error: `INTERNAL_ERROR for <id>`, message hidden
- [ ] `@GraphQlExceptionHandler` in advice handles a `Mono.error` from a controller (reactive path) and a synchronous throw
- [ ] Controller-local handler wins over advice
- [ ] `AccessDeniedException` → FORBIDDEN with no catch-all; with a `Throwable` catch-all → record what happens (shadowing)
- [ ] `@Min(18)` violation → one BAD_REQUEST per violation with `property` extension; without the handler → INTERNAL_ERROR
- [ ] Missing `caller-id` → 400 from the filter; GraphiQL still reachable when the filter is path-scoped
- [ ] Header value reaches `@ContextValue`; missing required value → error
- [ ] Union not-found returns `__typename == "CustomerNotFound"`, no errors
- [ ] Invalid document with `Accept: application/graphql-response+json` → 4xx; with `application/json` → 200 + errors

## T8 — Client failure modes (ch08, P7) — m08 proposals 1, 2, 4
- [ ] Table rows: success / partial / null+error / null-no-error / wrong path, for `retrieve`, `retrieveSync`, `execute().field().toEntity`, `toEntityList`
- [ ] One test per operation of the typed `call(op, vars, type)` helper (wrong alias must fail the test, not silently pass)
- [ ] Union decoding with and without member fragment
- [ ] Input DTO with an extra `id` field → server rejection text; `ArgumentValue` client input omits vs sends null (check `GraphQlJacksonModule` registration)
- [ ] `WebSocketGraphQlClient` stream ends with `SubscriptionErrorException` on server error
- [ ] `GraphQlClientInterceptor` adds a per-request header

## T9 — BFF downstream errors and batching (ch10, P8, P9) — m10-11 proposals 1–3
- [ ] Stub 404 → NOT_FOUND (or null where nullable by design); 400 → BAD_REQUEST; 500 and timeout → INTERNAL_ERROR with hidden message
- [ ] Watch-list mutation: domain failure → FAILURE status; unexpected failure → error entry (no bare `onErrorReturn`)
- [ ] `a: userProfile(id:1) b: userProfile(id:2) { watchList {id} }` → exactly one movie-service call (bulk) / bounded calls (per-id loader)
- [ ] `moviesByGenre` with `Genre!` rejects null before any upstream call
- [ ] WebClient vs RestClient-on-virtual-threads variants both pass

## T10 — Advanced execution (ch04, P11, P12) — m04 proposals 1–4
- [ ] 1 s-per-element services: default resolution ≈ 6 s vs root fetcher ≈ 4 s (use virtual time or generous bounds); order deterministic with `flatMapSequential`
- [ ] Selection-set globs: `level2/level3`, `*`, `**` truth table (does `**` match zero levels?)
- [ ] `Dto` suffix + `setClassNameExtractor` via `defaultTypeResolver` resolves every abstract type
- [ ] Declared but unregistered scalar → startup failure; extended-scalars version for graphql-java 25 compiles
- [ ] Bounded document cache: two variable values → one parse; inlined values → N parses; verify the GJ 25 provider signature first
- [ ] Wiring + controller for the same field: which wins, and does the inspector flag it?

## T11 — Tester behaviour (ch09, P10) — m09 proposals 1, 2, 4
- [ ] `satisfy` with an empty consumer passes with errors present; `expect` fails with "No matching errors."
- [ ] `path()` without handling errors fails
- [ ] `valueIsNull` vs `pathDoesNotExist` on a failed nullable field
- [ ] `HttpGraphQlTester` subscription → `UnsupportedOperationException`
- [ ] In-process subscription via `ExecutionGraphQlServiceTester`
- [ ] `@GraphQlTest` slice: does it include `WebGraphQlInterceptor` beans? (Boot 4)
