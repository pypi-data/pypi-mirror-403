# AnyAuthenticationCredential


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant_type** | **str** | Action allowed by the request | 
**login** | **str** | User e-mail | 
**password** | **str** | User password | 
**refresh_token** | **str** |  | 

## Example

```python
from gen.client.models.any_authentication_credential import AnyAuthenticationCredential

# TODO update the JSON string below
json = "{}"
# create an instance of AnyAuthenticationCredential from a JSON string
any_authentication_credential_instance = AnyAuthenticationCredential.from_json(json)
# print the JSON string representation of the object
print(AnyAuthenticationCredential.to_json())

# convert the object into a dict
any_authentication_credential_dict = any_authentication_credential_instance.to_dict()
# create an instance of AnyAuthenticationCredential from a dict
any_authentication_credential_from_dict = AnyAuthenticationCredential.from_dict(any_authentication_credential_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


