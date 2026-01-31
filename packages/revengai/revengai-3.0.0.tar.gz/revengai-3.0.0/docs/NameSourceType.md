# NameSourceType


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** | The source (process) the function name came from | 
**function_id** | **int** |  | [optional] 
**binary_id** | **int** |  | [optional] 

## Example

```python
from revengai.models.name_source_type import NameSourceType

# TODO update the JSON string below
json = "{}"
# create an instance of NameSourceType from a JSON string
name_source_type_instance = NameSourceType.from_json(json)
# print the JSON string representation of the object
print(NameSourceType.to_json())

# convert the object into a dict
name_source_type_dict = name_source_type_instance.to_dict()
# create an instance of NameSourceType from a dict
name_source_type_from_dict = NameSourceType.from_dict(name_source_type_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


