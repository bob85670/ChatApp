#!/usr/bin/python3

# Student name and No.: Lau Tsz Yin 3035686516
# Development platform: MacOs
# Python version: Python 3.9.7

import sys
import socket
import threading
import select
import json
import time

def main(argv):
	# set port number
	# default is 32349 if no input argument
	if len(argv) == 2:
		port = int(argv[1])
	else:
		port = 32349

	# create socket and bind
	sockfd = socket.socket()
	try:
		sockfd.bind(('', port))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)

	# set socket listening queue
	sockfd.listen(5)

	# add the listening socket to the READ socket list
	RList = [sockfd]

	# create an empty WRITE socket list
	CList = []

	numOfPeers = 0

	Data = []

	# {newfd : immed_data}, e,g, {<socket.socket fd=4, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, 
	# proto=0, laddr=('127.0.0.1', 32349), raddr=('127.0.0.1', 53509)>: {'UN': 'Peter', 'UID': 'peter@hku.hk'}}
	Record = {}

	# {newfd: email}, e.g. {<socket.socket fd=4, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM,
	# proto=0, laddr=('127.0.0.1', 32349), raddr=('127.0.0.1', 53509)>: 'peter@hku.hk' }
	emailRecord = {}

	


	# start the main loop
	while True:
		# use select to wait for any incoming connection requests or
		# incoming messages or 10 seconds
		try:
			Rready, Wready, Eready = select.select(RList, [], [], 10)
		except select.error as emsg:
			print("At select, caught an exception:", emsg)
			sys.exit(1)
		except KeyboardInterrupt:
			print("At select, caught the KeyboardInterrupt")
			sys.exit(1)

		# if has incoming activities
		if Rready:
			# for each socket in the READ ready list
			for sd in Rready:

				# if the listening socket is ready
				# that means a new connection request
				# accept that new connection request
				# add the new client connection to READ socket list
				# add the new client connection to WRITE socket list
				if sd == sockfd:
					newfd, caddr = sockfd.accept()
					print("A new client has arrived. It is at:", caddr)
					print("newfd:", newfd, " caddr: ", caddr)

					numOfPeers += 1
					print("No. of peers: ", numOfPeers)

					RList.append(newfd)
					CList.append(newfd)

					print("CList: ", CList)


				# else is a client socket being ready
				# that means a message is waiting or 
				# a connection is broken
				# if a new message arrived, send to everybody
				# except the sender
				# if broken connection, remove that socket from READ 
				# and WRITE lists
				else:
					rmsg = sd.recv(500)
					if rmsg:
						print("Got a message!!")

						immed = rmsg.decode("ascii")
						receive_msg = json.loads(immed)
						print("immed: ", immed)
						print("receive_msg is received from", caddr)


						#Receive JOIN message
						if receive_msg["CMD"] == "JOIN":

							#Update Record
							immed_data = {"UN": receive_msg["UN"], "UID": receive_msg["UID"]}
							print("Added peer: ", immed_data)


							Record[newfd] = immed_data
							print("Record: ", Record)

							emailRecord[newfd] = receive_msg["UID"]
							print("emailRecord: ", emailRecord)


							#send ACK message 
							try:
								msg_Ack = {"CMD": "ACK", "TYPE": "OKAY"}
								jstr = json.dumps(msg_Ack)
								sd.send(jstr.encode("ascii"))
								print("ACK command sent")
							except:
								print("Cannot send ACK. Socket is not connected")

							time.sleep(0.1)

							#send updated peer list
							peerList = []
							for a in Record.values():
								peerList.append(a)
							print("peerList: ", peerList)

							try:
								for q in CList:
									print("q: ", q)
									msg_List = {"CMD": "LIST", "DATA": peerList} 
									jstr2 = json.dumps(msg_List)
									q.send(jstr2.encode("ascii"))

								print("LIST command sent to all connected clients")
							except:
								print("Cannot send the peer list.")

							
						#Receive SEND message
						elif receive_msg["CMD"] == "SEND":

							print("receive_msg with key TO: ", receive_msg["TO"])
							
							def get_key(val):
								for key, value in emailRecord.items():
									if val == value:
										return key
							
							"""
							if len(CList) > 1:
								print("Relay it to others.")
								for p in CList:
									if p != sd:
										p.send(rmsg)
							"""
							if len(receive_msg["TO"]) == 0:	#Remark: empty list = False
								#Broadcast 
								try:
									for p in CList:
										if p != sd:
											msg_msg = {"CMD": "MSG", "TYPE":"ALL", "MSG": receive_msg["MSG"], "FROM": receive_msg["FROM"]}
											jstr = json.dumps(msg_msg)
											p.send(jstr.encode("ascii"))
									print("MSG command sent to all connected clients")
								except:
									print("Cannot send the MSG command.")


							elif len(receive_msg["TO"]) > 1:
								#Group
					
								immed_socket = []
								for i in range(len(receive_msg["TO"])):
									immed_socket.append(get_key(receive_msg["TO"][i]))

								print("immed_socket: ", immed_socket)

								try:
									for p in immed_socket:
										msg_msg = {"CMD": "MSG", "TYPE":"GROUP", "MSG": receive_msg["MSG"], "FROM": receive_msg["FROM"]}
										jstr = json.dumps(msg_msg)
										p.send(jstr.encode("ascii"))
									print("MSG command sent to a group of clients")
								except:
									print("Cannot send the MSG command.")

							elif len(receive_msg["TO"]) == 1:
								#Private

								immed_socket = []
								immed_socket.append(get_key(receive_msg["TO"][0]))
								print("immed_socket: ", immed_socket)

								try:
									msg_msg = {"CMD": "MSG", "TYPE": "PRIVATE", "MSG": receive_msg["MSG"], "FROM": receive_msg["FROM"]}
									jstr = json.dumps(msg_msg)
									immed_socket[0].send(jstr.encode("ascii"))
									print("MSG command sent to one client")
								except:
									print("Cannot send the MSG command.")




						else:
							print("It is an unknown command. We will ignore it.")


					else:
						print("A client connection is broken!!")


						CList.remove(sd)
						RList.remove(sd)

						#print("sd is: ", sd)
						#print("sockfd is:", sockfd)
						

						numOfPeers -= 1
						print("No. of peers: ", numOfPeers)

		
						removed_socket = Record.pop(sd)
						print("Removed socket is: ", removed_socket)

						r_s = emailRecord.pop(sd)
						print("Record: ", Record)
						print("emailRecord: ", emailRecord)

						#send updated peer list to others
						peerList = []
						for a in Record.values():
							peerList.append(a)
						print("peerList after removing socket: ", peerList)

						try:
							for q in CList:
								msg_List = {"CMD": "LIST", "DATA": peerList} 
								jstr2 = json.dumps(msg_List)
								q.send(jstr2.encode("ascii"))

							print("LIST command sent to all other connected clients")
						except:
							print("Cannot send the peer list.")


		# else did not have activity for 10 seconds, 
		# just print out "Idling"
		else:
			print("Idling")


if __name__ == '__main__':
	if len(sys.argv) > 2:
		print("Usage: chatserver [<Server_port>]")
		sys.exit(1)
	main(sys.argv)