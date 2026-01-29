from multiprocessing import Value, connection
import psutil
import requests
import time
from signalr import Connection
from requests import Session
from threading import Thread
import gevent
import json
from json import JSONEncoder
import os

# signalr library has a bug, here is below a fix:
def Connection_close(self):
	gevent.kill(self._Connection__greenlet)
	while not self._Connection__greenlet.dead:
		gevent.sleep()
	self._Connection__transport.close()

Connection.close = Connection_close

class eStartWorkSpaceType:
	Start = 0
	Restart = 1
	ManualStart = 2

class eManualStartOption:
	_None = 0
	Silent = 1
	NoQuantityValues = 2
	Safeties = 4
	RestartFromBeginning = 8

class eStopReason:
	Interrupted = 0
	Terminated = 1

class MAPIService:
	""" Base class of every MAPI services that manages REST request commands
	"""
	def __init__(self, url = None):
		"""Construct a MAPIService from its base url.

		Parameters
		----------
		url : string, optional
			Base url from the service, by default the url is construct using environment variable MAPI_DEFAULT_URL or MAPI registry parameters else "http://localhost:80". 
		
		Raises
		------
		Exception
			If MAPI REST API is not activvated and url is not specified.
		"""
		if url == None:
			url = os.getenv('MAPI_DEFAULT_URL', None)					
		self._mapi_base_url = url
		if url == None:        			
			protocol = "http"
			hostname = "localhost"
			port = 80
			try:
				import winreg				
				key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\D2T\MORPHEE")
				protocol = winreg.QueryValueEx(key, "RESTProtocol")[0]
				hostname = winreg.QueryValueEx(key, "RESTServerName")[0]
				port = winreg.QueryValueEx(key, "RestPort")[0]
			except:
				pass
			if port == 0:
				raise Exception("REST MAPI is not activated. Go to UEditor MAPI configuration and set a REST port different from 0!")
			if protocol == "":
				protocol = "http"
			if hostname == "":
				hostname = "localhost"	
			self._mapi_base_url = f"{protocol}://{hostname}:{port}"
	
	@property
	def mapi_base_url(self) -> str:
		""" Base url of the MAPI object
		"""				
		return self._mapi_base_url			
		
	def invoke_web_request(self, sub_url, method="Get", body=None, raw=False):
		"""Invoke a REST request to the mapi service.

		Parameters
		----------
		sub_url : string
			Sub url to be added to mapi_base_url (including the query parameters if needed)
		method : string, optional
			Common REST verb (Get, Post, Delete, ...), by default "Get"
		body : object, optional
			Object to be added the body, by default None
		raw : bool, optional
			Define the format content, by default False. If true, the web request result is returned. Else, the body and the result are in json format and automatically parsed.

		Returns
		-------
		object
			The result of the REST request converted from json if raw is False

		Raises
		------
		Exception
			Sent by the server (in case of status code 500). The exception contains a json object with the server description
		Exception
			Sent when the status code is different from 200.
		Exception
			Sent when format is wrong (only if raw is False)
		"""
		url = f"{self._mapi_base_url}/{sub_url}".rstrip("/")
		
		if body is not None:
			if raw:
				res = requests.request(method, url, data=body)
			else:
				res = requests.request(method, url, json=body, headers={"Content-Type": "application/json"})
		else:
			res = requests.request(method, url)
		if  not raw and res.status_code == 500 and res.headers.get("Content-Type") and "json" in res.headers.get("Content-Type"):
			raise Exception(res.json())
		if res.status_code != 200:
			raise Exception(f"invoke_web_request on {url} error:status = {res.status_code}") 
		if not raw and res.headers.get("Content-Type") and "json" not in res.headers.get("Content-Type"):
			raise Exception(f"invoke_web_request on {url} error: bad content type = {res.headers.get('Content-Type')}")		
		if raw:
			return res
		else:
			if res.text == None or res.text == "":
				return None				
			return res.json()
		
	def invoke_web_get_request(self, sub_url):
		"""Invoke REST request with verb GET to the mapi service.

		Parameters
		----------
		sub_url : string
			Sub url to be added to mapi_base_url (including the query parameters if needed)

		Returns
		-------
		object
			The result of the REST request converted from json

		Raises
		------
		Exception
			Sent by the server (in case of status code 500). The exception contains a json object with the server description
		Exception
			Sent when the status code is different from 200.
		Exception
			Sent when format is wrong
		"""
		return self.invoke_web_request(sub_url)
	
	def invoke_web_post_request(self, sub_url):
		"""Invoke REST request with verb POST to the mapi service.

		Parameters
		----------
		sub_url : string
			Sub url to be added to mapi_base_url (including the query parameters if needed)

		Returns
		-------
		object
			The result of the REST request converted from json

		Raises
		------
		Exception
			Sent by the server (in case of status code 500). The exception contains a json object with the server description
		Exception
			Sent when the status code is different from 200.
		Exception
			Sent when format is wrong
		"""
		return self.invoke_web_request(sub_url, "POST")

class MAPIServiceWithSignalR(MAPIService):
	"""Manage signalR hub from MAPI services
	"""
	def __init__(self, url, hubName):
		"""Construct a MAPIServiceWithSignalR from its base url and hub name.

		Parameters
		----------
		url : string
			Base url from the service, by default the url is construct using MAPI registry parameters or "http://localhost:80" if the registry is not found. 
		hubName : string
			The signalR hub of the MAPI service.
		"""
		super().__init__(url)
		self.connection = None
		self.hub = None	
		self.session = None		
		self.disposed = False
		self.hubName = hubName
				
	def __enter__(self):
		return self	
	
	def __exit__(self, exception_type, exception_value, traceback):
		if self.connection != None:			
			self.disposed = True			
			self.thread.join(1)
			
	def init_signalr(self):
		"""Call init_signalr if you intend to use the signalr hub.
		Used with keyword on the MAPIServiceWithSignalR to be sure that the communication is closed at the end
		"""
		if self.session == None:	
			#self.connection.start()		
			self.thread = Thread(target=self.handle_signalr, args=[], daemon=True)	
			self.thread.start()
			while self.hub == None and self.thread.is_alive():
				time.sleep(0.1)								
	
	def handle_signalr(self):
		"""Internal thread method that manages the signalr communication
		"""
		self.session = Session()
		with self.session:				
			self.connection = Connection(self.get_signalr_hub_url(), self.session)
			self.hub = self.connection.register_hub(self.hubName)		
			with self.connection:					
				while not self.disposed:
					self.connection.wait(0.1)					
		
	def get_signalr_hub_url(self):
		"""Returns the signalr path of the MAPI service

		Returns
		-------
		string
			Signalr path
		"""
		return self.invoke_web_get_request("SignalRHubUrl")	        

