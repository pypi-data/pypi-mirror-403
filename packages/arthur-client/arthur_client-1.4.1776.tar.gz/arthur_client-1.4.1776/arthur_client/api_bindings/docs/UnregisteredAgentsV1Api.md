# arthur_client.api_bindings.UnregisteredAgentsV1Api

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_unregistered_agent**](UnregisteredAgentsV1Api.md#delete_unregistered_agent) | **DELETE** /api/v1/unregistered_agents/{unregistered_agent_id} | Delete Unregistered Agent.
[**get_unregistered_agent**](UnregisteredAgentsV1Api.md#get_unregistered_agent) | **GET** /api/v1/unregistered_agents/{unregistered_agent_id} | Get Unregistered Agent.
[**get_unregistered_agents**](UnregisteredAgentsV1Api.md#get_unregistered_agents) | **GET** /api/v1/workspaces/{workspace_id}/unregistered_agents | Get Unregistered Agents.
[**patch_unregistered_agent**](UnregisteredAgentsV1Api.md#patch_unregistered_agent) | **PATCH** /api/v1/unregistered_agents/{unregistered_agent_id} | Patch Unregistered Agent.
[**put_unregistered_agents**](UnregisteredAgentsV1Api.md#put_unregistered_agents) | **PUT** /api/v1/workspaces/{workspace_id}/unregistered_agents | Put Unregistered Agents.


# **delete_unregistered_agent**
> delete_unregistered_agent(unregistered_agent_id)

Delete Unregistered Agent.

Delete an unregistered agent. Requires unregistered_agent_delete permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = arthur_client.api_bindings.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with arthur_client.api_bindings.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = arthur_client.api_bindings.UnregisteredAgentsV1Api(api_client)
    unregistered_agent_id = 'unregistered_agent_id_example' # str | 

    try:
        # Delete Unregistered Agent.
        api_instance.delete_unregistered_agent(unregistered_agent_id)
    except Exception as e:
        print("Exception when calling UnregisteredAgentsV1Api->delete_unregistered_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **unregistered_agent_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[OAuth2AuthorizationCode](../README.md#OAuth2AuthorizationCode)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Successful Response |  -  |
**500** | Internal Server Error |  -  |
**404** | Not Found |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_unregistered_agent**
> UnregisteredAgentResponse get_unregistered_agent(unregistered_agent_id)

Get Unregistered Agent.

Get a single unregistered agent by ID. Requires unregistered_agent_read permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.unregistered_agent_response import UnregisteredAgentResponse
from arthur_client.api_bindings.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = arthur_client.api_bindings.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with arthur_client.api_bindings.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = arthur_client.api_bindings.UnregisteredAgentsV1Api(api_client)
    unregistered_agent_id = 'unregistered_agent_id_example' # str | 

    try:
        # Get Unregistered Agent.
        api_response = api_instance.get_unregistered_agent(unregistered_agent_id)
        print("The response of UnregisteredAgentsV1Api->get_unregistered_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UnregisteredAgentsV1Api->get_unregistered_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **unregistered_agent_id** | **str**|  | 

### Return type

[**UnregisteredAgentResponse**](UnregisteredAgentResponse.md)

### Authorization

[OAuth2AuthorizationCode](../README.md#OAuth2AuthorizationCode)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**500** | Internal Server Error |  -  |
**404** | Not Found |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_unregistered_agents**
> ResourceListUnregisteredAgentResponse get_unregistered_agents(workspace_id, name=name, show_registered=show_registered, page=page, page_size=page_size)

Get Unregistered Agents.

Lists unregistered agents in the workspace with pagination and filtering. By default shows agents not yet linked to a model. Requires workspace_governance_view permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.resource_list_unregistered_agent_response import ResourceListUnregisteredAgentResponse
from arthur_client.api_bindings.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = arthur_client.api_bindings.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with arthur_client.api_bindings.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = arthur_client.api_bindings.UnregisteredAgentsV1Api(api_client)
    workspace_id = 'workspace_id_example' # str | 
    name = 'name_example' # str | Filter agents by name (case-insensitive partial match) (optional)
    show_registered = False # bool | If true, show agents linked to models; if false, show unlinked agents (optional) (default to False)
    page = 1 # int | The page to return starting from 1 up to total_pages. (optional) (default to 1)
    page_size = 20 # int | The number of records per page. The max is 1000. (optional) (default to 20)

    try:
        # Get Unregistered Agents.
        api_response = api_instance.get_unregistered_agents(workspace_id, name=name, show_registered=show_registered, page=page, page_size=page_size)
        print("The response of UnregisteredAgentsV1Api->get_unregistered_agents:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UnregisteredAgentsV1Api->get_unregistered_agents: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **str**|  | 
 **name** | **str**| Filter agents by name (case-insensitive partial match) | [optional] 
 **show_registered** | **bool**| If true, show agents linked to models; if false, show unlinked agents | [optional] [default to False]
 **page** | **int**| The page to return starting from 1 up to total_pages. | [optional] [default to 1]
 **page_size** | **int**| The number of records per page. The max is 1000. | [optional] [default to 20]

### Return type

[**ResourceListUnregisteredAgentResponse**](ResourceListUnregisteredAgentResponse.md)

### Authorization

[OAuth2AuthorizationCode](../README.md#OAuth2AuthorizationCode)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**500** | Internal Server Error |  -  |
**404** | Not Found |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **patch_unregistered_agent**
> UnregisteredAgentResponse patch_unregistered_agent(unregistered_agent_id, patch_unregistered_agent)

Patch Unregistered Agent.

Update specific fields of an unregistered agent. Requires unregistered_agent_update permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.patch_unregistered_agent import PatchUnregisteredAgent
from arthur_client.api_bindings.models.unregistered_agent_response import UnregisteredAgentResponse
from arthur_client.api_bindings.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = arthur_client.api_bindings.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with arthur_client.api_bindings.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = arthur_client.api_bindings.UnregisteredAgentsV1Api(api_client)
    unregistered_agent_id = 'unregistered_agent_id_example' # str | 
    patch_unregistered_agent = arthur_client.api_bindings.PatchUnregisteredAgent() # PatchUnregisteredAgent | 

    try:
        # Patch Unregistered Agent.
        api_response = api_instance.patch_unregistered_agent(unregistered_agent_id, patch_unregistered_agent)
        print("The response of UnregisteredAgentsV1Api->patch_unregistered_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UnregisteredAgentsV1Api->patch_unregistered_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **unregistered_agent_id** | **str**|  | 
 **patch_unregistered_agent** | [**PatchUnregisteredAgent**](PatchUnregisteredAgent.md)|  | 

### Return type

[**UnregisteredAgentResponse**](UnregisteredAgentResponse.md)

### Authorization

[OAuth2AuthorizationCode](../README.md#OAuth2AuthorizationCode)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**500** | Internal Server Error |  -  |
**404** | Not Found |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **put_unregistered_agents**
> PutUnregisteredAgentsResponse put_unregistered_agents(workspace_id, put_unregistered_agents)

Put Unregistered Agents.

Creates or updates unregistered agents detected in the workspace. Requires workspace_governance_view permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.put_unregistered_agents import PutUnregisteredAgents
from arthur_client.api_bindings.models.put_unregistered_agents_response import PutUnregisteredAgentsResponse
from arthur_client.api_bindings.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = arthur_client.api_bindings.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with arthur_client.api_bindings.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = arthur_client.api_bindings.UnregisteredAgentsV1Api(api_client)
    workspace_id = 'workspace_id_example' # str | 
    put_unregistered_agents = arthur_client.api_bindings.PutUnregisteredAgents() # PutUnregisteredAgents | 

    try:
        # Put Unregistered Agents.
        api_response = api_instance.put_unregistered_agents(workspace_id, put_unregistered_agents)
        print("The response of UnregisteredAgentsV1Api->put_unregistered_agents:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling UnregisteredAgentsV1Api->put_unregistered_agents: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **str**|  | 
 **put_unregistered_agents** | [**PutUnregisteredAgents**](PutUnregisteredAgents.md)|  | 

### Return type

[**PutUnregisteredAgentsResponse**](PutUnregisteredAgentsResponse.md)

### Authorization

[OAuth2AuthorizationCode](../README.md#OAuth2AuthorizationCode)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**500** | Internal Server Error |  -  |
**400** | Bad Request |  -  |
**404** | Not Found |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

