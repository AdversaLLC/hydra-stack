# Ch 5 — Mutation: CRUD Application (14 lessons)

Labels as in ch02. Era: Boot 2.7.2 / SfG 1.0 (banners dated 2022-08-05). Stack: H2 + R2DBC + `ReactiveCrudRepository`.

## What the course teaches
- **REST → GraphQL mapping.** The two GETs become `Query` fields. POST, PUT and DELETE become `Mutation` fields.
- **Schema.** `createCustomer(customer: CustomerInput!): Customer`, `updateCustomer(id: ID!, customer: CustomerInput!): Customer`, `deleteCustomer(id: ID!): DeleteResponse!`. `CustomerInput { name: String, age: Int, city: String }` has no id and every field is nullable. `DeleteResponse { id: ID!, status: Status }` with `enum Status { SUCCESS, FAILURE }` (frame-confirmed).
- **Layers.** Entity with Spring Data `@Id`, a separate DTO, and `BeanUtils.copyProperties` conversion. The controller stays thin.
- **Binding.** `@MutationMapping` + `@Argument CustomerDto customer`, with no `@RequestBody`. `@Argument("customer")` renames. `ID` arrives as an `Integer`.
- **Service.** Create: `Mono.just(dto).map(toEntity).flatMap(repo::save)`. Update: `findById(id).map(found -> toEntity(id, dto)).flatMap(save)`; a missing id ends empty → `null`. Delete: `deleteById(id).thenReturn(SUCCESS).onErrorReturn(FAILURE)`.
- **Seed.** `data.sql` drops and recreates the table at every start (demo only).
- **Demo.** The mutation returns the created object, so the client selects fields in one round trip. Updating only `name` sets `age` and `city` to **null**: the update is a full replace.
- **Not found.** `null` on a nullable field. Error and result-type options are deferred to ch07.
- **Several mutations** in one operation run **serially in document order** (2 × 2 s delays → about 4 s). Query root fields run concurrently. One operation cannot mix query and mutation fields.
- **Selected columns upstream?** Usually not worth it. GraphQL's win is the slow client edge; a REST upstream cannot be trimmed anyway.

## Current in 2.0.6
- `@MutationMapping` = `@SchemaMapping(typeName = "Mutation")` [S `data/method/annotation/MutationMapping.java`].
- `@Argument` binds a map into a DTO through its constructor, or a default constructor plus setters, recursively. Failures raise `BindException` with per-path field errors [S `data/method/annotation/Argument.java` javadoc; `data/GraphQlArgumentBinder.java:375` BeanWrapper].
- **Binder configuration is new in 2.0.** `GraphQlArgumentBinder.Options` (`nameResolver`, `fallBackOnDirectFieldAccess`, `conversionService`), applied through `AnnotatedControllerDetectionSupport.configureBinder(...)` / `setBinderOptions(...)` (both 2.0.0). The old `setFallBackOnDirectFieldAccess` and the boolean/ConversionService binder constructors are `@Deprecated(since = "2.0", forRemoval = true)` [S `data/method/annotation/support/AnnotatedControllerDetectionSupport.java`; `data/GraphQlArgumentBinder.java:100-122`].
- **Partial updates.** An `ArgumentValue<T>` field inside the input DTO tells omitted, explicit null and value apart, at any nesting level (1.1.0). `isEmpty()`/`ifPresent()` are 1.4.0 [S `data/ArgumentValue.java:28-115`].
- Spring adds no execution-strategy code. Serial mutation order is graphql-java's default [S: grep `ExecutionStrategy` over the tree finds only javadoc mentions].
- `@GraphQlExceptionHandler` (1.2) and `DataFetcherExceptionResolverAdapter` (1.0) are the error alternatives to `null` (ch07) [S ground-truth table].

## Decision rules
- One `input` per write payload. Use separate create and update inputs when the update should be partial.
- Return the mutated object, or a payload type. Give delete a small result type (id + status) rather than a Boolean or null.
- Check existence before saving an update, so a missing id gives empty → `null` rather than a failed write.
- For partial updates, declare `ArgumentValue<T>` fields and merge only the fields that are not omitted into the loaded row (`patterns.md` P3).
- Serial ≠ transactional. If two writes must succeed together, use one mutation field that runs both in a transaction.
- Optimise the client edge first. Push the selection down to the database only when profiling shows wide rows or blobs.

## Traps
- `map` around `save` gives `Mono<Mono<…>>`; use `flatMap`.
- The course's update throws away the loaded row (`found`), so it is a full replace.
- `deleteById` on a missing id most likely completes normally, so the answer is SUCCESS for nothing deleted [U: Spring Data].
- `onErrorReturn(FAILURE)` swallows connection failures with no log.
- `Customer!` (non-null) returning empty → null propagates to the parent [U spec].
- A null from update means "not found", but also "save returned nothing". The client cannot tell which.
- Write operations under `type Query` lose serial execution and hide side effects.
- A hard-coded next id (6) in multi-mutation demos works only because the author knew the auto-increment value. A document cannot reference an earlier field's result.
- `@Id` missing → Spring Data cannot tell insert from update [U]. `copyProperties` silently skips renamed fields [U].
- One document may hold a named query and a named mutation, but one request executes one `operationName` [U spec].

## 2.0 delta

| Since | Change |
|---|---|
| 1.1 | `ArgumentValue<T>` in input DTOs [S] |
| 1.2 | `@GraphQlExceptionHandler` for not-found errors (ch07) [S]; inspector flags unmapped Mutation fields [S] |
| 1.4 | `ArgumentValue.isEmpty()`, `ifPresent()` [S] |
| 2.0 | `GraphQlArgumentBinder.Options` + `configureBinder`; old binder setters deprecated for removal [S]. `ArgumentValue` for **client** input types [S wiki-2.0] |
