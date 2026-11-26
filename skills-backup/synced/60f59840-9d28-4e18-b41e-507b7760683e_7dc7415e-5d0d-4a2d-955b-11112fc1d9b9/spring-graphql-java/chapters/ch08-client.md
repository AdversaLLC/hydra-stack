# Ch 8 — GraphQL Client (26 lessons, numbered 1–27; no lesson 16)

Labels as in ch02. Era: Boot 2.7.2 / **spring-graphql 1.0.1** (jar in stack traces). One project holds the server (lecture 14 copy) and a `clientapp` package sharing the DTOs. A `CommandLineRunner` calls `localhost:8080/graphql` over real HTTP.

## What the course teaches
- **`HttpGraphQlClient`** wraps `WebClient`: `builder().webClient(b -> b.baseUrl(url)).build()`, or `builder(webClient)`. Every call is a POST.
- **Raw document.** `document("{ … }").execute()` → `ClientGraphQlResponse`; `field("customers").toEntityList(Dto.class)`.
- **Aliases** change the response key, so decode `field("a")`. On 1.0.1 the wrong key threw `FieldAccessException … errors: []`.
- **Document files** in `graphql-documents/`, loaded with `documentName("customer-by-id")` and `.variable("id", id)`. `retrieve(path)` is `execute` + field + decode.
- **Two aliases → wrapper DTO.** `retrieve("")` decodes all of `data`. `execute().map(r -> r.toEntity(Both.class))` is equivalent.
- **Errors.** `execute()`, then branch on the field: value → decode; no value → keep its error (message, classification, extensions) in a home-made result holder. Or use `onErrorReturn`/`onErrorResume`. The course uses `field.hasValue()` / `field.getError()`.
- **Union decoding.** Select `__typename` (aliased `type`) plus one inline fragment per member, read `field("customerById.type")`, then decode to the matching DTO. A client-side marker interface unifies the return type.
- **CRUD.** One `crud-operations.graphql` with five named operations, every root field aliased `response:`, and one generic helper `call(op, vars, ParameterizedTypeReference<T>)`.
- **Create.** Sending a DTO with `id = null` fails because `CustomerInput` has no `id`. The fixes are a separate input DTO or `@JsonInclude(NON_NULL)`.
- **Subscriptions.** `WebSocketGraphQlClient.builder("ws://…/graphql", new ReactorNettyWebSocketClient())`, `retrieveSubscription(path).toEntity(T)` → `Flux`.
- **Headers.** Static ones on the builder; per call, `client.mutate().header(...).build()`.

## Current in 2.0.6
- `HttpGraphQlClient.builder()`, `builder(WebClient)`, `builder(WebClient.Builder)`; `mutate()`; `url`/`header`/`headers`/`codecConfigurer` inherited from `WebGraphQlClient.Builder` [S `client/HttpGraphQlClient.java`, `client/WebGraphQlClient.java:63`].
- `RequestSpec` terminals: `retrieve(String)`, `retrieveSync(String)` (1.3), `retrieveSubscription(String)`, `execute()`, `executeSync()` (1.3), `executeSubscription()`. There is **no** no-arg `retrieve()`; `retrieve("")` = whole `data` [S `client/GraphQlClient.java:191-321`; `support/AbstractGraphQlResponse.java:70-80`].
- **`ResponseField` has only `getPath()`, `getParsedPath()`, `getValue()`, `getErrors()`**. `hasValue()`/`getError()` do not exist [S `ResponseField.java:39-95`]. `getErrors()` returns errors at, above *and below* the path [S javadoc table]. `ClientResponseField` adds `toEntity(Class|ParameterizedTypeReference)` and `toEntityList(...)` [S `client/ClientResponseField.java:46-77`].
- **Failure semantics (the core table).**

| Case | `retrieve(path).toEntity` | `execute()` → `field(path).toEntity` |
|---|---|---|
| Success | value | value |
| Partial: value present, nested errors | **throws** `FieldAccessException` | value (inspect `getErrors()`) |
| Field null **with** errors | throws `FieldAccessException` | throws `FieldAccessException` |
| Field null, no errors | completes **empty** | `null` (`toEntityList` → empty list) |
| Wrong path / alias, valid response | empty / `null` / empty list, **silent** | same, silent |

