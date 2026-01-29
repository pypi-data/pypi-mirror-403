# REST MAPI Package

REST MAPI (MORPHEE API) package allows to control MORPHEE at runtime using MORPHEE REST API. MAPI main principle is to provide so called MAPI services. From MAPI, you should first ask for a specific service before using it. 

:information_source: Each service has access rights that could be set in UEditor.
## Install
To install restmapi pyhton module, run:
```python
pip install restmapi
```
## Example
Here a small example to start MORPHEE using REST MAPI.
```python
from restmapi.services import MAPIServices

with MAPIServices.instance.get_service("MorpheeProcessControl") as morphee_process_control:
	if morphee_process_control.is_morphee_process_started() != True:
		morphee_process_control.start()
```

## Documentation
You can find the full documentation ([here](https://download.enorise.com/DownloadPortal/uploads/help/PythonRestMapi/SimulationControl.html))

