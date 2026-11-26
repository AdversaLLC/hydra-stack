# Patterns — copy-ready, Spring for GraphQL 2.0.6

Each pattern is a minimal snippet in our own words, built from the strongest proposals in the study notes. Evidence: **[S file]** = the APIs used were found in the v2.0.6 source (paths relative to `spring-graphql/src/main/java/org/springframework/graphql/`, test classes under `spring-graphql-test/…/test/tester/`). **[U]** = not run, or depends on Boot, Reactor, graphql-java or Spring Data behaviour that was not checked. **No pattern here has been compiled or run yet.** `TESTS-TODO.md` lists the suites that would pin each one; treat a pattern as ready only after its test passes.

---

## P0 — Dependencies and properties (Boot side) [U]
```xml
<artifactId>spring-boot-starter-graphql</artifactId>
<artifactId>spring-boot-starter-webflux</artifactId>   <!-- or -web for MVC + virtual threads -->
<artifactId>spring-graphql-test</artifactId>           <!-- test scope -->
<!-- graphql-java-extended-scalars: pick the line that matches graphql-java 25, not 18.1 -->
```
```properties
spring.graphql.graphiql.enabled=true        # dev only
spring.graphql.websocket.path=/graphql      # exposes subscriptions over WebSocket
spring.graphql.websocket.keep-alive=15s     # 1.3+ [S wiki-1.3]
```
Boot 4 may have renamed the HTTP path property (`spring.graphql.http.path`?) [U]. Check the Boot 4 configuration metadata before relying on any of these names.

## P1 — BatchMapping contract (N+1 fix) [S]
```java
@BatchMapping(typeName = "Customer", field = "orders")          // attributes: BatchMapping.java:81-97
Mono<Map<Customer, List<Order>>> orders(List<Customer> customers) {
    List<String> names = customers.stream().map(Customer::name).toList();
    return orders.byCustomerNames(names)                         // ONE upstream call: Mono<Map<String, List<Order>>>
        .map(byName -> customers.stream().collect(Collectors.toMap(
            c -> c, c -> byName.getOrDefault(c.name(), List.of()), (a, b) -> a)));
}
```

| Rule | Why | Evidence |
|---|---|---|
| Return one of `Mono<Map<K,V>>`, `Map<K,V>`, `Flux<V>`, `Collection<V>` (optionally inside `Callable`) | Anything else fails at registration | [S `data/method/annotation/support/AnnotatedControllerConfigurer.java:364,389`] |
| Prefer the Map form | Order-proof by construction | [S `BatchMapping` javadoc] |
| Flux/Collection form: exactly one element per key, **in key order**: `flatMapSequential` or `concatMap`, never `flatMap`; `defaultIfEmpty(List.of())` per key | Size errors are loud (DataLoader assertion); order errors silently misassign data | course lessons 27–28; [S javadoc] |
| Map form: still put an entry for **every** key | An absent key most likely becomes null and breaks `[T]!` | [U java-dataloader] |
| Keys need sound `equals`/`hashCode` (records, or Lombok `@Data`) | The mapped loader receives a de-duplicated `Set<K>` | [S `execution/BatchLoaderRegistry.java:145`] |
| No `@Argument` on a batch method; allowed are keys, `@ContextValue`, `GraphQLContext`, `BatchLoaderEnvironment`, `Principal` | Throws "Unexpected argument type" | [S `…/support/BatchLoaderHandlerMethod.java:145-170`] |
| Cap a large fan-in with `maxBatchSize` (1.1+) | Upstream URL or IN-list limits | [S `BatchMapping.java:103-105`] |

## P2 — Parameter binding card, and batching a field that has arguments

