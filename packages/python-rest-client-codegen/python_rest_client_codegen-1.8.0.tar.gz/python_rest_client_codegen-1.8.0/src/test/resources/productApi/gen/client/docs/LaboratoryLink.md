# LaboratoryLink


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**href** | **str** | Any URI that is using http or https protocol | 
**id** | **int** | Identifier of the laboratory | [optional] 
**name** | **str** | Name of the laboratory | [optional] 

## Example

```python
from gen.client.models.laboratory_link import LaboratoryLink

# TODO update the JSON string below
json = "{}"
# create an instance of LaboratoryLink from a JSON string
laboratory_link_instance = LaboratoryLink.from_json(json)
# print the JSON string representation of the object
print(LaboratoryLink.to_json())

# convert the object into a dict
laboratory_link_dict = laboratory_link_instance.to_dict()
# create an instance of LaboratoryLink from a dict
laboratory_link_from_dict = LaboratoryLink.from_dict(laboratory_link_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


