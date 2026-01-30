# AuthenticationCredential


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant_type** | **str** | Action allowed by the request | 

## Example

```python
from gen.client.models.authentication_credential import AuthenticationCredential

# TODO update the JSON string below
json = "{}"
# create an instance of AuthenticationCredential from a JSON string
authentication_credential_instance = AuthenticationCredential.from_json(json)
# print the JSON string representation of the object
print(AuthenticationCredential.to_json())

# convert the object into a dict
authentication_credential_dict = authentication_credential_instance.to_dict()
# create an instance of AuthenticationCredential from a dict
authentication_credential_from_dict = AuthenticationCredential.from_dict(authentication_credential_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