| Parameter | Binds to | Evidence |
|---|---|---|
| `@Argument T x` | Argument `x` (name from `@Argument("…")` or the parameter name; needs `-parameters`) | [S `…/support/ArgumentMethodArgumentResolver.java:107,117`] |
| `@Argument ArgumentValue<T> x` / `ArgumentValue` field in an input DTO | Omitted vs null vs value | [S `data/ArgumentValue.java`] |
| `@Arguments T all` | All arguments into one object | [S `…/support/AnnotatedControllerConfigurer.java:175`] |
| Unannotated non-simple type | The **parent/source** (any position) | [S `…/support/SourceMethodArgumentResolver.java:51-71`] |
| Unannotated `Integer`/`int`/dates | Nothing; fails with "no source/parent either" | [S same] |
| Unannotated `String`/`Number` | Taken as the source, then fails on the type | [S same, comment line 55] |
| `DataFetchingEnvironment`, `DataFetchingFieldSelectionSet`, `GraphQLContext`, `Locale`, `GraphqlErrorBuilder` | Per-field context | [S `…/support/DataFetchingEnvironmentMethodArgumentResolver.java`] |
| `@ContextValue("k")` / `@LocalContextValue` | GraphQL context entry | [S `…/support/ContextValueMethodArgumentResolver.java:54-81`] |
| `DataLoader<K,V> name` | Loader looked up by value-type name, then parameter name | [S `…/support/DataLoaderMethodArgumentResolver.java:53-64`] |

Field arguments plus batching: put the argument into a composite key and use a named loader [U: not run].
```java
record OrdersKey(String customer, int limit) {}

@Configuration
class Loaders {
    Loaders(BatchLoaderRegistry registry, OrderClient client) {          // execution/BatchLoaderRegistry.java:79,145
        registry.<OrdersKey, List<Order>>forName("ordersByKey")
            .registerMappedBatchLoader((keys, env) -> client.byKeys(keys)); // Mono<Map<OrdersKey, List<Order>>>
    }
}
@SchemaMapping(typeName = "Customer")
CompletableFuture<List<Order>> orders(Customer c, @Argument int limit,
                                      DataLoader<OrdersKey, List<Order>> ordersByKey) {
    return ordersByKey.load(new OrdersKey(c.name(), limit));
}
```

## P3 — Partial update with `ArgumentValue` [S API; U merge behaviour]
```java
record CustomerPatch(ArgumentValue<String> name, ArgumentValue<Integer> age) {}

@MutationMapping
Mono<Customer> patchCustomer(@Argument int id, @Argument CustomerPatch patch) {
    return repo.findById(id).map(row -> {
        patch.name().ifPresent(row::setName);             // ifPresent: 1.4.0
        if (patch.age().isEmpty()) row.setAge(null);      // explicit null clears; isEmpty: 1.4.0
        else patch.age().ifPresent(row::setAge);          // omitted → untouched
        return row;
    }).flatMap(repo::save);
}
```
`ArgumentValue` works as a field "within the object structure" of an `@Argument` parameter [S `data/ArgumentValue.java:28-48`]. Binding into a record vs a setter DTO was not run [U]. 2.0 binder options (`nameResolver` etc.) are set via `AnnotatedControllerDetectionSupport.configureBinder(...)` [S].

## P4 — Exception handling with `@GraphQlExceptionHandler` [S]
```java
public class AppException extends RuntimeException {
    final ErrorType type; final Map<String, Object> ext;            // org.springframework.graphql.execution.ErrorType
    public AppException(ErrorType type, String msg, Map<String, Object> ext) { super(msg); this.type = type; this.ext = ext; }
    public static <T> Mono<T> notFound(String what, Object id) {
        return Mono.error(new AppException(ErrorType.NOT_FOUND, what + " not found", Map.of("id", id)));
    }
}

@ControllerAdvice
class GraphQlErrorAdvice {
    @GraphQlExceptionHandler                                          // handles AppException and all subclasses
    GraphQLError app(AppException ex, DataFetchingEnvironment env) {
        return GraphqlErrorBuilder.newError(env)                      // keep path + locations
            .errorType(ex.type).message(ex.getMessage()).extensions(ex.ext).build();
    }
}
// controller: return service.byId(id).switchIfEmpty(AppException.notFound("Customer", id));
```
- Resolution order: the controller's own `@GraphQlExceptionHandler` first, then applicable `@ControllerAdvice` [S `data/method/annotation/support/AnnotatedControllerExceptionResolver.java:175-210`]. Errors from returned `Mono`/`Flux` are routed there via `onErrorResume` [S `…/support/AnnotatedControllerConfigurer.java:542-545`]. Handler methods may take `DataFetchingEnvironment`; they share the controller argument resolvers [S `…/support/AnnotatedControllerDetectionSupport.java:268`]. Return `GraphQLError`, `Collection<GraphQLError>`, `Mono` of these, or `void` [S `AnnotatedControllerExceptionResolver.java:400-416`].
- **Don't add a `Throwable`/`RuntimeException` catch-all.** The framework default already returns `INTERNAL_ERROR for <executionId>` with the message hidden and logged [S `execution/ExceptionResolversExceptionHandler.java:66-125`]. A catch-all inside the data fetcher would also swallow Spring Security's `AccessDeniedException` before `SecurityDataFetcherExceptionResolver` maps it to FORBIDDEN [S inference from the two files above; Boot resolver order U]. This refines the m07 proposal, which asked for a message-hiding catch-all.
- Non-controller `DataFetcher`s: register `AnnotatedControllerConfigurer#getExceptionResolver()` with `GraphQlSource.Builder#exceptionResolvers` [S `data/method/annotation/GraphQlExceptionHandler.java:35-40`].
- Fallback for code outside controllers: extend `DataFetcherExceptionResolverAdapter`, override `resolveToSingleError(ex, env)` and return `null` to pass on [S `execution/DataFetcherExceptionResolverAdapter.java:114,125`].

