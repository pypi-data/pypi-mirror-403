

from jk_hwriter import HWriter

from ..HElement_HAbstractElementList import *
from ..XMLWriteSettings import *
from ..ImplementationErrorException import ImplementationErrorException
from ._CompiledColorSchema import _CompiledColorSchema







class HToolkit_Write_XML(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	@staticmethod
	def _writeAsXML(root:HElement, xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, specialElements2:list, specialElements:list, w:HWriter):

		# ----

		if xmlWriteSettings.writeXmlHeader:
			w.write(ccs.c_m, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>", ccs.c_r)
			if xmlWriteSettings.printStyle != EnumXMLPrintStyle.SingleLine:
				w.writeLn()
		if specialElements2 is not None:
			for specialElement in specialElements2:
				w.write(ccs.c_s, specialElement, ccs.c_r)
				if xmlWriteSettings.printStyle != EnumXMLPrintStyle.SingleLine:
					w.writeLn()
		if specialElements is not None:
			for specialElement in specialElements:
				HToolkit_Write_XML.__writeXmlSpecialTag(specialElement, w)
				if xmlWriteSettings.printStyle != EnumXMLPrintStyle.SingleLine:
					w.writeLn()

		if xmlWriteSettings.printStyle == EnumXMLPrintStyle.Pretty:
			if xmlWriteSettings.checkInlineOverride is not None:
				if xmlWriteSettings.checkInlineOverride(None, root):
					HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, root, True, w)
				else:
					HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, root, False, w)
			else:
				HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, root, False, w)
		elif xmlWriteSettings.printStyle == EnumXMLPrintStyle.Simple:
			HToolkit_Write_XML.__addXmlSimple(xmlWriteSettings, ccs, root, False, w)
		elif xmlWriteSettings.printStyle == EnumXMLPrintStyle.SingleLine:
			HToolkit_Write_XML.__addXmlSingleLine(xmlWriteSettings, ccs, root, w)
			w.writeLn()
		else:
			raise ImplementationErrorException("(None)" if xmlWriteSettings is None else str(xmlWriteSettings.printStyle))
	#

	@staticmethod
	def __addXmlPretty(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, e:HElement, bForceInline:bool, w:HWriter):
		if bForceInline:
			HToolkit_Write_XML.__writeXmlOpeningTag(xmlWriteSettings, ccs, e, w)
			for eChild in e.children:
				if isinstance(eChild, HElement):
					HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, eChild, True, w)
				else:
					if isinstance(eChild, HText):
						HToolkit_Write_XML.__addXmlText(xmlWriteSettings, ccs, eChild, w)
					elif isinstance(eChild, HComment):
						HToolkit_Write_XML.__addXmlComment(xmlWriteSettings, ccs, eChild, w)
					else:
						raise ImplementationErrorException("(None)" if eChild is None else str(type(eChild)))
			HToolkit_Write_XML.__writeXmlClosingTag(xmlWriteSettings, ccs, e, w)
			return

		if len(e.children) == 0:
			HToolkit_Write_XML.__writeXmlOpeningClosingTag(xmlWriteSettings, ccs, e, w)
			w.writeLn()
		else:
			if e.hasOnlyTexts:
				HToolkit_Write_XML.__writeXmlOpeningTag(xmlWriteSettings, ccs, e, w)
				for eChild in e.children:
					if isinstance(eChild, HText):
						HToolkit_Write_XML.__addXmlText(xmlWriteSettings, ccs, eChild, w)
					elif isinstance(eChild, HComment):
						HToolkit_Write_XML.__addXmlComment(xmlWriteSettings, ccs, eChild, w)
					else:
						raise ImplementationErrorException("(None)" if eChild is None else str(type(eChild)))
				HToolkit_Write_XML.__writeXmlClosingTag(xmlWriteSettings, ccs, e, w)
				w.writeLn()
			else:
				HToolkit_Write_XML.__writeXmlOpeningTag(xmlWriteSettings, ccs, e, w)
				w.writeLn()
				w.incrementIndent()
				for eChild in e.children:
					if isinstance(eChild, HElement):
						if bForceInline:
							HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, eChild, True, w)
						else:
							bForceInlineNew = False if xmlWriteSettings.checkInlineOverride is None else xmlWriteSettings.checkInlineOverride(e, eChild)
							if bForceInlineNew:
								HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, eChild, bForceInlineNew, w)
								w.writeLn()
							else:
								HToolkit_Write_XML.__addXmlPretty(xmlWriteSettings, ccs, eChild, False, w)
					else:
						if isinstance(eChild, HText):
							HToolkit_Write_XML.__addXmlText(xmlWriteSettings, ccs, eChild, w)
							w.writeLn()
						elif isinstance(eChild, HComment):
							HToolkit_Write_XML.__addXmlComment(xmlWriteSettings, ccs, eChild, w)
							w.writeLn()
						else:
							raise ImplementationErrorException("(None)" if eChild is None else str(type(eChild)))
				w.decrementIndent()
				HToolkit_Write_XML.__writeXmlClosingTag(xmlWriteSettings, ccs, e, w)
				w.writeLn()
	#

	@staticmethod
	def __writeXmlOpeningTag(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, e:HElement, w:HWriter):
		w.write(
			ccs.c_d,
			"<",
			ccs.c_tn,
			e.name,
			ccs.c_r,
		)
		if len(e.attributes) > 0:
			for a in e.attributes:
				w.write(
					" ",
					ccs.c_an,
					a.name,
					ccs.c_d,
					"=",
					"\"",
					ccs.c_r
				)
				if ((a.value is not None) and (len(a.value) > 0)):
					HToolkit_Write_XML.__addXmlAttributeValue(xmlWriteSettings, ccs, a.value, w)
				w.write(
					ccs.c_d,
					"\"",
					ccs.c_r
				)
		w.write(
			ccs.c_d,
			">",
			ccs.c_r
		)
	#

	@staticmethod
	def __writeXmlOpeningClosingTag(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, e:HElement, w:HWriter):
		w.write(
			ccs.c_d,
			"<",
			ccs.c_tn,
			e.name,
			ccs.c_r
		)
		if len(e.attributes) > 0:
			for a in e.attributes:
				w.write(
					" ",
					ccs.c_an,
					a.name,
					ccs.c_d,
					"=",
					"\"",
					ccs.c_r
				)
				if ((a.value is not None) and (len(a.value) > 0)):
					HToolkit_Write_XML.__addXmlAttributeValue(xmlWriteSettings, ccs, a.value, w)
				w.write(
					ccs.c_d,
					"\"",
					ccs.c_r
				)
		w.write(
			ccs.c_d,
			"/>",
			ccs.c_r
		)
	#

	@staticmethod
	def __writeXmlClosingTag(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, e:HElement, w:HWriter):
		w.write(
			ccs.c_d,
			"</",
			ccs.c_tn,
			e.name,
			ccs.c_d,
			">",
			ccs.c_r
		)
	#

	@staticmethod
	def __addXmlAttributeValue(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, text:str, w:HWriter):
		if not text:
			return

		# ----

		if xmlWriteSettings.attributeEncoding == EnumXMLTextOutputEncoding.AlwaysAsIs:
			w.write(
				ccs.c_av,
				text,
				ccs.c_r,
				)
		elif xmlWriteSettings.attributeEncoding == EnumXMLTextOutputEncoding.EncodeReservedCharsAsEntities:
			sb = [ ccs.c_av ]
			for c in text:
				if c == "\"":
					sb.append("&quot")
				elif c == "&":
					sb.append("&amp")
				elif c == "<":
					sb.append("&lt")
				elif c == ">":
					sb.append("&gt")
				else:
					sb.append(c)
			sb.append(ccs.c_r)
			w.write(*sb)
		elif xmlWriteSettings.attributeEncoding == EnumXMLTextOutputEncoding.OnReservedCharsOutputTextAsCData:
			raise Exception("Attributes are not allowed to contain CData!")
		else:
			raise ImplementationErrorException("(None)" if xmlWriteSettings is None else str(xmlWriteSettings.attributeEncoding))
	#

	@staticmethod
	def __addXmlText(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, htext:HText, w:HWriter):
		text = htext.text
		if not text:
			return

		# ----

		if xmlWriteSettings.textEncoding == EnumXMLTextOutputEncoding.AlwaysAsIs:
			w.write(
				ccs.c_t,
				text.replace("\n", "\n" + ccs.c_t),
				ccs.c_r
				)
		elif xmlWriteSettings.textEncoding == EnumXMLTextOutputEncoding.EncodeReservedCharsAsEntities:
			sb = [ ccs.c_t ]
			for c in text:
				if c == "\n":
					sb.append("\n" + ccs.c_t)
				elif c == "\"":
					sb.append("&quot")
				elif c == "&":
					sb.append("&amp")
				elif c == "<":
					sb.append("&lt")
				elif c == ">":
					sb.append("&gt")
				else:
					sb.append(c)
			sb.append(ccs.c_r)
			w.write(*sb)
		elif xmlWriteSettings.textEncoding == EnumXMLTextOutputEncoding.OnReservedCharsOutputTextAsCData:
			if ((text.find("&") >= 0) or (text.find("\"") >= 0) or (text.find(">") >= 0) or (text.find("<") >= 0)):
				w.write(
					ccs.c_t,
					"<![CDATA["
					)
				if text.find("<![CDATA[") >= 0:
					raise Exception("Text may not contain \"<![CDATA[\"! Recursive CDATA-definitions are not allowed!")
				w.write(
					text.replace("\n", "\n" + ccs.c_t),
					"]]>",
					ccs.c_r)
			else:
				w.write(
					ccs.c_t,
					text.replace("\n", "\n" + ccs.c_t),
					ccs.c_r
					)
		else:
			raise ImplementationErrorException("(None)" if xmlWriteSettings is None else str(xmlWriteSettings.textEncoding))
	#

	@staticmethod
	def __addXmlComment(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, htext:HComment, w:HWriter):
		text = htext.text
		if not text:
			return

		# ----

		if xmlWriteSettings.textEncoding in (EnumXMLTextOutputEncoding.AlwaysAsIs, EnumXMLTextOutputEncoding.EncodeReservedCharsAsEntities, EnumXMLTextOutputEncoding.OnReservedCharsOutputTextAsCData):
			w.write(
				ccs.c_t,
				"<!--",
				text.replace("\n", "\n" + ccs.c_t),
				"-->",
				ccs.c_r
				)

		else:
			raise ImplementationErrorException("(None)" if xmlWriteSettings is None else str(xmlWriteSettings.textEncoding))
	#

	@staticmethod
	def __addXmlSingleLine(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, e:HElement, w:HWriter):
		if not e.children:
			HToolkit_Write_XML.__writeXmlOpeningClosingTag(xmlWriteSettings, ccs, e, w)
		else:
			HToolkit_Write_XML.__writeXmlOpeningTag(xmlWriteSettings, ccs, e, w)
			for eChild in e.children:
				if isinstance(eChild, HText):
					HToolkit_Write_XML.__addXmlText(xmlWriteSettings, ccs, eChild, w)
				elif isinstance(eChild, HComment):
					HToolkit_Write_XML.__addXmlComment(xmlWriteSettings, ccs, eChild, w)
				elif isinstance(eChild, HElement):
					HToolkit_Write_XML.__addXmlSingleLine(xmlWriteSettings, ccs, eChild, w)
				else:
					raise ImplementationErrorException("(None)" if eChild is None else str(type(eChild)))
			HToolkit_Write_XML.__writeXmlClosingTag(xmlWriteSettings, ccs, e, w)
	#

	@staticmethod
	def __addXmlSimple(xmlWriteSettings:XMLWriteSettings, ccs:_CompiledColorSchema, e:HElement, bParentIsMixedContent:bool, w:HWriter):
		if not e.children:
			HToolkit_Write_XML.__writeXmlOpeningClosingTag(xmlWriteSettings, ccs, ccs, e, w)
			w.writeLn()
		else:
			if e.children.hasTexts:
				HToolkit_Write_XML.__writeXmlOpeningTag(xmlWriteSettings, ccs, ccs, e, w)
				for eChild in e.children:
					if isinstance(eChild, HElement):
						HToolkit_Write_XML.__addXmlSimple(xmlWriteSettings, ccs, eChild, True, w)
					elif isinstance(eChild, HText):
						HToolkit_Write_XML.__addXmlText(xmlWriteSettings, ccs, ccs, eChild, w)
					elif isinstance(eChild, HComment):
						HToolkit_Write_XML.__addXmlComment(xmlWriteSettings, ccs, eChild, w)
					else:
						raise ImplementationErrorException("(None)" if eChild is None else str(type(eChild)))
				HToolkit_Write_XML.__writeXmlClosingTag(xmlWriteSettings, ccs, e, w)
				if not bParentIsMixedContent:
					w.writeLn()

			else:
				HToolkit_Write_XML.__writeXmlOpeningTag(xmlWriteSettings, ccs, e, w)
				w.writeLn()
				for eChild in e.children:
					if isinstance(eChild, HElement):
						HToolkit_Write_XML.__addXmlSimple(xmlWriteSettings, eChild, False, w)
					else:
						raise ImplementationErrorException("(None)" if eChild is None else str(type(eChild)))
				HToolkit_Write_XML.__writeXmlClosingTag(xmlWriteSettings, ccs, e, w)
				w.writeLn()
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

	@staticmethod
	def writeXML(root:HElement, w:HWriter, xmlWriteSettings:XMLWriteSettings):
		assert isinstance(root, HElement)
		assert isinstance(xmlWriteSettings, XMLWriteSettings)
		assert isinstance(w, HWriter)
		ccs = _CompiledColorSchema(xmlWriteSettings.colorSchema)

		HToolkit_Write_XML._writeAsXML(root, xmlWriteSettings, ccs, None, None, w)
	#

#