class MAPIServices(MAPIService):
	"""MAPI services service is the main entry point of MAPI.
	A singleton attribute instance can be used to request other MAPI services (e.g. MAPIServices.instance.get_service("MorpheeProcessControl"))
	"""
	instance = None

	def __init__(self, url=None):
		"""Constructs a MAPI services. Usually you do not need to create a MAPIServices, we prefer using MAPIServices.instance.
		Note that if you need to connect a distant computer you should create your own MAPIServices object.

		Parameters
		----------
		url : string, optional
			Base url from the service (without api/Services), by default the url is construct using MAPI registry parameters or "http://localhost:80" if the registry is not found. 
		"""
		super().__init__(url)
		self._mapi_base_url = f"{self._mapi_base_url}/api/Services/"

	def get_available_rest_services(self):
		"""List of available MAPI services
		Note that the list change at runtime, if MORPHEE is started some new services are added to the list.

		Returns
		-------
		List of string
			Available service names.
		"""
		return self.invoke_web_get_request("List")

	def get_service(self, name):
		"""Query the MAPI service object proxy from its name

		Parameters	
		----------
		name : string
			MAPI service name (can be retrieved from get_available_rest_services() list)

		Returns
		-------
		object
			Proxy object that map every REST request of the service
		"""
		serviceDesc =  self.invoke_web_get_request(f"Service/{name}")
		objType = serviceDesc["DefaultProxyType"].replace("FEV.Morphee.MAPI.Service.xMODRESTServices.", "")
		objType = objType.replace("FEV.Morphee.MAPI.Internal.","")
		objType = objType.replace("FEV.Morphee.MAPI.","")
		objType = objType.split(",")[0]
		return eval(objType)(serviceDesc["URL"])

	def get_version(self):
		"""Current version of MAPI

		Returns
		-------
		string
			MAPI version
		"""
		return self.invoke_web_get_request("Version")

	def register_rest_service(self, name, contract, defaultProxyType, url, processId):
		"""Allow to register new MAPI service (internal usage only) 

		Parameters
		----------
		name : string
			New service name
		contract : string
			C# interface type of the contract
		defaultProxyType : string
			C# default proxy type class
		url : string
			Complete url of the new MAPI service
		processId : int
			Process id that manages the new MAPI service. If the process is killed, MAPI will remove automatically the registered service
		"""
		self.invoke_web_post_request(f"RegisterService?name={name}&contract={contract}&defaultProxyType={defaultProxyType}&url={url}&processId={processId}")

	def unregister_rest_service(self, name):
		"""Unregister a MAPI service previously registered with register_rest_service

		Parameters
		----------
		name : string
			MAPI service name
		"""
		self.invoke_web_post_request(f"UnregisterService?name={name}")		

class MorpheeProcessControlServiceProxy(MAPIServiceWithSignalR):
	"""MorpheeProcessControl MAPI service allows to control MORPHEE process:
	Test if MORPHEE is launched.
	Start MORPHEE.
	Manage MORPHEE report dialog.
	Call init_signalr if you intend to use the signalr hub events and with keyword on the MorpheeProcessControlServiceProxy object to be sure that the communication is closed at the end.
	"""
	def __init__(self, url):
		"""DO NOT create MorpheeProcessControlServiceProxy by yourself. Always use MAPIServices.get_service("MorpheeProcessControl") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url, "MorpheeProcessControl")
		
	def is_morphee_started(self):
		"""Check if morphee is started and MORPHEE MAPI REST services are available.
		Note that when MORPHEE starts, it can take some time before having MORPHEE MAPI REST services.
		You can is_morphee_process_started() to know that MORPHEE process is started.

		Returns
		-------
		bool
			Returns True if MORPHEE is started and available for REST requests.
		"""
		return self.invoke_web_get_request("IsMorpheeStarted")
	
	def is_morphee_process_started(self):
		"""Check if MORPHEE process is started. is_morphee_process_started() becomes true immediately after the process creation, but is_morphee_started() becomes true only when MORPHEE MAPI services are available.

		Returns
		-------
		bool
			Returns True if MORPHEE is started.
		"""
		return self.invoke_web_get_request("IsMorpheeProcessStarted")
	
	def get_number_of_instances(self):
		"""Get the number of MORPHEE instances including the master instance

		Returns
		-------
		int
			Number of MORPHEE instances
		"""
		return self.invoke_web_get_request("NumberOfInstances")

	def is_morphee_instance_started(self, instance):
		"""Check if morphee instance is started and MORPHEE MAPI REST services are available.
		Note that when MORPHEE starts, it can take some time before having MORPHEE MAPI REST services.
		You can is_morphee_instance_process_started() to know that MORPHEE process is started.

		Parameters
		----------
		instance : int
			Requested MORPHEE instance number

		Returns
		-------
		bool
			Returns True if MORPHEE is started and MORPHEE MAPI services are available
		"""
		return self.invoke_web_get_request(f"IsMorpheeInstanceStarted?instance={instance}")
	
	def is_morphee_instance_process_started(self, instance):
		"""Check if MORPHEE process is started. is_morphee_instance_process_started() becomes true immediately after the process creation, but is_morphee_instance_started() becomes true only when MORPHEE MAPI services are available.

		Parameters
		----------
		instance : int
			Requested MORPHEE instance number

		Returns
		-------
		bool
			Returns True if MORPHEE instance is started.
		"""
		return self.invoke_web_get_request(f"IsMorpheeInstanceProcessStarted?instance={instance}")

	def start(self, cmdLine = None, startAs = None, sessionId = None):
		"""Start MORPHEE.

		Parameters
		----------
		cmdLine : string, optional
			process command line arguments, by default None. For example, "-1" to start MORPHEE instance1.
		startAs : string, optional
			account used for starting the process, by default None.
			Values:
			- "lsa" Start the process as local system administrator account	
			- "morphee_interactive" Start the process as the current TM interactive user
			- "current" Start the process as the current windows login
			- "runas" Start the process using the administrator account (process will start by RunAs.exe application)
		sessionId : string, optional
			Current windows sessionId, by default None. When started in a RDP session, the current user session has to be set if you want to see the MORPHEE window into your RDP session.
			The method get_current_session_id should returns the current id.

		Returns
		-------
		Process
			Returns the MORPHEE process object.
		"""
		if cmdLine == None and startAs == None and sessionId == None:		
			pid = self.invoke_web_post_request("Start")
		else:
			query = ""
			if cmdLine != None:
				query = f"commandLine={cmdLine}&"
			if startAs != None:
				query += f"startAs={startAs}&"		
			if sessionId != None:
				query += f"sessionId={sessionId}&"
			query = query.rstrip("&")								
			pid = self.invoke_web_post_request(f"Start?{query}")								
		return psutil.Process(pid)

	def get_current_session_id(self):
		"""Get the current Windows session id (CAUTION that method fails for now).

		Returns
		-------
		int
			Current session id.
		"""
		return os.getsid(os.getpid())

	def is_report_pending(self, instance = 0):
		"""Check if a MORPHEE report is displayed. If yes, use get_report_messages to get the content.

		Parameters
		----------
		instance : int, optional
			MORPHEE instance number (0 master instance), by default 0.

		Returns
		-------
		bool
			Return if a MORPHEE report is displayed.
		"""
		return self.invoke_web_get_request(f"Report/{instance}/Pending")

	def get_report_messages(self, instance = 0):
		"""Get the content of a pending MORPHEE report window.

		Parameters
		----------
		instance : int, optional
			MORPHEE instance number (0 master instance), by default 0

		Returns
		-------
		ReportMessage array
			Returns an array of ReportMessage.
			The class RestReportMessage contains 3 parameters:
				- string severity ("Warning", "Error" or "FatalError")
				- string message
				- string source
		"""
		return self.invoke_web_get_request(f"Report/{instance}/Messages")

	def close_report(self, instance = 0, result = None):
		"""Close a pending MORPHEE report.
		Note that the report default button is OK if every messages are warning.
		If one message is an error or FatalError, the default button is Cancel.
		If one message is a FatalError, the OK button is disabled.

		Parameters
		----------
		instance : int, optional
			MORPHEE instance number (0 master instance), by default 0
		result : string, optional
			 A string convert from DialogResult enum ("OK" or "Cancel"). If the parameter is omitted, the report is closed using the default button.
		"""
		if result == None:		
			self.invoke_web_post_request(f"Report/{instance}/Close")
		else:
			self.invoke_web_post_request(f"Report/{instance}/Close?result={result}")

	def get_main_window_handles(self):
		"""Get MainWindow handles of morphee processes.

		Returns
		-------
		int array
			Returns MainWindow handles of morphee processes. You can use them to show/hide/activate MORPHEE main window.
		"""
		return self.invoke_web_get_request("MainWindowHandles")
		
	def register_started_callback(self, action):
		"""Register a signalR callback to be called when a MORPHEE instance is started.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with an int parameter
			A callback function with  a parameter (instance number who send the event (0 for master instance)).
		"""
		self.hub.client.on('MorpheeStarted', action)

	def register_stopped_callback(self, action):
		"""Register a signalR callback to be called when a MORPHEE instance is stopped.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with an int parameter
			A callback function with  a parameter (instance number who send the event (0 for master instance)).
		"""
		self.hub.client.on('MorpheeStopped', action)

	def register_report_updated_callback(self, action):
		"""Register a signalR callback to be called when a MORPHEE instance open or close a report dialog.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with an int parameter
			A callback function with  a parameter (instance number who send the event (0 for master instance)).
		"""
		self.hub.client.on('MorpheeReportUpdated', action)						

class MorpheeResultsServiceProxy(MAPIService):
	"""MORPHEEResults MAPI service allows to get MORPHEE result files"""
	def __init__(self, url=None):
		"""DO NOT create MorpheeResultsServiceProxy by yourself. Always use MAPIServices.get_service("MorpheeResults") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url)

	def list(self, filter, skip, count):
		"""Get the MorpheeResultProxy list of MORPHEE testrun results.

		Parameters
		----------
		filter : string
			Use filter to filter the list of URLs. We get only result folder that starts with filter. Note that filter must be the complete name of a subfolder with \ separator (e.g. master\TESTRESULTS) 
		skip : int
			0 based start page index
		count : int
			Number of testrun grouped by page

		Returns
		-------
		MorpheeResultProxy array
			List of MorpheeResultProxy. Each MorpheeResultProxy manages result files of a MORPHEE testrun.
		"""
		return [MorpheeResultProxy(url) for url in self.invoke_web_get_request(f"List?skip={skip}&count={count}&filter={filter}")]