## P5 — Bean Validation on arguments [S trigger; U Boot validator wiring]
```java
record NewCustomer(@NotBlank String name, @Min(18) int age) {}

@Controller @Validated
class CustomerController {
    @MutationMapping Mono<Customer> createCustomer(@Argument @Valid NewCustomer customer) { return service.create(customer); }
}

@ControllerAdvice
class ValidationAdvice {
    @GraphQlExceptionHandler
    List<GraphQLError> invalid(ConstraintViolationException ex, DataFetchingEnvironment env) {
        return ex.getConstraintViolations().stream()
            .map(v -> GraphqlErrorBuilder.newError(env).errorType(ErrorType.BAD_REQUEST)
                .message(v.getMessage())
                .extensions(Map.of("property", v.getPropertyPath().toString())).build())
            .map(GraphQLError.class::cast).toList();
    }
}
```
Spring applies method validation when a `jakarta.validation` Validator is present and the method/class has `@Validated`, or a parameter has `@Valid`/a constraint. It throws `ConstraintViolationException`, which **no built-in resolver maps** (it would otherwise become INTERNAL_ERROR) [S `data/method/annotation/support/ValidationHelper.java:62-88`; `AnnotatedControllerConfigurer.java:124-157`]. How constraint paths look with 2.0 flexible binding is [U].

## P6 — Subscription event bus [U Reactor semantics; S Spring side]
```java
@Service
class CustomerEvents {
    private final Sinks.Many<CustomerEvent> sink = Sinks.many().multicast().onBackpressureBuffer();
    private final Flux<CustomerEvent> live = sink.asFlux().cache(0);   // course's correction: share, no replay

    void publish(CustomerEvent e) {
        sink.emitNext(e, Sinks.EmitFailureHandler.busyLooping(Duration.ofMillis(50))); // don't drop on concurrent emit
    }
    Flux<CustomerEvent> stream() { return live; }
}

@SubscriptionMapping Flux<CustomerEvent> customerEvents() { return events.stream(); }   // SDL: customerEvents: CustomerEvent
// in the service, after the write succeeded (and after commit): .doOnNext(c -> events.publish(created(c)))
```
- Spring wraps the returned publisher per subscription and does not share it [S `execution/ReactiveAdapterRegistryHelper.java:89-104`]. Sharing, replay and lifetime are this class's job.
- What `cache(0)` protects against (sink auto-cancel when the last subscriber leaves) is [U]. `TESTS-TODO.md` T5 pins it; follow the test, not this comment.
- One JVM only. Multiple instances need a broker [U].
- Stream errors: implement `SubscriptionExceptionResolverAdapter.resolveToSingleError(Throwable)` [S `execution/SubscriptionExceptionResolverAdapter.java:116`].
- Auth for subscriptions: `connection_init` payload via `AuthenticationWebSocketInterceptor` + `BearerTokenAuthenticationExtractor` [S `server/webflux/AuthenticationWebSocketInterceptor.java`]. Bean wiring under Boot is [U].

