# Ch 6 — Subscription (7 lessons)

Labels as in ch02. Era: Boot 2.7.2 / SfG 1.0. The startup log shows `GraphQL endpoint HTTP POST /graphql` and `GraphQL endpoint WebSocket /graphql`.

## What the course teaches
- A subscription is one request answered by a stream of server messages (push notifications).
- **Schema** (a second file, `sub.graphqls`): `type Subscription { customerEvents: CustomerEvent }`, `CustomerEvent { id: ID!, action: Action }`, `enum Action { CREATED, UPDATED, DELETED }`. The field type is the **element**, not `[CustomerEvent]`.
- **Event service.** A `Sinks.many().multicast().onBackpressureBuffer()` with `emit(e) → tryEmitNext(e)` and `stream() → sink.asFlux()`.
- **Emitting.** From the CRUD service: `.doOnNext(emit CREATED/UPDATED)` after `save`; `deleteById(id).doOnSuccess(emit DELETED)`.
- **Controller.** `@SubscriptionMapping Flux<CustomerEvent> customerEvents()` returns the shared stream.
- **Transport.** `spring.graphql.websocket.path=/graphql`; it may share the HTTP path [U: Boot property].
- **[CORRECTION] lesson.** `sink.asFlux().cache(0)`, explained as "making the publisher hot".
- **Demo.** Two browser windows; GraphiQL shows only the latest event.

## Current in 2.0.6
- `@SubscriptionMapping` = `@SchemaMapping(typeName = "Subscription")` [S `data/method/annotation/SubscriptionMapping.java`].
- The return value becomes a `Flux` per subscription: a `Publisher` via `Flux.from`, other reactive types via the adapter registry, a plain value as `Flux.just`, null as empty. Spring **does not share or cache** it; sharing is the app's job [S `execution/ReactiveAdapterRegistryHelper.java:89-104`].
- Spring offers no event-bus helper. `Sinks.` appears only in `client/WebSocketGraphQlTransport.java` and `server/webmvc/GraphQlSseHandler.java` [S grep].
- **WebSocket protocol is graphql-transport-ws.** `GraphQlWebSocketHandler` lists `graphql-transport-ws` and `graphql-ws` as sub-protocols, but closes sessions that negotiate the legacy Apollo `graphql-ws` [S `server/webflux/GraphQlWebSocketHandler.java:78,166`]. Messages: `connection_init`, `connection_ack`, `ping`, `pong`, `subscribe`, `next`, `error`, `complete` [S `server/support/GraphQlWebSocketMessageType.java`]. A `subscribe` before ack closes as unauthorised; a missing init within the timeout closes; a second init closes [S same handler, about lines 175-255].
- **Auth** via the `connection_init` payload: `AuthenticationWebSocketInterceptor` + `BearerTokenAuthenticationExtractor` (`Authorization` key), 1.3 [S `server/webflux/AuthenticationWebSocketInterceptor.java`, `server/support/BearerTokenAuthenticationExtractor.java`].
- **Keep-alive** pings (1.3, Boot property `spring.graphql.websocket.keep-alive`) [S wiki-1.3]. A `CorsConfiguration` constructor arrived in 1.4.6 [S handler javadoc].
- **SSE transport** for subscriptions on WebFlux and MVC (`GraphQlSseHandler`, 1.3.0). It answers non-subscription operations with an error [S `server/webflux/GraphQlSseHandler.java`].
- **Stream errors** go through `SubscriptionExceptionResolver` (1.0.1) and are wrapped in `SubscriptionPublisherException` [S `execution/SubscriptionExceptionResolver.java`, `SubscriptionPublisherException.java`]. Controller subscription errors are routed to `handleSubscriptionError` [S `data/method/annotation/support/AnnotatedControllerConfigurer.java:536`].
- Coming in 2.1 (main only): `GraphQlWebSocketHandler.builder(...)` with `maxSubscriptionsPerSession` [S main tree].

## Decision rules
- SDL: `field: Event`, never `[Event]`. Use a union when event kinds carry different payloads.
- One sink per stream, owned by one service. Producers emit; subscription handlers only read.
- Emit **after** the write succeeds, from the service layer, so every write path publishes. Emit after commit when a transaction is involved.
- Handle `EmitResult` (or use `emitNext` with a failure handler). Don't ignore `tryEmitNext`'s result.
- Choose the sink flavour on purpose: buffer vs best effort, and what happens when the last subscriber leaves (auto-cancel).
- A sink lives in one JVM. With more than one instance, use a broker.
- Production subscriptions need auth (`connection_init`), keep-alive, and limits.

## Traps
- **The "hot" correction is under-explained.** A multicast sink is already shared and live [U: Reactor]. The most plausible real effect of `cache(0)` is to hold one permanent subscription to the sink, so the buffer sink's auto-cancel does not shut it down when the last GraphQL subscriber disconnects [U: Reactor `autoCancel`; no Reactor source on disk]. Keep `cache(0)`, or a sink with auto-cancel off, and pin the behaviour with the test in `TESTS-TODO.md` T5.
- `cache()` with no argument replays the whole history to every new subscriber and grows without bound [U].
- "Cold" means the source re-runs per subscriber. It does not "replay"; replay is `cache(n)`/`replay`.
- Concurrent `tryEmitNext` from two request threads can fail, and the event is lost silently [U].
- `doOnSuccess` on `deleteById` emits DELETED for a phantom id [U].
- A side effect in `doOnNext` runs once per subscription of that `Mono`. A retry emits twice [U].
- GraphiQL's single result pane overwrites. It is not a lost event.
- Clients using the legacy Apollo `graphql-ws` protocol are closed [S].
- The course's `${lec}` + `@EnableR2dbcRepositories` package switch is scaffolding.

## 2.0 delta

| Since | Change |
|---|---|
| 1.0.1 | `SubscriptionExceptionResolver`, `SubscriptionPublisherException` [S] |
| 1.3 | `connection_init` auth interceptor, keep-alive, SSE transport [S] |
| 1.3 | Interceptors on `WebSocketGraphQlTester` [S wiki-1.3] |
| 1.4.6 | WebSocket CORS configuration [S] |
| 2.1 (main) | `maxSubscriptionsPerSession` (not in 2.0.6) [S main] |
