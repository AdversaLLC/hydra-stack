# Ch 4 — GraphQL Advanced (30 lessons + 1 resource note)

Labels as in ch02. Era: Spring for GraphQL **1.0.1** / graphql-java 18.2 (stack traces in lessons 17 and 22). Lesson 13 has no video; it was the Maven dependency resource.

## What the course teaches
- **Selection set.** Inject `DataFetchingFieldSelectionSet`. `getFields()` lists qualified paths below the current field. A child handler sees only its own subtree.
- **`DataFetchingEnvironment`.** Gives arguments, source, selection set, context, the parsed `Document` and the executing `OperationDefinition`. Use the narrowest parameter you can.
- **Sequential execution problem.** Two services each delay every element by 1 s. Customers + orders take about 6 s in GraphQL against about 4 s in a hand-written REST pipeline. Children start only after the **whole** parent list is done.
- **Fix by taking control.** One root fetcher builds `CustomerWithOrder`, looks ahead with `selectionSet.contains("orders")` and attaches orders with `flatMapSequential` (about 4 s, ordered). Delete the child `@SchemaMapping` so the property serves the pre-filled data.
- **Programmatic wiring.** A class implementing graphql-java `DataFetcher<T>`, registered through a `RuntimeWiringConfigurer` bean (`w.type("Query", t -> t.dataFetcher("customers", f))`). A `Map<String, DataFetcher>` form also exists.
- **Glob patterns are selection-set paths, not wiring.** A bare name means a direct child. `a/b` is explicit, `*` spans one level, `**` spans any depth (`**/level3`, `level2/**/level5`).
- **Extended scalars.** Add `graphql-java-extended-scalars` (the starter does not bring it). Declare `scalar X` in SDL **and** register `ExtendedScalars.X` in wiring. Java types must match the coercing: `Date` = `LocalDate`, `DateTime` = `OffsetDateTime`. A declared but unregistered scalar fails startup.
- **Object/JSON scalar** for open-ended maps. It costs selection, types and docs inside.
- **No void.** Return a small payload type rather than a null `Object`.
- **Interfaces.** Implementing types repeat the shared fields. Java DTOs need no Java interface. Clients use inline fragments `... on Fruit { … }` and `__typename`.
- **Unions** are for unrelated types (search). A member with no fragment comes back as `{}`.
- **Type resolution** is by simple class name. Renaming `Fruit` to `FruitDto` breaks those elements one by one (partial data + errors). Fix: `ClassNameTypeResolver.addMapping(FruitDto.class, "Fruit")` wired per abstract type.
- **Operation caching.** A graphql-java `PreparsedDocumentProvider` keyed by document text, plugged in via Boot's `GraphQlSourceBuilderCustomizer` → `configureGraphQl(g -> g.preparsedDocumentProvider(p))`. Inlined values defeat it, variables keep hit rates high, and an unbounded map is a leak: use LRU/Caffeine.

