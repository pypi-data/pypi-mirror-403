# Vat


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | Vat Id | [optional] 
**name** | **str** | Vat name | [optional] 
**value** | **float** | Vat value | [optional] 

## Example

```python
from gen.client.models.vat import Vat

# TODO update the JSON string below
json = "{}"
# create an instance of Vat from a JSON string
vat_instance = Vat.from_json(json)
# print the JSON string representation of the object
print(Vat.to_json())

# convert the object into a dict
vat_dict = vat_instance.to_dict()
# create an instance of Vat from a dict
vat_from_dict = Vat.from_dict(vat_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