## P7 — Client: typed call helper and error handling with 2.0.6 APIs [S]
```java
// graphql-documents/customer.graphql : every root field aliased "response"
// query ById($id: ID!) { response: customerById(id: $id) { id name } }

<T> Mono<T> call(String op, Map<String, Object> vars, ParameterizedTypeReference<T> type) {
    return client.documentName("customer").operationName(op).variables(vars)
                 .retrieve("response").toEntity(type);                 // throws on ANY error at/under path
}

Mono<Result<Customer>> byIdWithErrors(int id) {
    return client.documentName("customer").operationName("ById").variable("id", id).execute()
        .map(r -> {
            ClientResponseField f = r.field("response");
            Customer c = f.toEntity(Customer.class);   // non-null value decodes even with nested errors
            return c != null ? Result.ok(c, f.getErrors()) : Result.failed(f.getErrors());
        });                                          // null + errors → FieldAccessException: catch below
}
// callers: .onErrorResume(FieldAccessException.class, e -> Mono.just(Result.failed(e.getField().getErrors())))
```
- `ResponseField` has `getPath`, `getParsedPath`, `getValue`, `getErrors`. **There is no `hasValue()`/`getError()`** [S `ResponseField.java:39-95`]. `FieldAccessException.getResponse()/getField()` [S `client/FieldAccessException.java:62-69`]. Semantics table: ch08 [S `client/DefaultGraphQlClient.java:245-252`, `client/DefaultClientResponseField.java:89-107`].
- A wrong path or alias is **silent** (null / empty list): one test per operation.
- Blocking stack: `HttpSyncGraphQlClient.builder(restClientBuilder)` + `retrieveSync`/`executeSync`; use `configureMessageConverters`, not the deprecated `messageConverters` [S `client/HttpSyncGraphQlClient.java:64-128`].
- Per-request headers: a `GraphQlClientInterceptor` registered with `builder.interceptor(...)` [S `client/GraphQlClientInterceptor.java`].

## P8 — BFF downstream-error policy [S handler path; U WebClient exception types]
```java
@ControllerAdvice
class DownstreamErrors {
    @GraphQlExceptionHandler
    GraphQLError upstream(WebClientResponseException ex, DataFetchingEnvironment env) {
        ErrorType t = switch (ex.getStatusCode().value()) {
            case 404 -> ErrorType.NOT_FOUND;
            case 400, 422 -> ErrorType.BAD_REQUEST;
            case 401 -> ErrorType.UNAUTHORIZED;
            case 403 -> ErrorType.FORBIDDEN;
            default -> ErrorType.INTERNAL_ERROR;
        };
        String msg = t == ErrorType.INTERNAL_ERROR ? "Upstream failure" : ex.getStatusText();  // hide 5xx detail
        return GraphqlErrorBuilder.newError(env).errorType(t).message(msg)
            .extensions(Map.of("upstreamStatus", ex.getStatusCode().value())).build();
    }
}
// Domain outcomes only: client.add(input).map(ok).onErrorResume(DuplicateEntry.class, e -> Mono.just(failure()))
// Never a bare onErrorReturn(FAILURE): it hides 404, 5xx and timeouts alike.
```
Errors from a returned `Mono` reach the advice [S `…/support/AnnotatedControllerConfigurer.java:542-545`]. `WebClientResponseException` and timeouts are Spring Framework/Reactor types [U]. Make "not found" behave the same across all fields. If a nullable field must be null on 404, map it in the client (`onErrorResume(NotFound.class, e -> Mono.empty())`), not with a catch-all.

## P9 — Cross-service batching [S API; U not run]

| Upstream has… | Use |
|---|---|
| A bulk endpoint (`GET /movie?ids=…`) | `@BatchMapping` Map form on the parent type (P1): one call per request, whatever the number of parents |
| Only per-id endpoints | Registry loader with bounded fan-out; the key `Set` already deduplicates |
| Field arguments | Composite key + named loader (P2) |

```java
registry.forTypePair(Integer.class, Movie.class)                          // execution/BatchLoaderRegistry.java:65
    .withOptions(o -> o.setMaxBatchSize(100))                             // DataLoaderOptions [U: setter name in DataLoader 5]
    .registerMappedBatchLoader((ids, env) -> Flux.fromIterable(ids)
        .flatMap(movieClient::byId, 8)                                    // ≤ 8 concurrent upstream calls
        .collectMap(Movie::id));
@SchemaMapping(typeName = "UserProfile")
CompletableFuture<List<Movie>> watchList(Customer c, DataLoader<Integer, Movie> loader) {
    return loader.loadMany(c.watchList());
}
```
The acceptance test: `a: userProfile(id:1) { watchList {id} } b: userProfile(id:2) { watchList {id} }` → exactly **one** movie-service call (TESTS-TODO T9).