class MorpheeResultProxy(MAPIService):
	"""MORPHEEResultProxy represents the results of one TestRun (it describe the content of one .files file)"""
	def __init__(self, url):
		"""DO NOT create MorpheeResultProxy by yourself. Always use MAPIServices.get_service("MorpheeResults").list() method to create one.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url)

	def get_files(self):
		"""Result files description. It returns the content of the .files.

		Returns
		-------
		MorpheeResultFileProxy array
			Each entry of the .files MORPHEE file.
		"""
		return [MorpheeResultFileProxy(self._mapi_base_url, url) for url in self.invoke_web_get_request("")]

class MorpheeResultFileProxy(MAPIService):
	"""MorpheeResultFileProxy is one MORPHEE result file"""
	def __init__(self, parent_url, entry):
		"""DO NOT create MorpheeResultFileProxy by yourself. Always use MorpheeResultProxy.get_files() method to create one.

		Parameters
		----------
		parent_url : string
			Base URL to create of the REST service.
		entry :
			Json object returned by the server		
					
		"""
		super().__init__(f"{parent_url}/{entry['id']}")
		self._group = entry['group']
		self._id = entry['id']
		self._local = entry['local']
		self._name = entry['name']
		self._storage_key = entry['storageKey']
		self._type = entry['type']

	@property
	def group(self) -> str:
		"""Point group name"""		
		return self._group		
				
	@property
	def id(self) -> str:
		"""Point file id (unique id used inside the url)"""		
		return self.id			
			
	@property
	def local(self) -> int:
		"""Integer value that defines the status of the file (-1 file is deleted, 0 the file is located one another computer, 1 local file"""		
		return self._local					
	
	@property
	def name(self) -> str:
		"""Full path of the result file"""		
		return self._name					
	
	@property
	def storage_key(self) -> str:
		"""Storage key name"""		
		return self._storage_key
						
	@property
	def type(self) -> str:
		"""File format (MASCII, CSV, MDF4,...)"""		
		return self._type					

	def get_raw_content(self):
		"""Get raw content of a MORPHEE result file. To be used on MDF4 files.

		Returns
		-------
		byte array
			Content of the file.
		"""
		return self.invoke_web_request("", "GET", None, True).content

	def get_text_content(self):
		"""Get text content of a MORPHEE result file. To be used on MASCII or CSV files.

		Returns
		-------
		string
			Content of the file.
		"""
		content = self.invoke_web_request("", "GET", None, True).text
		return content#.decode('utf-8')

class MeasurementProxy(MAPIService):
	"""MeasurementProxy is a dynamic object that manages a MORPHEE acquisition.
	Do not create it by ourself, it should be created by using a MeasurementManagerProxy object.
	Note that the object has to be deleted, so use with keyword on it!
	"""
	def __init__(self, url, id):
		"""DO NOT create MeasurementProxy by yourself. Always use MeasurementManagerProxy.create() or MeasurementManagerProxy.create_ex() methods to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(f"{url}/{id}")
		self._id = id	
	
	@property
	def id(self) -> int:
		"""Unique id of the MORPHEE measurement object"""		
		return self._id						

	def get_quantities(self):
		"""Get the list of quantities to measure. Only number quantities are supported.

		Returns
		-------
		string array
			Quantities id from the measurement.
		"""
		return self.invoke_web_get_request(f"Quantities")
	
	def set_quantities(self, quantities):
		"""Set the list of quantities to measure. Only number quantities are supported.

		Parameters
		----------
		quantities : string array
			New quantity id list.
		"""
		self.invoke_web_request(f"Quantities", "POST", quantities, False)

	def get_period(self):
		"""Get sampling period in second.

		Returns
		-------
		double
			Sampling period in second.
		"""
		return self.invoke_web_get_request(f"Period")

	def set_period(self, period):
		"""Set sampling period in second.

		Parameters
		----------
		period : double
			Sampling period in second.
		"""
		self.invoke_web_request(f"Period", "POST", period, False)

	def get_number_of_bloc_values(self):
		"""Get bloc number of values. Each time the buffer size reaches NumberOfBlocValues the event MeasurementBufferReady is raised.

		Returns
		-------
		uint
			Number of values per bloc.
		"""
		return self.invoke_web_get_request(f"NumberOfBlocValues")

	def set_number_of_bloc_values(self, number_of_bloc_values):
		"""Set bloc number of values. Each time the buffer size reaches NumberOfBlocValues the event MeasurementBufferReady is raised.

		Parameters
		----------
		number_of_bloc_values : uint
			Number of values per bloc.
		"""
		self.invoke_web_request(f"NumberOfBlocValues", "POST", number_of_bloc_values, False)		
	
	def get_number_of_values(self):
		"""Get total number of values. It defines the size of the internal buffer.

		Returns
		-------
		unit
			Total number of values.
		"""
		return self.invoke_web_get_request(f"NumberOfValues")

	def set_number_of_values(self, number_of_values):
		"""Set total number of values. It defines the size of the internal buffer.
		Note that duration and number_of_values cannot be both set.

		Parameters
		----------
		number_of_values : unit
			Total number of values.
		"""
		self.invoke_web_request(f"NumberOfValues", "POST", number_of_values, False)	
		
	def get_duration(self):
		"""Get duration of the measurement. Duration = NumberOfValues * Period.

		Returns
		-------
		double
			Duration of the acquisition buffer.
		"""
		return self.invoke_web_get_request(f"Duration")

	def set_duration(self, duration):
		"""Set duration of the measurement. Duration = NumberOfValues * Period.
		Note that duration and number_of_values cannot be both set.

		Parameters
		----------
		duration : double
			Duration of the acquisition buffer.
		"""
		self.invoke_web_request(f"Duration", "POST", duration, False)	
	
	def get_measurement_mode(self):
		"""Get the Measurement Mode. If MeasurementMode is OneShot (1), the measurement stop at the end of the Duration and NumberOfBlocValues is ignored. If MeasurementMode is Continuous (0), the measurement does not stop until you read the values with GetValues. If MeasurementMode is StepByStep (2), values are acquired at each TriggerGetValues call.

		Returns
		-------
		uint
			Continuous (0), OneShot (1), StepByStep (2).
		"""
		return self.invoke_web_get_request(f"MeasurementMode")

	def set_measurement_mode(self, measurement_mode):
		"""Set the Measurement Mode. If MeasurementMode is OneShot (1), the measurement stop at the end of the Duration and NumberOfBlocValues is ignored. If MeasurementMode is Continuous (0), the measurement does not stop until you read the values with GetValues. If MeasurementMode is StepByStep (2), values are acquired at each TriggerGetValues call.

		Parameters
		----------
		measurement_mode : uint
			Continuous (0), OneShot (1), StepByStep (2).
		"""
		self.invoke_web_request(f"MeasurementMode", "POST", measurement_mode, False)	
		
	def get_status(self):
		"""The current status of the Measurement. To change properties of the measurement, the Status should be Created.
		<div class="grid table-desc" markdown>
		| Created   |  0  |  Measurement is Created, properties can be set to configure it.                          |
		| Activated |  1  |  Measurement is Activated, properties can not be set. Measurement is ready to start.     |
		| Started   |  2  |  Measurement is Started. Use GetValues to retrieves the result buffer.                   |
		| Disposed  |  3  |  Measurement is Disposed. It could happen if the associated mode has stopped.            |
		| Unknown   |  4  |  Unknown state indicates a serious internal error.                                       |
		</div>

		Returns
		-------
		uint
			Current status
		"""
		return self.invoke_web_get_request(f"Status")
	
	def get_last_error(self):
		"""String error description of the last error. For example, after Activate method call, the user can get the reason why the activation was performed.

		Returns
		-------
		string
			Last error message.
		"""
		return self.invoke_web_get_request(f"LastError")

	def activate(self):
		"""Activate the measurement. During the activation, MORPHEE checks the properties. To activate the measurement, the Status should be Created. If it works the Status is set to Activated.

		Returns
		-------
		bool
			Returns True if all properties are correct.
		"""
		return self.invoke_web_get_request(f"Activate")
	
	def start(self):
		"""Start the measurement. To start the measurement, the Status should be Activated. If it works the Status is set to Started.

		Returns
		-------
		bool
			Returns False if the operation could not be performed. Use LastError property to have the description of the error.
		"""
		return self.invoke_web_get_request(f"Start")
	
	def stop(self):
		"""Stop the measurement. To stop the measurement, the Status should be Started. If it works the Status is set to Activated.

		Returns
		-------
		bool
			Returns False if the operation could not be performed. Use LastError property to have the description of the error.
		"""
		return self.invoke_web_get_request(f"Stop")
	
	def deactivate(self):
		"""Deactivate the measurement. During the activation, MORPHEE checks the properties. To Deactivate the measurement, the Status should be Activated. If it works the Status is set to Created.

		Returns
		-------
		bool
			Returns False if the operation could not be performed. Use LastError property to have the description of the error.
		"""
		return self.invoke_web_get_request(f"Deactivate")
	
	def get_values(self):
		"""return buffered values with timestamp as first columns.
		If MeasurementMode is Continuous, the buffer is cleared in order to continue the acquistion. If MeasurementMode is OneShot, the buffer values remains in buffer until you starts again the measurement.

		Returns
		-------
		double array
			Measurement values.
		"""
		return self.invoke_web_get_request(f"Values")
	
	def trigger_get_values(self):
		"""If MeasurementMode is StepByStep, it triggers the Measurement to get value at the next tick

		Returns
		-------
		bool
			Returns False if the operation could not be performed. Use LastError property to have the description of the error.
		"""
		return self.invoke_web_post_request(f"TriggerGetValues")

	def get_properties(self):
		"""Get Measurement object properties in Json format using one single request.

		Returns
		-------
		MeasurementProperties
			Returns an object with every properties of the measurement (only for read purpose).
		"""
		return self.invoke_web_get_request(f"")	
	
	def delete(self):
		"""Delete/Release Measurement object.
		After that, any call to the measurement raise an exception

		"""
		self.invoke_web_request(f"", "DELETE", None, True)
	
	def __enter__(self):
		return self	
	
	def __exit__(self, exception_type, exception_value, traceback):
		self.delete()

class MeasurementManagerProxy(MAPIServiceWithSignalR):
	"""MeasurementManagerProxy manages a MORPHEE acquisition by creating dynamically MeasurementProxy objects.
	Do not create it by ourself, it should be created by using a UserApplicationMonitoringProxy object or UserApplicationControlProxy object.
	Call init_signalr if you intend to use the signalr hub events and with keyword on the MeasurementManagerProxy object to be sure that the communication is closed at the end.
	"""
	def __init__(self, url):
		"""DO NOT create MeasurementManagerProxy by yourself. Always use MAPIServices.get_service("UserApplicationMonitoring").get_measurement_manager() or MAPIServices.get_service("UserApplicationControl").get_measurement_manager() methods to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url, "Measurement")

	def get_version(self):
		"""Current version of MAPI

		Returns
		-------
		string
			MAPI version
		"""
		return self.invoke_web_get_request("Version")
	
	def create_ex(self, workspace_index) -> MeasurementProxy:
		"""Create a new measurement.
		The measurement will be disposed automatically when the associated workspace stops.

		Parameters
		----------
		workspace_index : int
			0 based index of the workspace

		Returns
		-------
		MeasurementProxy
			Returns a MeasurementManagerProxy object. Use with keyword to automatically delete the object or use delete method explicitely.
		"""
		return MeasurementProxy(self._mapi_base_url, self.invoke_web_post_request(f"Create?mode={workspace_index}"))

	def create(self) -> MeasurementProxy:
		return MeasurementProxy(self._mapi_base_url, self.invoke_web_post_request(f""))

	def register_callback(self, measurement_id, event_name, action):
		"""Register a callback function.
		inti_signalr() method should be called first.

		Parameters
		----------
		measurement_id : int
			Id of the measurement.
		event_name : string
			Name of the event (BufferReady, BufferFull, StatusChanged, Disposed).
		action : function(instance, name, params)
			Callback function with 1 parameter (int: measurement_id) or with 2 (int: measurement_id, double[] values) for BufferReady.
		"""
		self.hub.server.invoke("Register", measurement_id, event_name)
		self.hub.client.off(event_name, action) # avoid that the same handler is registered twice
		self.hub.client.on(event_name, action)
	
class UserApplicationMonitoringProxy(MAPIServiceWithSignalR):
	"""UserApplicationMonitoring MAPI service allows to monitor a running MORPHEE application.
	For example, get MORPHEE status, get channel value, ...
	Call init_signalr if you intend to use the signalr hub events and with keyword on the UserApplicationMonitoring object to be sure that the communication is closed at the end.
	"""
	def __init__(self, url):
		"""DO NOT create UserApplicationMonitoringProxy by yourself. Always use MAPIServices.get_service("UserApplicationMonitoring") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url, "MorpheeEvent")

	def get_version(self):
		"""Current version of MAPI

		Returns
		-------
		string
			MAPI version
		"""
		return self.invoke_web_get_request("Version")

	def get_status(self):
		"""Get MORPHEE status. Be carefull it is differeent MORPHEE kernel status. It is a new set of values:
		<div class="grid table-desc" markdown>
		| Integer value | MORPHEE Status                 |
		|---------------|--------------------------------|
		|     1         | Start                          |
		|     2         | Security Red Level             |
		|     3         | Stop                           |
		|     4         | Running                        |
		|     5         | Security Orange level          |
		|     6         | Manual mode                    |
		|     7         | Suspended                      |
		|     8         | Error                          |
		|     9         | Bench mode loading/unloading   |
		|     10        | In mode Initializing cycle     |
		|     11        | In mode stopping cycle         |
		</div>

		Returns
		-------
		int
			Returns MORPHEE status
		"""
		return self.invoke_web_get_request("Status")

	def get_mode(self):
		"""Get Morphee current mode.
		* 0 for bench
		* 1 for campaign
		* 2 for test
		* Otherwise -1

		Returns
		-------
		int
			Returns Morphee current mode.
		"""
		return self.invoke_web_get_request("Mode")

	def get_channel_value(self, id):
		"""Get the value of a channel.

		Parameters
		----------
		id : string
			Id of a numerical quantity channel.

		Returns
		-------
		double
			Returns the current value of the quantity.
		"""
		return self.invoke_web_get_request(f"Channels/{id}/Value")

	def get_channel_text_value(self, id):
		"""Get a channel or constant value as a string.

		Parameters
		----------
		id : string
			Channel or Constant identifier

		Returns
		-------
		string
			Returns actual value of the channel or the constant.
		"""
		return self.invoke_web_get_request(f"Channels/{id}/TextValue")

	def get_channels_values(self, ids):
		"""Get channels values.
		If a channel does not exist an empty array is returned.

		Parameters
		----------
		ids : string array
			List of ids of a numerical quantities channel.

		Returns
		-------
		double array
			The result is an array of double that contains the value of each channels.
		"""
		return self.invoke_web_request("GetChannelsValues", "POST", ids)

	def get_dot_files_path(self):
		"""Get the path of the currently used .files file.

		Returns
		-------
		string
			Returns the path of the .files file.
		"""
		return self.invoke_web_get_request("FilesPath")

	def get_current_results(self):
		"""Result files description. It returns the content of the current .files.

		Returns
		-------
		MorpheeResultFileProxy array
			Each entry of the .files MORPHEE file.
		"""
		results = self.invoke_web_get_request("Results/current")
		return [MorpheeResultFileProxy(f"{self._mapi_base_url}/Results/current", result) for result in results]
	
	def get_bench_results(self):
		"""Result files description. It returns the content of the bench .files.

		Returns
		-------
		MorpheeResultFileProxy array
			Each entry of the .files MORPHEE file.
		"""
		results = self.invoke_web_get_request(f"Results/bench")
		return [MorpheeResultFileProxy(f"{self._mapi_base_url}/Results/bench", result) for result in results]
	
	def get_campaign_results(self):
		"""Result files description. It returns the content of the campaign .files.

		Returns
		-------
		MorpheeResultFileProxy array
			Each entry of the .files MORPHEE file.
		"""
		results = self.invoke_web_get_request(f"Results/campaign")
		return [MorpheeResultFileProxy(f"{self._mapi_base_url}/Results/campaign", result) for result in results]
	
	def get_test_results(self):
		"""Result files description. It returns the content of the test .files.

		Returns
		-------
		MorpheeResultFileProxy array
			Each entry of the .files MORPHEE file.
		"""
		results = self.invoke_web_get_request(f"Results/test")
		return [MorpheeResultFileProxy(f"{self._mapi_base_url}/Results/test", result) for result in results]

	def is_method_running(self, component, method):
		"""Test whether a method is running or not.

		Parameters
		----------
		component : string
			The component name that owns the method.
		method : string
			Method name.

		Returns
		-------
		bool
			Returns True if the method is running.
		"""
		return self.invoke_web_get_request(f"Components/Component/{component}/Methods/{method}/IsRunning")

	def get_quantities(self, skip, count):
		"""Get quantities name grouped by page.

		Parameters
		----------
		skip : int
			0 based index of the firs quantity of the page
		count : int
			Number of quantities in the page

		Returns
		-------
		string array
			Returns quantities name grouped by page.
		"""
		return self.invoke_web_get_request(f"Quantities/Ids?count={count}&skip={skip}")

	def get_component_quantities(self, component, skip, count):
		"""Get component quantities name grouped by page.

		Parameters
		----------
		component : string
			Component name (only the father name is sufficient).
		skip : int
			0 based index of the firs quantity of the page
		count : int
			Number of quantities in the page

		Returns
		-------
		string array
			Returns component quantities name grouped by page.
		"""
		return self.invoke_web_get_request(f"Components/Component/{component}/Quantities/Ids/?count={count}&skip={skip}")

	def get_quantities_properties(self, skip, count):
		"""Get quantities properties grouped by page.

		Parameters
		----------
		skip : int
			0 based start page index
		count : int
			Number of quantities per page

		Returns
		-------
		QuantityProperties array
			Returns quantities properties (see MORPHEE Quantities property description page).
		"""
		return self.invoke_web_get_request(f"Quantities/Properties?count={count}&skip={skip}")

	def get_component_quantities_properties(self, component, skip, count):
		"""Get component quantities properties

		Parameters
		----------
		component : string
			Component name (only the father name is sufficient).
		skip : int
			0 based start page index.
		count : int
			Number of quantities per page

		Returns
		-------
		QuantityProperties array
			Returns quantities properties (see MORPHEE Quantities property description page).
		"""
		return self.invoke_web_get_request(f"Components/Component/{component}/Quantities?count={count}&skip={skip}")

	def get_quantity_properties(self, id):
		"""Get quantity properties from quantity id.

		Parameters
		----------
		id : string
			Quantity id.

		Returns
		-------
		QuantityProperties
			Returns quantity properties (see MORPHEE Quantities property description page).
		"""
		return self.invoke_web_get_request(f"Quantities/Quantity/{id}")

	def get_quantity_value(self, id):
		"""Get quantity value from quantity id.
		Despite get_channel_text_value, all type are supported!

		Parameters
		----------
		id : string
			Quantity id.

		Returns
		-------
		string
			Returns quantity value from quantity id.
		"""
		return self.invoke_web_get_request(f"Quantities/Quantity/{id}/Value")

	def get_components(self, skip, count):
		"""Get components properties grouped by page.

		Parameters
		----------
		skip : int
			0 based index of the first component of the page
		count : int
			Number of components in the page

		Returns
		-------
		ComponentProperties array
			Component properties:
			<div class="grid table-desc" markdown>
			| **Type** | **Name** | **Description**                                     |
			|----------|----------|-----------------------------------------------------|
			| string   | name     | Father name of the component                        |
			| int      | mode     | Mode of the component (0 Bench, 1 Campaign, 2 Test) |
			| Method[] | methods  | Methods of the component                            |
			</div>
			Method properties:
			<div class="grid table-desc" markdown>
			| **Type** | **Name** | **Description**                           |
			|----------|----------|-------------------------------------------|
			| string   | name     | Method name                               |
			| bool     | isAlive  | Check if the method is currently running. |
			</div>
		"""
		return self.invoke_web_get_request(f"Components?count={count}&skip={skip}")

	def get_component(self, name):
		"""Get properties of a component from its name. 

		Parameters
		----------
		name : string
			Component father name

		Returns
		-------
		ComponentProperties
			Component properties:
			<div class="grid table-desc" markdown>
			| **Type** | **Name** | **Description**                                     |
			|----------|----------|-----------------------------------------------------|
			| string   | name     | Father name of the component                        |
			| int      | mode     | Mode of the component (0 Bench, 1 Campaign, 2 Test) |
			| Method[] | methods  | Methods of the component                            |
			</div>
			Method properties:
			<div class="grid table-desc" markdown>
			| **Type** | **Name** | **Description**                           |
			|----------|----------|-------------------------------------------|
			| string   | name     | Method name                               |
			| bool     | isAlive  | Check if the method is currently running. |
			</div>
		"""
		return self.invoke_web_get_request(f"Components/Component/{name}")

	def get_storage_keys(self, mode_name):
		"""List of available storage keys.

		Parameters
		----------
		mode_name : string
			Name of the mode (bench, campaign, test, current).

		Returns
		-------
		string array
			List of stoage keys of a mode.
		"""
		return self.invoke_web_get_request(f"StorageKeys/{mode_name}")

	def get_storage_key(self, name, mode_name):
		"""Get properties of a storage key.

		Parameters
		----------
		name : string
			Name of the storageKey
		mode_name : string
			Name of the mode (bench, campaign, test, current).

		Returns
		-------
		StorageKeyProperties
			Storage key properties
			<div class="grid table-desc" markdown>
			| **Type**               | **Name**         | **Description**                                                                 |
			|------------------------|------------------|---------------------------------------------------------------------------------|
			| string                 | name             | File group name                                                                 |
			| string                 | CurrentFilePath  | Current point file name                                                         |
			| string                 | LastFilePath     | Previous point file name                                                        |
			| bool                   | IsOpen           | True, if the point file is opened (that means that you cannot open it directly) |
			| int                    | NumberOfPoints   | Number of point written into the file                                           |
			</div>

		"""
		return self.invoke_web_get_request(f"StorageKeys/{mode_name}/{name}")

	def get_storage_key_quantities(self, name, mode_name):
		"""List of quantities to be stored into the file.

		Parameters
		----------
		name : string
			Name of the storageKey.
		mode_name : string
			Name of the mode (bench, campaign, test, current).

		Returns
		-------
		string array
			Quantities name.
		"""
		return self.invoke_web_get_request(f"StorageKeys/{mode_name}/{name}/Quantities")

	def get_measurement_manager(self) -> MeasurementManagerProxy:
		"""Get Measurement manager object that manages acquisition Measurement objects.

		Returns
		-------
		MeasurementManagerProxy
			Returns Measurement manager.
		"""
		return MeasurementManagerProxy(f"{self._mapi_base_url}/Measurement/")
	
	def register_callback(self, event_name, action):
		"""Register a callback function.
		inti_signalr() method should be called first.

		Parameters
		----------
		event_name : string
			MORPHEE event name. See MORPHEE documentation for default event names (e.g. "$BenchSarted").
		action : function(instance, name, params)
			Callback function with 3 parameters (int: MORPHEE instancenumber, string: name of the event, string: extra parameters).
		"""
		self.hub.server.invoke("register", event_name)
		self.hub.client.off('OnMorpheeEvent', action) # avoid that the same handler is registered twice
		self.hub.client.on('OnMorpheeEvent', action)
		
