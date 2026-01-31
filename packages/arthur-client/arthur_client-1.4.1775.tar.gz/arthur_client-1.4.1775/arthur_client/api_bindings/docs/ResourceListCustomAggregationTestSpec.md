# ResourceListCustomAggregationTestSpec


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**records** | [**List[CustomAggregationTestSpec]**](CustomAggregationTestSpec.md) | List of records. | 
**pagination** | [**Pagination**](Pagination.md) | Pagination information. | 

## Example

```python
from arthur_client.api_bindings.models.resource_list_custom_aggregation_test_spec import ResourceListCustomAggregationTestSpec

# TODO update the JSON string below
json = "{}"
# create an instance of ResourceListCustomAggregationTestSpec from a JSON string
resource_list_custom_aggregation_test_spec_instance = ResourceListCustomAggregationTestSpec.from_json(json)
# print the JSON string representation of the object
print(ResourceListCustomAggregationTestSpec.to_json())

# convert the object into a dict
resource_list_custom_aggregation_test_spec_dict = resource_list_custom_aggregation_test_spec_instance.to_dict()
# create an instance of ResourceListCustomAggregationTestSpec from a dict
resource_list_custom_aggregation_test_spec_from_dict = ResourceListCustomAggregationTestSpec.from_dict(resource_list_custom_aggregation_test_spec_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


