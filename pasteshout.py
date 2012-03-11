"""
I do not take any responsability of any harm done by this code.
Do what you want with it at your own risk.

author: SizeOne
blog: sizeonedev.wordpress.com
"""
import hashlib
import random
import urllib
import httplib
from HTMLParser import HTMLParser
from datetime import datetime
import time
from threading import Thread

class MyHTMLParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.links=[]

	def getLinks(self):
		return self.links

	def handle_starttag(self, tag, attrs):
		#print "Encountered a start tag:", tag
		if(tag=="a"):
			for attr in attrs:
				for i in xrange(len(attr)):
					if(attr[i]=="href"):
						if(not "/u/" in attr[i+1] and not "/archive/" in attr[i+1]):
							#print attr[i+1]
							self.links.append(attr[i+1])

class TAGScrambler():

	def makeDict(self,str_tags):
		spl=str_tags.split(" ")
		print "Cleaning dictionary..."
		for word in spl:
			try:
				int(word)
				while(not spl.remove(word)):
					pass
			except ValueError:
				pass
		if(self.ctag==None):
			print "Choosing end tag..."
			endtag=random.choice(spl)
		else:
			print "End tag given"
			endtag=self.ctag
		print endtag
		try:
			while(True):
				spl.remove(endtag)
		except ValueError:
			pass
		return spl,endtag

	def __init__(self,tags,salt,limit=200,ctag=None):
		self.salt=salt
		self.limit=limit
		self.ctag=ctag
		self.keylist,self.__endblock_tag=self.makeDict(tags)

	def joinArray(self,array):
		s=""
		for a in array:
			s+=a+" "
		return s

	def checkHeader(self,control,header):
		spl=header.split(" ")
		try:
			spl.remove("")
		except ValueError:
			pass
		l=len(control)/2
		base=0
		sum=0
		for i in xrange(len(control)/2):
			x=(i*2)
			y=(i*2)+2
			seq = control[x:y]
			while(base<len(spl)):
				h=self.joinArray(spl[0:base+1])
				base+=1
				key = hashlib.md5(h).hexdigest()
				if(seq in key):
					sum+=1
					break
		if(sum==l and base==len(spl)):
			return True
		else:
			return False

	def makeHeader(self,control,limit=50):
		while(True):
			header=""
			for i in xrange(len(control)/2):
				while True:
					header+=random.choice(self.keylist)+" "
					key = hashlib.md5(header).hexdigest()
					if(control[i*2:(i*2)+2] in key):
						break
			if(len(header)<=limit):
				return header

	# last - last key used, keyword - TAG
	def makeKey(self,last,keyWord):
		# make a hash from the keyword
		key = hashlib.md5(keyWord+self.salt).hexdigest()
		# some operations that use the last value 
		# to generate an index to a byte in key
		l=len(key)
		i=(last*1337)%(l/2)
		# get that byte
		byte=key[2*i:(2*i)+2]
		val=int("0x"+byte, 0)
		return val

	def findKey(self,last,wanted):
		for word in self.keylist:
			key=self.makeKey(last,word)
			if(key==wanted and word!=""):
				return word, key
		return None, 0

	def encode(self,message,seed):
		output=""
		last=seed
		i=0
		b=-1
		limit=0
		while(i<len(message)):
			k,v=self.findKey(last,ord(message[i]))
			if(k==None):
				last=random.sample(range(20),1)[0]
				b=last
				limit+=1
				if not limit < self.limit :
					print "This message is very hard to encode! I'm out :/"
					return None
				continue
			else:
				if(b!=-1):
					output+=str(b)+" "
					b=-1
					limit=0
				output+=k+" "
				last=v
				i+=1
		return self.__endblock_tag+" "+output+self.__endblock_tag+" "

	def decode(self,message,seed):
		spl=message.split(" ")
		output=""
		last=seed
		fase1=True
		for word in spl:
			#skip till control
			if(fase1 and word!=self.__endblock_tag):
				continue
			elif(word==self.__endblock_tag):
				if(fase1==False):
					return output
				else:
					fase1=False
				continue
			try:
				last=int(word)
			except ValueError:
				if(word!=None and word!=""):
					val=self.makeKey(last,word)
					last=val
					output+=chr(val)
		return output

	def fillMessage(self, message, fill=1024):
		beg=""
		end=""
		while(len(beg)<fill):
			beg+=random.choice(self.keylist)+" "
			end+=random.choice(self.keylist)+" "
		return beg+message+end

