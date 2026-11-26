---
name: spring-graphql-java
description: "Spring for GraphQL, GraphQL Java, Spring Boot GraphQL, @QueryMapping, @MutationMapping, @SubscriptionMapping, @SchemaMapping, @BatchMapping, N+1, DataLoader, @Argument, ArgumentValue, @GraphQlExceptionHandler, ErrorType, WebGraphQlInterceptor, HttpGraphQlClient, HttpSyncGraphQlClient, WebSocketGraphQlClient, GraphQlTester, HttpGraphQlTester. Writing, reviewing or debugging Java GraphQL servers, clients and tests on Spring for GraphQL 2.0.6 (WebFlux or MVC): schema-first controllers, batching, errors and validation, subscriptions, REST-aggregating BFFs. Built from all 171 lessons of the GraphQL Masterclass course, with course-era (1.0) differences flagged."
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T23:21:24.604Z"
  authored_by: "agent"
  authored_at: "2026-10-22T23:21:24.557Z"
  authoring_session: "df249c20-fa50-4f4d-9ba4-14b516173576"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T23:21:24.596Z"
---

# Spring for GraphQL (Java) — study skill v2

**Provenance.** Built 2026-10-22 from the transcripts and OCR of all 171 lessons of "GraphQL Masterclass with Spring Boot [Updated for 3.2.0]" (via the per-module study notes `notes/m01-02.md` … `m10-11.md`). Graded against the **spring-graphql v2.0.6** source (tag v2.0.6, main code), the project wiki release notes for 1.2–2.0, and `ground-truth-spring-graphql.md`. The previous skill was written from the syllabus only; every correction to it is listed in [CHANGES.md](CHANGES.md).

**Course era.** Despite the title, every console banner shows Spring Boot **2.7.2** and the jars are **spring-graphql 1.0.1** / graphql-java 18.2. Each chapter therefore states the course behaviour first, what is **current in 2.0.6** second, and closes with a "2.0 delta" table.

**Labels used everywhere.**
- **[S file]**: confirmed in the v2.0.6 source. Paths are relative to `spring-graphql/src/main/java/org/springframework/graphql/` (testers: `spring-graphql-test/…/test/tester/`). Notes m03–m10-11 checked against the v2.0.6 tag. Notes m01-02 checked against `main`; the claims used here were re-checked on v2.0.6 on 2026-10-22.
- **[U]**: course-only, spec-level, or Spring Boot / Reactor / graphql-java / Spring Data behaviour that was not checked. A claim is never upgraded from [U] without a source check.
- When notes disagree, the later note wins; the affected spots say so. Examples: m03 settles "POST only in 2.0.6", and m05-06 corrects the `ArgumentValue` `@since` dates.
- Nothing in this skill has been compiled or run. [TESTS-TODO.md](TESTS-TODO.md) lists the suites that would make it so.

## How to use this skill
1. **Writing code** → [patterns.md](patterns.md) (P0–P13, each tagged with evidence).
2. **Quick decision or API name** → [cheatsheet.md](cheatsheet.md).
3. **A concept by course section** → the chapter (table below), loaded on demand.
4. **A term** → [glossary.md](glossary.md).
5. **"Is the old advice still right?"** → [CHANGES.md](CHANGES.md) (103 deduplicated corrections).
6. **Before calling anything ready** → implement and pass the matching suite in [TESTS-TODO.md](TESTS-TODO.md). Follow the test result, not the [U] text.

