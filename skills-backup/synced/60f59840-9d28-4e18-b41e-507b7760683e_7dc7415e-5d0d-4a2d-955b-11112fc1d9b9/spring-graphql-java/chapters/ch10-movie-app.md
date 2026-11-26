# Ch 10 — Movie Application With GraphQL (22 lessons + jar note) and Bonus (1 lesson)

Labels as in ch02. Era: Boot 2.7.2 (lesson 21 console) → SfG 1.0 code. One runnable jar from the course resources serves three REST services on port 7070. Its file name is in an unextracted resource note [U].

## What the course teaches
- **Setting.** A streaming company with team-owned REST services (customer, movie, review). Several front ends need differently shaped data → one GraphQL layer in front. That is a backend-for-frontend, though the course never uses the term.
- **Upstreams.** `GET /review/{movieId}`; `GET /movie?ids=1&ids=2` (batch by ids); `GET /movie/{genre}/recommended` (top five); `GET/PUT /customer/{id}`; `POST /customer/watchlist` → list of ids. There is no remove-from-watch-list endpoint.
- **Schema design first, from the use cases.** `enum Genre` (11 values). `interface Movie` with `MovieSummary` and `MovieDetails` (adds `reviews`). `UserProfile { id name favoriteGenre watchList: [MovieSummary]! recommended: [MovieSummary]! }`. Queries `userProfile`, `movieDetails`, `moviesByGenre(genre: Genre)`. Mutations `addToWatchList(input: WatchListInput!): WatchListResponse!` and `updateProfile(input: CustomerInput!): UserProfile`.
- **Payload type** `WatchListResponse { status: Status!, watchList: [MovieSummary]! }`. Mobile reads only the status; the browser also selects the list. An unselected list costs no movie call.
- **DTOs follow the upstream payloads**, not the GraphQL types. One `Movie` class feeds both movie views; `Customer.watchList` stays `List<Integer>`, and a field handler shadows it.
- **Clients.** One `@Service` per upstream holding a `WebClient` with a `@Value` base URL that ends in `/`. `moviesByIds` short-circuits an empty list.
- **Controllers.** `userProfile` → customer client. In `MovieController`, `@SchemaMapping(typeName="UserProfile")` handles `watchList` (ids → movies) and `recommended` (genre → top five). `ReviewController` handles `MovieDetails.reviews`. `movieDetails` reuses the batch endpoint with `List.of(id)` and `.next()`.
- **Mutations** return the parent DTO, so the existing field handlers fill the response. `addToWatchList` wraps the ids in `WatchListResponse` and uses a catch-all `onErrorReturn(FAILURE)`.
- **Demo.** Aliased `moviesByGenre` rows sharing `fragment … on Movie` with `... on MovieDetails { reviews }`; aliasing `rating` on the client; profile reload after mutations.
- **Bonus.** At scale, many GraphQL services → schema registry and federation; the course stops there.

## Current in 2.0.6
- The same mapping mechanics as ch02. `ID!` → `Integer` via the binder's conversion [S `data/GraphQlArgumentBinder.java`]. Handlers may live in any `@Controller`. `SchemaMapping.field()` defaults to the method name [S `data/method/annotation/SchemaMapping.java:47`].
- An unknown customer → upstream 404 → nothing resolves it → `userProfile: null` + `INTERNAL_ERROR for <executionId>`, logged at ERROR [S `execution/ExceptionResolversExceptionHandler.java`].
- Errors in the `Mono` returned by a controller **do** reach `@GraphQlExceptionHandler` / `@ControllerAdvice`, through `onErrorResume` [S `data/method/annotation/support/AnnotatedControllerConfigurer.java:542-545`]. This settles an open question in the m10-11 notes.
- Interface field mapping (1.3): one `@SchemaMapping` on an interface field registers for every implementing type [S wiki-1.3; `AnnotatedControllerConfigurer` interface-mapping helper].
- Federation support since 1.3, improved in 1.4. In 2.0.6 it lives in `data/federation/` (`FederationSchemaFactory`, `EntityMapping`, `EntitiesDataFetcher`) [S].
- Cursor pagination (`ScrollSubrange`, `ConnectionTypeDefinitionConfigurer`, 1.2) is the current answer to "millions of movies" [S ground-truth table].
- On Java 21+, blocking controller methods run on virtual threads (1.3), so a `RestClient`-based upstream client is viable [S wiki-1.3].
- A `BatchLoaderRegistry` (`forTypePair`/`forName`, `registerBatchLoader`/`registerMappedBatchLoader`, `withOptions`) and a `DataLoader` controller parameter (resolved by value type or parameter name) support cross-service batching [S `execution/BatchLoaderRegistry.java:65-145`; `data/method/annotation/support/DataLoaderMethodArgumentResolver.java`].

