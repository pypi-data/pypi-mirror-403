# Barcodes


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cip** | **str** |  | [optional] 
**cip13** | **str** |  | [optional] 
**ean** | **str** |  | [optional] 

## Example

```python
from gen.client.models.barcodes import Barcodes

# TODO update the JSON string below
json = "{}"
# create an instance of Barcodes from a JSON string
barcodes_instance = Barcodes.from_json(json)
# print the JSON string representation of the object
print(Barcodes.to_json())

# convert the object into a dict
barcodes_dict = barcodes_instance.to_dict()
# create an instance of Barcodes from a dict
barcodes_from_dict = Barcodes.from_dict(barcodes_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


