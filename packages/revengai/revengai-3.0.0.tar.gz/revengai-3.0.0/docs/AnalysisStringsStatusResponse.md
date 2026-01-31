# AnalysisStringsStatusResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**BinariesTaskStatus**](BinariesTaskStatus.md) | The current status of the strings extraction task | 

## Example

```python
from revengai.models.analysis_strings_status_response import AnalysisStringsStatusResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisStringsStatusResponse from a JSON string
analysis_strings_status_response_instance = AnalysisStringsStatusResponse.from_json(json)
# print the JSON string representation of the object
print(AnalysisStringsStatusResponse.to_json())

# convert the object into a dict
analysis_strings_status_response_dict = analysis_strings_status_response_instance.to_dict()
# create an instance of AnalysisStringsStatusResponse from a dict
analysis_strings_status_response_from_dict = AnalysisStringsStatusResponse.from_dict(analysis_strings_status_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


