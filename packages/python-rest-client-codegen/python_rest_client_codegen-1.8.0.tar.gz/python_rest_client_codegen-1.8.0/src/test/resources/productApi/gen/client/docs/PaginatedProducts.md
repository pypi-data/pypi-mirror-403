# PaginatedProducts


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | [**PagingMetadata**](PagingMetadata.md) |  | 
**records** | [**List[Product]**](Product.md) |  | 

## Example

```python
from gen.client.models.paginated_products import PaginatedProducts

# TODO update the JSON string below
json = "{}"
# create an instance of PaginatedProducts from a JSON string
paginated_products_instance = PaginatedProducts.from_json(json)
# print the JSON string representation of the object
print(PaginatedProducts.to_json())

# convert the object into a dict
paginated_products_dict = paginated_products_instance.to_dict()
# create an instance of PaginatedProducts from a dict
paginated_products_from_dict = PaginatedProducts.from_dict(paginated_products_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


