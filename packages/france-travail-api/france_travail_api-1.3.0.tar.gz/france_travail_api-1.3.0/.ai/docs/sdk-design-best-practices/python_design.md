## Introduction

### Design principles

The Azure SDK should be designed to enhance the productivity of developers connecting to Azure services. Other qualities (such as completeness, extensibility, and performance) are important but secondary. Productivity is achieved by adhering to the principles described below:azu

#### Idiomatic

- The SDK should follow the design guidelines and conventions for the target language. It should feel natural to a developer in the target language.
- We embrace the ecosystem with its strengths and its flaws.
- We work with the ecosystem to improve it for all developers.

#### Consistent

- Client libraries should be consistent within the language, consistent with the service and consistent between all target languages. In cases of conflict, consistency within the language is the highest priority and consistency between all target languages is the lowest priority.
- Service-agnostic concepts such as logging, HTTP communication, and error handling should be consistent. The developer should not have to relearn service-agnostic concepts as they move between client libraries.
- Consistency of terminology between the client library and the service is a good thing that aids in diagnosability.
- All differences between the service and client library must have a good (articulated) reason for existing, rooted in idiomatic usage rather than whim.
- The Azure SDK for each target language feels like a single product developed by a single team.
- There should be feature parity across target languages. This is more important than feature parity with the service.

#### Approachable

- We are experts in the supported technologies so our customers, the developers, don’t have to be.
- Developers should find great documentation (hero tutorial, how to articles, samples, and API documentation) that makes it easy to be successful with the Azure service.
- Getting off the ground should be easy through the use of predictable defaults that implement best practices. Think about progressive concept disclosure.
- The SDK should be easily acquired through the most normal mechanisms in the target language and ecosystem.
- Developers can be overwhelmed when learning new service concepts. The core use cases should be discoverable.

#### Diagnosable

- The developer should be able to understand what is going on.
- It should be discoverable when and under what circumstances a network call is made.
- Defaults are discoverable and their intent is clear.
- Logging, tracing, and exception handling are fundamental and should be thoughtful.
- Error messages should be concise, correlated with the service, actionable, and human readable. Ideally, the error message should lead the consumer to a useful action that they can take.
- Integrating with the preferred debugger for the target language should be easy.

#### Dependable

- Breaking changes are more harmful to a user’s experience than most new features and improvements are beneficial.
- Incompatibilities should never be introduced deliberately without thorough review and very strong justification.
- Do not rely on dependencies that can force our hand on compatibility.

### General guidelines

The API surface of your client library must have the most thought as it is the primary interaction that the consumer has with your service.

✅ **DO** support 100% of the features provided by the Azure service the client library represents. Gaps in functionality cause confusion and frustration among developers.

### Non-HTTP based services

These guidelines were written primarily with a HTTP based request/response in mind, but many general guidelines apply to other types of services as well. This includes, but is not limited to, packaging and naming, tools and project structures.

Please contact the Architecture board for more guidance on non HTTP/REST based services.

### Supported python versions

✅ **DO** support Python 3.10+.

## Azure SDK API Design

Your API surface will consist of one or more *service clients* that the consumer will instantiate to connect to your service, plus a set of supporting types.

### Service client

The service client is the primary entry point for users of the library. A service client exposes one or more methods that allow them to interact with the service.

✅ **DO** expose the service clients the user is more likely to interact with from the root namespace of your package. Specialized service clients may be placed in sub-namespaces.

✅ **DO** name service client types with a **Client** suffix.

✅ **DO** provide separate sync and async clients. See the Async Support section for more information.

```
# Yes
class CosmosClient: ...
# No
class CosmosProxy: ...
# No
class CosmosUrl: ...
```


✅ **DO** make the service client immutable. See the Client Immutability section for more information.

#### Constructors and factory methods

Only the minimal information needed to connect and interact with the service should be required in order to construct a client instance. All additional information should be optional and passed in as optional keyword-only arguments.

##### Client configuration

✅ **DO** provide a constructor that takes positional binding parameters (for example, the name of, or a URL pointing to the service instance), a positional `credential`

parameter, a `transport`

keyword-only parameter, and keyword-only arguments for passing settings through to individual HTTP pipeline policies. See the Authentication section for more information on the `credential`

parameter.

⛔️ **DO NOT** use an “options bag” object to group optional parameters. Instead, pass as individual keyword-only arguments.

✅ **DO** accept optional default request options as keyword arguments and pass them along to its pipeline policies. See Common service operation parameters for more information.

```
# Change default number of retries to 18 and overall timeout to 2s.
client = ExampleClient('https://contoso.com/xmpl',
DefaultAzureCredential(),
max_retries=18,
timeout=2)
```


✅ **DO** allow users to pass in a `transport`

keyword-only argument that allows the caller to specify a specific transport instance. The default value should be the `RequestsTransport`

for synchronous clients and the `AioHttpTransport`

for async clients.

✅ **DO** use a separate factory classmethod `from_connection_string`

to create a client from a connection string (if the client supports connection strings). The `from_connection_string`

factory method should take the same set of arguments (excluding information provided in the connection string) as the constructor. The constructor (`__init__`

method) **must not** take a connection string, even if it means that using the `from_connection_string`

is the only supported method to create an instance of the client.

The method **should** parse the connection string and pass the values along with any additional keyword-only arguments except `credential`