## Current in 2.0.6
- A `Flux` return is collected to a list before graphql-java sees it [S `execution/ContextDataFetcherDecorator.java:52`, `ReactiveAdapterRegistryHelper.java:69`]. That is the root cause of the 6 s result.
- Resolvable environment-type parameters: `DataFetchingEnvironment`, `GraphQLContext`, `DataFetchingFieldSelectionSet`, `GraphqlErrorBuilder`, `Locale`/`Optional<Locale>` [S `data/method/annotation/support/DataFetchingEnvironmentMethodArgumentResolver.java`].
- `RuntimeWiringConfigurer` is not deprecated. It gained `setTypeDefinitionRegistry` (1.3.0) and a `configure(builder, List<WiringFactory>)` variant [S `execution/RuntimeWiringConfigurer.java`].
- A raw `DataFetcher` is not a `SelfDescribingDataFetcher`. The inspector cannot see its return type and reports "No class information" skipped types [S `execution/SchemaMappingInspector.java:339`].
- Spring installs a default `ClassNameTypeResolver` on **every** interface and union (`putIfAbsent`); explicit wiring overrides it for one type only [S `execution/DefaultSchemaResourceGraphQlSourceBuilder.java:155-160,227-229`]. It walks Java interfaces and superclasses, skips `java.*`, has `setClassNameExtractor(Function)` and `getMappings()` (1.3) [S `execution/ClassNameTypeResolver.java`]. `GraphQlSource.SchemaResourceBuilder.defaultTypeResolver(...)` replaces it globally [S `execution/GraphQlSource.java:215`]. Explicit mappings feed schema inspection [S `DefaultSchemaResourceGraphQlSourceBuilder.java:233-238`].
- `configureGraphQl(Consumer<GraphQL.Builder>)` exists [S `execution/GraphQlSource.java:150`]. Spring has no `PreparsedDocumentProvider` of its own. The only "preparsed" reference is APQ: `SerializableGraphQlRequest.getDocument()` returns graphql-java's persisted-query marker when `query` is absent and `extensions.persistedQuery` is set [S `server/support/SerializableGraphQlRequest.java:77-90`]. The provider's method signature in graphql-java 25 is [U].
- No annotation for custom fetchers exists (the author predicted one) [S: none in the tree].

## Decision rules
- Is the parent a slow stream and the children independent? Take over the subtree in one root fetcher, using the selection set and `flatMapSequential`, and delete the child mappings. With many parents and a bulk upstream, `@BatchMapping` usually wins.
- Prefer a controller method that takes `DataFetchingEnvironment` over a raw `DataFetcher`. You keep argument binding and inspection.
- Selection paths: use an explicit `a/b` for fixed shapes, `**/x` when depth varies.
- Scalars need three things to agree: dependency version, SDL `scalar` declaration, wiring registration. Check the coercing before choosing the Java type.
- Interface when types share real fields; union when they share nothing; `Object` scalar only for truly open data.
- Type resolution ladder: name DTOs like the schema types → `setClassNameExtractor` via `defaultTypeResolver` for a suffix convention → `addMapping` for a few exceptions → a hand-written resolver last, never with a catch-all `else`.
- Operation cache: key on document text, bounded (LRU), with variables and stable documents. APQ is an option.

## Traps
- A child `@SchemaMapping` left in place after taking over a subtree re-fetches and overrides the pre-filled property.
- A bare deep name in `contains("level3")` silently returns false.
- Two registrations for one field (wiring + controller): which wins is [U].
- `java.util.Date` with `ExtendedScalars.Date` fails at runtime [U].
- `BigDecimal.valueOf(double)` loses precision before the scalar ever sees it. Build from a String.
- `Flux<Object>` gives the inspector no class information unless member types are found by naming convention (1.3).
- Moving the abstract type name (`Product` → `Result`) without moving the explicit resolver wiring breaks `FruitDto` again. The global default avoids that.
- An uncovered union member shows up as `{}` and looks like a server bug.
- The operation name is not part of the course's cache key. It helps monitoring, not the hit rate.
- `logging.level.root=DEBUG` logs request content (a privacy risk) and is very noisy.
- extended-scalars 18.1 belongs to graphql-java 18. 2.0 runs graphql-java 25; pick the matching line [U: version].

## 2.0 delta

| Since | Change |
|---|---|
| 1.2 | Inspector, and its blind spot for raw `DataFetcher`s [S] |
| 1.3 | `ClassNameTypeResolver.getMappings()`, inspector discovery of union/interface member types by naming convention [S wiki-1.3], `RuntimeWiringConfigurer.setTypeDefinitionRegistry` [S] |
| 1.3 | Interface field mapping [S wiki-1.3] |
| 2.0 | graphql-java 25: re-check the extended-scalars version and the `PreparsedDocumentProvider` signature [U] |
| 2.0.6 | APQ marker support in `SerializableGraphQlRequest` [S] |
