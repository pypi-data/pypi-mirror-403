


from .HAttribute import HAttribute



class HAttributeList(list):

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
				assert isinstance(i, HAttribute)
			self.extend(items)
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def names(self) -> list:
		return [
			a.name for a in self
		]
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def setAttributeValue(self, name:str, value:str) -> HAttribute:
		for a in self:
			if a.name == name:
				a.value = value
				return a
		a = HAttribute(name, value)
		self.append(a)
		return a
	#

	def add(self, name:str, value:str) -> HAttribute:
		a = HAttribute(name, value)
		self.append(a)
		return a
	#

	def getAttribute(self, name:str, bCaseSensitive:bool = True) -> HAttribute:
		if bCaseSensitive:
			for a in self:
				if a.name == name:
					return a
		else:
			name = name.lower()
			for a in self:
				if a.name.lower() == name:
					return a
		return None
	#

	def getAttributeValue(self, name:str, bCaseSensitive:bool = True) -> str:
		if bCaseSensitive:
			for a in self:
				if a.name == name:
					return a.value
		else:
			name = name.lower()
			for a in self:
				if a.name.lower() == name:
					return a.value
		return None
	#

	def remove(self, nameOrAttrObj, bCaseSensitive:bool = True) -> bool:
		if isinstance(nameOrAttrObj, str):
			if bCaseSensitive:
				for i in range(0, len(self)):
					if self[i].name == nameOrAttrObj:
						del self[i]
						return True
			else:
				nameOrAttrObj = nameOrAttrObj.lower()
				for i in range(0, len(self)):
					if self[i].name.lower() == nameOrAttrObj:
						del self[i]
						return True
			return False
		elif isinstance(nameOrAttrObj, HAttribute):
			nameOrAttrObj = nameOrAttrObj.name
			if bCaseSensitive:
				for i in range(0, len(self)):
					if self[i].name == nameOrAttrObj:
						del self[i]
						return True
			else:
				nameOrAttrObj = nameOrAttrObj.lower()
				for i in range(0, len(self)):
					if self[i].name.lower() == nameOrAttrObj:
						del self[i]
						return True
			return False
		else:
			raise Exception(str(type(nameOrAttrObj)))
		return False
	#

	def removeAll(self, name:str, bCaseSensitive:bool = True) -> bool:
		count = 0
		if bCaseSensitive:
			for i in range(len(self) - 1, -1, -1):
				if self[i].name == name:
					del self[i]
					count += 1
		else:
			name = name.lower()
			for i in range(len(self) - 1, -1, -1):
				if self[i].name.lower() == name:
					del self[i]
					count += 1
		return count
	#

	def isDeepEqualTo(self, obj) -> bool:
		if isinstance(obj, HAttributeList):
			if len(obj) != len(self):
				return False
			if len(self) == 0:
				return True
			n = len(self)
			for a1 in self:
				for a2 in obj:
					if a1.isEqualToDeep(a2):
						n -= 1
			return n == 0
		else:
			return False
	#

	def deepClone(self):
		return HAttributeList([
			x.clone() for x in self
		])
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#




















