# ProductProscriptionCreationParameters


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**batch** | **str** | The batch value | [optional] 

## Example

```python
from gen.client.models.product_proscription_creation_parameters import ProductProscriptionCreationParameters

# TODO update the JSON string below
json = "{}"
# create an instance of ProductProscriptionCreationParameters from a JSON string
product_proscription_creation_parameters_instance = ProductProscriptionCreationParameters.from_json(json)
# print the JSON string representation of the object
print(ProductProscriptionCreationParameters.to_json())

# convert the object into a dict
product_proscription_creation_parameters_dict = product_proscription_creation_parameters_instance.to_dict()
# create an instance of ProductProscriptionCreationParameters from a dict
product_proscription_creation_parameters_from_dict = ProductProscriptionCreationParameters.from_dict(product_proscription_creation_parameters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


