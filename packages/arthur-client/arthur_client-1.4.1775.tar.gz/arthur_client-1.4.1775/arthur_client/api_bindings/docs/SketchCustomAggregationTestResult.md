# SketchCustomAggregationTestResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_kind** | **str** |  | [optional] [default to 'sketch']
**row_count** | **int** | Count of rows the sketch saw. | 
**min** | **int** | Minimum value seen in the sketch metric. | 
**max** | **int** | Maximum value seen in the sketch metric. | 
**q1** | **int** | Q1 value of the sketch metric. | 
**q3** | **int** | Q3 value of the sketch metric. | 

## Example

```python
from arthur_client.api_bindings.models.sketch_custom_aggregation_test_result import SketchCustomAggregationTestResult

# TODO update the JSON string below
json = "{}"
# create an instance of SketchCustomAggregationTestResult from a JSON string
sketch_custom_aggregation_test_result_instance = SketchCustomAggregationTestResult.from_json(json)
# print the JSON string representation of the object
print(SketchCustomAggregationTestResult.to_json())

# convert the object into a dict
sketch_custom_aggregation_test_result_dict = sketch_custom_aggregation_test_result_instance.to_dict()
# create an instance of SketchCustomAggregationTestResult from a dict
sketch_custom_aggregation_test_result_from_dict = SketchCustomAggregationTestResult.from_dict(sketch_custom_aggregation_test_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


