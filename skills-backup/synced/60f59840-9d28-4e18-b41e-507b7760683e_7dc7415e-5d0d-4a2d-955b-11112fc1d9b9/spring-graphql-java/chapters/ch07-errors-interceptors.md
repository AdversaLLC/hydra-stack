# Ch 7 — Input Validation & Error Handling (16 lessons)

Labels as in ch02. Era: Boot 2.7.2 / **spring-graphql 1.0.1** (a decompiled jar in lesson 14). Nothing from 1.2 appears: no `@GraphQlExceptionHandler`, no `@ControllerAdvice`, no Adapter. Despite the title, no Bean Validation is shown, only one manual age check.

## What the course teaches
- GraphQL has no status vocabulary; HTTP is just one transport. A response has `data` and `errors`; "not found" is an `errors` entry, not a 404.
- **A thrown exception** gives `field: null` plus one error: message `INTERNAL_ERROR for <id>`, `locations`, `path`, `extensions.classification`. The real message is hidden. With aliases there is one error per path. Working and failing fields together → partial data + errors.
- **Raw `DataFetcherExceptionResolver`** returning `Mono<List<GraphQLError>>`, built with graphql-java `GraphqlErrorBuilder` and **Spring's** `ErrorType` (BAD_REQUEST, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, INTERNAL_ERROR). It must be a bean. `newError(env)` keeps path/locations.
- **Extensions.** `.extensions(Map)`; `classification` is filled from `errorType`.
- **One `ApplicationException(ErrorType, message, extensions)`** with static `Mono.error` factories and `switchIfEmpty(notFound(id))`.
- **Validation assignment.** `Mono.just(in).filter(age >= 18).flatMap(create).switchIfEmpty(mustBe18(in))`, with the input echoed in extensions.
- **Union for expected outcomes.** `union CustomerResponse = Customer | CustomerNotFound`, `customerById(id: ID!): CustomerResponse!`. The handler returns `Mono<Object>` with `.cast(Object.class)`. `ClassNameTypeResolver.addMapping(CustomerDto.class, "Customer")`. The client uses `__typename` plus one inline fragment per member; union members share no selectable fields.
- **`WebGraphQlInterceptor`** copies a `caller-id` header into the GraphQL context (`configureExecutionInput(...graphQLContext(Map))`). The handler reads it from `DataFetchingEnvironment`.
- **`WebFilter`** rejects a missing header with HTTP 400 before GraphQL. Side effect: GraphiQL itself gets 400.
- **Security.** No GraphQL-specific dependency. Spring Security at the transport, plus `@PreAuthorize`/`@Secured` on service methods. There is no demo.

