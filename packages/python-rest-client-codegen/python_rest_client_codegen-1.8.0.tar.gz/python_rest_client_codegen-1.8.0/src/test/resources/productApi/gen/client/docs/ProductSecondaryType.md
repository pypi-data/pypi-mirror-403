# ProductSecondaryType


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Id of the product secondary type | [optional] 
**name** | **str** | Readable name for display | [optional] 

## Example

```python
from gen.client.models.product_secondary_type import ProductSecondaryType

# TODO update the JSON string below
json = "{}"
# create an instance of ProductSecondaryType from a JSON string
product_secondary_type_instance = ProductSecondaryType.from_json(json)
# print the JSON string representation of the object
print(ProductSecondaryType.to_json())

# convert the object into a dict
product_secondary_type_dict = product_secondary_type_instance.to_dict()
# create an instance of ProductSecondaryType from a dict
product_secondary_type_from_dict = ProductSecondaryType.from_dict(product_secondary_type_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


