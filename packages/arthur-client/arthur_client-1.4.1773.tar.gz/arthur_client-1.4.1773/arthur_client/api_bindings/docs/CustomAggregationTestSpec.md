# CustomAggregationTestSpec


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**reported_aggregations** | [**List[ReportedCustomAggregation]**](ReportedCustomAggregation.md) | Metadata for every aggregation the custom aggregation reports. | 
**aggregate_args** | [**List[CustomAggregationVersionSpecSchemaAggregateArgsInner]**](CustomAggregationVersionSpecSchemaAggregateArgsInner.md) | List of parameters to the custom aggregation&#39;s query function. | 
**sql** | **str** | DuckDBSQL query for the custom aggregation. | 
**name** | **str** | Name of the custom aggregation function. | 
**description** | **str** |  | [optional] 
**aggregation_arg_configuration** | [**List[MetricsArgSpec]**](MetricsArgSpec.md) | List of argument values for the aggregation&#39;s aggregate function. | 
**start_timestamp** | **datetime** | The start timestamp to use for fetching data. | 
**end_timestamp** | **datetime** | The end timestamp to use for fetching data. | 
**dataset_id** | **str** | ID of the dataset to use for the custom aggregation test. | 
**id** | **str** | ID of the custom aggregation test. | 
**authored_by** | [**User**](User.md) |  | 
**workspace_id** | **str** | ID of the parent workspace the test was executed in. | 
**test_status** | [**CustomAggregationTestStatus**](CustomAggregationTestStatus.md) | Status of custom aggregation test. Deprecated, should not be used. Status should be inferred from the status of the linked job. | 
**created_at** | **datetime** | Time of custom aggregation test creation. | 
**job_id** | **str** | ID of the job created for the test execution. Can be polled to check job status. | 

## Example

```python
from arthur_client.api_bindings.models.custom_aggregation_test_spec import CustomAggregationTestSpec

# TODO update the JSON string below
json = "{}"
# create an instance of CustomAggregationTestSpec from a JSON string
custom_aggregation_test_spec_instance = CustomAggregationTestSpec.from_json(json)
# print the JSON string representation of the object
print(CustomAggregationTestSpec.to_json())

# convert the object into a dict
custom_aggregation_test_spec_dict = custom_aggregation_test_spec_instance.to_dict()
# create an instance of CustomAggregationTestSpec from a dict
custom_aggregation_test_spec_from_dict = CustomAggregationTestSpec.from_dict(custom_aggregation_test_spec_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


