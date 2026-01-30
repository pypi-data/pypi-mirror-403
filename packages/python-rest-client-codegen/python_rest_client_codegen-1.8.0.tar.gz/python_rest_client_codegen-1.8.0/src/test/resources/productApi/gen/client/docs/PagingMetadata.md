# PagingMetadata

All information about current and available pages

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**page** | **int** | Current page requested. Start at 0. | 
**per_page** | **int** | Number of item per page | 
**total_visible** | **int** | Total number of item visible by the client in the request | 
**total_found** | **int** | Total number of item found in database | 

## Example

```python
from gen.client.models.paging_metadata import PagingMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of PagingMetadata from a JSON string
paging_metadata_instance = PagingMetadata.from_json(json)
# print the JSON string representation of the object
print(PagingMetadata.to_json())

# convert the object into a dict
paging_metadata_dict = paging_metadata_instance.to_dict()
# create an instance of PagingMetadata from a dict
paging_metadata_from_dict = PagingMetadata.from_dict(paging_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


