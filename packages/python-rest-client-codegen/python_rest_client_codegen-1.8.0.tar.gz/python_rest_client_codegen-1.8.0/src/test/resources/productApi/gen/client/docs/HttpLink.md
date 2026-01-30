# HttpLink

A base type of objects representing links to resources.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**href** | **str** | Any URI that is using http or https protocol | 

## Example

```python
from gen.client.models.http_link import HttpLink

# TODO update the JSON string below
json = "{}"
# create an instance of HttpLink from a JSON string
http_link_instance = HttpLink.from_json(json)
# print the JSON string representation of the object
print(HttpLink.to_json())

# convert the object into a dict
http_link_dict = http_link_instance.to_dict()
# create an instance of HttpLink from a dict
http_link_from_dict = HttpLink.from_dict(http_link_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