to the constructor. Only provide a `from_connection_string`

factory method if the Azure portal exposes a connection string for your service.

```
class ExampleClientWithConnectionString:
@classmethod
def _parse_connection_string(cls, connection_string): ...
@classmethod
def from_connection_string(cls, connection_string, **kwargs):
endpoint, credential = cls._parse_connection_string(connection_string)
return cls(endpoint, credential, **kwargs)
```


```
"""Example client using some of the most common API patterns
"""
import models
import azure.core.pipeline.transport as transports
class Thing:
"""A simple model type representing a Thing.
:ivar name: The name of the thing.
:vartype name: str
:ivar size: The size of the thing.
:vartype size: int
"""
def __init__(self, name: str, size: int) -> None:
"""Create a new Thing
:param name: The name of the thing
:type name: str
:param size: The size of the thing
:type size: int
"""
# Please note that we are using attributes rather than properties.
self.name = name
self.size = size
@classmethod
def from_response(self, response: "azure.core.rest.HttpResponse") -> "Thing":
"""Factory method to, given a response, construct a ~Thing
"""
return Thing(**response.context['deserialized_data'])
def __repr__(self):
# For simple model types, we can just dump our __dict__ and
# truncate the output at 1024 characters.
return json.dumps(self.__dict__)[:1024]
class ExampleClient:
def __init__(self, endpoint: str, credential: "azure.core.credentials.TokenCredential", **kwargs) -> None:
"""Create a new example client instance
:param endpoint: Endpoint to connect to.
:type endpoint str:
:param credential: Credentials to use when connecting to the service.
:type credential: ~azure.core.credentials.TokenCredential
:keyword api_version: API version to use when talking to the service. Default is '2020-12-31'
:paramtype api_version: str
:keyword transport: HttpTransport to use. Default is ~transports.RequestsHttpTransport.
:paramtype transport: ~azure.core.pipeline.transport.HttpTransport
"""
self._api_version = kwargs.pop('api_version', '2020-12-31')
transport = kwargs.pop('transport', None) or transports.RequestsTransport(**kwargs)
# continue to build up your client...
self._pipeline = [
..., # List of policies for this specific client
transport
]
@classmethod
def from_connection_string(cls, connection_string: str, **kwargs) -> "Thing":
"""Optional factory method if the service supports connection strings
:param connection_string: Connection string containing endpoint and credentials
:type connection_string: str
:returns: The newly created client.
:rtype: ~ExampleClient
"""
endpoint, credential = _parse(connection_string)
return cls(endpoint, credential, **kwargs)
def get_thing(self, name: str, **kwargs) -> "Thing":
"""Get the Thing with name `name`.
:param name: The name of the ~Thing to get
:type name: str
:rtype: ~Thing
"""
model_factory = kwargs.pop('cls', Thing.from_response)
request = self._build_get_thing_request(name)
# Pass along all policy parameters when making the request
response = self._pipeline.send(request, **kwargs)
return model_factory(response)
def list_things(self, **kwargs) -> "azure.core.paging.ItemPaged[Thing]":
"""List all things.
:rtype: ~azure.core.ItemPaged[~Thing]
"""
...
return azure.core.paging.ItemPaged(...)
def begin_restart_thing(self, name: str, **kwargs) -> "azure.core.polling.LROPoller[bool]":
"""Restart the thing
:param name: The name of the thing to restart
:type name: str
"""
model = kwargs.pop('cls', dict)
request = self._build_begin_restart_thing(name)
# Pass along all policy parameters when making the request
response = self._pipeline.send(request, **kwargs)
# TODO: show how to construct the poller instance
return azure.core.polling.LROPoller(...)
```


✔️ **YOU MAY** use a separate factory classmethod `from_<resource type>_url`

(e.g. `from_blob_url`

) to create a client from a URL (if the service relies on passing URLs to resources around - e.g. Azure Blob Storage). The `from_url`

factory method should take the same set of optional keyword arguments as the constructor.

##### Specifying the Service Version

✅ **DO** accept an optional `api_version`

keyword-only argument of type string. If specified, the provided api version MUST be used when interacting with the service. If the parameter is not provided, the default value MUST be the latest non-preview API version understood by the client library (if there the service has a non-preview version) or the latest preview API version understood by the client library (if the service does not have any non-preview API versions yet). This parameter MUST be available even if there is only one API version understood by the service in order to allow library developers to lock down the API version they expect to interact with the service with.

```
from azure.identity import DefaultAzureCredential
# By default, use the latest supported API version
latest_known_version_client = ExampleClient('https://contoso.com/xmpl',
DefaultAzureCredential())
# ...but allow the caller to specify a specific API version as welll
specific_api_version_client = ExampleClient('https://contoso.com/xmpl',
DefaultAzureCredential(),
api_version='1971-11-01')
```


✅ **DO** document the service API version that is used by default.

✅ **DO** document in which API version a feature (function or parameter) was introduced in if not all service API versions support it.

✔️ **YOU MAY** validate the input `api_version`

value against a list of supported API versions.

✔️ **YOU MAY** include all service API versions that are supported by the client library in a `ServiceVersion`

enumerated value.

##### Additional constructor parameters

| Name | Description |
|---|---|
`credential` |
Credentials to use when making service requests (See Authentication) |
`application_id` |
Name of the client application making the request. Used for telemetry |
`api_version` |
API version to use when making service requests (See Service Version) |
`transport` |
Override the default HTTP transport (See Client Configuration) |