## Decision rules
- Schema per screen, client per upstream, handler per field. Put a field handler where its data source lives.
- The BFF's value is ids in → objects out, plus derived fields. A schema that echoes upstream JSON adds nothing.
- Judge the BFF by client round trips and payload size; server-side fan-out inside the data centre is cheap.
- Mutations return a payload type with an optional expensive part, or the read type the screen re-renders.
- **Downstream error policy** (`patterns.md` P8): map upstream 404 → NOT_FOUND (or null where the field is nullable by design), 400 → BAD_REQUEST, 5xx/timeout → INTERNAL_ERROR with the message hidden. Use `onErrorResume` only for named domain outcomes.
- **Batching across services** (`patterns.md` P9): with a bulk upstream, `@BatchMapping` (Map form) on the parent; without one, a registry loader with bounded fan-out and deduplication.
- Tighten types, don't loosen them: `rating: Float!`, required arguments non-null (`Genre!`), and one "not found" behaviour across fields.
- Typed `@ConfigurationProperties` for upstream URLs. Inject Boot's `WebClient.Builder`. Set timeouts.

## Traps
- `moviesByGenre(genre: Genre)` is nullable, but the handler needs a value → most likely a `/movie//recommended` call and an upstream error [U].
- `rating` moved from `Int` to `String` hides a type mismatch. Use `Float`.
- The API ends up with three accidental "not found" behaviours: unknown customer → null + INTERNAL_ERROR [S]; unknown movie → probably null with no error [U]; watch-list mutation → everything swallowed as FAILURE.
- `onErrorReturn` with no filter hides 404, 5xx and timeouts alike, with no log.
- A one-`Movie`-DTO design works only while no field returns the interface itself. If one did, the default resolver would look for a schema type named `Movie` and hit the interface [U on the exact failure].
- `CustomerInput` is a full replace (both fields required). The two inputs type the customer id differently (`ID!` vs `Int!`).
- Reusing the GraphQL input DTO as the upstream request body couples the public schema to the upstream contract.
- No timeouts, retries or pool settings on the course's `WebClient`s. A fresh `WebClient.builder()` ignores Boot's customised builder [U].
- A base URL without the trailing `/` most likely joins as `…/customer1` [U].
- Aliased parents (`a: userProfile`, `b: userProfile`) cost one upstream call each. The course does no `@BatchMapping`; the old skill claimed it did.
- Boot property names (`spring.graphql.path` vs a possible Boot 4 `spring.graphql.http.path`) are [U]. Check the Boot 4 metadata.

## 2.0 delta

| Since | Change |
|---|---|
| 1.2 | Cursor pagination (`ScrollSubrange`, connection types) [S] |
| 1.3 | Federation (`data/federation`), interface field mapping, virtual threads, `HttpSyncGraphQlClient` [S] |
| 1.4 | Better federation support; DataLoader observations [S wiki-1.4] |
| 2.0 | Binder options make separate input DTOs with non-Java-style names easy; JSpecify nullability (catches `Genre` vs `Genre!` only with annotations) [S wiki-2.0; U effect] |