class PasteSock():	
	def __init__(self,tags,destid,portid,pin,endTag):
		self.obfuscator=TAGScrambler(tags,portid,200,endTag)
		self.destid=destid
		self.seed=pin
		self.dict={}
		self.host="www.pastebin.com"
		self.update_link="/ajax/realtime_data.php?q=2&randval="
	
	def __readraw(self,id):
		if(id[0]=='/'):
			id=id[1:]
		link="/raw.php?i="+id
		conn = httplib.HTTPConnection(self.host)
		conn.request("GET", link)
		r = conn.getresponse()
		if(r.status==200):
			d = r.read()
			conn.close()
			#print d
			if(d=="Hey, it seems you are requesting a little bit too much from Pastebin. Please slow down!"):
				print "BLOCK"
				return None
			return d
		else:
			print "Problem!"
			conn.close()
			return ""

	def parse(self,data):
		parser = MyHTMLParser()
		parser.feed(data)
		return parser.getLinks()

	def feed(self):
		link=self.update_link+str(random.random())
		conn = httplib.HTTPConnection(self.host)
		conn.request("GET", link)
		r = conn.getresponse()
		if(r.status==200):
			d = r.read()
			conn.close()
			return d
		else:
			conn.close()
			return ""

	def listen(self, msg_callback):
		while(True):
			lst=self.parse(self.feed())
			for link in lst:
				try:
					self.dict[link]
					#ignore
					pass
				except KeyError:
					#print "Reading post "+link
					raw=self.__readraw(link)
					#print raw
					if(raw!=None and raw!=""):
						if(len(self.dict)>10000):
							self.dict={}
						self.dict[link]=link
						b,m=self.read(raw)
						if(b):
							msg_callback(m)
						else:
							pass
					else:
						print "BLOCK"
			time.sleep(5)
			

	def write(self,text):
		fline=text.split("\n")[0]
		#print fline
		if(not self.parseFirstLine(fline)):
			#print "Not HERE"
			text=self.buildPage(text)
		params = urllib.urlencode(
									{
										'post_key': '',
										'submit_hidden':'submit_hidden',
										'paste_code': text,
										'paste_format': 1,
										'paste_expire_date':'10M',
										'paste_private':0,
										'paste_name':''
									}
								 )
		headers = {
					"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain",
					"Host":"pastebin.com",
					"Origin":"http://pastebin.com",
					"Referer":"http://pastebin.com/index",
				  }
		conn = httplib.HTTPConnection("www.pastebin.com")
		conn.request("POST", "/post.php", params, headers)
		response = conn.getresponse()
		conn.close()
		return response.getheader("location")

	def buildPage(self,message,headerSize=50,fill=1024):
		output=self.makeFirstLine(headerSize)
		output+="\n"+self.makeFiller()
		enc = self.obfuscator.encode(message,self.seed)
		fm=self.obfuscator.fillMessage(enc,fill)
		output+=fm
		return output

	def read(self,text):
		fline=text.split("\n")[0]
		if(self.parseFirstLine(fline)):
			#prepare
			return True, self.obfuscator.decode(text,self.seed)
		else:
			return False, "No message found!"

	def makeFirstLine(self,size=50):
		return self.obfuscator.makeHeader(self.destid,size)

	def parseFirstLine(self,line):
		return self.obfuscator.checkHeader(self.destid,line)

	def makeFiller(self):
		return """Unlock Any iphone  Now well there was no solution to unlock Iphone on baseband 04.11.08 which is the latest baseband from the Apple and it wasnt hacked till Now
Now with the Redsnow PATCHED You can  unlock Iphone 4 on baseband 04.11.08 in minutes Video turorial is also Includes

Download Files here http://iphone4unlocks.blogspot.com/

VIDEO How to unlock for baseband 04.11.08 on IOs 5.01 http://www.dailymotion.com/video/xohmox_iphone-4-unlock-on-baseband-04-11-08_tech#from=embediframe

steps are very plain And Simple and it will take around 5 to 10 min to unlock you can also found the Detailed tutorial for unlocking on Ios 5.01 
baseband 04.11.08 so if you have an iphone wokring only like Ipod its time to unlock it free just download the Files and patch and start unlocking right Now 
watch the Video before Unlocking
this Patch and Files are not tested on iphone 4s but it may work as well ther too i have few user reported that they successfully unlcoed iphone 4s aswell

Download Files here http://iphone4unlocks.blogspot.com/

VIDEO How to unlock for baseband 04.11.08 on IOs 5.01 http://www.dailymotion.com/video/xohmox_iphone-4-unlock-on-baseband-04-11-08_tech#from=embediframe

Iphone 4 Unlocks are 100% tested and working you just have to Download the redsnow with patch run the patch in compatability Mode and then will be able to unlock your iphone 4 easily
baseband supported 04/11/08 04.10.11 and 3.10  
so there is noo need to buy or use Gevey Now and start doing the Software Unlock today 


Download Files here http://iphone4unlocks.blogspot.com/

VIDEO How to unlock for baseband 04.11.08 on IOs 5.01 http://www.dailymotion.com/video/xohmox_iphone-4-unlock-on-baseband-04-11-08_tech#from=embediframe


there is also jailbreaking Files included if you have already jailbreaked your phone earlier than do nothin if you want to jailbreak ...you can
it is up to you 
Note: THis Unlock is for Iphone 4 baseband 04.11.08 and other supported bb are 04.10.11  and this is Purely Software Unlock no gevey Sim required this will sim unlock your phone just Like factory unlock
Tags ignore:
"""