##### Client immutability

✅ **DO** design the client to be immutable. This does not mean that you need to use read-only properties (attributes are still acceptable), but rather that the there should not be any scenarios that require callers to change properties/attributes of the client.

#### Service methods

##### Naming

☑️ **YOU SHOULD** prefer the usage one of the preferred verbs for method names. You should have a good (articulated) reason to have an alternate verb for one of these operations.

| Verb | Parameters | Returns | Comments |
|---|---|---|---|
`create_\<noun>` |
key, item, `[allow_overwrite=False]` |
Created item | Create new item. Fails if item already exists. |
`upsert_\<noun>` |
key, item | item | Create new item, or update existing item. Verb is primarily used in database-like services |
`set_\<noun>` |
key, item | item | Create new item, or update existing item. Verb is primarily used for dictionary-like properties of a service |
`update_\<noun>` |
key, partial item | item | Fails if item doesn’t exist. |
`replace_\<noun>` |
key, item | item | Completely replaces an existing item. Fails if the item doesn’t exist. |
`append_\<noun>` |
item | item | Add item to a collection. Item will be added last. |
`add_\<noun>` |
index, item | item | Add item to a collection. Item will be added at the given index. |
`get_\<noun>` |
key | item | Raises an exception if item doesn’t exist |
`list_\<noun>` |
`azure.core.ItemPaged[Item]` |
Return an iterable of `Item` s. Returns an iterable with no items if no items exist (doesn’t return `None` or throw) |
|
`\<noun>\_exists` |
key | `bool` |
Return `True` if the item exists. Must raise an exception if the method failed to determine if the item exists (for example, the service returned an HTTP 503 response) |
`delete_\<noun>` |
key | `None` |
Delete an existing item. Must succeed even if item didn’t exist. |
`remove_\<noun>` |
key | removed item or `None` |
Remove a reference to an item from a collection. This method doesn’t delete the actual item, only the reference. |

✅ **DO** standardize verb prefixes outside the list of preferred verbs for a given service across language SDKs. If a verb is called `download`

in one language, we should avoid naming it `fetch`

in another.

✅ **DO** prefix methods with `begin_`

for long running operations.

✅ **DO** prefix methods with `list_`

for methods that enumerate (lists) resources

##### Return types

Requests to the service fall into two basic groups - methods that make a single logical request, or a deterministic sequence of requests. An example of a single logical request is a request that may be retried inside the operation. An example of a deterministic sequence of requests is a paged operation.

The logical entity is a protocol neutral representation of a response. For HTTP, the logical entity may combine data from headers, body, and the status line. For example, you may wish to expose an `ETag`

header as an `etag`

attribute on the logical entity. For more information see Model Types.

✅ **DO** optimize for returning the logical entity for a given request. The logical entity MUST represent the information needed in the 99%+ case.

✅ **DO** raise an exception if the method call failed to accomplish the user specified task. This includes both situations where the service actively responded with a failure as well as when no response was received. See Exceptions for more information.

```
client = ComputeClient(...)
try:
# Please note that there is no status code etc. as part of the response.
# If the call fails, you will get an exception that will include the status code
# (if the request was made)
virtual_machine = client.get_virtual_machine('example')
print(f'Virtual machine instance looks like this: {virtual_machine}')
except azure.core.exceptions.ServiceRequestError as e:
print(f'Failed to make the request - feel free to retry. But the specifics are here: {e}')
except azure.core.exceptions.ServiceResponseError as e:
print(f'The request was made, but the service responded with an error. Status code: {e.status_code}')
```


Do not return `None`

or a `boolean`

to indicate errors:

```
# Yes
try:
resource = client.create_resource(name)
except azure.core.errors.ResourceExistsException:
print('Failed - we need to fix this!')
# No
resource = client.create_resource(name):
if not resource:
print('Failed - we need to fix this!')
```


⛔️ **DO NOT** throw an exception for “normal responses”.

Consider an `exists`

method. The method **must** distinguish between the service returned a client error 404/NotFound and a failure to even make a request:

```
# Yes
try:
exists = client.resource_exists(name):
if not exists:
print("The resource doesn't exist...")
except azure.core.errors.ServiceRequestError:
print("We don't know if the resource exists - so it was appropriate to throw an exception!")
# No
try:
client.resource_exists(name)
except azure.core.errors.ResourceNotFoundException:
print("The resource doesn't exist... but that shouldn't be an exceptional case for an 'exists' method")
```


##### Cancellation

✅ **DO** provide an optional keyword argument `timeout`

to allow callers to specify how long they are willing to wait for the method to complete. The `timeout`

is in seconds, and should be honored to the best extent possible.

✅ **DO** use the standard asyncio.Task.cancel method to cancel async methods.

#### Service Method Parameters

✅ **DO** provide optional operation-specific arguments as keyword only. See positional and keyword-only arguments for more information.

✅ **DO** provide keyword-only arguments that override per-request policy options. The name of the parameters MUST mirror the name of the arguments provided in the client constructor or factory methods.
For a full list of supported optional arguments used for pipeline policy and transport configuration (both at the client constructor and per service operation), see the Azure Core developer documentation.

✅ **DO** qualify a service parameter name if it conflicts with any of the documented pipeline policy or transport configuration options used with all service operations and client constructors.

