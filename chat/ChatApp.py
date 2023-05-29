#!/usr/bin/python3

# Student name and No.: Lau Tsz Yin 3035686516
# Development platform: MacOs
# Python version: Python 3.9.7
# Version: 

# *****************************************
# For self-use:
# 1. local file directory
# $ cd Desktop/COMP3234/PA1/chat
# 2. Handle Socket bind error
# $ ps -fA | grep python
# 3. Use shell script for mutil-user testing
# $ sh start-OSX-tab.sh
# *****************************************

from tkinter import *
from tkinter import ttk
from tkinter import font
import sys
import socket
import threading
import json
import os


#
# Global variables
#
MLEN=1000      #assume all commands are shorter than 1000 bytes
USERID = None
NICKNAME = None
SERVER = None
SERVER_PORT = None

HOST_PORT = 32349


#
# Functions to handle user input
#

turn_num = 1
a = 0
client = None
Data = []	#e.g. [["Tony", "Tony@hku.hk"], []]

def do_Join():
	"""#The following statement is just for demo purpose
	#Remove it when you implement the function
	console_print("Press do_Join()")"""

	global turn_num
	global a
	global client


	while turn_num:
		#connect to Chatserver using TCP if not connected yet
		try:

			#Notes: socket.AF_INET:the type of socket address, e.g.IPv4		socket.SOCK_STREAM:the type of socket, i.e. TCP
			client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			#client.settimeout(2.0)
			client.connect(('localhost', HOST_PORT))
			msg_successconnect = "Connected to server at "+ str(client.getpeername()[0])+ ":"+ str(client.getpeername()[1])
			console_print(msg_successconnect)
		except:
			print("Fail to join the server! Server may not be available. ")
			client.close()
			sys.exit(1)
			


		#send JOIN command
		try:
			msg_Join = {"CMD": "JOIN", "UN": str(NICKNAME), "UID": str(USERID)}
			jstr = json.dumps(msg_Join)
			console_print(jstr)
			client.send(jstr.encode("ascii"))
			console_print("JOIN command sent.")
		except:
			console_print("Cannot sent the JOIN command")


		#create a worker thread
		t1 = threading.Thread(target=listening_threadfuc, args=(client, ))
		t1.start()
		console_print("Slave thread started")

		a = 1

		break

	turn_num = 0
	
	#prevent duplicate join
	a -= 1
	if a <= -1:
		console_print("Duplicate Join: No need to join again!")



def listening_threadfuc(client):

	global Data

	console_print("arrived in thread...")
	#console_print(NICKNAME)
	while True:
		try:
			#keep listening
			rmsg = client.recv(500)
			console_print("Some message is received. ")
			immed = rmsg.decode("ascii")
			receive_msg = json.loads(immed)
			print("receive_msg: ", receive_msg)
			print("receive_msg CMD: ", receive_msg["CMD"])

			#receive ACK command
			if receive_msg["CMD"] == "ACK":
				console_print("Received ACK command.")

		
			#receive LIST command
			elif receive_msg["CMD"] == "LIST":
				console_print("Received LIST command.")

				x = receive_msg["DATA"]
				#print("receive_msg with key DATA: ", x)

				#update Data
				for i in range(len(x)):
					name = x[i]['UN']
					email = x[i]["UID"]
					if [name, email] not in Data:
						Data.append([name, email])
				#print("Data: ", Data)

				#print(x[0]["UN"])
				msg_peerlist = ""
				for i in range(len(x)):
					if i == len(x) - 1:
						msg_peerlist += str(x[i]["UN"]) + " (" + str(x[i]["UID"]) + ") "
						break

					msg_peerlist += str(x[i]["UN"]) + " (" + str(x[i]["UID"]) + ") " + ", "
			
				list_print(msg_peerlist)

				

			#receive MSG command
			elif receive_msg["CMD"] == "MSG":
				if receive_msg["TYPE"] == "ALL":
					console_print("Received MSG command.")

					a = receive_msg["FROM"]
					b = ""
					for i in a:
						if i == "@":
							break
						else:
							b += i
					b = b.capitalize()

					y = "[" + b + "] " + receive_msg["MSG"]
					chat_print(y, "bluemsg")


				elif receive_msg["TYPE"] == "GROUP":
					#print("arrive here.")

					for i in range(len(Data)):
						if Data[i][1] == receive_msg["FROM"]:
							name = Data[i][0]
							break

					y = "[" + name + "]" + receive_msg["MSG"]
					chat_print(y, "greenmsg")


				elif receive_msg["TYPE"] == "PRIVATE":
					for i in range(len(Data)):
						if Data[i][1] == receive_msg["FROM"]:
							name = Data[i][0]
							break

					y = "[" + name + "]" + receive_msg["MSG"]
					chat_print(y, "redmsg")

		except:
			#detect connection broken(as client is no longer a socket)
			console_print("The Slave threads dies")
			console_print("The connection is broken!")
			break




