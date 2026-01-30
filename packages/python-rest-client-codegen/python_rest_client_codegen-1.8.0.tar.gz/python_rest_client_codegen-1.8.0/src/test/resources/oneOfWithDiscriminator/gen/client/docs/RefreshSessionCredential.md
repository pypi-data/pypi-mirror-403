# RefreshSessionCredential


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**grant_type** | **str** | Action allowed by the request | 
**refresh_token** | **str** |  | 

## Example

```python
from gen.client.models.refresh_session_credential import RefreshSessionCredential

# TODO update the JSON string below
json = "{}"
# create an instance of RefreshSessionCredential from a JSON string
refresh_session_credential_instance = RefreshSessionCredential.from_json(json)
# print the JSON string representation of the object
print(RefreshSessionCredential.to_json())

# convert the object into a dict
refresh_session_credential_dict = refresh_session_credential_instance.to_dict()
# create an instance of RefreshSessionCredential from a dict
refresh_session_credential_from_dict = RefreshSessionCredential.from_dict(refresh_session_credential_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