```
# Set the default number of retries to 18 and timeout to 2s for this client instance.
client = ExampleClient('https://contoso.com/xmpl', DefaultAzureCredential(), max_retries=18, timeout=2)
# Override the client default timeout for this specific call to 32s (but max_retries is kept to 18)
client.do_stuff(timeout=32)
```


##### Parameter validation

The service client will have several methods that send requests to the service. **Service parameters** are directly passed across the wire to an Azure service. **Client parameters** aren’t passed directly to the service, but used within the client library to fulfill the request. Parameters that are used to construct a URI, or a file to be uploaded are examples of client parameters.

✅ **DO** validate client parameters. Validation is especially important for parameters used to build up the URL since a malformed URL means that the client library will end up calling an incorrect endpoint.

```
# No:
def get_thing(name: str) -> str:
url = f'https://<host>/things/{name}'
return requests.get(url).json()
try:
thing = get_thing('') # Ooops - we will end up calling '/things/' which usually lists 'things'. We wanted a specific 'thing'.
except ValueError:
print('We called with some invalid parameters. We should fix that.')
# Yes:
def get_thing(name: str) -> str:
if not name:
raise ValueError('name must be a non-empty string')
url = f'https://<host>/things/{name}'
return requests.get(url).json()
try:
thing = get_thing('')
except ValueError:
print('We called with some invalid parameters. We should fix that.')
```


⛔️ **DO NOT** validate service parameters. Don’t do null checks, empty string checks, or other common validating conditions on service parameters. Let the service validate all request parameters.

✅ **DO** verify that the developer experience when the service parameters are invalid to ensure appropriate error messages are generated by the service. Work with the service team if the developer experience is compromised because of service-side error messages.

##### Common service operation parameters

✅ **DO** support the common arguments for service operations:

| Name | Description | Applies to | Notes | |
|---|---|---|---|---|
`timeout` |
Timeout in seconds | All service methods | ||
`headers` |
Custom headers to include in the service request | All requests | Headers are added to all requests made (directly or indirectly) by the method. | |
`client_request_id` |
Caller specified identification of the request. | Service operations for services that allow the client to send a client-generated correlation ID. | Examples of this include `x-ms-client-request-id` headers. |
The client library must use this value if provided, or generate a unique value for each request when not specified. |
`response_hook` |
`callable` that is called with (response, headers) for each operation. |
All service methods |

✅ **DO** accept a Mapping (`dict`

-like) object in the same shape as a serialized model object for parameters.

```
# Yes:
class Thing:
def __init__(self, name, size):
self.name = name
self.size = size
def do_something(thing: "Thing"):
...
do_something(Thing(name='a', size=17)) # Works
do_something({'name': 'a', 'size', '17'}) # Does the same thing...
```


✅ **DO** use “flattened” named arguments for `update_`

methods. **May** additionally take the whole model instance as a named parameter. If the caller passes both a model instance and individual key=value parameters, the explicit key=value parameters override whatever was specified in the model instance.

```
class Thing:
def __init__(self, name, size, description):
self.name = name
self.size = size
self.description = description
def __repr__(self):
return json.dumps({
"name": self.name, "size": self.size, "description": self.description
})[:1024]
class Client:
def update_thing(self, name=None, size=None, thing=None): ...
thing = Thing(name='hello', size=4711, description='This is a description...')
client.update_thing(thing=thing, size=4712) # Will send a request to the service to update the model's size to 4712
thing.description = 'Updated'
thing.size = -1
# Will send a request to the service to update the model's size to 4713 and description to 'Updated'
client.update_thing(name='hello', size=4713, thing=thing)
```


#### Methods returning collections (paging)

Services may require multiple requests to retrieve the complete set of items in large collections. This is generally done by the service returning a partial result, and in the response providing a token or link that the client can use to retrieve the next batch of responses in addition to the set of items.

In Azure SDK for Python cilent libraries, this is exposed to users through the ItemPaged protocol. The `ItemPaged`

protocol optimizes for retrieving the full set of items rather than forcing users to deal with the underlying paging.

✅ **DO** return a value that implements the ItemPaged protocol for operations that return collections. The ItemPaged protocol allows the user to iterate through all items in a returned collection, and also provides a method that gives access to individual pages.

```
client = ExampleClient(...)
# List all things - paging happens transparently in the
# background.
for thing in client.list_things():
print(thing)
# The protocol also allows you to list things by page...
for page_no, page in enumerate(client.list_things().by_page()):
print(page_no, page)
```


✔️ **YOU MAY** expose a `results_per_page`

keyword-only parameter where supported by the service (e.g. an OData `$top`

query parameter).

⚠️ **YOU SHOULD NOT** expose a continuation parameter in the `list_`

client method - this is supported in the `by_page()`

function.

```
client = ExampleClient(...)
# No - don't pass in the continuation token directly to the method...
for thing in client.list_things(continuation_token='...'):
print(thing)
# Yes - provide a continuation_token to in the `by_page` method...
for page in client.list_things().by_page(continuation_token='...'):
print(page)
```


✅ **DO** return a value that implements the ItemPaged protocol even if the service API currently do not support server driven paging. This allows server driven paging to be added to the service API without introducing breaking changes in the client library.

#### Methods invoking long running operations

