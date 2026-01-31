# PostCustomAggregationTest


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

## Example

```python
from arthur_client.api_bindings.models.post_custom_aggregation_test import PostCustomAggregationTest

# TODO update the JSON string below
json = "{}"
# create an instance of PostCustomAggregationTest from a JSON string
post_custom_aggregation_test_instance = PostCustomAggregationTest.from_json(json)
# print the JSON string representation of the object
print(PostCustomAggregationTest.to_json())

# convert the object into a dict
post_custom_aggregation_test_dict = post_custom_aggregation_test_instance.to_dict()
# create an instance of PostCustomAggregationTest from a dict
post_custom_aggregation_test_from_dict = PostCustomAggregationTest.from_dict(post_custom_aggregation_test_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


