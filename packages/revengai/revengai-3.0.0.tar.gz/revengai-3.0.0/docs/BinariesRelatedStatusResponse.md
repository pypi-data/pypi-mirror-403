# BinariesRelatedStatusResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | The current status of the unpack binary task | 

## Example

```python
from revengai.models.binaries_related_status_response import BinariesRelatedStatusResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BinariesRelatedStatusResponse from a JSON string
binaries_related_status_response_instance = BinariesRelatedStatusResponse.from_json(json)
# print the JSON string representation of the object
print(BinariesRelatedStatusResponse.to_json())

# convert the object into a dict
binaries_related_status_response_dict = binaries_related_status_response_instance.to_dict()
# create an instance of BinariesRelatedStatusResponse from a dict
binaries_related_status_response_from_dict = BinariesRelatedStatusResponse.from_dict(binaries_related_status_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