Service operations that take a long time (currently defined in the Microsoft REST API Guidelines as not completing in 0.5s in P99) to complete are modeled by services as long running operations.

Python client libraries abstracts the long running operation using the Long running operation Poller protocol. In cases where a service API is not explicitly implemented as a long-running operation, but the common usage pattern requires a customer to sleep or poll a status - it’s likely that these API’s should still be represented in the SDK using the Poller protocol.

✅ **DO** return an object that implements the Poller protocol for long running operations.

✅ **DO** use a `begin_`

prefix for all long running operations.

#### Conditional request methods

✅ **DO** add a keyword-only `match_condition`

parameter for service methods that support conditional requests. The parameter should support the `azure.core.MatchConditions`

type defined in `azure-core`

as input.

✅ **DO** add a keyword-only `etag`

parameter for service methods that support conditional requests. For service methods that take a model instance that has an `etag`

property, the explicit `etag`

value passed in overrides the value in the model instance.

```
class Thing:
def __init__(self, name, etag):
self.name = name
self.etag = etag
thing = client.get_thing('theName')
# Uses the etag from the retrieved thing instance....
client.update_thing(thing, name='updatedName', match_condition=azure.core.MatchConditions.IfNotModified)
# Uses the explicitly provided etag.
client.update_thing(thing, name='updatedName2', match_condition=azure.core.MatchConditions.IfNotModified, etag='"igotthisetagfromsomewhereelse"')
```


#### Hierarchical clients

Many services have resources with nested child (or sub) resources. For example, Azure Storage provides an account that contains zero or more containers, which in turn contains zero or more blobs.

✅ **DO** create a client type corresponding to each level in the hierarchy except for leaf resource types. You **may** omit creating a client type for leaf node resources.

✅ **DO** make it possible to directly create clients for each level in the hierarchy. The constructor can be called directly or via the parent.

```
class ChildClient:
# Yes:
__init__(self, parent, name, credentials, **kwargs) ...
class ChildClient:
# Yes:
__init__(self, url, credentials, **kwargs) ...
```


✅ **DO** provide a `get_<child>_client(self, name, **kwargs)`

method to retrieve a client for the named child. The method must not make a network call to verify the existence of the child.

✅ **DO** provide method `create_<child>(...)`

that creates a child resource. The method **should** return a client for the newly created child resource.

☑️ **YOU SHOULD** provide method `delete_<child>(...)`

that deletes a child resource.

### Supporting types

#### Model types

Client libraries represent entities transferred to and from Azure services as model types. Certain types are used for round-trips to the service. They can be sent to the service (as an addition or update operation) and retrieved from the service (as a get operation). These should be named according to the type. For example, a `ConfigurationSetting`

in App Configuration, or a `VirtualMachine`

on for Azure Resource Manager.

Data within the model type can generally be split into two parts - data used to support one of the champion scenarios for the service, and less important data. Given a type `Foo`

, the less important details can be gathered in a type called `FooDetails`

and attached to `Foo`

as the `details`

attribute.

✅ **DO** support dicts as alternative inputs to model types.

✅ **DO** craft a constructor for models that are intended to be instantiated by a user (i.e. non-result types) with minimal required information and optional information as keyword-only arguments.

✔️ **YOU MAY** expose models from the generated layer by adding to the root `__init__.py`

(and `__all__`

) if they otherwise meet the guidelines.

⛔️ **DO NOT** duplicate models between the root and `aio`

namespace.

In order to facilitate round-trip of responses (common in get resource -> conditionally modify resource -> set resource workflows), output model types should use the input model type (e.g. `ConfigurationSetting`

) whenever possible. The `ConfigurationSetting`

type should include both server generated (read-only) attributes even though they will be ignored when used as input to the set resource method.

`<model>Item`

for each item in an enumeration if the enumeration returns a partial schema for the model. For example, GetBlobs() return an enumeration of BlobItem, which contains the blob name and metadata, but not the content of the blob.`<operation>Result`

for the result of an operation. The`<operation>`

is tied to a specific service operation. If the same result can be used for multiple operations, use a suitable noun-verb phrase instead. For example, use`UploadBlobResult`

for the result from`UploadBlob`

, but`ContainerChangeResult`

for results from the various methods that change a blob container.

✅ **DO** use a simple Mapping (e.g. `dict`

) rather than creating a `<operation>Result`

class if the `<operation>Result`

class is not used as an input parameter for other APIs.

The following table enumerates the various models you might create:

| Type | Example | Usage |
|---|---|---|
| Secret | The full data for a resource | |
| SecretDetails | Less important details about a resource. Attached to |
|
| SecretItem | A partial set of data returned for enumeration | |
| AddSecretResult | A partial or different set of data for a single operation | |
| SecretChangeResult | A partial or different set of data for multiple operations on a model |

```
# An example of a model type.
class ConfigurationSetting:
"""Model type representing a configuration setting
:ivar name: The name of the setting
:vartype name: str
:ivar value: The value of the setting
:vartype value: object
"""
def __init__(self, name: str, value: object):
self.name = name
self.value = value
def __repr__(self) -> str:
return json.dumps(self.__dict__)[:1024]
```


#### Enumerations

✅ **DO** use extensible enumerations.

✅ **DO** use UPPERCASE names for enum names.

