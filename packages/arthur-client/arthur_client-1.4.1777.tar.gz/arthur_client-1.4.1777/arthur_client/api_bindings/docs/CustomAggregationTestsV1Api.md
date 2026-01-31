# arthur_client.api_bindings.CustomAggregationTestsV1Api

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_custom_aggregation_test**](CustomAggregationTestsV1Api.md#delete_custom_aggregation_test) | **DELETE** /api/v1/custom_aggregation_tests/{custom_aggregation_test_id} | Delete Custom Aggregation Test.
[**get_custom_aggregation_test**](CustomAggregationTestsV1Api.md#get_custom_aggregation_test) | **GET** /api/v1/custom_aggregation_tests/{custom_aggregation_test_id} | Get Custom Aggregation Test By Id.
[**get_custom_aggregation_test_results**](CustomAggregationTestsV1Api.md#get_custom_aggregation_test_results) | **GET** /api/v1/custom_aggregation_tests/{custom_aggregation_test_id}/results | Get Custom Aggregation Test Results By Id.
[**get_custom_aggregation_tests_for_workspace**](CustomAggregationTestsV1Api.md#get_custom_aggregation_tests_for_workspace) | **GET** /api/v1/workspaces/{workspace_id}/custom_aggregation_tests | Get Custom Aggregation Tests.
[**post_custom_aggregation_test**](CustomAggregationTestsV1Api.md#post_custom_aggregation_test) | **POST** /api/v1/workspaces/{workspace_id}/custom_aggregation_tests | Post Custom Aggregation Test.
[**post_custom_aggregation_test_results**](CustomAggregationTestsV1Api.md#post_custom_aggregation_test_results) | **POST** /api/v1/custom_aggregation_tests/{custom_aggregation_test_id}/results | Post Custom Aggregation Test Results.


# **delete_custom_aggregation_test**
> delete_custom_aggregation_test(custom_aggregation_test_id)

Delete Custom Aggregation Test.

Requires custom_aggregation_test_delete permission.

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
    api_instance = arthur_client.api_bindings.CustomAggregationTestsV1Api(api_client)
    custom_aggregation_test_id = 'custom_aggregation_test_id_example' # str | 

    try:
        # Delete Custom Aggregation Test.
        api_instance.delete_custom_aggregation_test(custom_aggregation_test_id)
    except Exception as e:
        print("Exception when calling CustomAggregationTestsV1Api->delete_custom_aggregation_test: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **custom_aggregation_test_id** | **str**|  | 

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

# **get_custom_aggregation_test**
> CustomAggregationTestSpec get_custom_aggregation_test(custom_aggregation_test_id)

Get Custom Aggregation Test By Id.

Requires custom_aggregation_test_read permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.custom_aggregation_test_spec import CustomAggregationTestSpec
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
    api_instance = arthur_client.api_bindings.CustomAggregationTestsV1Api(api_client)
    custom_aggregation_test_id = 'custom_aggregation_test_id_example' # str | 

    try:
        # Get Custom Aggregation Test By Id.
        api_response = api_instance.get_custom_aggregation_test(custom_aggregation_test_id)
        print("The response of CustomAggregationTestsV1Api->get_custom_aggregation_test:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CustomAggregationTestsV1Api->get_custom_aggregation_test: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **custom_aggregation_test_id** | **str**|  | 

### Return type

[**CustomAggregationTestSpec**](CustomAggregationTestSpec.md)

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

# **get_custom_aggregation_test_results**
> ResourceListCustomAggregationTestResult get_custom_aggregation_test_results(custom_aggregation_test_id, page=page, page_size=page_size, time_range_after=time_range_after, time_range_before=time_range_before)

Get Custom Aggregation Test Results By Id.

Requires custom_aggregation_test_read_results permission. Also requires dataset_get_data_retrieval on the dataset the custom aggregation test is configured against.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.resource_list_custom_aggregation_test_result import ResourceListCustomAggregationTestResult
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
    api_instance = arthur_client.api_bindings.CustomAggregationTestsV1Api(api_client)
    custom_aggregation_test_id = 'custom_aggregation_test_id_example' # str | 
    page = 1 # int | The page number to fetch. (optional) (default to 1)
    page_size = 10 # int | The number of items per page. (optional) (default to 10)
    time_range_after = '2013-10-20T19:20:30+01:00' # datetime | Filter results to only include metrics with timestamp after this time. (optional)
    time_range_before = '2013-10-20T19:20:30+01:00' # datetime | Filter results to only include metrics with timestamp before this time. (optional)

    try:
        # Get Custom Aggregation Test Results By Id.
        api_response = api_instance.get_custom_aggregation_test_results(custom_aggregation_test_id, page=page, page_size=page_size, time_range_after=time_range_after, time_range_before=time_range_before)
        print("The response of CustomAggregationTestsV1Api->get_custom_aggregation_test_results:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CustomAggregationTestsV1Api->get_custom_aggregation_test_results: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **custom_aggregation_test_id** | **str**|  | 
 **page** | **int**| The page number to fetch. | [optional] [default to 1]
 **page_size** | **int**| The number of items per page. | [optional] [default to 10]
 **time_range_after** | **datetime**| Filter results to only include metrics with timestamp after this time. | [optional] 
 **time_range_before** | **datetime**| Filter results to only include metrics with timestamp before this time. | [optional] 

### Return type

[**ResourceListCustomAggregationTestResult**](ResourceListCustomAggregationTestResult.md)

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

# **get_custom_aggregation_tests_for_workspace**
> ResourceListCustomAggregationTestSpec get_custom_aggregation_tests_for_workspace(workspace_id, page=page, page_size=page_size, search=search, dataset_id=dataset_id)

Get Custom Aggregation Tests.

Requires workspace_list_custom_aggregation_tests permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.resource_list_custom_aggregation_test_spec import ResourceListCustomAggregationTestSpec
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
    api_instance = arthur_client.api_bindings.CustomAggregationTestsV1Api(api_client)
    workspace_id = 'workspace_id_example' # str | 
    page = 1 # int | The page number to fetch. (optional) (default to 1)
    page_size = 10 # int | The number of items per page. (optional) (default to 10)
    search = 'search_example' # str | Search for custom aggregation tests by aggregation name or description. (optional)
    dataset_id = 'dataset_id_example' # str | Filter for tests using a specific dataset. (optional)

    try:
        # Get Custom Aggregation Tests.
        api_response = api_instance.get_custom_aggregation_tests_for_workspace(workspace_id, page=page, page_size=page_size, search=search, dataset_id=dataset_id)
        print("The response of CustomAggregationTestsV1Api->get_custom_aggregation_tests_for_workspace:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CustomAggregationTestsV1Api->get_custom_aggregation_tests_for_workspace: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **str**|  | 
 **page** | **int**| The page number to fetch. | [optional] [default to 1]
 **page_size** | **int**| The number of items per page. | [optional] [default to 10]
 **search** | **str**| Search for custom aggregation tests by aggregation name or description. | [optional] 
 **dataset_id** | **str**| Filter for tests using a specific dataset. | [optional] 

### Return type

[**ResourceListCustomAggregationTestSpec**](ResourceListCustomAggregationTestSpec.md)

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

# **post_custom_aggregation_test**
> CustomAggregationTestSpec post_custom_aggregation_test(workspace_id, post_custom_aggregation_test)

Post Custom Aggregation Test.

Requires workspace_create_custom_aggregation_test permission. Will queue an async job to test the configured custom aggregation for the dataset. Requires dataset_create_data_retrieval on the dataset the test is configured to run against.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.custom_aggregation_test_spec import CustomAggregationTestSpec
from arthur_client.api_bindings.models.post_custom_aggregation_test import PostCustomAggregationTest
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
    api_instance = arthur_client.api_bindings.CustomAggregationTestsV1Api(api_client)
    workspace_id = 'workspace_id_example' # str | 
    post_custom_aggregation_test = arthur_client.api_bindings.PostCustomAggregationTest() # PostCustomAggregationTest | 

    try:
        # Post Custom Aggregation Test.
        api_response = api_instance.post_custom_aggregation_test(workspace_id, post_custom_aggregation_test)
        print("The response of CustomAggregationTestsV1Api->post_custom_aggregation_test:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CustomAggregationTestsV1Api->post_custom_aggregation_test: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **str**|  | 
 **post_custom_aggregation_test** | [**PostCustomAggregationTest**](PostCustomAggregationTest.md)|  | 

### Return type

[**CustomAggregationTestSpec**](CustomAggregationTestSpec.md)

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

# **post_custom_aggregation_test_results**
> MetricsUploadResult post_custom_aggregation_test_results(custom_aggregation_test_id, metrics_upload)

Post Custom Aggregation Test Results.

Requires custom_aggregation_test_create_results permission.

### Example

* OAuth Authentication (OAuth2AuthorizationCode):

```python
import arthur_client.api_bindings
from arthur_client.api_bindings.models.metrics_upload import MetricsUpload
from arthur_client.api_bindings.models.metrics_upload_result import MetricsUploadResult
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
    api_instance = arthur_client.api_bindings.CustomAggregationTestsV1Api(api_client)
    custom_aggregation_test_id = 'custom_aggregation_test_id_example' # str | 
    metrics_upload = arthur_client.api_bindings.MetricsUpload() # MetricsUpload | 

    try:
        # Post Custom Aggregation Test Results.
        api_response = api_instance.post_custom_aggregation_test_results(custom_aggregation_test_id, metrics_upload)
        print("The response of CustomAggregationTestsV1Api->post_custom_aggregation_test_results:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CustomAggregationTestsV1Api->post_custom_aggregation_test_results: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **custom_aggregation_test_id** | **str**|  | 
 **metrics_upload** | [**MetricsUpload**](MetricsUpload.md)|  | 

### Return type

[**MetricsUploadResult**](MetricsUploadResult.md)

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

