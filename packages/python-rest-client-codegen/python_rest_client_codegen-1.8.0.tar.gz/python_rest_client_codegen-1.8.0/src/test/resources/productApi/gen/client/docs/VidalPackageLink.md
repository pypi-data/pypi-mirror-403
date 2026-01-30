# VidalPackageLink


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**href** | **str** | Any URI that is using http or https protocol | 
**id** | **int** | Identifier of the vidal package | [optional] 

## Example

```python
from gen.client.models.vidal_package_link import VidalPackageLink

# TODO update the JSON string below
json = "{}"
# create an instance of VidalPackageLink from a JSON string
vidal_package_link_instance = VidalPackageLink.from_json(json)
# print the JSON string representation of the object
print(VidalPackageLink.to_json())

# convert the object into a dict
vidal_package_link_dict = vidal_package_link_instance.to_dict()
# create an instance of VidalPackageLink from a dict
vidal_package_link_from_dict = VidalPackageLink.from_dict(vidal_package_link_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