key_list = """phone unlock pins 2 software hardware free simfree any network tutorial instructions video iphone unlock iphone jailbreak unlock iphone jailbreak iphone unlock iphone 3gs unlock iphone4 jailbreak iphone 3gs jailbreak iphone4 jailbreak iphone unlock iphone simlock iphone iphone4 iphone unlock iphone unlock apple 04.11.08 04.10.11 3.10 How to unlock your iPhone4 tutorial hacking software iphone ipad ipod planting being d7 cydia winterboard apple ipod iphone touch apple ipod touch review store your 3gs itunes imac apps everytime application everytime touch steve case giveaway free leopard macintosh iphone 3gs app review jailbreak restore refresh sync fresh bought day ios How to unlock ANY pin locked iPhone pin number hack glitch exploit hacking householdhacker iphone traveler unlock for iphone4 unlock iphone 2g unlock the iphone how to unlock the iphone unlocking iphone 3gs unlock iphone 3gs unlocking an iphone how to unlock iphone4 how to unlock a iphone unlocking iphone4 unlock iphone 3g 4.2 unlock iphone4 4.1 unlocked iphone 3gs unlocking iphone 3g how to unlock an iphone4 how to unlock iphone 3 unlock iPhone unlock apple iPhone iPhone unlock code iPhone unlock unlock iPhone 3g unlock iPhone software iPhone crack unlock 3Gs unlock an iPhone iPhone4 unlock unlock iPhone4 how to unlock an iPhone unlocking iPhone 3g jailbreak iPhone unlocking iPhone unlock my iPhone iPhone unlocking iPhone 3g unlock code unlock iPhone sim 3g unlock iPhone 3g unlock how to unlock iPhone 3g unlock iPhone 3Gs unlock code for iPhone how to unlock iPhone4 jailbreak4 jailbreak iphone 3gs jailbreak 4G iphone unlock for how to unlocking sim 4g my iphones software an the program ios 4.2.1 4.3.5 unlock iphone unlock 4.2.1 how 4.3.5 iphone Ipod Touch IPod Touch App Apple Apple Inc. IOS (Apple) Itunes Imac Apps Howto Mobile Device Application Store Application Software Phone Review 5.0 ios5 jailbreak ios5 unlock iphone4 ios5.0 jailbreak ios4.3.5 unlock IPhone4 Steve Cell jailbreak 5.0.1 ios 5.0.1 5.1 ios 5.1 ios 4s AT&T Mobility IOS Through Iphone Apple Apple Inc. unlock unlocked unlocking ios ios5 gevey sim micro at&t at and tmobile mobile bug error hack cheat new iphone4 4s 3g 3gs gsm cdma usa us america american network carrier factory official unofficial jailbreak cydia ultrasnow untrasnow ultrasn0w snow sn0w turbo pro red green yellow white black buy free Phone howto mobile device Touch talk 04.11.08 4.11.8 04.10.01 Mobile Phone Cell Iphone AT&T AT&T Mobility Apple Apple Inc. Unlock iphone 4s T-Mobile jailbreak ios 5.0 5.0.1 baseband untethered tethered iPhone 4siPhone 4speedvsappleVS (band)AppIpod deviceApplication SoftwareImacIPod TouchSteveStoreGiveawayApple Inc.FreeLeopardMacintoshIphone 3gs Untethered unlock czdia ios 5.0 4.3.5 4.3.4 4.3.3 4.3.6 RedSn0w redsn0w redsnow Cydia tutorial SIRI on Apple enalbed redmonpie IOS (Apple) iphone3gs iphone4 iphone5 iphone4s IOS5 how-to jailbreakIOS5 os5 5.0.1 musclenerd chpwn downgrade all devices 2.8 2.7 2.6 0.9.8 0.9.7 0.9.6 rc mac apple pc jailbreak jailbreak 5 5.0.1 4.3.5 ios 4.3.5 4.3.5 iphone iphone 3gs iphone4 ipod touch ipod touch 3g ipod touch 4g ipad2 Untetheredwindows vista windows 7 mac download tutorial how to redsn0w 0.9.8b3 redsn0w duncan33303 iOS 4.3.4 4.3.5 Jailbreak tethered NOT UNTETHERED Free Cydia exploit MuscleNerd Redsn0w Windows Mac iPhone iPod touch itouch iPad 1st 2nd 3rd 4th 1g 2g 3g 3gs 4g firmware download dev team easy hack computer pc cydia unlock iOS 4.3.5 4.3.4 4.3.4/4.3.5 Tethered Jailbreak for iPhone, iPod touch, and iPad koi2281 jailbreak limera1n unlock hack tutorial wireless technology electronics howto cellphones hacking baseband download downgrade redmondpie devteam pwnagetool limra1n quickpwn ultrasn0w Greenpois0n laptops notebook video review technology medicine apple ipod touch macbook tips imac jailbreak 4.3.5 4.3.5 Jailbreak Jail Break How to howto tutorial iphone ipod touch ipad iphone4 ipad2 5g 4g 3g 2g 1g 1st 2nd 3rd 4th 5th gen generation redsnow redsn0w limera1n limerain spirit ultrasn0w ultrasnow pwnagetool sn0wbreeze snowbreeze 5.0 5.0b3 4.3.3 4.3.2 4.3.1 iOS 5 5.0 jailbreaking 4.3.5 ios 4.3.5 jailbreak tutorial redsn0w 0.9.6rc iphone 3gs ipod touch 4g 3g ipad downgrade fix white cydia untethered tethered redsn0w 0.9.6rc12 ios 4.3.2 jailbreak ios 4.3.5 jailbreak tutorial dinozambas2 jailbreak iso 4.3.5 tutorial hot topics unlock iphone4 iPad 2 jailbroken 4.3.3 4.2.1 4.2.6 4.3.5 Jailbreak 5.0 untethered greenpois0n rc6 verizon at&t att iphone4 iphone 3gs 3g ipod touch 2nd mc mb 4th 3rd gen generation itouch model cydia ipad redsn0w tethered itunes icrackuridevice windows mac linux error unlock 3.10.01 2.10.04 5.15.01 6.15.00 baseband unltrasn0w greenpoison limera1n pwnage tool chronic dev team easy fast 4.3 ios firmware animated boot logo 4.3.4 4.2.9 4.3.5 4.3.10 jailbreak redsnow redsn0w untethered tethered boot firmware download jailbreakme 3.0 beta ios version ipod touch iphone 4g 3g 3gs ipad ipad2 jailbreaking jailbroken fix error itunes l3gitjailbr3aks ios5downloads.com how to jailbreak ios jailbreak iOS 5 jailbreak 5.0 tethered untethered iOS iphone ipod touch ipad IOS"""

pc = PasteSock(key_list,"736f6e65","SizeOne",235413,"ipad4")

username=raw_input("Select username> ")

class Listener(Thread):

	def run(self):
		pc.listen(self.onMessage)

	def onMessage(self,msg):
		if("display:"in msg):
			disp=msg.split("display:")[1]
			if(username in disp):
				disp="me"+disp.split(username)[1]
			print disp

listener=Listener()
listener.start()


line=""
__exit=["exit","quit"]
print "Type your message or exit to quit..."
while(not line in __exit):
	line=raw_input("")
	if(line==""):
		continue
	if(not line in __exit): 
		message=pc.buildPage("display:"+username+": "+line)
		print "Check if your message was marked as spam: http://www.pastebin.com"+pc.write(message)

listener._Thread__stop()