## Core mental models (2.0.6 behaviour first)
1. **The schema is the contract; Java fills it.** Every field is a function with a property fallback. A registered handler for `Type.field` beats the parent's property, and a field the client does not select costs nothing. Unmapped fields are silent `null`s at runtime, so read the **SchemaMappingInspector** startup report (1.2+) [S `execution/SchemaMappingInspector.java`]. *Course era: no inspector; the course debugs by seeing null.*
2. **Parameter binding has three paths.** `@Argument` for arguments (needs `-parameters`). The unannotated non-simple parameter is the parent, at any position. Special types are resolved by type. An unannotated `Integer` fails; an unannotated `String` is taken as the parent [S `data/method/annotation/support/SourceMethodArgumentResolver.java:51-71`].
3. **Root fields overlap; children wait for the whole parent list.** A returned `Flux` is collected to a list before graphql-java sees it [S `execution/ContextDataFetcherDecorator.java:52`]. A slow parent stream → take over the subtree in a root fetcher. Many parents with per-parent I/O → batch. Never block the event loop; on Java 21+ blocking methods may run on virtual threads (1.3) [S wiki-1.3].
4. **`@BatchMapping` is a positional contract unless you use the Map form.** There are four return shapes. Size errors are loud, order errors are silent (`flatMap`). Every key needs an entry. Batch methods take no `@Argument` [S `…/support/BatchLoaderHandlerMethod.java:170`]; fields with arguments use a `DataLoader` parameter with a composite key.
5. **Three failure kinds, three tools.** Expected domain outcome → a non-null **union** result. Unexpected or field-level failure → `errors[]` with Spring's `ErrorType` via **`@GraphQlExceptionHandler`** (controller first, then `@ControllerAdvice`, including errors from returned `Mono`/`Flux`) [S `…/support/AnnotatedControllerConfigurer.java:542-545`]. Reject the whole request → a filter or Security. The default unhandled error already hides the message [S `execution/ExceptionResolversExceptionHandler.java`]. *Course era: a raw `DataFetcherExceptionResolver` that forwards every message.*
6. **Validation is half built in.** Jakarta constraints on controller arguments are enforced, but the resulting `ConstraintViolationException` is not mapped; add a handler [S `…/support/ValidationHelper.java`]. *The course only shows a manual Reactor check.*
7. **Subscriptions are an app-owned shared stream.** Spring wraps your publisher per subscriber and never shares it [S `execution/ReactiveAdapterRegistryHelper.java:89-104`]. Own one sink, emit after successful writes, handle `EmitResult`, and pin the sink's lifetime with a test. The transport is graphql-transport-ws (legacy Apollo protocol closed), SSE since 1.3, with `connection_init` auth and keep-alive since 1.3 [S `server/webflux/GraphQlWebSocketHandler.java:78,166`].
8. **The client is per field, and failures differ by API.** `retrieve(path)` throws on *any* error at or under the path and completes empty on a clean null. `execute().field(path)` decodes partial data. A wrong path is **silent**. `ResponseField` has only `getValue()`/`getErrors()` [S `ResponseField.java`]. *Course era: `hasValue()`/`getError()` and "wrong path throws".*
9. **Pick the tester by layer.** Engine (`ExecutionGraphQlServiceTester`), web (`WebGraphQlTester`), HTTP (`HttpGraphQlTester`, no subscriptions), socket (`WebSocketGraphQlTester`). `path()` fails on unexpected errors, so handle errors first with `expect`. `satisfy` accepts anything [S `DefaultGraphQlTester.java`].
10. **A BFF is schema per screen, client per upstream, handler per field.** Ids in, objects out. Decide the downstream-error policy and the batching strategy on purpose; the course leaves both to accident.
11. **The transport is POST only in 2.0.6.** GET/QUERY are on main (2.1) [S `server/webflux/GraphQlRequestPredicates.java:100`]. Request-level failures get 4xx only with `application/graphql-response+json` (1.4) [S wiki-1.4].

## Chapter index

