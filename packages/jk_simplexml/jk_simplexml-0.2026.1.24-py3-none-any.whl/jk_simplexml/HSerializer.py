

import typing

from .HElement_HAbstractElementList import HElement
from .XMLWriteSettings import XMLWriteSettings

from .impl.HToolkit_Write_PlainText import HToolkit_Write_PlainText
from .impl.HToolkit_Write_XML import HToolkit_Write_XML
from .impl.HToolkit_Write_Dump import HToolkit_Write_Dump
from .impl.HToolkit_Write_HTML import HToolkit_Write_HTML

from jk_hwriter import HWriter as _HWriter







class HSerializer(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	writeXML = HToolkit_Write_XML.writeXML

	writeDump = HToolkit_Write_Dump.writeDump

	writeHTMLDoc = HToolkit_Write_HTML.writeHTMLDoc
	writeHTML = HToolkit_Write_HTML.writeHTML

	################################################################################################################################
	## Constructor
	################################################################################################################################

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

	@staticmethod
	def toXMLStr(root:HElement, xmlWriteSettings:XMLWriteSettings) -> str:
		w = _HWriter()
		HToolkit_Write_XML.writeXML(root, w, xmlWriteSettings)
		return str(w)
	#

	@staticmethod
	def printXML(root:HElement, xmlWriteSettings:XMLWriteSettings):
		w = _HWriter()
		HToolkit_Write_XML.writeXML(root, w, xmlWriteSettings)
		print(w)
	#

	# --------------------------------------------------------------------------------------------------------------------------------

	@staticmethod
	def toDumpStr(root:HElement, _ = None) -> str:
		w = _HWriter()
		HToolkit_Write_Dump.writeDump(root, w)
		return str(w)
	#

	@staticmethod
	def printDump(root:HElement, _ = None):
		w = _HWriter()
		HToolkit_Write_Dump.writeDump(root, w)
		print(w)
	#

	# --------------------------------------------------------------------------------------------------------------------------------

	"""
	writePlainText = HToolkit_Write_PlainText.writePlainText

	@staticmethod
	def toPlainText(root:HElement, _ = None) -> str:
		w = _HWriter()
		HToolkit_Write_PlainText.writePlainText(root, w)
		return str(w)
	#

	@staticmethod
	def printPlainText(root:HElement, _ = None):
		w = _HWriter()
		HToolkit_Write_PlainText.writePlainText(root, w)
		print(w)
	#
	"""

	# --------------------------------------------------------------------------------------------------------------------------------

	@staticmethod
	def toHTMLStr(root:HElement, _ = None) -> str:
		w = _HWriter()
		HToolkit_Write_HTML.writeHTML(root, w)
		return str(w)
	#

	@staticmethod
	def toHTMLDocStr(root:HElement, _ = None) -> str:
		w = _HWriter()
		HToolkit_Write_HTML.writeHTMLDoc(root, w)
		return str(w)
	#

	@staticmethod
	def printHTML(root:HElement, _ = None):
		w = _HWriter()
		HToolkit_Write_HTML.writeHTML(root, w)
		print(w)
	#

	@staticmethod
	def printHTMLDoc(root:HElement, _ = None):
		w = _HWriter()
		HToolkit_Write_HTML.writeHTMLDoc(root, w)
		print(w)
	#

#