## Current in 2.0.6
- The default internal error is `ErrorType.INTERNAL_ERROR` with message `INTERNAL_ERROR for <executionId>`. The exception is logged at ERROR and its message is not exposed [S `execution/ExceptionResolversExceptionHandler.java:66-125`].
- Resolvers are tried in order; the first non-empty result wins [S same file].
- **Handler ladder (prefer from the top).**
  1. `@GraphQlExceptionHandler` in the controller (local), then in `@ControllerAdvice` (global), since 1.2.0 [S `data/method/annotation/GraphQlExceptionHandler.java:46`]. The controller's own handlers are tried first, then applicable advice beans [S `data/method/annotation/support/AnnotatedControllerExceptionResolver.java:175-210`]. Errors from a returned `Mono`/`Flux` reach these handlers through `onErrorResume` [S `…/support/AnnotatedControllerConfigurer.java:542-545`]. Supported return types: `void`, `GraphQLError`, `Collection<GraphQLError>`, `Mono` of these [S `AnnotatedControllerExceptionResolver.java:400-416`]. For non-controller fetchers, register `AnnotatedControllerConfigurer#getExceptionResolver()` [S `GraphQlExceptionHandler.java:35-37`].
  2. `DataFetcherExceptionResolverAdapter` with synchronous `resolveToSingleError` / `resolveToMultipleErrors`; returning null passes to the next resolver [S `execution/DataFetcherExceptionResolverAdapter.java:114,125`].
  3. The raw `DataFetcherExceptionResolver` (the course's choice).
- **Bean Validation runs, but nothing maps its exception.** `ValidationHelper` applies method validation when the method or class has `@Validated`, or a parameter has `@Valid` or a `@Constraint`, and throws `jakarta.validation.ConstraintViolationException` [S `data/method/annotation/support/ValidationHelper.java:62-88`]. No built-in resolver maps it, so it shows up as `INTERNAL_ERROR` unless you add a handler (`patterns.md` P5).
- **Security resolvers** `SecurityDataFetcherExceptionResolver` / `ReactiveSecurityDataFetcherExceptionResolver` map authentication failures to UNAUTHORIZED and access denied to FORBIDDEN [S `execution/SecurityExceptionResolverUtils.java:39,51`]. Their registration order relative to user resolvers is Boot's [U].
- `@ContextValue` (1.0.0) reads the GraphQL context. It throws `IllegalStateException` when the value is required and missing, unless the parameter is `Optional`/`Mono` [S `…/support/ContextValueMethodArgumentResolver.java:54-81`].
- `WebGraphQlRequest`: `getHeaders()`, `getUri()`; `getCookies()`/`getAttributes()` since 1.1.3; `getRemoteAddress()` since 1.3.0. `WebGraphQlResponse.getResponseHeaders()` and `transform` [S `server/WebGraphQlRequest.java`, `server/WebGraphQlResponse.java`].
- **HTTP status since 1.4.** With `application/graphql-response+json`, unparseable or invalid documents get 4xx. `application/json` keeps 200 + errors. Field errors are always 200 [S wiki-1.4; `server/webflux/GraphQlHttpHandler.java:101-111`].

## Decision rules — three failure kinds, three tools

| Failure kind | Tool | Example |
|---|---|---|
| Expected domain outcome the client branches on | Union result type (non-null field) | `Customer \| CustomerNotFound` |
| Unexpected, or a request-level problem in one field | `errors[]` with the right `ErrorType` via `@GraphQlExceptionHandler` | NOT_FOUND, BAD_REQUEST, FORBIDDEN |
| Reject the request itself | `WebFilter` / Spring Security, scoped to the GraphQL path | missing `caller-id` → 400 |

- Always build errors with `newError(env)` to keep `path`.
- Use NOT_FOUND / FORBIDDEN / UNAUTHORIZED for what they mean. BAD_REQUEST is for bad input.
- The catch-all handler **hides** messages of non-application exceptions.
- Use the interceptor to *enrich* (headers/cookies → context → `@ContextValue`) and a filter or Security to *reject*.
- Authenticate at the transport; authorise per service method. The interceptor sees the whole document, not fields.
- Prefer declarative constraints + a `ConstraintViolationException` handler over `filter` + `switchIfEmpty` chains.

## Traps
- Importing graphql-java's `ErrorType` instead of `org.springframework.graphql.execution.ErrorType`.
- A resolver that is not a bean is silently unused.
- Forwarding `ex.getMessage()` for every exception leaks NPE/SQL text.
- A catch-all resolver that always answers shadows every later resolver, possibly the security ones (Boot order [U]).
- The course checks `ApplicationException.class.equals(ex.getClass())`, an exact match, so subclasses fall to INTERNAL_ERROR. Use `instanceof`.
- Dropping `env` from `newError()` loses `path`/`locations`; aliased calls become ambiguous.
- `filter` + `switchIfEmpty(mustBe18)` also fires when the service returns empty, giving a wrong message.
- Echoing the whole input in `extensions` may leak sensitive fields.
- `Map.of` rejects null header values; default to `""` or use `Optional`.
- Silently returning empty data for an unknown caller looks like "no data". Use FORBIDDEN or a union.
- An unscoped `WebFilter` blocks GraphiQL, actuator and static files. Set a status; don't just return empty. On WebSocket it sees only the handshake [U].
- A user key named `classification` in extensions collides with the generated one [U].
- Leaving a union field nullable loses the "always answers" guarantee. Selecting a shared field directly on a union is a validation error [U spec].

## 2.0 delta

| Since | Change |
|---|---|
| 1.0.1 | `DataFetcherExceptionResolver.forSingleError` [S] |
| 1.1.3 | `WebGraphQlRequest.getCookies()`, `getAttributes()` [S] |
| 1.2 | `@GraphQlExceptionHandler` + `@ControllerAdvice` [S] |
| 1.3 | `WebGraphQlRequest.getRemoteAddress()`; WebSocket `connection_init` auth [S] |
| 1.4 | 4xx for invalid documents with `application/graphql-response+json` [S] |
| 2.0 | Spring Security 7; JSpecify nullability (whether it flags `CustomerResponse!` over `Mono<Object>` is [U]) |
