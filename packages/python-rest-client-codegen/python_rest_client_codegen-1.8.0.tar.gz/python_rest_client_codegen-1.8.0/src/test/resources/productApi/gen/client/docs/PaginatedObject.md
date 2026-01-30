# PaginatedObject

An object which is not complete (only a specific page is available)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PagingMetadata**](PagingMetadata.md) |  | 

## Example

```python
from gen.client.models.paginated_object import PaginatedObject

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedObject from a JSON string
paginated_object_instance = PaginatedObject.from_json(json)
# print the JSON string representation of the object
print(PaginatedObject.to_json())

# convert the object into a dict
paginated_object_dict = paginated_object_instance.to_dict()
# create an instance of PaginatedObject from a dict
paginated_object_from_dict = PaginatedObject.from_dict(paginated_object_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