class SetPoint:
	""" A setpoint contains a channel identifier, the target value and the duration in second.
	Use SetPoint class as parameter of UserApplicationControlProxy.set_channels_values.
		"""
	def __init__(self, id, value, duration):
		"""Create a set point to be used by UserApplicationControlProxy.set_channels_values method

		Parameters
		----------
		id : string
			Channel id
		value : double
			Target channel value
		duration : double
			Duration in second
		"""
		self.Id = id
		self.Value = value
		self.Duration = duration

class UserApplicationControlProxy(UserApplicationMonitoringProxy):
	"""UserApplicationControl MAPI service allows to control a running MORPHEE application.
	For example, get MORPHEE status, get or set channel value, start component method...
	Call init_signalr if you intend to use the signalr hub events and with keyword on the UserApplicationControl object to be sure that the communication is closed at the end.
		"""
	def __init__(self, url):
		"""DO NOT create UserApplicationControlProxy by yourself. Always use MAPIServices.get_service("UserApplicationControl") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url)

	def set_channel_value(self, channel_name, value, duration_in_seconds):
		"""Set the value of a channel.

		Parameters
		----------
		channel_name : string
			Id of a numerical quantity channel
		value : double
			new value.
		duration_in_seconds : double
			Duration of the slope. Put 0 to set the channel immediatly.
		"""
		self.invoke_web_post_request(f"Channels/{channel_name}/SetValue?value={value}&duration={duration_in_seconds}")

	def set_channels_values(self, set_point_array):
		"""Set multiple channel value

		Parameters
		----------
		set_point_array : Array of SetPoint
			List of set points to be applied in one request. A setpoint contains a channel identifier, the target value and the duration in second.
		"""
		self.invoke_web_request(f"SetChannelsValues", "POST", [x.__dict__ for x in set_point_array])

	def start_method(self, component_name, method_name, loop = False, exit_proc = True):
		"""Start a method in a MORPHEE service.
		To start a method from the current test description use "TEST" keywords and for campaign description use "CAMPAIGN" keyword and for bench mode use "BENCH" keyword.

		Parameters
		----------
		component_name : string
			The component name that owns the method (only the father name is sufficient).
		method_name : string
			Method name to be started.
		loop : bool, optional
			true to use an autorepeat service, by default False
		exit_proc : bool, optional
			true to use a service "Hold with procedure", by default True
		"""
		self.invoke_web_post_request(f"Components/Component/{component_name}/Methods/{method_name}/Start?loop={loop}&exitWithProc={exit_proc}")		

	def stop_method(self, component_name, method_name):
		"""Stop a method that runs in a MORPHEE service

		Parameters
		----------
		component_name : string
			The component name that owns the method (only the father name is sufficient).
		method_name : string
			Method name to be stopped.
		"""
		self.invoke_web_post_request(f"Components/Component/{component_name}/Methods/{method_name}/Stop")		

	def set_quantity_table(self, quantity_name, values):
		"""Set quantity table/LUT content values

		Parameters
		----------
		quantity_name : string
			Quantity table/lut id.
		values : double array array
			Matrix values
		"""
		self.invoke_web_request(f"QuantityTable/{quantity_name}/SetValue", "POST", values)				

	def storage_key_add_point(self, name, index):
		"""Add new point in current file.

		Parameters
		----------
		name : string
			Name of the storageKey (you can get available storage keys by calling get_storage_keys())
		index : string
			name of the mode (bench, campaign, test, current)
		"""
		self.invoke_web_post_request(f"StorageKeys/{index}/{name}/AddPoint")	

	def storage_key_start_acquisition(self, name, index, period_ms, duration_ms):
		"""Start periodic acquisition into current file

		Parameters
		----------
		name : string
			Name of the storageKey (you can get available storage keys by calling get_storage_keys()).
		index : string
			name of the mode (bench, campaign, test, current).
		period_ms : double
			acquisition period in milliseconde
		duration_ms : double
			duration in millisecondes. -1 for infinite
		"""
		self.invoke_web_post_request(f"StorageKeys/{index}/{name}/StartAcquisition?periodMs={period_ms}&durationMs={duration_ms}")	

	def storage_key_stop_acquisition(self, name, index):
		"""Stop pending acquisition.

		Parameters
		----------
		name : string
			Name of the storageKey (you can get available storage keys by calling get_storage_keys()).
		index : string
			name of the mode (bench, campaign, test, current).
		"""
		self.invoke_web_post_request(f"StorageKeys/{index}/{name}/StopAcquisition")	

	def storage_key_undo_last_point(self, name, index):
		"""Remove last point (Note that some file format such as MDF do not support that method)

		Parameters
		----------
		name : string
			Name of the storageKey (you can get available storage keys by calling get_storage_keys()).
		index : string
			name of the mode (bench, campaign, test, current).
		"""
		self.invoke_web_post_request(f"StorageKeys/{index}/{name}/UndoLastPoint")

	def storage_key_create_new_file(self, name, index):
		"""Initialize a brand new file.

		Parameters
		----------
		name : string
			Name of the storageKey (you can get available storage keys by calling get_storage_keys()).
		index : string
			name of the mode (bench, campaign, test, current).
		"""
		self.invoke_web_post_request(f"StorageKeys/{index}/{name}/CreateNewFile")			

class MorpheeRuntimeControlProxy(MAPIServiceWithSignalR):
	"""MorpheeRuntimeControl MAPI service allows to start/stop MORPHEE modes.
	Call init_signalr if you intend to use the signalr hub events and with keyword on the MorpheeRuntimeControlServiceProxy object to be sure that the communication is closed at the end.
		"""
	def __init__(self, url):
		"""DO NOT create MorpheeRuntimeControlServiceProxy by yourself. Always use MAPIServices.get_service("MorpheeRuntimeControl") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url, "MorpheeRuntimeControl")

	def get_current_mode(self):
		"""Get Morphee current mode.
		* 0 for Unknown
		* 1 for bench
		* 2 for campaign
		* 3 for test

		Returns
		-------
		int
			Returns Morphee current mode.
		"""
		return self.invoke_web_get_request("CurrentMode")

	def get_current_status(self):
		"""Get MORPHEE status. Be carefull it is differeent MORPHEE kernel status. It is a new set of values:
		<div class="grid table-desc" markdown>
		| Integer value | MORPHEE Status                 |
		|---------------|--------------------------------|
		|     0         | Loading/Unloading              |
		|     1         | Running                        |
		|     2         | Security                       |
		|     3         | Restarting                     |
		|     4         | Manual                         |
		</div>

		Returns
		-------
		int
			Returns MORPHEE status
		"""
		return self.invoke_web_get_request("CurrentStatus")

	def get_main_window_handle(self):
		"""Get MainWindow handle of morphee.

		Returns
		-------
		int
			Returns MainWindow handle of morphee. You can use them to show/hide/activate MORPHEE main window.
		"""
		return self.invoke_web_get_request("Windows/Main")["value"]

	def get_monproc_window_handle(self):
		"""Get procedure monitor Window handle of morphee.

		Returns
		-------
		int
			Returns procedure monitor handle of morphee. You can use them to show/hide/activate MORPHEE procedure monitor window.
		"""
		return self.invoke_web_get_request("Windows/MonitorProc")["value"]

	def can_stop_mode(self) -> bool:
		"""Check if MORPHEE can stop current mode.

		Returns
		-------
		int
			Returns true if MORPHEE can stop current mode.
		"""
		return self.invoke_web_get_request("CanStopCurrentMode")	

	def stop_current_mode(self):
		"""Stop current running mode.
		"""
		self.invoke_web_post_request("StopCurrentMode")		

	def can_change_mode(self, newMode) -> bool:
		"""Check if MORPHEE can start a specific mode.

		Parameters
		----------
		int/string : new mode (Bench, Campaign, Test) or (1, 2, 3)

		Returns
		-------
		int
			Returns true if MORPHEE can stop current mode.
		"""
		return self.invoke_web_get_request(f"CanChangeMode?mode={newMode}")	

	def start_campaign(self, filename: str = "default", silent: bool = True):
		"""Start a campaign.

		Parameters
		----------
		string : campaign file name (without extension) or campaign full path (with extension)
		bool : silent. True for silent mode (loading report error dialog are skipped).

		"""
		self.invoke_web_post_request(f"StartCampaign?filename={filename}&startType=Start&silent={silent}")

	def start_test(self, filename: str, silent: bool = True, startType: eStartWorkSpaceType = eStartWorkSpaceType.Start, manualStartOption: eManualStartOption = eManualStartOption._None, chainingIndex: int = -1, chainingMax: int = 0):
		"""Start a test. Note that if MORPHEE is in bench mode, it will automatically start the default campaign first.

		Parameters
		----------
		string : test file name (without extension) or test full path (with extension)
		bool : silent. True for silent mode (loading report error dialog are skipped).
		eStartWorkSpaceType : startType. How to start the test.
		eManualStartOption : manualStartOption. If startType is ManualStart, use manualStartOption enum to set the configuration of the context handling. Note that it a flag enum si values can be combined (e.g. eManualStartOption.Silent+eManualStartOption.RestartFromBeginning)
		int : chainingIndex. Index of current test during a TM chaining (-1 is the default value)</param>
		int : chainingMax. Number of test of the current TM chaining (0 is the default value)</param>		

		"""
		self.invoke_web_post_request(f"StartTest?filename={filename}&startType={int(startType)}&silent={silent}&manualStartOption={int(manualStartOption)}&chainingIndex={chainingIndex}&chainingMax={chainingMax}")

	def set_foreground(self):
		"""Set MORPHEE to foreground (Note that MORPHEE has to be allowed to go to front of the current process. For instance TestManager allows MORPHEE to go to front.).
		"""
		self.invoke_web_post_request("SetForeGround")	

	def lock_menu_items(self):
		""" Deactivate start test and start campaigne menu items
		"""
		self.invoke_web_post_request("LockStartMenuItems")

	def unlock_menu_items(self):
		""" Reactivate start test and start campaigne menu items
		"""
		self.invoke_web_post_request("UnlockStartMenuItems")

	def update_test_run_xpar(self):
		""" Update the contents of the testrun.xpar file (Parameters file) of the current mode
		"""
		self.invoke_web_post_request("UpdateTestRunXpar")

	def client_connected(self):
		""" If MORPHEE is started with -v, MORPHEE waits for ClientConnected to be called!
		"""
		self.invoke_web_post_request("ClientConnected")

	def register_started_callback(self, action):
		"""Register a signalR callback to be called when a MORPHEE mode is started.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with an int parameter
			A callback function with 2 parameters (instance number who send the event (0 for master instance), morphee mode)
		"""
		self.hub.client.on('OnModeStarted', action)

	def register_stopped_callback(self, action):
		"""Register a signalR callback to be called when a MORPHEE mode is stopped.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with an int parameter
			A callback function with 2 parameters (instance number who send the event (0 for master instance), morphee mode, reason)
		"""
		self.hub.client.on('OnModeStopped', action)
	
	def register_error_callback(self, action):
		"""Register a signalR callback to be called when a MORPHEE mode failed to start.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with an int parameter
			A callback function with 2 parameters (instance number who send the event (0 for master instance), morphee mode).
		"""
		self.hub.client.on('OnModeError', action)

