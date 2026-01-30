# LoginCredential


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant_type** | **str** | Action allowed by the request | 
**login** | **str** | User e-mail | 
**password** | **str** | User password | 

## Example

```python
from gen.client.models.login_credential import LoginCredential

# TODO update the JSON string below
json = "{}"
# create an instance of LoginCredential from a JSON string
login_credential_instance = LoginCredential.from_json(json)
# print the JSON string representation of the object
print(LoginCredential.to_json())

# convert the object into a dict
login_credential_dict = login_credential_instance.to_dict()
# create an instance of LoginCredential from a dict
login_credential_from_dict = LoginCredential.from_dict(login_credential_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