| File | Course module | Core of the chapter |
|---|---|---|
| [chapters/ch02-getting-started.md](chapters/ch02-getting-started.md) | 1–2 (34 lessons) | types, `@QueryMapping`, binding paths, nested fields, N+1, `@BatchMapping` contract, overrides, inspector |
| [chapters/ch03-structuring-queries.md](chapters/ch03-structuring-queries.md) | 3 (10) | aliases, fragments, operation names, variables, directives, and where each lands in Spring |
| [chapters/ch04-advanced.md](chapters/ch04-advanced.md) | 4 (30 + resource) | selection set and globs, sequential-execution problem, wiring, scalars, interfaces/unions, type resolver, document cache |
| [chapters/ch05-mutation-crud.md](chapters/ch05-mutation-crud.md) | 5 (14) | mutations, input binding, full-replace trap, `ArgumentValue` patches, serial ≠ transactional |
| [chapters/ch06-subscription.md](chapters/ch06-subscription.md) | 6 (7) | sink-based events, the "hot" correction, graphql-transport-ws, SSE, auth, keep-alive |
| [chapters/ch07-errors-interceptors.md](chapters/ch07-errors-interceptors.md) | 7 (16) | error model, handler ladder, Bean Validation gap, unions, interceptor vs filter, security resolvers |
| [chapters/ch08-client.md](chapters/ch08-client.md) | 8 (26) | `HttpGraphQlClient`, documents, failure table, unions, CRUD helper, sync/DGS clients, WebSocket client |
| [chapters/ch09-integration-test.md](chapters/ch09-integration-test.md) | 9 (11) | tester choice, error assertions, null vs absent, subscription tests, isolation |
| [chapters/ch10-movie-app.md](chapters/ch10-movie-app.md) | 10 (22 + jar note) + Bonus (1) | REST-aggregating BFF, downstream errors, batching across services, schema hygiene, federation pointer |

## Topic index
- **N+1 / batching**: ch02, ch10 · P1, P2, P9 · T1, T9
- **Parameter binding**: ch02 · P2 · T2
- **Schema inspection**: ch02, ch03, ch04 · T3
- **Aliases, fragments, variables, directives**: ch03 · T4
- **Omitted vs null / partial update**: ch03, ch05, ch08 · P3 · T6
- **Selection set, globs, slow parents**: ch04 · T10
- **Scalars**: ch04 · T10
- **Interfaces, unions, type resolver**: ch04, ch07 · P11
- **Document cache / APQ**: ch04 · P12
- **Mutations, serial order**: ch05 · T6
- **Subscriptions, sinks, transport, auth**: ch06 · P6 · T5
- **Errors, `@GraphQlExceptionHandler`, `ErrorType`**: ch07 · P4 · T7
- **Validation**: ch07 · P5 · T7
- **Interceptors, context, filters, security**: ch07 · P13 · T7
- **Client APIs and failure modes**: ch08 · P7 · T8
- **Testers and error assertions**: ch09 · P10 · T11
- **BFF, downstream errors**: ch10 · P8 · T9
- **Versions 1.0 → 2.0.6 → 2.1**: every chapter's "2.0 delta" footer; CHANGES.md

## Supporting files
- [patterns.md](patterns.md): copy-ready, own-words snippets P0–P13 with evidence labels.
- [cheatsheet.md](cheatsheet.md): need → API tables, query features, GraphQL vs REST.
- [glossary.md](glossary.md): terms, each with its chapter.
- [CHANGES.md](CHANGES.md): 106 raw → 103 deduplicated corrections to the old skill.
- [TESTS-TODO.md](TESTS-TODO.md): suites T1–T11 for a Claude Code session to implement.

## Scope and limits
- Spring for GraphQL 2.0.6 on Spring Framework 7 / GraphQL Java 25 / Jackson 3, WebFlux-first as in the course, with MVC/virtual-thread notes.
- Spring Boot itself (starters, `spring.graphql.*` property names, `@GraphQlTest`, `@AutoConfigureHttpGraphQlTester`, resolver ordering) was **not** in the checked source: always [U].
- Reactor sink semantics, java-dataloader 5 missing-key behaviour and graphql-java 25 internals (glob matching, `PreparsedDocumentProvider` signature, coercion) are [U].
- Not taught by the course: federation (Spring support exists since 1.3, `data/federation`), pagination (`ScrollSubrange`, 1.2), Netflix DGS server, graphql-java-kickstart.
- 2.1 (main) items appear only as "coming": GET/QUERY over HTTP, `maxSubscriptionsPerSession`.
