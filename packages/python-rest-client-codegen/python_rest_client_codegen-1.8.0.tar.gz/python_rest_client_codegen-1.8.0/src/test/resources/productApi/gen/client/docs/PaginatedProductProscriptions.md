# PaginatedProductProscriptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PagingMetadata**](PagingMetadata.md) |  | 
**records** | [**List[ProductProscription]**](ProductProscription.md) |  | 

## Example

```python
from gen.client.models.paginated_product_proscriptions import PaginatedProductProscriptions

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedProductProscriptions from a JSON string
paginated_product_proscriptions_instance = PaginatedProductProscriptions.from_json(json)
# print the JSON string representation of the object
print(PaginatedProductProscriptions.to_json())

# convert the object into a dict
paginated_product_proscriptions_dict = paginated_product_proscriptions_instance.to_dict()
# create an instance of PaginatedProductProscriptions from a dict
paginated_product_proscriptions_from_dict = PaginatedProductProscriptions.from_dict(paginated_product_proscriptions_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


