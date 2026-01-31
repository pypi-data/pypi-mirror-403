# ResourceListCustomAggregationTestResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**records** | [**List[CustomAggregationTestResult]**](CustomAggregationTestResult.md) | List of records. | 
**pagination** | [**Pagination**](Pagination.md) | Pagination information. | 

## Example

```python
from arthur_client.api_bindings.models.resource_list_custom_aggregation_test_result import ResourceListCustomAggregationTestResult

# TODO update the JSON string below
json = "{}"
# create an instance of ResourceListCustomAggregationTestResult from a JSON string
resource_list_custom_aggregation_test_result_instance = ResourceListCustomAggregationTestResult.from_json(json)
# print the JSON string representation of the object
print(ResourceListCustomAggregationTestResult.to_json())

# convert the object into a dict
resource_list_custom_aggregation_test_result_dict = resource_list_custom_aggregation_test_result_instance.to_dict()
# create an instance of ResourceListCustomAggregationTestResult from a dict
resource_list_custom_aggregation_test_result_from_dict = ResourceListCustomAggregationTestResult.from_dict(resource_list_custom_aggregation_test_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


