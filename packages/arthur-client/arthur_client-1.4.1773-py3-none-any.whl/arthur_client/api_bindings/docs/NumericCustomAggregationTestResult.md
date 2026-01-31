# NumericCustomAggregationTestResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_kind** | **str** |  | [optional] [default to 'numeric']
**value** | **int** | Value of the time series metric. | 

## Example

```python
from arthur_client.api_bindings.models.numeric_custom_aggregation_test_result import NumericCustomAggregationTestResult

# TODO update the JSON string below
json = "{}"
# create an instance of NumericCustomAggregationTestResult from a JSON string
numeric_custom_aggregation_test_result_instance = NumericCustomAggregationTestResult.from_json(json)
# print the JSON string representation of the object
print(NumericCustomAggregationTestResult.to_json())

# convert the object into a dict
numeric_custom_aggregation_test_result_dict = numeric_custom_aggregation_test_result_instance.to_dict()
# create an instance of NumericCustomAggregationTestResult from a dict
numeric_custom_aggregation_test_result_from_dict = NumericCustomAggregationTestResult.from_dict(numeric_custom_aggregation_test_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


