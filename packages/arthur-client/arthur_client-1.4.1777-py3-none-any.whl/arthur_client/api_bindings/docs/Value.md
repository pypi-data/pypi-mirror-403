# Value

Number or data sketch values representing the aggregation.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metric_kind** | **str** |  | [optional] [default to 'sketch']
**value** | **int** | Value of the time series metric. | 
**row_count** | **int** | Count of rows the sketch saw. | 
**min** | **int** | Minimum value seen in the sketch metric. | 
**max** | **int** | Maximum value seen in the sketch metric. | 
**q1** | **int** | Q1 value of the sketch metric. | 
**q3** | **int** | Q3 value of the sketch metric. | 

## Example

```python
from arthur_client.api_bindings.models.value import Value

# TODO update the JSON string below
json = "{}"
# create an instance of Value from a JSON string
value_instance = Value.from_json(json)
# print the JSON string representation of the object
print(Value.to_json())

# convert the object into a dict
value_dict = value_instance.to_dict()
# create an instance of Value from a dict
value_from_dict = Value.from_dict(value_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


