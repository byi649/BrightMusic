import urllib3
import requests
import regex
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import webbrowser
from datetime import datetime

def getSongs():

	songDetails = []
	i = 0
	nSongs = 0

	http = urllib3.PoolManager()

	for count in range(3):
		print(str(datetime.now()), ": Downloading page", str(count+1))
		r = http.request('GET', 'http://hikarinoakariost.info/page/' + str(count + 1))
		soup = BeautifulSoup(r.data, "lxml")

		recent = soup.find_all("div", "td-pb-span8 td-main-content")[0]
		units = recent.find_all("div", "td-block-span6")

		nSongs = nSongs + len(units)

		for tag in units:
			songDetails.append([[],[],[],[]])
			songDetails[i][0] = tag.find_all("h3", "entry-title td-module-title")[0].text
			songDetails[i][1] = tag.find_all("div", "td-excerpt")[0].text
			songDetails[i][2] = tag.find_all("h3", "entry-title td-module-title")[0].find_all("a", href=True)[0]['href']
			i = i + 1

	for songs in songDetails:
		if songs[0] is not None:
			tags = songs[1].split("|")
			for iter in tags:
				if iter.strip() != "Album" and iter.strip() != "Single":
					songs[3].append(iter.strip())
		else:
			raise UserWarning

	print(str(datetime.now()), ": Downloading MAL page")
	r2 = http.request('GET', 'https://myanimelist.net/animelist/Shironi')
	malsoup = BeautifulSoup(r2.data, "lxml")

	list = malsoup.find_all("table")[0]['data-items']
	list = regex.findall(r'(?<="anime_title":").+?(?=")', list, flags=regex.IGNORECASE)

	wantedSongs = []

	for anime in list:
		for songs in songDetails:
			if songs[0] is not None:
				for tag in songs[3]:
					results = fuzz.ratio(tag.lower(), anime.lower())
					if results > 70:
						songTitle = getSongTitle(songs[2])
						if songTitle == "Unparsed": songTitle = songs[0]
						wantedSongs.append([songTitle, tag, anime, str(results), songs[2], songs[0]])

	# Very inefficient - TODO: cut down on the loops
	filteredSongs = []

	for i in range(len(wantedSongs)):
		if wantedSongs[i][0] in [x[0] for x in filteredSongs]:
			for j in range(len(filteredSongs)):
				if wantedSongs[i][0] == filteredSongs[j][0] and wantedSongs[i][3] > filteredSongs[j][3]:
					del filteredSongs[j]
					filteredSongs.insert(j, wantedSongs[i])
		else:
			filteredSongs.append(wantedSongs[i])

	return filteredSongs

def getSongTitle(url):
	print(str(datetime.now()), ": Downloading song page", url)
	r = requests.get(url).text
	# Parse these formats, regardless of whitespace:
	# > 01 SONGNAME
	# > 1 SONGNAME
	# > 1. SONGNAME
	# > 01. SONGNAME
	# TODO: super fragile, replace with something more robust
	try:
		name = regex.findall(r'(?<=>[\s0]*1[.\s]+).+?(?=<)', r)[0]
	except:
		print(url)
		name = "Unparsed"
	return name.strip()