class AuthorityServiceServiceProxy(MAPIService):
	"""Authority MAPI service allows to get Authority info. Use the authority server to get authentification token that has to used in each web requests. 
	"""
	def __init__(self, url):
		"""DO NOT create AuthorityServiceServiceServiceProxy by yourself. Always use MAPIServices.get_service("Authority") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url)

	def info(self):
		""" returns authority info struct:
		* authMode: None or Flexlab or AzureAd
		* url: if authMode is Flexlab, url contains Flexlab server URL used for authentication.
		* clientId/tenantId: if authMode is AzureAd, clientId and tenantId define azure connection properties.
		"""
		return self.invoke_web_get_request("Info")

class SimulationControlRestServiceProxy(MAPIServiceWithSignalR):
	"""SimulationControl MAPI service allows to control simulations.
	"""
	def __init__(self, url):
		"""DO NOT create SimulationControlRestServiceProxy by yourself. Always use MAPIServices.get_service("SimulationControl") method to create it.

		Parameters
		----------
		url : string
			Base URL to create of the REST service.
		"""
		super().__init__(url, "SimulationControl")

	def start_simulation(self, name, xpar_parameters=None):
		"""Start new simulation

		Parameters
		----------
		name : string
			Simulation name
		xpar_parameters : bytes or string, optional
			XPAR parameters content, by default None
		"""
		url = f"start?name={name}"
		if xpar_parameters is not None:
			self.invoke_web_request(url, "POST", xpar_parameters, raw=True)
		else:
			self.invoke_web_post_request(url)

	def stop_simulation(self):
		"""Stop current simulation
		"""
		self.invoke_web_post_request("stop")

	def get_status(self):
		"""Get current simulation status

		Returns
		-------
		string
			Simulation status
		"""
		return self.invoke_web_get_request("status")

	def has_started(self):
		"""Get the information if the simulation has started

		Returns
		-------
		bool
			True if started
		"""
		return self.invoke_web_get_request("has_started")

	def pause_simulation(self):
		"""Pause current simulation
		"""
		self.invoke_web_post_request("pause")

	def resume_simulation(self):
		"""Resume current simulation
		"""
		self.invoke_web_post_request("resume")

	def get_current_name(self):
		"""Get current simulation name

		Returns
		-------
		string
			Simulation name
		"""
		return self.invoke_web_get_request("name")

	def get_simulation_progress(self):
		"""Get current simulation progress in percentage

		Returns
		-------
		int
			Progress percentage
		"""
		return self.invoke_web_get_request("progress")

	def delete_simulation(self, name):
		"""Delete simulation

		Parameters
		----------
		name : string
			Simulation name
		"""
		self.invoke_web_request(f"simulations/{name}", "DELETE")

	def get_simulations_list(self):
		"""Get list of all simulations

		Returns
		-------
		string array
			List of simulation names
		"""
		return self.invoke_web_get_request("simulations")

	def get_simulation_details(self, name):
		"""Get simulation details

		Parameters
		----------
		name : string
			Simulation name

		Returns
		-------
		SimulationDetails
			Simulation details object
		"""
		return self.invoke_web_get_request(f"simulations/{name}/details")

	def get_simulation_settings(self, name):
		"""Get simulation settings

		Parameters
		----------
		name : string
			Simulation name

		Returns
		-------
		SimulationSettings
			Simulation settings object
		"""
		return self.invoke_web_get_request(f"simulations/{name}/settings")

	def set_simulation_settings(self, name, settings):
		"""Set simulation settings

		Parameters
		----------
		name : string
			Simulation name
		settings : SimulationSettings
			Simulation settings object
		"""
		self.invoke_web_request(f"simulations/{name}/settings", "POST", settings)

	def get_variables(self, filter_str, format_str, skip=0, count=100):
		"""Get variables list

		Parameters
		----------
		filter_str : string
			Filter
		format_str : string
			Return format(json or string)
		skip : int, optional
			Number of variables to skip, by default 0
		count : int, optional
			Maximum number of variables to return, by default 100

		Returns
		-------
		object array
			List of variables
		"""
		return self.invoke_web_get_request(f"variables?filter={filter_str}&format={format_str}&skip={skip}&count={count}")

	def get_variables_values(self, names):
		"""Set variable value

		Parameters
		----------
		names : string array
			Quantity names

		Returns
		-------
		Variable array
			List of variables with values
		"""
		return self.invoke_web_request("variablesvalues", "POST", names)

	def get_channel_value(self, channel_name):
		"""Get channel current value

		Parameters
		----------
		channel_name : string
			Channel name

		Returns
		-------
		double
			Channel value
		"""
		return self.invoke_web_get_request(f"channels/{channel_name}/value")

	def get_table_value(self, table_name):
		"""Get table current value

		Parameters
		----------
		table_name : string
			Table name

		Returns
		-------
		string
			Table value
		"""
		return self.invoke_web_get_request(f"tables/{table_name}/value")

	def set_channel_value(self, channel_name, value):
		"""Set channel value

		Parameters
		----------
		channel_name : string
			Channel name
		value : double
			Value to be set
		"""
		self.invoke_web_request(f"channels/{channel_name}/value", "POST", value)

	def set_table_value(self, table_name, value):
		"""Set table value

		Parameters
		----------
		table_name : string
			Table name
		value : double array array
			Value to be set
		"""
		self.invoke_web_request(f"tables/{table_name}/value", "POST", value)

	def get_result_file(self, path, group, id):
		"""Get results file content

		Parameters
		----------
		path : string
			Results subfolder name
		group : string
			Section in .files
		id : string
			Id of the file

		Returns
		-------
		bytes
			File content
		"""
		return self.invoke_web_request(f"results/{path}/{group}/{id}", "GET", raw=True).content

	def get_result_files(self, path):
		"""Get results files

		Parameters
		----------
		path : string
			Results subfolder name

		Returns
		-------
		ResultFile array
			List of result files
		"""
		return self.invoke_web_get_request(f"results/{path}")

	def get_results_url_array(self, filter_str, skip=0, count=100):
		"""Get results array

		Parameters
		----------
		filter_str : string
			Filter
		skip : int, optional
			Number of results to skip, by default 0
		count : int, optional
			Maximum number of results to return, by default 100

		Returns
		-------
		string array
			List of result URLs
		"""
		return self.invoke_web_get_request(f"results/list?filter={filter_str}&count={count}&skip={skip}")

	def get_last_result(self):
		"""Get last results subfolder name

		Returns
		-------
		string
			Last result subfolder name
		"""
		return self.invoke_web_get_request("results/last")

	def get_last_log_files_zip(self):
		"""Get last log files zip archive

		Returns
		-------
		bytes
			Zip archive content
		"""
		return self.invoke_web_request("results/last_log_files", "GET", raw=True).content

	def get_last_report_messages(self):
		"""Get last report messages

		Returns
		-------
		RestReportMessage array
			List of report messages
		"""
		return self.invoke_web_get_request("results/last_report_messages")

	def get_parameters(self, name):
		"""Get parameters array for specific simulation

		Parameters
		----------
		name : string
			Simulation name

		Returns
		-------
		Parameter array
			List of parameters
		"""
		return self.invoke_web_get_request(f"simulations/{name}/parameters")
	
	def register_status_changed_callback(self, action):
		"""Register a signalR callback to be called when the simulation status changes.
		init_signalr() method has to be called before to initialize signalR communication.

		Parameters
		----------
		action : Function with a string parameter
			A callback function with a parameter (new status).
		"""
		self.hub.client.on('StatusChanged', action)

try:		
	MAPIServices.instance = MAPIServices()
	MAPIServices.instance.get_version()	
except:
	MAPIServices.instance = None

