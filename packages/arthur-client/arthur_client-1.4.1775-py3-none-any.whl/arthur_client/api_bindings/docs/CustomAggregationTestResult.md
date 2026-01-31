# CustomAggregationTestResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**test_run_id** | **str** | ID of the custom aggregation test run. | 
**metric_name** | **str** | Name of the generated metric. | 
**timestamp** | **datetime** | Timestamp for the time bucket the aggregation value is for. | 
**value** | [**Value**](Value.md) |  | 
**dimensions** | [**List[Dimension]**](Dimension.md) | List of dimensions for the value. | 

## Example

```python
from arthur_client.api_bindings.models.custom_aggregation_test_result import CustomAggregationTestResult

# TODO update the JSON string below
json = "{}"
# create an instance of CustomAggregationTestResult from a JSON string
custom_aggregation_test_result_instance = CustomAggregationTestResult.from_json(json)
# print the JSON string representation of the object
print(CustomAggregationTestResult.to_json())

# convert the object into a dict
custom_aggregation_test_result_dict = custom_aggregation_test_result_instance.to_dict()
# create an instance of CustomAggregationTestResult from a dict
custom_aggregation_test_result_from_dict = CustomAggregationTestResult.from_dict(custom_aggregation_test_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