class Ui_Form(QtWidgets.QWidget):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.wantedSongs = getSongs()
		self.setupUi(self)

	def setupUi(self, Form):
		width = 800
		Form.setObjectName("Form")
		Form.resize(width + 20, width + 20)
		self.formLayoutWidget = QtWidgets.QWidget(Form)
		self.formLayoutWidget.setGeometry(QtCore.QRect(10, 10, width + 10, width + 10))
		self.formLayoutWidget.setObjectName("formLayoutWidget")

		self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
		self.formLayout.setContentsMargins(0, 0, 0, 0)
		self.formLayout.setObjectName("formLayout")
		self.formLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
		self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldsStayAtSizeHint)

		self.SongTable = QtWidgets.QTableWidget(self.formLayoutWidget)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
		# self.SongTable.setSizePolicy(sizePolicy)
		self.SongTable.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.SongTable.setGridStyle(QtCore.Qt.SolidLine)
		self.SongTable.setRowCount(len(self.wantedSongs))
		self.SongTable.setColumnCount(5)
		self.SongTable.setObjectName("SongTable")
		self.SongTable.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
		self.SongTable.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem())
		self.SongTable.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem())
		self.SongTable.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem())
		self.SongTable.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem())
		self.SongTable.horizontalHeader().setCascadingSectionResizes(True)
		self.SongTable.horizontalHeader().setStretchLastSection(False)
		self.SongTable.horizontalHeader().setDefaultSectionSize(width/5)
		self.SongTable.verticalHeader().setVisible(False)
		self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.SongTable)

		self.retranslateUi(Form)
		QtCore.QMetaObject.connectSlotsByName(Form)
		self.populateTable(Form)
		self.highlightSongs(Form)

	def retranslateUi(self, Form):
		_translate = QtCore.QCoreApplication.translate
		Form.setWindowTitle(_translate("Form", "Form"))
		self.SongTable.horizontalHeaderItem(0).setText(_translate("Form", "Song name"))
		self.SongTable.horizontalHeaderItem(1).setText(_translate("Form", "Tag"))
		self.SongTable.horizontalHeaderItem(2).setText(_translate("Form", "Anime"))
		self.SongTable.horizontalHeaderItem(3).setText(_translate("Form", "Fuzzy score"))
		self.SongTable.horizontalHeaderItem(4).setText(_translate("Form", "Link"))

	def populateTable(self, Form):
		for i in range(len(self.wantedSongs)):
			self.SongTable.setItem(i, 0, QtWidgets.QTableWidgetItem(self.wantedSongs[i][0]))
			self.SongTable.setItem(i, 1, QtWidgets.QTableWidgetItem(self.wantedSongs[i][1]))
			self.SongTable.setItem(i, 2, QtWidgets.QTableWidgetItem(self.wantedSongs[i][2]))
			self.SongTable.setItem(i, 3, QtWidgets.QTableWidgetItem(self.wantedSongs[i][3]))
			self.SongTable.setItem(i, 4, QtWidgets.QTableWidgetItem(self.wantedSongs[i][4]))

		self.SongTable.itemDoubleClicked.connect(self.OpenLink)

	def OpenLink(self, item):
		if item.column() == 4:
			webbrowser.open(item.text())

	def highlightSongs(self, Form):
		with open("seen.txt", "r", encoding="utf-8-sig") as f:
			# Song Name | Album
			seenSongs = [x.split(" | ") for x in f.readlines()]
			seenSongs = [x[0].strip() for x in seenSongs]

		for i in range(len(self.wantedSongs)):
			if self.wantedSongs[i][5].lower().find("character song") > 0:
				self.SongTable.item(i, 0).setForeground(QtGui.QColor(35, 118, 252))
				self.SongTable.item(i, 1).setForeground(QtGui.QColor(35, 118, 252))
				self.SongTable.item(i, 2).setForeground(QtGui.QColor(35, 118, 252))
				self.SongTable.item(i, 3).setForeground(QtGui.QColor(35, 118, 252))
				self.SongTable.item(i, 4).setForeground(QtGui.QColor(35, 118, 252))

			if self.wantedSongs[i][0] in seenSongs:
				# TODO: do a fuzzy search for album name
				self.SongTable.item(i, 0).setForeground(QtGui.QColor(162, 175, 196))
				self.SongTable.item(i, 1).setForeground(QtGui.QColor(162, 175, 196))
				self.SongTable.item(i, 2).setForeground(QtGui.QColor(162, 175, 196))
				self.SongTable.item(i, 3).setForeground(QtGui.QColor(162, 175, 196))
				self.SongTable.item(i, 4).setForeground(QtGui.QColor(162, 175, 196))

def main():
	app = QtWidgets.QApplication(sys.argv)
	ex = Ui_Form()
	ex.show()
	sys.exit(app.exec_())

if __name__ == "__main__":

	# Profile main()
	if False:
		import pstats
		import cProfile

		cProfile.run('main()', 'profile.tmp')
		p = pstats.Stats('profile.tmp')
		p.sort_stats('time').print_stats(10)

	else:
		main()
