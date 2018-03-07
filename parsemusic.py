import requests
import regex
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import sys
import webbrowser
from datetime import datetime
import multiprocessing
from tkinter import *
from tkinter import ttk
import html
import codecs
import romkan


def main():
	ui = Ui_Form()


def getSongs(pages):

	songDetails = []

	pool = multiprocessing.Pool(processes=10)
	FrontPageList = pool.map(getFrontPage, [x + 1 for x in range(pages)])

	for count in range(pages):
		r = FrontPageList[count]
		soup = BeautifulSoup(r.content, "lxml")

		recent = soup.find_all("div", "td-pb-span8 td-main-content")[0]
		units = recent.find_all("div", "td-block-span6")

		for tag in units:
			detailArray = [
				tag.find_all("h3", "entry-title td-module-title")[0].text,
				tag.find_all("div", "td-excerpt")[0].text,
				tag.find_all("h3", "entry-title td-module-title")[0].find_all("a", href=True)[0]['href'],
				[]
			]
			songDetails.append(detailArray)

	for songs in songDetails:
		if songs[0] is not None:
			print(songs[1])
			tags = songs[1].split("|")
			for iter in tags:
				if iter.strip() != "Album" and iter.strip() != "Single":
					songs[3].append(iter.strip())
		else:
			raise UserWarning

	print(str(datetime.now()), ": Downloading MAL page")
	r2 = requests.get('https://myanimelist.net/animelist/Shironi')
	malsoup = BeautifulSoup(r2.content, "lxml")

	list = malsoup.find_all("table")[0]['data-items']
	list = regex.findall(r'(?<="anime_title":").+?(?=")', list, flags=regex.IGNORECASE)

	wantedSongs = []
	parseList = []

	for anime in list:
		for songs in songDetails:
			if songs[0] is not None:
				for tag in songs[3]:
					anime = decode_escapes(anime)
					results = fuzz.ratio(tag.lower(), anime.lower())
					if results > 70:
						parseList.append(songs[2])
						wantedSongs.append([songs[0], tag, anime, str(results), songs[2], songs[0]])

	pool = multiprocessing.Pool(processes=10)
	songTitleList = pool.map(getSongTitle, parseList)

	# Very inefficient - TODO: cut down on the loops
	filteredSongs = []

	for i in range(len(wantedSongs)):
		wantedSongs[i][0] = songTitleList[i]
		if wantedSongs[i][0] in [x[0] for x in filteredSongs]:
			for j in range(len(filteredSongs)):
				if wantedSongs[i][0] == filteredSongs[j][0] and wantedSongs[i][3] > filteredSongs[j][3]:
					del filteredSongs[j]
					filteredSongs.insert(j, wantedSongs[i])
		else:
			filteredSongs.append(wantedSongs[i])

	return filteredSongs


def getFrontPage(pageNumber):
	print(str(datetime.now()), ": Downloading page", str(pageNumber))
	r = requests.get('http://hikarinoakariost.info/page/' + str(pageNumber))
	return r


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
	except Exception as e:
		print(url)
		name = "Unparsed"

	name = html.unescape(name.strip())
	name = romkan.to_roma(name)
	return name


class Ui_Form():

	def __init__(self):
		self.pagesToGet = "1"
		self.root = Tk()
		self.root.Title = "Songs"

		self.drawUI()

		self.root.mainloop()

	def drawUI(self):

		# Draw frames
		self.tableFrame = Frame(self.root)
		self.tableFrame.pack(side='left', fill='both', expand=1)

		self.inputFrame = Frame(self.root)
		self.inputFrame.pack(side='top', pady='10', padx='10')

		self.buttonFrame = Frame(self.root)
		self.buttonFrame.pack(side='top')

		# Draw table
		columns = ['Tag', 'Anime', 'Fuzzy', 'Link']
		self.tree = ttk.Treeview(self.tableFrame, columns=(columns), height=3)
		self.tree.pack(side='left', fill='both', expand=1)

		self.vsb = ttk.Scrollbar(self.tableFrame, orient="vertical", command=self.tree.yview)
		self.vsb.pack(side='right', fill='y')
		self.vsb.pack_propagate(False)
		self.tree.configure(yscrollcommand=self.vsb.set)

		self.tree.bind('<Double-1>', self.itemClicked)

		for items in columns:
			self.tree.column(items, width=200)
			self.tree.heading(items, text=items)

		self.tree.column('#0', width=300)
		self.tree.heading('#0', text="Song name")

		self.tree.column('Fuzzy', width=50)

		# Draw button
		self.updateButton = Button(self.buttonFrame, text="Get song list", command=self.updateTableItems)
		self.updateButton.pack(side='bottom')

		# Draw pages input box
		self.pageInput = Entry(self.inputFrame, textvariable=self.pagesToGet)
		self.pageInput.insert(0, "1")
		self.pageInput.pack(side='right')

		# Draw pages input label
		self.pageLabel = Label(self.inputFrame, text="Pages to get: ")
		self.pageLabel.pack(side='left')

	def fillTable(self):
		self.tree.configure(height=(len(self.songArray)))
		for i, song in enumerate(self.songArray):
			self.tree.insert('', 'end', 'song' + str(i), text=song[0], values=(song[1:5]))

	def updateTableItems(self):
		self.songArray = getSongs(int(self.pageInput.get()))
		x = self.tree.get_children()
		for item in x:
			self.tree.delete(item)
		self.fillTable()
		self.highlightSongs()

	def highlightSongs(self):
		with open("seen.txt", "r", encoding="utf-8-sig") as f:
			# Song Name | Album
			seenSongs = [x.split(" | ") for x in f.readlines()]
			seenSongs = [[x[0].strip(), x[1].strip()] for x in seenSongs]

		for i in range(len(self.songArray)):
			if self.songArray[i][5].lower().find("character song") > 0:
				self.tree.item('song' + str(i), tags="cSong")

			for song in seenSongs:
				resultsName = fuzz.ratio(self.songArray[i][0].lower(), song[0].lower())
				resultsAlbum = fuzz.ratio(self.songArray[i][2].lower(), song[1].lower())
				if resultsName > 60 and resultsAlbum > 70:
					# TODO: do a fuzzy search for album name
					self.tree.item('song' + str(i), text=song[0], tags="sSong")

			if self.songArray[i][0] == "Unparsed":
				self.tree.item('song' + str(i), tags="pSong")

		self.tree.tag_configure('cSong', foreground='#%02x%02x%02x' % (216, 138, 138))
		self.tree.tag_configure('sSong', foreground='#%02x%02x%02x' % (162, 175, 196))
		self.tree.tag_configure('pSong', foreground='#%02x%02x%02x' % (206, 20, 73))

	def itemClicked(self, event):
		song = self.tree.selection()[0]
		webbrowser.open(self.tree.item(song).get('values')[3])


def decode_escapes(s):
	# Blame Yuru Camp△
	ESCAPE_SEQUENCE_RE = re.compile(r'''
		( \\U........      # 8-digit hex escapes
		| \\u....          # 4-digit hex escapes
		| \\x..            # 2-digit hex escapes
		| \\[0-7]{1,3}     # Octal escapes
		| \\N\{[^}]+\}     # Unicode characters by name
		| \\[\\'"abfnrtv]  # Single-character escapes
		)''', re.UNICODE | re.VERBOSE)

	def decode_match(match):
		return codecs.decode(match.group(0), 'unicode-escape')

	return ESCAPE_SEQUENCE_RE.sub(decode_match, s)


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