```
# Yes
class MyGoodEnum(str, Enum):
ONE = 'one'
TWO = 'two'
# No
class MyBadEnum(str, Enum):
One = 'one' # No - using PascalCased name.
two = 'two' # No - using all lower case name.
```


### Exceptions

☑️ **YOU SHOULD** prefer raising existing exception types from the `azure-core`

package over creating new exception types.

⛔️ **DO NOT** create new exception types when a built-in exception type will suffice.

⚠️ **YOU SHOULD NOT** create a new exception type unless the developer can handle the error programmatically. Specialized exception types related to service operation failures should be based on existing exception types from the `azure-core`

package.

For higher-level methods that use multiple HTTP requests, either the last exception or an aggregate exception of all failures should be produced.

✅ **DO** include any service-specific error information in the exception. Service-specific error information must be available in service-specific properties or fields.

✅ **DO** document the errors that are produced by each method. Don’t document commonly thrown errors that wouldn’t normally be documented in Python (e.g. `ValueError`

, `TypeError`

, `RuntimeError`

etc.)

### Authentication

✅ **DO** use the credentials classes in `azure-core`

whenever possible.

✅ **DO** use authentication policy implementations in `azure-core`

whenever possible.

✔️ **YOU MAY** add additional credential types if required by the service. Contact the Architecture board for guidance if you believe you have need to do so.

✅ **DO** support all authentication methods that the service supports.

### Namespaces

In the guidelines below, the term “namespace” is used to denote a python package or module (i.e. something that you would `import`

in your code). The term “distribution package” is used to describe the artifact you publish to and install from your package manager (i.e. something that you would `pip install`

).

✅ **DO** implement your library as a sub-package of the `azure`

root namespace.

Note: You MUST NOT use

`microsoft`

as your root namespace. If you need to include`microsoft`

in the namespace (e.g. because of policy requirements for extensions to other projects such as`opentelemetry`

), you should concatenate it with the package specific namespace with an underscore (e.g.`microsoft_myservice`

). You may still use`microsoft-myservice`

as the distribution package name in this scenario.

✅ **DO** pick a package name that allows the consumer to tie the namespace to the service being used. As a default, use the compressed service name at the end of the namespace. The namespace does NOT change when the branding of the product changes. Avoid the use of marketing names that may change.

A compressed service name is the service name without spaces. It may further be shortened if the shortened version is well known in the community. For example, “Azure Media Analytics” would have a compressed service name of `mediaanalytics`

, and “Azure Service Bus” would become `servicebus`

. Separate words using an underscore if necessary. For example, `mediaanalytics`

could be separated into `media_analytics`


✔️ **YOU MAY** include a group name segment in your namespace (for example, `azure.<group>.<servicename>`

) if your service or family of services have common behavior (for example, shared authentication types).

✅ **DO** avoid introducing new distribution packages that only differ in name. For existing packages, this means that you should not change the name of the package just to introduce a group name.

If you want to use a group name segment, use one of the following groups:

| Namespace Group | Functional Area |
|---|---|
`ai` |
Artificial intelligence, including machine learning |
`analytics` |
Gathering data for metrics or usage |
`containers` |
Services related to containers |
`communication` |
Communication services |
`data` |
Dealing with structured data stores like databases |
`diagnostics` |
Gathering data for diagnosing issues |
`digitaltwins` |
Digital Twins, digital representations of physical spaces and IoT devices |
`identity` |
Authentication and authorization |
`iot` |
Internet of things |
`management` |
Control Plane (Azure Resource Manager) |
`media` |
Audio and video technologies |
`messaging` |
Messaging services, like push notifications or pub-sub |
`mixedreality` |
Mixed reality technologies |
`monitor` |
Services that are offered by Azure Monitor |
`quantum` |
Quantum computing technologies |
`search` |
Search technologies |
`security` |
Security and cryptography |
`storage` |
Storage of unstructured data |

✅ **DO** place management (Azure Resource Manager) APIs in the `mgmt`

group. Use the grouping `azure.mgmt.<servicename>`

for the namespace. Since more services require control plane APIs than data plane APIs, other namespaces may be used explicitly for control plane only.

✅ **DO** register the chosen namespace with the Architecture Board. Open an issue to request the namespace. See the registered namespace list for a list of the currently registered namespaces.

✅ **DO** use an `.aio`

suffix added to the namespace of the sync client for async clients.

Example:

```
# Yes:
from azure.exampleservice.aio import ExampleServiceClient
# No: Wrong namespace, wrong client name...
from azure.exampleservice import AsyncExampleServiceClient
```


#### Example Namespaces

Here are some examples of namespaces that meet these guidelines:

`azure.storage.blob`

`azure.keyvault.certificates`

`azure.ai.textanalytics`

`azure.mgmt.servicebus`


### Async support

The `asyncio`

library has been available since Python 3.4, and the `async`

/`await`

keywords were introduced in Python 3.5. Despite such availability, most Python developers aren’t familiar with or comfortable using libraries that only provide asynchronous methods.

✅ **DO** provide both sync and async versions of your APIs

✅ **DO** use the `async`

/`await`

keywords (requires Python 3.5+). Do not use the yield from coroutine or asyncio.coroutine syntax.

✅ **DO** provide two separate client classes for synchronous and asynchronous operations. Do not combine async and sync operations in the same class.