## P10 — Tester choice and error assertions [S]
```java
@Test void underAgeCreateIsBadRequest() {
    tester.mutate().header("caller-id", "test").build()                   // filter-protected endpoint
        .documentName("crud-operations").operationName("CreateCustomer")
        .variable("customer", Map.of("name", "kid", "age", 10)).execute()
        .errors().expect(e -> e.getErrorType() == ErrorType.BAD_REQUEST).verify()
        .path("response").valueIsNull();                                  // present-but-null, not pathDoesNotExist
}
@Test void eventArrives() {                                               // in-process, no socket
    Flux<CustomerEvent> events = graphQlTester.document("subscription { customerEvents { id action } }")
        .executeSubscription().toFlux("customerEvents", CustomerEvent.class);
    StepVerifier.create(events.take(1))
        .then(() -> service.delete(1).block())
        .assertNext(e -> assertThat(e.action()).isEqualTo(Action.DELETED))
        .verify(Duration.ofSeconds(5));
}
```
- Tester table: ch09. `HttpGraphQlTester` cannot subscribe [S `WebTestClientTransport.java:71-74`]; `ExecutionGraphQlServiceTester` and `WebGraphQlTester` can, in-process [S `AbstractDirectGraphQlTransport.java:57-67`].
- `path()` fails on unexpected errors [S `DefaultGraphQlTester.java:323-330`]. `expect` requires a match; `satisfy` accepts everything [S `DefaultGraphQlTester.java:285-291`].
- WebSocket tester: `RANDOM_PORT` + `@LocalServerPort`, `stop()` in `@AfterEach` [S `WebSocketGraphQlTester.java:42-48`].

## P11 — Type resolution for interfaces and unions [S]
The default `ClassNameTypeResolver` is already installed on every interface and union [S `execution/DefaultSchemaResourceGraphQlSourceBuilder.java:155-160`]. To use a `Dto` suffix everywhere, replace the default once (Boot customizer wiring is [U]):
```java
@Bean GraphQlSourceBuilderCustomizer typeResolution() {                   // Boot type [U]
    ClassNameTypeResolver r = new ClassNameTypeResolver();
    r.setClassNameExtractor(c -> c.getSimpleName().replaceFirst("Dto$", ""));   // ClassNameTypeResolver.java:54
    return b -> b.defaultTypeResolver(r);                                  // GraphQlSource.java:215
}
```
For a few exceptions use `r.addMapping(FruitDto.class, "Fruit")`; explicit mappings also feed schema inspection [S `DefaultSchemaResourceGraphQlSourceBuilder.java:233-238`]. Never write a resolver with a catch-all `else`.

## P12 — Bounded document cache [U graphql-java 25 signature]
```java
@Bean GraphQlSourceBuilderCustomizer docCache() {                         // Boot type [U]
    Cache<String, PreparsedDocumentEntry> cache = Caffeine.newBuilder().maximumSize(10_000).build();
    PreparsedDocumentProvider p = (input, parseAndValidate) ->            // check: sync vs async method in GJ 25
        cache.get(input.getQuery(), k -> parseAndValidate.apply(input));
    return b -> b.configureGraphQl(g -> g.preparsedDocumentProvider(p));  // GraphQlSource.java:150 [S]
}
```
This only helps with static documents and variables. The key is the document text; the operation name is not part of it.

## P13 — Header → context → handler; reject in a filter [S]
```java
@Component class CallerId implements WebGraphQlInterceptor {
    public Mono<WebGraphQlResponse> intercept(WebGraphQlRequest req, Chain chain) {
        String id = Objects.requireNonNullElse(req.getHeaders().getFirst("caller-id"), "");
        req.configureExecutionInput((in, b) -> b.graphQLContext(Map.of("caller-id", id)).build());
        return chain.next(req);
    }
}
@QueryMapping Flux<Customer> customers(@ContextValue(name = "caller-id", required = false) String caller) { … }
```
Reject with a `WebFilter` scoped to the GraphQL path only, and set a status [U: WebFlux]. For subscriptions, check in `WebSocketGraphQlInterceptor` at connection init, not in the filter, which sees only the handshake [U].
