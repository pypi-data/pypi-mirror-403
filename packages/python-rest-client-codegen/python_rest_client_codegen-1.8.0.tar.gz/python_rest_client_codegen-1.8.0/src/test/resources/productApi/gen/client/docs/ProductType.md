# ProductType


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Id of the product type (machine name) | [optional] 
**name** | **str** | Readable name for display | [optional] 

## Example

```python
from gen.client.models.product_type import ProductType

# TODO update the JSON string below
json = "{}"
# create an instance of ProductType from a JSON string
product_type_instance = ProductType.from_json(json)
# print the JSON string representation of the object
print(ProductType.to_json())

# convert the object into a dict
product_type_dict = product_type_instance.to_dict()
# create an instance of ProductType from a dict
product_type_from_dict = ProductType.from_dict(product_type_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