Sources: [S `client/DefaultGraphQlClient.java:245-252` (`getValidField`), `client/DefaultClientResponseField.java:89-107`].
- `FieldAccessException` carries `getResponse()` and `getField()`; message "Invalid field '<path>', errors: …" [S `client/FieldAccessException.java:45-69`].
- Document location `classpath:graphql-documents/`, extensions `.graphql` **and** `.gql`, overridable with `documentSource(...)` [S `client/AbstractGraphQlClientBuilder.java:94`, `support/ResourceDocumentSource.java:49`, `client/GraphQlClient.java:107`].
- `WebSocketGraphQlClient.builder(String|URI, WebSocketClient)`; `keepAlive(Duration)` since 1.3, off by default [S `client/WebSocketGraphQlClient.java:92-99`]. A subscription stream can end with `SubscriptionErrorException` or `WebSocketDisconnectedException` [S `GraphQlClient.java` javadoc].
- `GraphQlClientInterceptor` (1.0.0): `intercept`, `interceptSubscription`, `andThen`; registered with `builder.interceptor(...)`. `attribute(...)` values are for interceptors [S `client/GraphQlClientInterceptor.java`]; that they are not sent to the server is [U].
- **`HttpSyncGraphQlClient`** (1.3) over `RestClient`: `builder()`, `builder(RestClient)`, `builder(RestClient.Builder)`. `messageConverters(...)` is deprecated for removal since 2.0.0 in favour of `configureMessageConverters(Consumer)` [S `client/HttpSyncGraphQlClient.java:55-128`].
- **`DgsGraphQlClient`** (since **1.3**, not 2.0). 2.0 adds chaining several requests into one exchange, `queryAlias`, and a no-arg `retrieve()`/`retrieveSync()` [S `client/DgsGraphQlClient.java:54,126,209,228`; wiki-2.0].
- **`ArgumentValue` on client input types (2.0)**, serialised through `client/json/GraphQlJacksonModule.java` / `GraphQlJackson2Module.java` [S wiki-2.0; files present]. Whether default codecs register it automatically is [U].
- Default JSON is Jackson 3, with Jackson 2 as fallback [S ground truth].

## Decision rules
- One client per remote service, built from Boot's `WebClient.Builder` (or `RestClient.Builder`) and injected.
- Fixed operations live in document files. Alias every root field `response:` and use one `call(op, vars, type)` helper with **one test per operation**, because a wrong path is silent.
- Use `retrieve` only when *any* error should fail the call. Use `execute()` + field checks when partial data is useful or the caller acts on the error type or extensions.
- Unions: `__typename` + one fragment per member + a switch on the **schema** type name.
- Input DTOs mirror schema `input` types exactly. For partial updates use `ArgumentValue` (2.0), not `NON_NULL`.
- Static header → builder. Per-user header → `GraphQlClientInterceptor` or a WebClient filter; `mutate()` per request only off the hot path.
- Blocking-friendly stack (virtual threads)? `HttpSyncGraphQlClient` with `retrieveSync`/`executeSync`.

## Traps
- `hasValue()` / `getError()` from the course do not compile on 2.0.6.
- Assuming 1.0's "wrong path throws". On 2.0.6 it is silent.
- Calling `subscribe()` inside client code loses errors (`onErrorDropped`), backpressure and cancellation. Return the publisher.
- A missing union-member fragment decodes to an object with empty fields.
- `retrieve` on a subscription document gives one response, not a stream.
- `http://` for the WebSocket URL; it must be `ws://`.
- Client documents placed in `graphql/` (the server schema folder).
- `Map.of` rejects null variable values.
- `@JsonInclude(NON_NULL)` makes "clear this field" impossible.
- A `mutate().build()` per request builds a new client each time [U: cost].
- A base URL without `/graphql` posts to the wrong path.

## 2.0 delta

| Since | Change |
|---|---|
| after 1.0.1 | `ResponseField.hasValue()`/`getError()` gone; missing field no longer throws (release not identified) [S current; U when] |
| 1.3 | `HttpSyncGraphQlClient`, `retrieveSync`/`executeSync`, `DgsGraphQlClient`, WebSocket `keepAlive` [S] |
| 2.0 | `ArgumentValue` for client input, `DgsGraphQlClient` multi-query + `queryAlias`, Kotlin extensions, Jackson 3, `configureMessageConverters` [S] |
