# biotmed_notification_sdk

APIs document (version: 5.3.32)

This Python SDK provides a client library for interacting with the BioT  Service API. BioT is a comprehensive platform for medical device integration and healthcare data management, enabling secure communication between medical devices and cloud services.

For more information about BioT, see [BioT](https://www.biot-med.com).

## Installation

```bash
pip install biotmed_notification_sdk
```

## Configuration

### Creating and Configuring the ApiClient

The SDK requires configuration with an access token and the service endpoint. You'll need to:

1. **Configure the service path** by appending the service-specific path to your BioT base URL
2. **Provide an access token** (as a string or callable function)
3. **Optionally set up language management** (as a string or callable function)

#### Service Path Configuration

Each BioT service has its own path that must be appended to the base URL:

- **Generic Entity Service**: `/generic-entity`
- **Organization Service**: `/organization`
- **DMS Service**: `/dms`
- **File Service**: `/file`
- **Notification Service**: `/notification`
- **UMS Service**: `/ums`
- **Settings Service**: `/settings`
- **Measurement Service**: `/measurement`
- **Device Service**: `/device`

**Important**: Always append the service path to your `biot_base_url` when configuring the SDK.

#### Access Token Configuration

The SDK supports both static tokens and dynamic token providers (callable pattern). You can pass either:

- **A string**: A static access token (not recommended for long-running applications)
- **A callable** (function or callable object): A token provider that returns a token when called, enabling automatic token refresh

Using a callable allows the SDK to refresh tokens automatically before they expire, ensuring your API calls remain authenticated.

```python
# Option 1: Static token (simple but tokens expire)
access_token = "your-static-token-here"

# Option 2: Callable function for dynamic token refresh
def get_access_token() -> str:
    # Implement your token retrieval/refresh logic here
    # This function will be called by the SDK when authentication is needed
    # You can authenticate however you prefer (OAuth, service user, etc.)
    return "your-access-token"

# Option 3: Callable object (Token Provider pattern)
class TokenProvider:
    def __call__(self) -> str:
        # Return the token, only refresh if expired
        if self._is_token_expired():
            self._token = self._refresh_token()
        return self._token
    
    def _is_token_expired(self) -> bool:
        # Check if token needs refresh
        # Your expiration check logic here
        return True
    
    def _refresh_token(self) -> str:
        # Your token refresh implementation
        # This is only called when token is expired
        return "your-new-access-token"

token_provider = TokenProvider()
```

#### Language Configuration

Similarly, the `accept_language` parameter supports both static strings and callables for dynamic language selection:

```python
# Option 1: Static language
accept_language = "en-us"

# Option 2: Callable for dynamic language selection
def get_accept_language() -> str:
    # Return language based on user preferences, system settings, etc.
    return "en-us"  # Examples: "en-us", "fr-fr", "de-de", etc.
```

#### Complete Configuration Example

```python
import biotmed_notification_sdk
from typing import Callable

# BioT configuration
biot_base_url = "https://api.example.biot-med.com"  # or your production URL

# Token provider (callable for automatic refresh)
def get_access_token() -> str:
    # Implement your token retrieval/refresh logic
    # This will be called by the SDK when authentication is needed
    # Authenticate using your preferred method (OAuth, service user credentials, etc.)
    return "your-access-token"

# Language provider (optional, callable for dynamic language)
def get_accept_language() -> str:
    return "en-us"

# Configure SDK with service path appended to base URL
configuration = biotmed_notification_sdk.Configuration(
    host=biot_base_url + "/service-path",  # Replace with your service path (e.g., "/generic-entity", "/organization", "/dms")
    access_token=get_access_token,  # Callable token provider
    accept_language=get_accept_language  # Optional: callable language provider
)

# Create ApiClient
with biotmed_notification_sdk.ApiClient(configuration) as api_client:
    # Create API instances
    api = biotmed_notification_sdk.YourAPIClass(api_client)  # Replace with your actual API class name
    # Use the API...
```

## Usage Examples

### Different Approaches for Creating Resources

The SDK supports multiple approaches for creating resources, each with different trade-offs between type safety, flexibility, and developer experience. Choose the approach that best fits your use case.

#### Approach 1: Direct Model Construction with Inline Custom Attributes

Use direct Pydantic model construction when you want maximum type safety for standard fields and don't mind type checker warnings for custom attributes:

```python
from uuid import UUID

create_request = biotmed_notification_sdk.CreateResourceRequest(  # Replace with your actual request model name
    _name="My Resource",
    _ownerOrganization=biotmed_notification_sdk.ReferenceAttributeUUIDIdRequest(
        id=UUID("your-organization-id")
    ),
    customField1="value1",  # pyright: ignore[reportCallIssue]
    customField2="value2",  # pyright: ignore[reportCallIssue]
    # ... other fields
)

response = api.create_resource(create_request, template_name="YourTemplate")  # Replace with your actual method name
```

**Pros:**
- Full type safety and IDE autocomplete for all schema-defined fields
- Direct, intuitive syntax
- Compile-time validation for standard fields
- Clear separation between standard and custom fields in code

**Cons:**
- Type checker warnings for custom attributes (requires `# pyright: ignore[reportCallIssue]` comments)
- Custom attributes are not statically typed
- Can clutter constructor calls with many custom attributes

**Best for:** When you have a few custom attributes and want maximum type safety for standard fields.

---

#### Approach 2: Custom Attributes with **kwargs

Separate custom attributes into a dictionary and unpack them using `**kwargs`. This provides cleaner code organization:

```python
from typing import Dict, Any
from uuid import UUID

# Custom attributes not defined in the schema
custom_attrs: Dict[str, Any] = {
    "customField1": "value1",
    "customField2": "value2"
}

create_request = biotmed_notification_sdk.CreateResourceRequest(  # Replace with your actual request model name
    _name="My Resource",
    _ownerOrganization=biotmed_notification_sdk.ReferenceAttributeUUIDIdRequest(
        id=UUID("your-organization-id")
    ),
    **custom_attrs  # Unpack custom attributes
)

response = api.create_resource(create_request, template_name="YourTemplate")  # Replace with your actual method name
```

**Pros:**
- No type checker warnings on the model construction line
- Full type safety for standard fields
- Easy to build custom attributes dynamically
- Better code organization when you have many custom attributes

**Cons:**
- Separation of custom attributes from standard fields
- Slightly more verbose than Approach 1

**Best for:** When you have many custom attributes or need to build them dynamically. This is the recommended approach for most use cases.

---

#### Approach 3: Using model_validate with Dictionary

Use `model_validate` when you're working with dictionaries, need maximum flexibility, or are building requests from external data sources:

```python
create_request = biotmed_notification_sdk.CreateResourceRequest.model_validate({  # Replace with your actual request model name
    "_name": "My Resource",
    "_ownerOrganization": {
        "id": "your-organization-id"
    },
    "customField1": "value1",
    "customField2": "value2",
    # ... other fields (all as dictionary keys)
})

response = api.create_resource(create_request, template_name="YourTemplate")  # Replace with your actual method name
```

**Pros:**
- Maximum flexibility - works with any dictionary structure
- Perfect for building requests from external data (JSON, API responses, etc.)
- Can easily handle dynamic field names
- Runtime validation still occurs via Pydantic

**Cons:**
- No static type checking or IDE autocomplete
- No compile-time validation
- Field names must match JSON names (e.g., `_name` not `name`)
- Less readable than constructor-based approaches

**Best for:** When working with dynamic data, parsing JSON, or when field names are determined at runtime. Also useful for global entities or cases where you need to set fields to `None`.

---

### Comparison Summary

| Feature | Approach 1<br/>(Direct + Inline) | Approach 2<br/>(Direct + **kwargs) | Approach 3<br/>(model_validate) |
|---------|----------------------------------|-----------------------------------|----------------------------------|
| Type safety (standard fields) | ✅ Full | ✅ Full | ❌ None |
| IDE autocomplete | ✅ Yes | ✅ Yes | ❌ No |
| Custom attributes support | ⚠️ With warnings | ✅ Clean | ✅ Clean |


### Accessing Response Data

When retrieving resources, you can access both standard fields and custom attributes using these recommended approaches:

#### Using .get() Method (Recommended)

The `.get()` method is the simplest and safest way to access both standard fields and custom attributes:

```python
response = api.get_resource(template_name, resource_id)  # Replace with your actual method name

# Access standard fields
resource_name = response.get("_name")
resource_id = response.get("id")

# Access custom attributes
custom_value = response.get("customField1")
```

#### Using Dot Notation (Recommended for Standard Fields)

For standard fields, dot notation provides type safety and IDE autocomplete:

```python
response = api.get_resource(template_name, resource_id)  # Replace with your actual method name

# Access standard fields (type-safe, IDE autocomplete)
resource_name = response._name
resource_id = response.id

# For custom attributes, use getattr with default
custom_value = getattr(response, "customField1", None)
```

#### Using additional_properties (Recommended for Custom Attributes)

For custom attributes specifically, you can access them directly through `additional_properties`:

```python
response = api.get_resource(template_name, resource_id)  # Replace with your actual method name

# Access custom attributes
custom_value = response.additional_properties.get("customField1")
```

**Note**: When accessing custom attributes that aren't defined in the response model schema, type checkers may show warnings. You can safely ignore these warnings since custom attributes are stored in `additional_properties` and are accessible at runtime.

### Search Examples

The SDK provides powerful search capabilities with various filter options.

#### Basic Search

```python
from biotmed_notification_sdk import SearchRequestV2, FilterV2, Order

search_request = SearchRequestV2(
    limit=10,
    page=0,
    sort=[Order(prop="_creationTime", order="DESC")]
)

response = api.search_resources(search_request)  # Replace with your actual method name
```

#### Search with Filters

```python
# Search by name (like filter)
search_request = SearchRequestV2(
    filter={
        "_name": FilterV2(like="test")
    },
    limit=10,
    page=0,
    sort=[Order(prop="_creationTime", order="DESC")]
)

response = api.search_resources(search_request)  # Replace with your actual method name
```

#### Search with Multiple Filters

```python
# Search with multiple conditions
search_request = SearchRequestV2(
    filter={
        "_name": FilterV2(like="test"),
        "_creationTime": FilterV2(
            var_from="2024-01-01T00:00:00Z",
            to="2024-12-31T23:59:59Z"
        )
    },
    limit=10,
    page=0
)

response = api.search_resources(search_request)  # Replace with your actual method name
```

### Error Handling

Always wrap API calls in try-except blocks to handle errors gracefully:

```python
from biotmed_notification_sdk import ApiException

try:
    response = api.get_resource(template_name, resource_id)  # Replace with your actual method name
    print(response.model_dump_json(by_alias=True, indent=2))
except ApiException as e:
    # Handle API errors
    error_response = e.data
    if isinstance(error_response, biotmed_notification_sdk.ErrorResponse):
        print(f"API Error: {error_response.model_dump_json(by_alias=True, indent=2)}")
    else:
        print(f"Exception: {e}")
```

### Complete Example

Here's a complete example combining all the concepts:

```python
import biotmed_notification_sdk
from biotmed_notification_sdk import ApiException
from uuid import UUID
from typing import Dict, Any

# Configuration
biot_base_url = "https://api.<>.biot-med.com"

def get_access_token() -> str:
    # Implement your token retrieval/refresh logic
    # Authenticate using your preferred method (OAuth, service user credentials, etc.)
    return "your-access-token"

configuration = biotmed_notification_sdk.Configuration(
    host=biot_base_url + "/service-path",  # Replace with your service path
    access_token=get_access_token,  # Callable token provider
    accept_language=lambda: "en-us"  # Optional: callable language provider
)

# Use ApiClient
with biotmed_notification_sdk.ApiClient(configuration) as api_client:
    api = biotmed_notification_sdk.YourAPIClass(api_client)  # Replace with your actual API class name
    
    # Search example
    try:
        search_request = biotmed_notification_sdk.SearchRequestV2(
            filter={
                "_name": biotmed_notification_sdk.FilterV2(like="test")
            },
            limit=10,
            page=0
        )
        search_response = api.search_resources(search_request)  # Replace with your actual method name
        print(f"Found {len(search_response.data)} resources")
    except ApiException as e:
        print(f"Search error: {e}")
    
    # Create example with custom attributes
    try:
        custom_attrs: Dict[str, Any] = {
            "customField": "customValue"
        }
        create_request = biotmed_notification_sdk.CreateResourceRequest(  # Replace with your actual request model name
            _name="My Resource",
            _ownerOrganization=biotmed_notification_sdk.ReferenceAttributeUUIDIdRequest(
                id=UUID("your-organization-id")
            ),
            **custom_attrs
        )
        create_response = api.create_resource(  # Replace with your actual method name
            create_request, 
            template_name="YourTemplate"
        )
        print(f"Created resource: {create_response.id}")
    except ApiException as e:
        print(f"Create error: {e}")
    
    # Get example
    try:
        get_response = api.get_resource("YourTemplate", resource_id)  # Replace with your actual method name
        
        # Access data using .get() method
        name = get_response.get("_name")
        custom_value = get_response.get("customField")
        
        print(f"Resource name: {name}")
        print(f"Custom field: {custom_value}")
    except ApiException as e:
        print(f"Get error: {e}")
```

## Additional Resources

- [BioT Developer Guide](https://docs.biot-med.com/docs/device-integration)
- [BioT API Reference](https://docs.biot-med.com/api-reference)
- [BioT Search API Documentation](https://docs.biot-med.com/docs/using-biot-search-apis)

## License

This project is licensed under the MIT License.


