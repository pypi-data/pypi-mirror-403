# ProductProscription


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** |  | [optional] 
**batch** | **str** |  | [optional] 
**created_at** | **datetime** |  | [optional] 

## Example

```python
from gen.client.models.product_proscription import ProductProscription

# TODO update the JSON string below
json = "{}"
# create an instance of ProductProscription from a JSON string
product_proscription_instance = ProductProscription.from_json(json)
# print the JSON string representation of the object
print(ProductProscription.to_json())

# convert the object into a dict
product_proscription_dict = product_proscription_instance.to_dict()
# create an instance of ProductProscription from a dict
product_proscription_from_dict = ProductProscription.from_dict(product_proscription_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


