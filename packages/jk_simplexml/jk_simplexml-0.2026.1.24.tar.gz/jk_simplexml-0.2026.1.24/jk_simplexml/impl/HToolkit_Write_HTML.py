




from jk_hwriter import HWriter

from jk_rawhtml.htmlgeneral import *
from jk_rawhtml._HTMLElementProto import _HTMLElementProto, HTMLElement
from jk_rawhtml._HTMLRawTextProto import _HTMLRawTextProto
from jk_rawhtml._HTMLTextProto import _HTMLTextProto
from jk_rawhtml.HTML5Scope import HTML5Scope

from ..HElement_HAbstractElementList import *






class HTMLScopeDefault(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	spanNameBegin = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eNameB"})
	spanElementName = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eElementName"})
	spanNameEnd = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eNameE"})
	spanAttributes = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eAttributes"})
	spanAttrName = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eAttrName"})
	spanAttrValue = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eAttrValue"})
	divText = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eText"})
	divTextInline = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eTextInline"})
	divMain = _HTMLElementProto("div", tagType=HTML_TAG_TYPE_STRUCTURE, extraAttributes={"class": "eElement"})
	divMainInline = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eElementInline"})
	divElement = _HTMLElementProto("div", tagType=HTML_TAG_TYPE_STRUCTURE, extraAttributes={"class": "eElementWrapper"})
	divElementInline = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_INLINE_ALL, extraAttributes={"class": "eElementWrapper"})
	divChildren = _HTMLElementProto("div", tagType=HTML_TAG_TYPE_STRUCTURE, extraAttributes={"class": "eElementChildren"})
	divChildrenInline = _HTMLElementProto("span", tagType=HTML_TAG_TYPE_STRUCTURE, extraAttributes={"class": "eElementChildrenInline"})

	raw_html = _HTMLRawTextProto()

	html = _HTMLTextProto()

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

	def __enter__(self):
		return self
	#

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#





class HToolkit_Write_HTML(object):

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
	def __convertElementToHTML(scope:HTMLScopeDefault, e:HElement, bInline:bool) -> HTMLElement:
		divMain = scope.divMainInline if bInline else scope.divMain
		divChildren = scope.divChildrenInline if bInline else scope.divChildren
		# build attribute list

		eAttrList = scope.spanAttributes()
		for a in e.attributes:
			if a.value:
				eAttrList.children.extend([
					scope.raw_html(" "),
					scope.spanAttrName()[
						a.name,
					],
					"=\"",
					scope.spanAttrValue()[
						a.value,
					],
					"\""
				])
			else:
				eAttrList.children.extend([
					scope.raw_html(" "),
					scope.spanAttrName()[
						a.name,
					],
				])

		bChildsInline = e.name in [ "h1", "h2", "h3", "a", "b", "i", "img", "span", "label", "strong" ]

		eChildrenList = []
		for c in e.children:
			if isinstance(c, HText):
				if bChildsInline:
					eChildrenList.append(scope.divTextInline()[
						c.text
					])
				else:
					eChildrenList.append(scope.divText()[
						c.text
					])
			else:
				eChildrenList.append(HToolkit_Write_HTML.__convertElementToHTML(scope, c, bInline or bChildsInline))

		if eChildrenList:
			if bChildsInline:
				return divMain()[
					scope.divElementInline()[
						scope.spanNameBegin()[
							"<",
							scope.spanElementName()[
								e.name
							],
						],
						eAttrList,
						scope.spanNameEnd()[
							">",
						],
						eChildrenList,
						scope.spanNameBegin()[
							"</",
							scope.spanElementName()[
								e.name
							],
						],
						scope.spanNameEnd()[
							">",
						]
					]
				]
			else:
				return divMain()[
					scope.divElement()[
						scope.spanNameBegin()[
							"<",
							scope.spanElementName()[
								e.name
							],
						],
						eAttrList,
						scope.spanNameEnd()[
							">",
						]
					],
					divChildren()[
						eChildrenList
					],
					scope.divElement()[
						scope.spanNameBegin()[
							"</",
							scope.spanElementName()[
								e.name
							],
						],
						scope.spanNameEnd()[
							">",
						]
					]
				]
		else:
			return divMain()[
				scope.divElement()[
					scope.spanNameBegin()[
						"<",
						scope.spanElementName()[
							e.name
						],
					],
					eAttrList,
					scope.spanNameEnd()[
						" />",
					]
				]
			]
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

	@staticmethod
	def writeHTMLDoc(root:HElement, w:HWriter):
		assert isinstance(root, HElement)
		assert isinstance(w, HWriter)

		H = HTML5Scope()
		scope = HTMLScopeDefault()

		htmlRoot = H.html()[
			H.head()[
				H.raw_style_css("""
					body {
						font-family: 'Courier New', Courier, monospace;
						font-size: 12px;
						background-color: #f0f0f0;
						color: #404040;
						font-weight: normal;
					}
					.eElement {
						margin-left: 20px;
					}
					.eElementInline {
					}
					.eElementChildren {
					}
					.eElementChildrenInline {
					}
					.eTextInline {
						color: #006000;
						background-color: #f0f8f0;
					}
					.eText {
						margin-left: 20px;
						color: #006000;
						background-color: #f0f8f0;
						display: block;
					}
					.eNameB {
						color: #000060;
					}
					.eElementName {
						background-color: #e8e8f8;
						font-weight: bold;
					}
					.eAttrName {
						font-weight: bold;
						color: #008080;
					}
					.eAttrValue {
						font-weight: bold;
						color: #808000;
					}
				""")
			],
			H.body()[
				HToolkit_Write_HTML.__convertElementToHTML(scope, root, False)
			]
		]

		htmlRoot._serialize(w)
	#

	@staticmethod
	def writeHTML(root:HElement, w:HWriter):
		assert isinstance(root, HElement)
		assert isinstance(w, HWriter)

		scope = HTMLScopeDefault()
		htmlElement = HToolkit_Write_HTML.__convertElementToHTML(scope, root, False)
		htmlElement._serialize(w)
	#

#










