import urllib3
import regex
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

def getSongs():
	http = urllib3.PoolManager()
	r = http.request('GET', 'http://hikarinoakariost.info/')
	soup = BeautifulSoup(r.data, "lxml")

	recent = soup.find_all("div", "td-pb-span8 td-main-content")[0]
	units = recent.find_all("div", "td-block-span6")

	nSongs = len(units)

	songDetails = []
	i = 0

	for tag in units:
		songDetails.append([])
		songDetails[i].append([])
		songDetails[i].append([])
		songDetails[i][0] = tag.find_all("h3", "entry-title td-module-title")[0].string
		songDetails[i][1] = tag.find_all("div", "td-excerpt")[0].string
		i = i + 1


	for songs in songDetails:
		j = 0
		if songs[0] is not None:
			tags = songs[1].split("|")
			songs.append([])
			for iter in tags:
				if iter.strip() != "Album" and iter.strip() != "Single":
					songs[2].append([])
					songs[2][j] = iter.strip()
					j = j + 1

	r2 = http.request('GET', 'https://myanimelist.net/animelist/Shironi')
	malsoup = BeautifulSoup(r2.data, "lxml")

	list = malsoup.find_all("table")[0]['data-items']
	list = regex.findall(r'(?<="anime_title":").+?(?=")', list, flags=regex.IGNORECASE)

	wantedSongs = []

	for anime in list:
		for songs in songDetails:
			if songs[0] is not None:
				for tag in songs[2]:
					results = fuzz.ratio(tag.lower(), anime.lower())
					if results > 70:
						wantedSongs.append([songs[0], tag, anime, results])

	return wantedSongs

class Ui_Form(QtWidgets.QWidget):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.wantedSongs = getSongs()
		self.setupUi(self)

	def setupUi(self, Form):
		Form.setObjectName("Form")
		Form.resize(820, 820)
		self.formLayoutWidget = QtWidgets.QWidget(Form)
		self.formLayoutWidget.setGeometry(QtCore.QRect(10, 10, 810, 810))
		self.formLayoutWidget.setObjectName("formLayoutWidget")
		self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
		self.formLayout.setContentsMargins(0, 0, 0, 0)
		self.formLayout.setObjectName("formLayout")
		self.formLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
		self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldsStayAtSizeHint)
		self.tableWidget = QtWidgets.QTableWidget(self.formLayoutWidget)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(1)
		sizePolicy.setVerticalStretch(1)
		#sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
		self.tableWidget.setSizePolicy(sizePolicy)
		self.tableWidget.setLineWidth(1)
		self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.tableWidget.setShowGrid(True)
		self.tableWidget.setGridStyle(QtCore.Qt.SolidLine)
		self.tableWidget.setRowCount(len(self.wantedSongs))
		self.tableWidget.setColumnCount(4)
		self.tableWidget.setObjectName("tableWidget")
		item = QtWidgets.QTableWidgetItem()
		self.tableWidget.setHorizontalHeaderItem(0, item)
		item = QtWidgets.QTableWidgetItem()
		self.tableWidget.setHorizontalHeaderItem(1, item)
		item = QtWidgets.QTableWidgetItem()
		self.tableWidget.setHorizontalHeaderItem(2, item)
		item = QtWidgets.QTableWidgetItem()
		self.tableWidget.setHorizontalHeaderItem(3, item)
		self.tableWidget.horizontalHeader().setVisible(True)
		self.tableWidget.horizontalHeader().setCascadingSectionResizes(True)
		self.tableWidget.horizontalHeader().setStretchLastSection(True)
		self.tableWidget.horizontalHeader().setDefaultSectionSize(200)
		self.tableWidget.verticalHeader().setVisible(False)
		self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.tableWidget)

		self.retranslateUi(Form)
		QtCore.QMetaObject.connectSlotsByName(Form)
		self.populateTable(Form)

	def retranslateUi(self, Form):
		_translate = QtCore.QCoreApplication.translate
		Form.setWindowTitle(_translate("Form", "Form"))
		item = self.tableWidget.horizontalHeaderItem(0)
		item.setText(_translate("Form", "Song name"))
		item = self.tableWidget.horizontalHeaderItem(1)
		item.setText(_translate("Form", "Tag"))
		item = self.tableWidget.horizontalHeaderItem(2)
		item.setText(_translate("Form", "Anime"))
		item = self.tableWidget.horizontalHeaderItem(3)
		item.setText(_translate("Form", "Fuzzy score"))

	def populateTable(self, Form):
		for i in range(len(self.wantedSongs)):
			self.tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(self.wantedSongs[i][0]))
			self.tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(self.wantedSongs[i][1]))
			self.tableWidget.setItem(i, 2, QtWidgets.QTableWidgetItem(self.wantedSongs[i][2]))
			self.tableWidget.setItem(i, 3, QtWidgets.QTableWidgetItem(str(self.wantedSongs[i][3])))



app = QtWidgets.QApplication(sys.argv)
ex = Ui_Form()
ex.show()
sys.exit(app.exec_())
