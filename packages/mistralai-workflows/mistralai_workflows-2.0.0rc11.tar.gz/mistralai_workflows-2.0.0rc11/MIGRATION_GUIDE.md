# Migrating from v1.0 to v2.0

## Class Renaming

The following classes have been renamed:

```
AbraxasClient -> WorkflowsClient
InternalAbraxasConcurrencyWorkflow -> InternalConcurrencyWorkflow
AbraxasWorkflowError -> WorkflowError
AbraxasActivityError -> ActivityError
AbraxasWorkflowOutboundInterceptor -> WorkflowContextWorkflowOutboundInterceptor
AbraxasWorkflowInboundInterceptor -> WorkflowContextWorkflowInboundInterceptor
AbraxasActivityInboundInterceptor -> WorkflowContextActivityInboundInterceptor
AbraxasTemporalWorkerCodec -> MistralWorkflowsPayloadCodec
AbraxasWorkerJSONPayloadConverter -> WithContextJSONPayloadConverter
AbraxasWorkerPayloadConverter -> MistralWorkflowsPayloadConverter
```

## Deprecated fields

The `activity_name` field of the `@activity` decorator has been deprecated and replaced by `name`:

❌ `@activity(activity_name="my-activity")`

✅ `@activity(name="my-activity)`

## Environment configuration

- `ABRAXAS_ENDPOINT` has been removed:

It used to control several other env variables:

1. `SERVER_URL` was set to `https://api.{ABRAXAS_ENDPOINT}`. You should set this URL directly now.
2. `OTEL_ENDPOINT` was set to `https://api.{ABRAXAS_ENDPOINT}/api/otel`. Set it directly if you want to specify the URL of the OpenTelemetry collector.
3. For local development only, `TEMPORAL_SERVER_URL` was set to `https://front.{ABRAXAS_ENDPOINT}:443`. Set it directly if you want to specify the URL of the Temporal server.
4. `OTEL_ENABLED` was set to True when this env variable was set. You should now set it explicitely

- `ABRAXAS_BASE_URL` has been removed. Use `SERVER_URL` instead.
- `ABRAXAS_API_VERSION` has been renamed to `API_VERSION`
- `ABRAXAS_ALLOW_OVERRIDE_NAMESPACE` has been renamed to `ALLOW_OVERRIDE_NAMESPACE`
- `ABRAXAS_ENABLE_CONFIG_DISCOVERY` has been renamed to `ENABLE_CONFIG_DISCOVERY`
- `ABRAXAS_API_HEADERS` has been renamed to `MISTRAL_API_HEADERS`
- `ABRAXAS_CA_BUNDLE`has been renamed to `CA_BUNDLE`
- `ABRAXAS_API_KEY` has been renamed to `MISTRAL_API_KEY`

## Task Context Manager Breaking Changes ⚠️

### Task Context Manager Is Now Async

The task context manager is now **fully async**.

**Migration Required:**
- Change all `with task(...)` to `async with task(...)`
- Change all `t.set_state()` calls to `await t.set_state()`
- Change all `t.update_state()` calls to `await t.update_state()`

```python
# ❌ OLD (synchronous)
with workflows.task("processing", state={"progress": 0}) as t:
    t.set_state({"progress": 50})
    t.set_state({"progress": 100})

# ✅ NEW (async)
async with workflows.task("processing", state={"progress": 0}) as t:
    await t.set_state({"progress": 50})
    await t.set_state({"progress": 100})
```