def do_Send():
	"""#The following statements are just for demo purpose
	#Remove them when you implement the function
	chat_print("Press do_Send()")
	chat_print("Receive private message", "redmsg")
	chat_print("Receive group message", "greenmsg")
	chat_print("Receive broadcast message", "bluemsg")"""

	global client
	global Data

	#get the List of receipent and messages
	x = get_tolist()
	print("x: ", x)
	storeList = list(x)
	storeList.append(",")
	storeList.append(" ")
	immed = ""
	receipentList = []
	for i in storeList:
		if i == ",":
			continue
		else:
			if i == " ":
				receipentList.append(immed)
				immed = ""
				continue
			else:
				immed += i
	print("receipentList: ", receipentList)

	y = get_sendmsg()
	print("y: ", y)

	#send SEND command & display outgoing message
	if receipentList[0] == "ALL":

		#Broadcast message
		try:
			msg_Send = {"CMD": "SEND", "MSG": y, "TO": [], "FROM" : str(USERID)}
			jstr = json.dumps(msg_Send)
			#console_print(jstr)
			client.send(jstr.encode("ascii"))
			console_print("SEND(Broadcast) command sent.")
		except:
			console_print("Cannot send the SEND(Broadcast) command. ")

		c = "[To: ALL] " + y
		chat_print(c)

	elif len(receipentList) > 1:

		#Group message
		try:
			emailList = []
			for i in range(len(receipentList)):
				for j in range(len(Data)):
					if Data[j][0] == receipentList[i]:
						emailList.append(Data[j][1])
			print("emailList: ", emailList)

			msg_Send = {"CMD": "SEND", "MSG": y, "TO": emailList, "FROM" : str(USERID)}
			jstr = json.dumps(msg_Send)
			#console_print(jstr)
			client.send(jstr.encode("ascii"))
			console_print("SEND(Group) command sent.")
		except:
			console_print("Fail to send message. Maybe some receiver are not connected to the server.")

		a = ""
		for i in range(len(receipentList)):
			if i == len(receipentList) - 1:
				a += receipentList[i]
				break

			a += receipentList[i]
			a += ", "

		c = "[To: " + a + "] " + y
		chat_print(c)


	elif len(receipentList) == 1:

		#Private message
		try:
			emailList = []
			for j in range(len(Data)):
				if Data[j][0] == receipentList[0]:
					emailList.append(Data[j][1])
			print("emailList: ", emailList)

			msg_Send = {"CMD": "SEND", "MSG": y, "TO": emailList, "FROM": str(USERID)}
			jstr = json.dumps(msg_Send)
			client.send(jstr.encode("ascii"))
			console_print("SEND(Private) command sent.")
		except:
			console_print("Fail to send message. Maybe the receiver is not connected to the server.")

		c = "[To: " + receipentList[0] + "] " + y
		chat_print(c)

	


def do_Leave():
	"""#The following statement is just for demo purpose
	#Remove it when you implement the function
	list_print("Press do_Leave()")"""

	global client 
	global turn_num
	
	client.close()
	list_print("")
	console_print("The connection is closed.")
	print("The connection is closed.")
	turn_num = 1



#################################################################################
#Do not make changes to the following code. They are for the UI                 #
#################################################################################

#for displaying all log or error messages to the console frame
def console_print(msg):
	console['state'] = 'normal'
	console.insert(1.0, "\n"+msg)
	console['state'] = 'disabled'

#for displaying all chat messages to the chatwin message frame
#message from this user - justify: left, color: black
#message from other user - justify: right, color: red ('redmsg')
#message from group - justify: right, color: green ('greenmsg')
#message from broadcast - justify: right, color: blue ('bluemsg')
def chat_print(msg, opt=""):
	chatWin['state'] = 'normal'
	chatWin.insert(1.0, "\n"+msg, opt)
	chatWin['state'] = 'disabled'

#for displaying the list of users to the ListDisplay frame
def list_print(msg):
	ListDisplay['state'] = 'normal'
	#delete the content before printing
	ListDisplay.delete(1.0, END)
	ListDisplay.insert(1.0, msg)
	ListDisplay['state'] = 'disabled'

#for getting the list of recipents from the 'To' input field
def get_tolist():
	msg = toentry.get()
	toentry.delete(0, END)
	return msg

#for getting the outgoing message from the "Send" input field
def get_sendmsg():
	msg = SendMsg.get(1.0, END)
	SendMsg.delete(1.0, END)
	return msg

