from restmapi.services import MAPIServices
from restmapi.services import SetPoint


__all__ = ['MAPIServices', 'SetPoint']


if __debug__:
	if MAPIServices.instance != None:		
		print(f"MAPI version: {MAPIServices.instance.get_version()}")


__author__  = "Xavier Dourille <xavier.dourille@enorise.com>"
# __version__ added below by build pipeline


__version__ = '1.0.5.0'
