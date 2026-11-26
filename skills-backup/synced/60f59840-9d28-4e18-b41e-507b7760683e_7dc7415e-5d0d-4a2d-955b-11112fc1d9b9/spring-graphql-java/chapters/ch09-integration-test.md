# Ch 9 — Integration Test (11 lessons)

Labels as in ch02. Era: Boot 2.7.2 / SfG 1.0 (logs dated 2022-08-12). Tests target the ch05–ch07 apps via `@TestPropertySource(properties = "lec=…")`. `spring-graphql-test/src/main` is identical between v2.0.6 and main (`diff -rq` empty, m09 note), so this chapter also holds for 2.1 so far.

## What the course teaches
- `HttpGraphQlTester` is to `HttpGraphQlClient` what `WebTestClient` is to `WebClient`: the same request model, but only `execute()`, then JSONPath assertions.
- Setup: `@SpringBootTest` + `@AutoConfigureHttpGraphQlTester`, then autowire the tester (the `spring-graphql-test` dependency was already present).
- `path("customers").entityList(Object.class).hasSizeGreaterThan(2)`, `path("customers[0].name").entity(String.class).isEqualTo("sam")`.
- Make each new test fail once to prove it asserts. Failure messages include the request.
- Test documents in `src/test/resources/graphql-test/`, with `documentName("crud-operations")`, `operationName(...)` and a `response` alias.
- Create/update/delete tests: DTO variables, `satisfies(consumer)` with AssertJ, enum assertions as strings or Java enums.
- **Error test** (under-age create → BAD_REQUEST). It first fails with HTTP 400 from the module 7 `WebFilter`; fixed with `tester.mutate().header("caller-id", …).build()`. Then `pathDoesNotExist()` fails on `"response": null`; `valueIsNull()` is right.
- **Subscription test.** `@SpringBootTest(webEnvironment = DEFINED_PORT)`, `WebSocketGraphQlTester.builder("ws://localhost:8080/graphql", client)`, trigger with `executeAndVerify()`, then `executeSubscription().toFlux("customerEvents", T.class).take(1)` with `StepVerifier`.

## Current in 2.0.6
- Request terminals: `execute()`, `executeAndVerify()`, `executeSubscription()` only. `executeAndVerify()` = `execute().path("$.errors").pathDoesNotExist()` [S `spring-graphql-test/…/tester/GraphQlTester.java`; `DefaultGraphQlTester.java:183-185`].
- A bare path is prefixed with `$.data.` unless it starts with `$` or `data.` [S `DefaultGraphQlTester.java:398-406`]. `path("errors")` therefore does not reach the errors array.
- **`path()` verifies that there are no unexpected errors first** [S `DefaultGraphQlTester.java:323-330`].
- **The four error methods** [S `GraphQlTester.java:493-529`; `DefaultGraphQlTester.java:285-291`]:

| Method | Effect |
|---|---|
| `filter(pred)` | Marks matching errors as expected; does not require any |
| `expect(pred)` | Marks matching errors as expected; **fails if none match** ("No matching errors.") |
| `verify()` | Fails if any unexpected errors remain; returns `Traversable` |
| `satisfy(consumer)` | Marks **all** errors expected, then runs your consumer (weakest) |

- `valueIsNull()` (key present, value null) vs `pathDoesNotExist()` (key absent).
- `HttpGraphQlTester` is built on `WebTestClient` [S `HttpGraphQlTester.java:42,51`]. Its transport asserts status 200 and a JSON content type, sends `Accept: application/json` [S `WebTestClientTransport.java:56-63`], and **cannot run subscriptions** (`UnsupportedOperationException`) [S same file `:71-74`]. Because it sends `application/json`, a 1.4+/2.0 server still answers 200 + errors for invalid documents, so `errors()` assertions keep working [S `server/webflux/GraphQlHttpHandler.java:101-111`].
- `Subscription.toFlux(path, type)` maps each event through `path(...)`, so **an event carrying errors fails the stream** [S `GraphQlTester.java`].
- `WebSocketGraphQlTester`: `builder(String|URI, WebSocketClient)`, `create(URI, WebSocketClient)`, `start()`/`stop()`, `interceptor(s)` (1.3 per the wiki; no `@since` in the source) [S `WebSocketGraphQlTester.java:42-102`].
- In-process testers: `ExecutionGraphQlServiceTester` (engine) and `WebGraphQlTester` (+ interceptors). Both run subscriptions without a socket [S `AbstractDirectGraphQlTransport.java:57-67`].
- Jackson 3 (`tools.jackson.databind`) if present, otherwise Jackson 2 [S `AbstractGraphQlTesterBuilder.java:62-66,135-139`].
- `@GraphQlTest` and `@AutoConfigureHttpGraphQlTester` belong to Spring Boot; their Boot 4 module names are [U].

## Decision rules — pick the tester by the layer you need

| Tester | Covers | Skips | Subscriptions |
|---|---|---|---|
| `ExecutionGraphQlServiceTester` | Engine, controllers, resolvers | Interceptors, filters, HTTP | yes, in-process |
| `WebGraphQlTester` | + `WebGraphQlInterceptor`s, headers | WebFilters, codecs, HTTP | yes, in-process |
| `HttpGraphQlTester` | Full HTTP stack, WebFilters, codecs | — | **no** |
| `WebSocketGraphQlTester` | Real socket, handshake, `connection_init` | — (needs a started server) | yes |

- Expect errors? Call `errors().expect(...)` (or `filter`) **before** `path()`. Use `satisfy` only with real assertions inside.
- A failed nullable field → `valueIsNull()`. An absent key → `pathDoesNotExist()`.
- Filter-protected endpoint → build a header-carrying tester with `mutate().header(...)` in `@BeforeEach`.
- Subscriptions: subscribe first, trigger in `StepVerifier.then(...)`, bound with `take(n)`, `verify(Duration)`, then `stop()` the WebSocket tester in `@AfterEach`. Use `RANDOM_PORT` + `@LocalServerPort`.
- Isolation: no hard-coded generated ids, reset data per test, or assert relative to what the test created.
- Keep the "watch it fail once" habit.

## Traps
- Looking for `retrieve(...)` on the tester.
- `customers.[0]` works through Jayway leniency [U]; `customers[0]` is the conventional form.
- `satisfy` with an empty consumer lets any error pass.
- HTTP 400 from a filter is transport. The tester throws before any GraphQL assertion.
- The course triggers the event **before** subscribing and still passes. The likeliest reason is that the buffer sink keeps events until its first subscriber, so a second such test in the same context would hang [U: Reactor]. Subscribe first.
- `verifyComplete()` with no timeout hangs forever [U].
- `DEFINED_PORT` 8080 collides with a running dev app or a parallel CI job.
- Asserting id 5 after inserts, or deleting id 3/1, couples tests to seed data and run order. Per-class `@TestPropertySource` builds separate contexts (slower) [U].
- The old P13 not-found test is wrong for the course apps: lec14 returns null with no error, and lec15 returns the `CustomerNotFound` union member.
- Selecting `name` directly on a union-returning field is a validation error. Use `... on Customer { name }`.

## 2.0 delta

| Since | Change |
|---|---|
| 1.2 | Nested `path(path, consumer)` [S] |
| 1.3 | `variables(Map)`, `fragment()`/`fragmentName()`, WebSocket tester interceptors [S] |
| 1.3.5 | `returnResponse()` [S] |
| 2.0.6 | `EntityList.singleElement()` (no `@since`), Jackson 3 mapping [S]; Kotlin reified extensions [S wiki-2.0] |
