# Product


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**any_type** | **object** |  | [optional] 
**id** | **int** |  | [optional] 
**vidal_package** | [**VidalPackageLink**](VidalPackageLink.md) |  | [optional] 
**is_automatic_vidal_sync_enabled** | **bool** | Indicates if automatic synchronization to vidal is enabled | [optional] 
**barcodes** | [**Barcodes**](Barcodes.md) |  | [optional] 
**name** | **str** |  | [optional] 
**short_name** | **str** |  | [optional] 
**dci** | **str** |  | [optional] 
**unit_weight** | **float** | Weight of a single unit in grams | [optional] 
**unit_price** | **float** | Public price of the product | [optional] 
**manufacturer_price** | **float** | Manufacturer price of the product | [optional] 
**type** | [**ProductType**](ProductType.md) |  | [optional] 
**secondary_type** | [**ProductSecondaryType**](ProductSecondaryType.md) |  | [optional] 
**laboratory** | [**LaboratoryLink**](LaboratoryLink.md) |  | [optional] 
**vat** | [**Vat**](Vat.md) |  | [optional] 
**narcotic_prescription** | **bool** |  | [optional] 
**storage_type** | **str** |  | [optional] 
**status** | [**ProductStatus**](ProductStatus.md) |  | [optional] 
**market_status** | [**ProductMarketStatus**](ProductMarketStatus.md) |  | [optional] 
**dispensation_place** | [**ProductDispensationPlace**](ProductDispensationPlace.md) |  | [optional] 
**is_otc** | **bool** |  | [optional] 
**is_drug_in_sport** | **bool** |  | [optional] 
**images** | [**HttpLink**](HttpLink.md) |  | [optional] 
**created_at** | **datetime** | Creation date of this product | [optional] 
**statistics** | [**Statistics**](Statistics.md) |  | [optional] 
**restricted** | **bool** | If True, can only be sold by LABORATORY. If False, it can be sold by anyone. | [optional] 
**proscriptions** | [**HttpLink**](HttpLink.md) |  | [optional] 

## Example

```python
from gen.client.models.product import Product

# TODO update the JSON string below
json = "{}"
# create an instance of Product from a JSON string
product_instance = Product.from_json(json)
# print the JSON string representation of the object
print(Product.to_json())

# convert the object into a dict
product_dict = product_instance.to_dict()
# create an instance of Product from a dict
product_from_dict = Product.from_dict(product_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


