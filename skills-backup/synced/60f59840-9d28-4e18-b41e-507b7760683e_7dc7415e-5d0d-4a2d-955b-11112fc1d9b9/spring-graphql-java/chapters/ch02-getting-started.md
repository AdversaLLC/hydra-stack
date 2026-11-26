# Ch 2 — Getting Started With GraphQL (33 lessons; module 1 intro adds 1)

Labels: **[S file]** = confirmed in the v2.0.6 source (paths relative to `spring-graphql/src/main/java/org/springframework/graphql/`). **[U]** = course-only, spec-level or unverified. Course era: Boot 2.7.2 / Spring for GraphQL 1.0.x (console banners, lessons 5–27).

## What the course teaches
- **Motivation.** REST suffers from over-fetching (unneeded payload) and under-fetching (chained calls). GraphQL is a typed query language plus a runtime. The client picks fields; the server publishes the type system [U].
- **Types.** There are five built-in scalars (`Int Float String Boolean ID`; `ID` serialises as a string). Lists are `[T]`, non-null is `T!`, sets are closed with `enum`. There are three root types: `Query`, `Mutation`, `Subscription`. `#` starts a comment, but SDL descriptions use `"…"` strings [U].
- **Setup.** Initializr with Spring for GraphQL + Reactive Web (WebFlux/Netty) + Lombok on Java 17. Every return type in the course is `Mono`/`Flux`.
- **Properties.** `spring.graphql.schema.locations` (the course narrows it to one folder per lecture), `spring.graphql.path=/graphql`, and `spring.graphql.graphiql.enabled=true` (UI at `/graphiql`) [U: Boot property names].
- **Hello world.** Write the schema first (`resources/graphql/*.graphqls`, any file name), then a `@Controller` (not `@RestController`) with a `@QueryMapping` method named after the field. Renaming the method silently returns `null`; the annotation value fixes it.
- **Arguments.** `@Argument` per argument. `!` in the schema makes an argument required, and GraphiQL flags a missing one before sending. `@Argument("name")` renames.
- **Root fields run concurrently.** With 0.8/0.9/1.0 s delays the total is about 1.0 s, not 2.7 s. The `Mono.zip` mental model applies. Never block the event loop.
- **Custom types and inputs.** `customers: [Customer]!` (never null), `customerById(id: ID!): Customer` (nullable). `input` types group arguments and bind to a plain DTO.
- **Nested objects.** `Customer.orders` is filled by `@SchemaMapping(typeName="Customer")` with the parent as a parameter. It runs only when selected, once per parent.
- **N+1 and `@BatchMapping`.** One call with every parent. The Flux form must match size **and** order. A size mismatch fails loudly (`DataLoaderAssertionException` → `INTERNAL_ERROR`, lesson 27). An order mismatch (`flatMap` emits in completion order) silently misassigns data (lesson 28). Fixes: `flatMapSequential`, or the Map form (lesson 29).
- **Overrides and splitting.** A handler for `Type.field` wins over the parent's property. Several controllers can contribute fields of one type (address, account).

## Current in 2.0.6
- `@QueryMapping` is meta-annotated `@SchemaMapping(typeName = "Query")` [S `data/method/annotation/QueryMapping.java:38`]. The field name defaults to the method name [S `SchemaMapping.java`].
- **Parameter binding has three paths.**
  1. `@Argument` binds by name. With no explicit name and no `-parameters` compiler flag, startup fails with "parameter name information not found" [S `data/method/annotation/support/ArgumentMethodArgumentResolver.java:117`].
  2. An unannotated parameter is resolved as the **source/parent** by the fallback resolver. Primitives and their wrappers, dates, URI/URL, Locale and Class are excluded; `CharSequence` and `Number` are deliberately not excluded [S `…/support/SourceMethodArgumentResolver.java:51-71`]. So an unannotated `Integer limit` fails ("no source/parent either"), and an unannotated `String` is taken as the parent.
  3. Special types (`DataFetchingEnvironment`, selection set, `GraphQLContext`, `Principal` and so on) are resolved by type.
