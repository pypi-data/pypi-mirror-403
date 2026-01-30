# ImageVersions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**xsmall** | **str** | URI to S3 file (width 100px, height computed with original image aspect ratio) | [optional] 
**small** | **str** | URI to S3 file (width 350px, height computed with original image aspect ratio) | [optional] 
**medium** | **str** | URI to S3 file (width 1024px, height computed with original image aspect ratio) | [optional] 
**large** | **str** | URI to S3 file (width 1920px, height computed with original image aspect ratio) | [optional] 
**xlarge** | **str** | URI to S3 file (width 3840px, height computed with original image aspect ratio) | [optional] 
**original** | **str** | URI to S3 file (Original size) | [optional] 

## Example

```python
from gen.client.models.image_versions import ImageVersions

# TODO update the JSON string below
json = "{}"
# create an instance of ImageVersions from a JSON string
image_versions_instance = ImageVersions.from_json(json)
# print the JSON string representation of the object
print(ImageVersions.to_json())

# convert the object into a dict
image_versions_dict = image_versions_instance.to_dict()
# create an instance of ImageVersions from a dict
image_versions_from_dict = ImageVersions.from_dict(image_versions_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