#for initializing the App
def init():
	global USERID, NICKNAME, SERVER, SERVER_PORT

	#check if provided input argument
	if (len(sys.argv) > 2):
		print("USAGE: ChatApp [config file]")
		sys.exit(0)
	elif (len(sys.argv) == 2):
		config_file = sys.argv[1]
	else:
		config_file = "config.txt"

	#check if file is present
	if os.path.isfile(config_file):
		#open text file in read mode
		text_file = open(config_file, "r")
		#read whole file to a string
		data = text_file.read()
		#close file
		text_file.close()
		#convert JSON string to Dictionary object
		config = json.loads(data)
		USERID = config["USERID"].strip()
		NICKNAME = config["NICKNAME"].strip()
		SERVER = config["SERVER"].strip()
		SERVER_PORT = config["SERVER_PORT"]
	else:
		print("Config file not exist\n")
		sys.exit(0)


if __name__ == "__main__":
	init()

#
# Set up of Basic UI
#
win = Tk()
win.title("ChatApp")

#Special font settings
boldfont = font.Font(weight="bold")

#Frame for displaying connection parameters
topframe = ttk.Frame(win, borderwidth=1)
topframe.grid(column=0,row=0,sticky="w")
ttk.Label(topframe, text="NICKNAME", padding="5" ).grid(column=0, row=0)
ttk.Label(topframe, text=NICKNAME, foreground="green", padding="5", font=boldfont).grid(column=1,row=0)
ttk.Label(topframe, text="USERID", padding="5" ).grid(column=2, row=0)
ttk.Label(topframe, text=USERID, foreground="green", padding="5", font=boldfont).grid(column=3,row=0)
ttk.Label(topframe, text="SERVER", padding="5" ).grid(column=4, row=0)
ttk.Label(topframe, text=SERVER, foreground="green", padding="5", font=boldfont).grid(column=5,row=0)
ttk.Label(topframe, text="SERVER_PORT", padding="5" ).grid(column=6, row=0)
ttk.Label(topframe, text=SERVER_PORT, foreground="green", padding="5", font=boldfont).grid(column=7,row=0)


#Frame for displaying Chat messages
msgframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
msgframe.grid(column=0,row=1,sticky="ew")
msgframe.grid_columnconfigure(0,weight=1)
topscroll = ttk.Scrollbar(msgframe)
topscroll.grid(column=1,row=0,sticky="ns")
chatWin = Text(msgframe, height='15', padx=10, pady=5, insertofftime=0, state='disabled')
chatWin.grid(column=0,row=0,sticky="ew")
chatWin.config(yscrollcommand=topscroll.set)
chatWin.tag_configure('redmsg', foreground='red', justify='right')
chatWin.tag_configure('greenmsg', foreground='green', justify='right')
chatWin.tag_configure('bluemsg', foreground='blue', justify='right')
topscroll.config(command=chatWin.yview)

#Frame for buttons and input
midframe = ttk.Frame(win, relief=RAISED, borderwidth=0)
midframe.grid(column=0,row=2,sticky="ew")
JButt = Button(midframe, width='8', relief=RAISED, text="JOIN", command=do_Join).grid(column=0,row=0,sticky="w",padx=3)
QButt = Button(midframe, width='8', relief=RAISED, text="LEAVE", command=do_Leave).grid(column=0,row=1,sticky="w",padx=3)
innerframe = ttk.Frame(midframe,relief=RAISED,borderwidth=0)
innerframe.grid(column=1,row=0,rowspan=2,sticky="ew")
midframe.grid_columnconfigure(1,weight=1)
innerscroll = ttk.Scrollbar(innerframe)
innerscroll.grid(column=1,row=0,sticky="ns")
#for displaying the list of users
ListDisplay = Text(innerframe, height="3", padx=5, pady=5, fg='blue',insertofftime=0, state='disabled')
ListDisplay.grid(column=0,row=0,sticky="ew")
innerframe.grid_columnconfigure(0,weight=1)
ListDisplay.config(yscrollcommand=innerscroll.set)
innerscroll.config(command=ListDisplay.yview)
#for user to enter the recipents' Nicknames
ttk.Label(midframe, text="TO: ", padding='1', font=boldfont).grid(column=0,row=2,padx=5,pady=3)
toentry = Entry(midframe, bg='#ffffe0', relief=SOLID)
toentry.grid(column=1,row=2,sticky="ew")
SButt = Button(midframe, width='8', relief=RAISED, text="SEND", command=do_Send).grid(column=0,row=3,sticky="nw",padx=3)
#for user to enter the outgoing message
SendMsg = Text(midframe, height='3', padx=5, pady=5, bg='#ffffe0', relief=SOLID)
SendMsg.grid(column=1,row=3,sticky="ew")

#Frame for displaying console log
consoleframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
consoleframe.grid(column=0,row=4,sticky="ew")
consoleframe.grid_columnconfigure(0,weight=1)
botscroll = ttk.Scrollbar(consoleframe)
botscroll.grid(column=1,row=0,sticky="ns")
console = Text(consoleframe, height='10', padx=10, pady=5, insertofftime=0, state='disabled')
console.grid(column=0,row=0,sticky="ew")
console.config(yscrollcommand=botscroll.set)
botscroll.config(command=console.yview)

win.mainloop()
