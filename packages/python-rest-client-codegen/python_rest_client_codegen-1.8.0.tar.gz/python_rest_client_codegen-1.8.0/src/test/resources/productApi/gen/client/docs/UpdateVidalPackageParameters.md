# UpdateVidalPackageParameters


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**vidal_package_id** | **int** | Vidal package to set | [optional] 

## Example

```python
from gen.client.models.update_vidal_package_parameters import UpdateVidalPackageParameters

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateVidalPackageParameters from a JSON string
update_vidal_package_parameters_instance = UpdateVidalPackageParameters.from_json(json)
# print the JSON string representation of the object
print(UpdateVidalPackageParameters.to_json())

# convert the object into a dict
update_vidal_package_parameters_dict = update_vidal_package_parameters_instance.to_dict()
# create an instance of UpdateVidalPackageParameters from a dict
update_vidal_package_parameters_from_dict = UpdateVidalPackageParameters.from_dict(update_vidal_package_parameters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


