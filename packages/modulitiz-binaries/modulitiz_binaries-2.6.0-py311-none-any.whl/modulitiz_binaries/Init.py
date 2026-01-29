import os

from modulitiz_nano.ModuloPyinstaller import ModuloPyinstaller
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.init.AbstractInit import AbstractInit

ModuloPyinstaller.cdProjectsDir()

class Init(AbstractInit):
	NOMEFILE_ICONA="logo_icona.ico"
	
	__cartellaFileBinari: str|None=None
	__cartellaGeckoDriver: str|None=None
	
	@classmethod
	def getCartellaScriptCorrente(cls) -> str:
		return os.path.dirname(__file__)
	
	@classmethod
	def getCartellaFileBinari(cls)->str:
		if cls.__cartellaFileBinari is not None:
			return cls.__cartellaFileBinari
		cartellaFileBinari=os.path.normpath(ModuloFiles.pathJoin(cls.getCartellaScriptCorrente(),'binaries'))
		cls.__cartellaFileBinari=cartellaFileBinari
		return cartellaFileBinari
	
	@classmethod
	def getCartellaGeckoDriver(cls)->str:
		if cls.__cartellaGeckoDriver is not None:
			return cls.__cartellaGeckoDriver
		cartellaGeckoDriver=ModuloFiles.pathJoin(cls.getCartellaFileBinari(),'geckodriver')
		cls.__cartellaGeckoDriver=cartellaGeckoDriver
		return cartellaGeckoDriver
