# TestCustomAggregationJobSpec


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_type** | **str** |  | [optional] [default to 'test_custom_aggregation']
**test_custom_aggregation_id** | **str** | The id of the custom aggregation test. | 

## Example

```python
from arthur_client.api_bindings.models.test_custom_aggregation_job_spec import TestCustomAggregationJobSpec

# TODO update the JSON string below
json = "{}"
# create an instance of TestCustomAggregationJobSpec from a JSON string
test_custom_aggregation_job_spec_instance = TestCustomAggregationJobSpec.from_json(json)
# print the JSON string representation of the object
print(TestCustomAggregationJobSpec.to_json())

# convert the object into a dict
test_custom_aggregation_job_spec_dict = test_custom_aggregation_job_spec_instance.to_dict()
# create an instance of TestCustomAggregationJobSpec from a dict
test_custom_aggregation_job_spec_from_dict = TestCustomAggregationJobSpec.from_dict(test_custom_aggregation_job_spec_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