```
# Yes
# In module azure.example
class ExampleClient:
def some_service_operation(self, name, size) ...
# In module azure.example.aio
class ExampleClient:
# Same method name as sync, different client
async def some_service_operation(self, name, size) ...
# No
# In module azure.example
class ExampleClient:
def some_service_operation(self, name, size) ...
class AsyncExampleClient: # No async/async pre/postfix.
async def some_service_operation(self, name, size) ...
# No
# In module azure.example
class ExampleClient: # Don't mix'n match with different method names
def some_service_operation(self, name, size) ...
async def some_service_operation_async(self, name, size) ...
```


✅ **DO** use the same client name for sync and async packages

Example:

| Sync/async | Namespace | Distribution package name | Client name |
|---|---|---|---|
| Sync | `azure.sampleservice` |
`azure-sampleservice` |
`azure.sampleservice.SampleServiceClient` |
| Async | `azure.sampleservice.aio` |
`azure-sampleservice-aio` |
`azure.sampleservice.aio.SampleServiceClient` |

✅ **DO** use the same namespace for the synchronous client as the synchronous version of the package with `.aio`

appended.

Example:

```
from azure.storage.blob import BlobServiceClient # Sync client
from azure.storage.blob.aio import BlobServiceClient # Async client
```


☑️ **YOU SHOULD** ship a separate package for async support if the async version requires additional dependencies.

✅ **DO** use the same name for the asynchronous version of the package as the synchronous version of the package with `-aio`

appended.

✅ **DO** use `aiohttp`

as the default HTTP stack for async operations. Use `azure.core.pipeline.transport.AioHttpTransport`

as the default `transport`

type for the async client.

## Azure SDK distribution packages

### Packaging

✅ **DO** name your package after the namespace of your main client class. For example, if your main client class is in the `azure.data.tables`

namespace, your package name should be azure-data-tables.

✅ **DO** use all lowercase in your package name with a dash (-) as a separator.

⛔️ **DO NOT** use underscore (_) or period (.) in your package name. If your namespace includes underscores, replace them with dash (-) in the distribution package name.

✅ **DO** follow the specific package guidance from the azure-sdk-packaging wiki

✅ **DO** follow the namespace package recommendations for Python 3.x for packages that only need to target 3.x.

✅ **DO** provide both source distributions (`sdist`

) and wheels.

✅ **DO** publish both source distributions (`sdist`

) and wheels to PyPI.

✅ **DO** test correct behavior for both CPython and PyPy for pure and universal Python wheels.

✅ **DO** depend on `azure-nspkg`

for Python 2.x.

✅ **DO** depend on `azure-<group>-nspkg`

for Python 2.x if you are using namespace grouping.

✅ **DO** include `__init__.py`

for the namespace(s) in sdists

#### Service-specific common library code

There are occasions when common code needs to be shared between several client libraries. For example, a set of cooperating client libraries may wish to share a set of exceptions or models.

✅ **DO** gain Architecture Board approval prior to implementing a common library.

✅ **DO** minimize the code within a common library. Code within the common library is available to the consumer of the client library and shared by multiple client libraries within the same namespace.

A common library will only be approved if:

- The consumer of the non-shared library will consume the objects within the common library directly, AND
- The information will be shared between multiple client libraries

Let’s take two examples:

-
Implementing two Cognitive Services client libraries, we find that they both rely on the same business logic. This is a candidate for choosing a common library.

-
Two Cognitive Services client libraries have models (data classes) that are the same in shape, but has no or minimal logic associated with them. This is not a good candidate for a shared library. Instead, implement two separate classes.


### Package Versioning

✅ **DO** use semantic versioning for your package.

✅ **DO** use the `bN`

pre-release segment for beta releases.

Don’t use pre-release segments other than the ones defined in PEP440 (`aN`

, `bN`

, `rcN`

). Build tools, publication tools, and index servers may not sort the versions correctly.

✅ **DO** change the version number if *anything* changes in the library.

✅ **DO** increment the patch version if only bug fixes are added to the package.

✅ **DO** increment the minor version if any new functionality is added to the package.

✅ **DO** increment (at least) the minor version if the default REST API version is changed, even if there’s no public API change to the library.

⛔️ **DO NOT** increment the major version for a new REST API version unless it requires breaking API changes in the python library itself.

✅ **DO** increment the major version if there are breaking changes in the package. Breaking changes require prior approval from the Architecture Board.

✅ **DO** select a version number greater than the highest version number of any other released Track 1 package for the service in any other scope or language.

The bar to make a breaking change is extremely high for stable client libraries. We may create a new package with a different name to avoid diamond dependency issues.

### Dependencies

✅ **DO** only pick external dependencies from the following list of well known packages for shared functionality:

| Package | Usage |
|---|---|
`requests` |
Synchronous HTTP |
`aiohttp` |
Asynchronous HTTP |
`aiodns` |
Asynchronous DNS resolution |
`typing-extensions` |
Backports for Python type hints |
`cryptography` |
Cryptographic recipes and primitives |
`certifi` |
Mozilla CA bundle |

⛔️ **DO NOT** use external dependencies outside the list of well known dependencies. To get a new dependency added, contact the Architecture Board.

⛔️ **DO NOT** vendor dependencies unless approved by the Architecture Board.

When you vendor a dependency in Python, you include the source from another package as if it was part of your package.

⛔️ **DO NOT** pin a specific version of a dependency unless that is the only way to work around a bug in said dependencies versioning scheme.

