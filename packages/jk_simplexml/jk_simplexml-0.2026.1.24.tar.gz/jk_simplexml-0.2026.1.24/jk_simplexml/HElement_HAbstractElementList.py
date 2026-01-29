


import jk_prettyprintobj

# from __future__ import annotations		# allowed only in python3.7 and above

import typing

from .HAttribute import HAttribute
from .HText import HText
from .HComment import HComment
from .HAttributeList import HAttributeList
from .HAbstractElement import HAbstractElement




class HElement(HAbstractElement, jk_prettyprintobj.DumpMixin):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	def __init__(self, name:str, attributes = None, children = None):
		self.name = name
		self.attributes = HAttributeList(attributes)
		self.children = HAbstractElementList(children)
		self.tag = None
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def hasOnlyTexts(self) -> bool:
		return self.children.hasOnlyTexts
	#

	@property
	def hasTexts(self) -> bool:
		return self.children.hasTexts
	#

	@property
	def hasOnlyElements(self) -> bool:
		return self.children.hasOnlyElements
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	def _dumpVarNames(self) -> list:
		return [
			"name",
			"attributes",
			"children",
			"tag",
		]
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def append(self, item:HAbstractElement):
		if isinstance(item, HAttribute):
			a = self.attributes.getAttribute(item.name, False)
			if a:
				a.value = item.value
			else:
				self.attributes.append(item)
		else:
			self.children.append(item)
	#

	def add(self, item:HAbstractElement):
		if isinstance(item, HAttribute):
			a = self.attributes.getAttribute(item.name, False)
			if a:
				a.value = item.value
			else:
				self.attributes.append(item)
		else:
			self.children.append(item)
	#

	def __str__(self):
		if self.attributes:
			return self.name + " " + " ".join([ str(x) for x in self.attributes ])
		else:
			return self.name
	#

	def __repr__(self):
		if self.attributes:
			return self.name + " " + " ".join([ str(x) for x in self.attributes ])
		else:
			return self.name
	#

	def nameIs(self, name:str) -> bool:
		return self.name == name
	#

	def containsAttribute(self, name:str, possibleValues:typing.Union[tuple,list] = None) -> bool:
		a = self.attributes.getAttribute(name)
		if a is None:
			return False
		else:
			if possibleValues:
				for v in possibleValues:
					if a.value == v:
						return True
				return False
			else:
				return True
	#

	def hasAttribute(self, name:str, possibleValues:typing.Union[tuple,list] = None) -> bool:
		a = self.attributes.getAttribute(name)
		if a is None:
			return False
		else:
			if possibleValues:
				for v in possibleValues:
					if a.value == v:
						return True
				return False
			else:
				return True
	#

	def getAttribute(self, name:str, bCaseSensitive:bool = True) -> "HAttribute":
		return self.attributes.getAttribute(name, bCaseSensitive)
	#

	def getAttributeValue(self, name:str, bCaseSensitive:bool = True) -> str:
		return self.attributes.getAttributeValue(name, bCaseSensitive)
	#

	def containsChildElement(self, name:str):
		for c in self.children:
			if c.__class__.__name__ == "HElement":
				if c.name == name:
					return True
		return False
	#

	def hasChildElement(self, name:str):
		for c in self.children:
			if c.__class__.__name__ == "HElement":
				if c.name == name:
					return True
		return False
	#

	def containsChildElements(self, names:typing.Union[tuple,list]):
		ret = []
		for c in self.children:
			if c.__class__.__name__ == "HElement":
				for name in names:
					if c.name == name:
						ret.append(name)
		if ret:
			return ret
		else:
			return None
	#

	def hasChildElements(self, names:typing.Union[tuple,list]):
		ret = []
		for c in self.children:
			if c.__class__.__name__ == "HElement":
				for name in names:
					if c.name == name:
						ret.append(name)
		if ret:
			return ret
		else:
			return None
	#

	def setAttributeValue(self, name:str, value:str) -> "HAttribute":
		return self.attributes.setAttributeValue(name, value)
	#

	def createChildElement(self, name:str) -> "HElement":
		return self.children.createElement(name)
	#

	def getCreateChildElement(self, name:str) -> "HElement":
		return self.children.getCreateElement(name)
	#

	def createChildText(self, text:str) -> "HText":
		return self.children.createText(text)
	#

	def createChildComment(self, text:str) -> "HComment":
		return self.children.createComment(text)
	#

	def getAllText(self) -> str:
		return self.children.getAllText()
	#

	def removeChildElement(self, name:str) -> "HElement":
		return self.children.removeElement(name)
	#

	def getChildElement(self, name:str) -> "HElement":
		return self.children.getElement(name)
	#

	def getChildElements(self, name:str) -> list:
		return self.children.getElements(name)
	#

	def setChildText(self, text:str):
		return self.children.setText(text)
	#

	def toPlainText(self, HWriter) -> str:
		raise NotImplementedError()
	#

	def isDeepEqualTo(self, obj) -> bool:
		if isinstance(obj, HElement):
			if obj.name != self.name:
				return False
			if not obj.attributes.isDeepEqualTo(obj.attributes):
				return False
			return True
		else:
			return False
	#

	def isShallowEqualTo(self, obj) -> bool:
		if isinstance(obj, HElement):
			if obj.name != self.name:
				return False
			if not obj.attributes.isDeepEqualTo(obj.attributes):
				return False
			if not obj.children.isDeepEqualTo(obj.children):
				return False
			return True
		else:
			return False
	#

	def deepClone(self):
		e = HElement(self.name)
		e.attributes.extend([ x.deepClone() for x in self.attributes ])
		e.children.extend([ x.deepClone() for x in self.children ])
		return e
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#