- `@BatchMapping` accepts **four** return shapes: `Mono<Map<K,V>>`, `Map<K,V>`, `Flux<V>`, `Collection<V>`, optionally wrapped in `Callable` [S `…/support/AnnotatedControllerConfigurer.java:364,389`]. It has a `maxBatchSize` attribute (since 1.1.0, default -1) [S `data/method/annotation/BatchMapping.java:103-105`].
- A batch method may only take the key collection, `@ContextValue`, `GraphQLContext`, `BatchLoaderEnvironment` and `Principal`. Anything else (for example `@Argument`) throws "Unexpected argument type" [S `…/support/BatchLoaderHandlerMethod.java:145-170`].
- The mapped loader receives a `Set<K>`, so parent keys are de-duplicated by `equals`/`hashCode` [S `execution/BatchLoaderRegistry.java:145`].
- `SchemaMappingInspector` (since 1.2.0) reports schema fields with neither a `DataFetcher` nor a matching property, and registrations that point at non-existent fields [S `execution/SchemaMappingInspector.java:93`]. How Boot logs the report is [U].
- `typeName` is inferred from the simple class name of the source parameter, or set once with a class-level `@SchemaMapping` [S `SchemaMapping.java` javadoc].

## Decision rules
- Write the schema field first, then the handler. The schema is the contract; extra Java properties are invisible.
- Every argument gets `@Argument`; only the parent stays unannotated.
- Make lookups by id nullable, and lists non-null with empty results. Use `[T!]!` when elements must not be null [U spec].
- Batch any per-parent field that does I/O, provided the backend accepts a list of keys. Prefer the Map form; use `flatMapSequential` if you must use the Flux form.
- Keep `typeName` explicit whenever the DTO class name differs from the GraphQL type name (`CustomerDto` vs `Customer`).
- Count resolver calls (a log line or counter) to see N+1. Don't judge by the data.

## Traps
- An unmapped nullable field returns `null` with no error at runtime. Read the inspection report (1.2+) instead.
- `-parameters` missing → `@Argument` without a name fails [S].
- Field arguments and batching conflict. Lesson 25 silently drops `limit` when switching to `@BatchMapping`. For per-field arguments, use `@SchemaMapping` with a `DataLoader` parameter (see `patterns.md` P2), or redesign.
- The Map form is order-proof but **not miss-proof**. An absent key most likely yields null, which breaks a non-null `[T]!` [U: java-dataloader behaviour]. Fill every key (`getOrDefault(..., List.of())`).
- Keys without sound `equals`/`hashCode` break the Map form.
- An accidental override: a stray method named after a field replaces real data (lesson 30's `age` = 100).
- Opening `/graphql` in a browser. That is the POST endpoint; the UI is `/graphiql`.
- "Java 11 also works" was true on Boot 2.7. Framework 7 needs Java 17+ [U: baseline not in ground truth].
- The per-lecture `schema.locations` + `scanBasePackages` trick is teaching scaffolding, not a layout.

## 2.0 delta

| Since | Change |
|---|---|
| 1.1 | `@BatchMapping(maxBatchSize)` [S] |
| 1.2 | `SchemaMappingInspector` startup report [S] |
| 1.3 | Blocking controller methods run on virtual threads (Java 21+, with an Executor) [S wiki-1.3] |
| 1.3 | Interface field mapping: one `@SchemaMapping` on an interface field covers every implementation [S wiki-1.3] |
| 1.4 | DataLoader 5 baseline and a `graphql.dataloader` observation [S wiki-1.4]. Whether the size-assertion text changed is [U]. |
| 2.0 | Spring Framework 7, GraphQL Java 25, Jackson 3. JSpecify nullability checked by the inspector (only for Kotlin or JSpecify-annotated Java). `GraphQlArgumentBinder.Options` (`nameResolver` etc.) [S wiki-2.0] |
| 2.0.6 | HTTP endpoint is POST only [S `server/webflux/GraphQlRequestPredicates.java:100`]. GET/QUERY exist only on main (2.1). |