Only applications are expected to pin exact dependencies. Libraries are not. A library should use a compatible release identifier for the dependency.

### Binary extensions (native code)

✅ **DO** seek approval by the Architecture Board before implementing a binary extension.

✅ **DO** support Windows, Linux (manylinux - see PEP513, PEP571), and MacOS. Support the earliest possible manylinux to maximize your reach.

✅ **DO** support both x86 and x64 architectures.

### Docstrings

✅ **DO** follow the documentation guidelines unless explicitly overridden in this document.

✅ **DO** provide docstrings for all public modules, types, constants and functions.

✅ **DO** document any `**kwargs`

directly consumed by a method. You may refer to the signature of a called method if the `**kwargs`

are passed through.

Example:

```
def request(method, url, headers, **kwargs): ...
def get(*args, **kwargs):
"Calls `request` with the method "GET" and forwards all other arguments."
return request("GET", *args, **kwargs)
```


✅ **DO** document exceptions that may be raised explicitly in the method and any exceptions raised by the called method.

#### Code snippets

✅ **DO** include example code snippets alongside your library’s code within the repository. The snippets should clearly and succinctly demonstrate the operations most developers need to perform with your library. Include snippets for every common operation, and especially for those that are complex or might otherwise be difficult for new users of your library. At a bare minimum, include snippets for the champion scenarios you’ve identified for the library.

✅ **DO** build and test your example code snippets using the repository’s continuous integration (CI) to ensure they remain functional.

✅ **DO** include the example code snippets in your library’s docstrings so they appear in its API reference. If the language and its tools support it, ingest these snippets directly into the API reference from within the docstrings. Each sample should be a valid `pytest`

.

Use the `literalinclude`

directive in Python docstrings to instruct Sphinx to [ingest the snippets automatically][1].

⛔️ **DO NOT** combine more than one operation in a code snippet unless it’s required for demonstrating the type or member, or it’s *in addition to* existing snippets that demonstrate atomic operations. For example, a Cosmos DB code snippet should not include both account and container creation operations–create two different snippets, one for account creation, and one for container creation.

## Repository Guidelines

### Documentation style

There are several documentation deliverables that must be included in or as a companion to your client library. Beyond complete and helpful API documentation within the code itself (docstrings), you need a great README and other supporting documentation.

`README.md`

- Resides in the root of your library’s directory within the SDK repository; includes package installation and client library usage information. ([example][https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/appconfiguration/azure-appconfiguration/README.md])`API reference`

- Generated from the docstrings in your code; published on docs.microsoft.com.`Code snippets`

- Short code examples that demonstrate single (atomic) operations for the champion scenarios you’ve identified for your library; included in your README, docstrings, and Quickstart.`Quickstart`

- Article on docs.microsoft.com that is similar to but expands on the README content; typically written by your service’s content developer.`Conceptual`

- Long-form documentation like Quickstarts, Tutorials, How-to guides, and other content on docs.microsoft.com; typically written by your service’s content developer.

✅ **DO** include your service’s content developer in the adparch review for your library. To find the content developer you should work with, check with your team’s Program Manager.

✅ **DO** follow the Azure SDK Contributors Guide. (MICROSOFT INTERNAL)

✅ **DO** adhere to the specifications set forth in the Microsoft style guides when you write public-facing documentation. This applies to both long-form documentation like a README and the docstrings in your code. (MICROSOFT INTERNAL)

☑️ **YOU SHOULD** attempt to document your library into silence. Preempt developers’ usage questions and minimize GitHub issues by clearly explaining your API in the docstrings. Include information on service limits and errors they might hit, and how to avoid and recover from those errors.

As you write your code, *doc it so you never hear about it again.* The less questions you have to answer about your client library, the more time you have to build new features for your service.

### Samples

Code samples are small applications that demonstrate a certain feature that is relevant to the client library. Samples allow developers to quickly understand the full usage requirements of your client library. Code samples shouldn’t be any more complex than they needed to demonstrate the feature. Don’t write full applications. Samples should have a high signal to noise ratio between useful code and boilerplate code for non-related reasons.

✅ **DO** include code samples alongside your library’s code within the repository. The samples should clearly and succinctly demonstrate the code most developers need to write with your library. Include samples for all common operations. Pay attention to operations that are complex or might be difficult for new users of your library. Include samples for the champion scenarios you’ve identified for the library.

✅ **DO** place code samples within the /samples directory within the client library root directory. The samples will be packaged into the resulting distribution package.

✅ **DO** ensure that each sample file is runnable.

✅ **DO** avoid using features newer than the Python 3 baseline support. The current supported Python version is 3.8.

✅ **DO** ensure that code samples can be easily grafted from the documentation into a users own application. For example, don’t rely on variable declarations in other samples.

✅ **DO** write code samples for ease of reading and comprehension over code compactness and efficiency.

✅ **DO** ensure that samples can run in Windows, macOS, and Linux development environments.

⛔️ **DO NOT** combine multiple scenarios in a code sample unless it’s required for demonstrating the type or member. For example, a Cosmos DB code sample doesn’t include both account and container creation operations. Create a sample for account creation, and another sample for container creation.

Combined scenarios require knowledge of additional operations that might be outside their current focus. The developer must first understand the code surrounding the scenario they’re working on, and can’t copy and paste the code sample into their project.