class HAbstractElementList(list):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	def __init__(self, items = None):
		super().__init__(self)

		if items:
			for i in items:
				assert isinstance(i, HAbstractElement)
			self.extend(items)
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def hasOnlyTexts(self) -> bool:
		for a in self:
			if not isinstance(a, HText):
				return False
		return True
	#

	@property
	def hasTexts(self) -> bool:
		for a in self:
			if isinstance(a, HText):
				return True
		return False
	#

	@property
	def hasOnlyElements(self) -> bool:
		for a in self:
			if not isinstance(a, HText):
				return False
		return True
	#

	@property
	def hasElements(self) -> bool:
		for a in self:
			if isinstance(a, HElement):
				return True
		return False
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def add(self, item:HAbstractElement):
		self.append(item)
	#

	def isDeepEqualTo(self, other) -> bool:
		if isinstance(other, HAbstractElementList):
			if len(other) != len(self):
				return False
			for item, otherItem in zip(self, other):
				if not item.isDeepEqualTo(other):
					return False
			return True
		else:
			return False
	#

	def isShallowEqualTo(self, other) -> bool:
		if isinstance(other, HAbstractElementList):
			if len(other) != len(self):
				return False
			for item, otherItem in zip(self, other):
				if not item.isShallowEqualTo(other):
					return False
			return True
		else:
			return False
	#

	def removeAllText(self):
		for i in range(len(self) - 1, -1, -1):
			c = self[i]
			if c.__class__.__name__ == "HText":
				del self[i]
	#

	def removeAllElements(self):
		for i in range(len(self) - 1, -1, -1):
			c = self[i]
			if c.__class__.__name__ == "HElement":
				del self[i]
	#

	def setText(self, text:str):
		if text is None:
			raise Exception("text == None!")
		self.removeAllText()
		self.append(HText(text))
	#

	def getElement(self, name:str) -> "HElement":
		for c in self:
			if c.__class__.__name__ == "HElement":
				if c.name == name:
					return c
		return None
	#

	def getElements(self, name:str) -> list:
		ret = []
		for c in self:
			if c.__class__.__name__ == "HElement":
				if c.name == name:
					ret.append(c)
		return ret
	#

	def removeAt(self, index:int) -> "HElement":
		c = self[index]
		del self[index]
		return c
	#

	def removeElement(self, name:str) -> "HElement":
		for i in range(0, len(self)):
			c = self[i]
			if c.__class__.__name__ == "HElement":
				if c.name == name:
					del self[i]
					return c
		return None
	#

	def createElement(self, name:str) -> "HElement":
		c = HElement(name)
		self.append(c)
		return c
	#

	def getCreateElement(self, name:str) -> "HElement":
		for c in self:
			if c.__class__.__name__ == "HElement":
				if c.name == name:
					return c

		c = HElement(name)
		self.append(c)
		return c
	#

	def createText(self, text:str) -> "HText":
		c = HText(text)
		self.append(c)
		return c
	#

	def createComment(self, text:str) -> "HComment":
		c = HComment(text)
		self.append(c)
		return c
	#

	def getAllText(self) -> str:
		ret = []
		for c in self:
			if c.__class__.__name__ == "HText":
				ret.append(c.text)
		return "".join(ret)
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#




















