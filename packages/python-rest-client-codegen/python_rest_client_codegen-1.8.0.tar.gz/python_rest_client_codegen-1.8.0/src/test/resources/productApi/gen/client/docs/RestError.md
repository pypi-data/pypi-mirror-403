# RestError


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **str** | Unique code to identify an error : * &#x60;CODE000&#x60; - Using outdated resource * &#x60;CODE001&#x60; - Invalid credentials * &#x60;CODE002&#x60; - Cannot renew token * &#x60;CODE003&#x60; - Invalid User CGV * &#x60;CODE004&#x60; - Resource already exists * &#x60;CODE005&#x60; - User account is disabled * &#x60;CODE006&#x60; - Invalid schedule * &#x60;CODE007&#x60; - Wrong Address according CHRONOPOST * &#x60;CODE008&#x60; - Invalid Mangopay Mandate * &#x60;CODE009&#x60; - Invalid Status * &#x60;CODE010&#x60; - Empty Meta-Order * &#x60;CODE011&#x60; - Empty User Address * &#x60;CODE012&#x60; - Empty User Legal Name * &#x60;CODE013&#x60; - Invalid quantities * &#x60;CODE014&#x60; - Invalid Meta-Order * &#x60;CODE015&#x60; - Can not release quantity greater than claimed * &#x60;CODE016&#x60; - Can not release a negative quantity of items  | 
**message** | **str** | Unique code to identify an error : * &#x60;MESSAGE000&#x60; - Using outdated resource * &#x60;MESSAGE001&#x60; - Invalid credentials * &#x60;MESSAGE002&#x60; - Cannot renew token * &#x60;MESSAGE003&#x60; - Invalid User CGV * &#x60;MESSAGE004&#x60; - Resource already exists * &#x60;MESSAGE005&#x60; - User account is disabled * &#x60;MESSAGE006&#x60; - Invalid schedule * &#x60;MESSAGE007&#x60; - Wrong Address according CHRONOPOST * &#x60;MESSAGE008&#x60; - Invalid Mangopay Mandate * &#x60;MESSAGE009&#x60; - Invalid Status * &#x60;MESSAGE010&#x60; - Empty Meta-Order * &#x60;MESSAGE011&#x60; - Empty User Address * &#x60;MESSAGE012&#x60; - Empty User Legal Name * &#x60;MESSAGE013&#x60; - Invalid quantities * &#x60;MESSAGE014&#x60; - Invalid Meta-Order * &#x60;MESSAGE015&#x60; - Can not release quantity greater than claimed * &#x60;MESSAGE016&#x60; - Can not release a negative quantity of items  | 

## Example

```python
from gen.client.models.rest_error import RestError

# TODO update the JSON string below
json = "{}"
# create an instance of RestError from a JSON string
rest_error_instance = RestError.from_json(json)
# print the JSON string representation of the object
print(RestError.to_json())

# convert the object into a dict
rest_error_dict = rest_error_instance.to_dict()
# create an instance of RestError from a dict
rest_error_from_dict = RestError.from_dict(rest_error_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


