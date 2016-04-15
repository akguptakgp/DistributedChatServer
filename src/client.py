import socket,sys
from threading import Thread
import random
from datetime import datetime
import sys
import time
from functools import partial
import tkMessageBox
import Tkinter as tk
import select
import copy
import MySQLdb
import socket
import fcntl
import struct

class VectorClock(object):
	def __init__(self,string=None):
		if(string==None):
			self.Max_Clients=5
			self.vector_clock=[0 for i in range(self.Max_Clients)]
		else:
			string=string.split(',')
			self.Max_Clients=len(string)
			self.vector_clock=[0 for i in range(self.Max_Clients)]
			for i in range(self.Max_Clients):
				self.vector_clock[i]=int(string[i])
	def __str__(self):
		return ",".join(str(self.vector_clock[i]) for i in range(self.Max_Clients))	
	def increment(self,nodeId):
		self.vector_clock[nodeId]+=1
	
	def merge(self,b): # pass b as string
		b=b.split(',')
		for i in range(self.Max_Clients):
			self.vector_clock[i]=max(self.vector_clock[i],int(b[i]))

class message(object):
	def __init__(self,msg,msg_type,Client_id,Group_id,time_stamp=None,isDeliverable=True):
		self.Client_id=Client_id         # a string value
		self.Group_id=Group_id			 # a string value
		self.clock=time_stamp			 # a VectorClock value
		self.text=msg                    # string
		self.msg_type=msg_type           # 0 or 1
		self.isDeliverable = isDeliverable
	
	def __str__(self):
		if(self.msg_type==0):
			return "@#"+str(self.Client_id)+"#"+str(self.Group_id)+"#"+str(self.text)+"#"+str(self.clock)+"#"+str(self.isDeliverable) # client-client type
		else:
			return "^#"+str(self.Client_id)+"#"+str(self.Group_id)+"#"+str(self.text)


class Window(tk.Frame):
	def __init__(self,parent,client_object):
		tk.Frame.__init__(self, parent)
		self.selected_gid=1
		self.frame1=tk.Frame(parent)
		self.frame1.pack(side=tk.TOP)
		self.frame2=tk.Frame(parent)
		self.frame2.pack(side=tk.BOTTOM)

		self.text_show=tk.Text(self.frame1,height=40,width=20)
		self.text_show.pack(side=tk.LEFT,pady=15,padx=15)
		self.Group_list=tk.Listbox(self.frame1,selectmode=tk.SINGLE)
		self.Group_list.pack(padx=15,pady=30)

		self.text_type=tk.Text(self.frame2,height=2,width=20)
		self.text_type.pack(side=tk.LEFT,pady=15,padx=15)
		self.refresh=tk.Button(self.frame1,text="Refresh")
		self.refresh=tk.Button(self.frame1,text="Refresh",command=partial(self.disp_group))
		self.refresh.pack(pady=30)
		self.opp=tk.Button(self.frame1,text="Open Chat",command=partial(self.open_group))
		self.opp.pack(pady=30)

		self.logout=tk.Button(self.frame1,text="Logout",command=partial(client_object.action,5))
		self.logout.pack(side=tk.BOTTOM)		
		self.send=tk.Button(self.frame2,text="Send",command=partial(client_object.action,3,self.text_type,str(self.selected_gid)))
		self.send.pack(side=tk.LEFT)
		self.join=tk.Button(self.frame2,text="Join",command=partial(client_object.action,2,self.text_type))
		self.join.pack(side=tk.LEFT)
		self.Make=tk.Button(self.frame2,text="Make Group",command=partial(client_object.action,1,self.text_type))
		self.Make.pack(side=tk.LEFT)
		self.leave=tk.Button(self.frame1,text="Leave",command=partial(client_object.action,4,self.text_type))
		self.leave.pack(side=tk.BOTTOM)
		self.save_client=client_object
		self.display_list=[]

	def fetch_data(self):
		return self.text_type.get()

	def print_list(self,datalist):
		for items in datalist:
			self.text_show.insert(tk.END, items+'\n')
		return
	def print_line(self,data):
		self.text_show.insert(tk.END,data+'\n')

	def open_group(self,custom_selection=None):
		time.sleep(3)
		print "ChattingTable called with grp id",custom_selection
		tr=self.Group_list.curselection()
		if(custom_selection==None):
			if(len(tr)==0):
				print "Please select some group"
				return
		elif(custom_selection!=None):
			custom_selection=int(custom_selection)-1
			print custom_selection
			print self.display_list[custom_selection][6:7]
			print self.save_client.Grp_Info[self.display_list[custom_selection][6:7]]
			gid=self.display_list[custom_selection][6:7]
			self.selected_gid=gid
			self.text_show.delete("1.0",tk.END)
			if gid not in self.save_client.ChattingTable:
				return
			self.text_show.insert(tk.END, "chatting history of group:"+gid+'\n')
			for i in self.save_client.ChattingTable[gid]:
				print i
				self.text_show.insert(tk.END, i+'\n')
			return	

		print self.display_list[tr[0]][6:7]
		print self.save_client.Grp_Info[self.display_list[tr[0]][6:7]]
		gid=self.display_list[tr[0]][6:7]
		self.selected_gid=gid
		self.text_show.delete("1.0",tk.END)
		if gid not in self.save_client.ChattingTable:
			return
		self.text_show.insert(tk.END, "chatting history of group:"+gid+'\n')
		for i in self.save_client.ChattingTable[gid]:
			print i
			self.text_show.insert(tk.END, i+'\n')

	def disp_group(self):
		self.Group_list.delete(0,tk.END)
		self.display_list=[]
		for item in self.save_client.Grp_Info:
			self.display_list.append('group:'+item)
			to_insert='group:'+item+'->'
			for el in self.save_client.Grp_Info[item]:
				to_insert+=el+','
			self.Group_list.insert(tk.END,to_insert[:-1])	

class Client(object): # for logout, login for the time assume no logout because we need to store on disk 
	def __init__(self):
		if(len(sys.argv)<4):
			print " usage: python client.py serverportoffest clientID option"
			sys.exit(0)
		if(not self.RepresentsInt(sys.argv[2])):
			print "User ID must be an integer"
			sys.exit(0)
		if(not self.RepresentsInt(sys.argv[1])):
			print "serverportoffest must be an integer"
			sys.exit(0)
		if(self.RepresentsInt(sys.argv[3])):
			if(int(sys.argv[3])!=0 and int(sys.argv[3])!=1):
				print "only two values allowed 0-new client, 1- old client"
				sys.exit(0)
			elif(int(sys.argv[3])==0):
				print "new client"
			elif(int(sys.argv[3])==1):
				print "old Client"	
		else:
			print "only two values allowed 0-new client, 1- old client"
			sys.exit(0)
		self.uid=sys.argv[2]
		self.clocks={}	 # map of gid to VectorClock
		# self.serverIp=self.get_ip_address('eth0')
		self.serverIp="10.5.16.223"
		self.serverPort=50089+int(sys.argv[1])
		self.clientPort=random.randint(10000,60000)
		self.ClientId_IP={}
		self.Grp_Info={}
		self.BufferedMsg={}
		self.ChattingTable={}
		self.delay_queue={}	 # map of gid to list of delayed messages
		self.order_queue={}	 # map of gid to list of delayed messages
		self.uidRecord = []
		# self.clientIp='0.0.0.0'
		self.clientIp=self.get_ip_address('eth0')
		# Create two threads as follows
		self.thread1=True
		self.gui=None
		self.db=MySQLdb.connect("10.5.18.68","12CS10006","btech12","12CS10006")
		cursor = self.db.cursor()
		sql="SELECT VERSION();"
		cursor.execute(sql)
		print self.get_ip_address('eth0')  # '192.168.0.110'

		print cursor.fetchall()
		Thread(target=self.execute, args=()).start()
		self.thread2=True
		Thread(target=self.RecvAndServe, args=()).start()	


	def get_ip_address(self,ifname):
	    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	    return socket.inet_ntoa(fcntl.ioctl(
	        s.fileno(),
	        0x8915,  # SIOCGIFADDR
	        struct.pack('256s', ifname[:15])
	    )[20:24])
	def RepresentsInt(self,s):
	    try: 
	        int(s)
	        return True
	    except ValueError:
	        return False
	# msg : string
	def empty_delay_queue(self,msg):
		while(1):
			check = 0
			delay_delivery = False
			while(msg.text != None and msg.Group_id in self.delay_queue and len(self.delay_queue[msg.Group_id]) > 0 and self.delay_queue[msg.Group_id][0].isDeliverable == False):
				clock = self.clocks[msg.Group_id]
				if(int(msg.Client_id) != int(self.uid)):
					if(clock.vector_clock[int(msg.Client_id) - 1] != msg.clock.vector_clock[int(msg.Client_id) - 1] - 1):
						delay_delivery = True
					else:
						for member in self.Grp_Info[msg.Group_id]:
							if(self.Grp_Info[msg.Group_id][member] == True and int(member) != int(msg.Client_id) and clock.vector_clock[int(member) - 1] < msg.clock.vector_clock[int(member) - 1]):
								delay_delivery = True
								break
				if(delay_delivery == True):
					break
				else:
					check += 1
					x = self.delay_queue[msg.Group_id].pop(0)
					print x.text,' delivered by ',x.Client_id,x.Group_id
					if(x.Group_id in self.ChattingTable.keys()):
						self.ChattingTable[x.Group_id].append(x.Client_id+" : "+x.text)
					else:
						self.ChattingTable[x.Group_id] = [x.Client_id+" : "+x.text]
					self.gui.open_group(x.Group_id)

			while(msg.Group_id in self.delay_queue and len(self.delay_queue[msg.Group_id]) > 0 and self.delay_queue[msg.Group_id][0].isDeliverable == True):
				check += 1
				x = self.delay_queue[msg.Group_id].pop(0)
				print x.text,' delivered by ',x.Client_id,x.Group_id
				if(x.Group_id in self.ChattingTable.keys()):
					self.ChattingTable[x.Group_id].append(x.Client_id+" : "+x.text)
				else:
					self.ChattingTable[x.Group_id] = [x.Client_id+" : "+x.text]
				self.gui.open_group(x.Group_id)
			if(check == 0):
				break
	def cbcastSend(self,gid,msg,isDeliverable=True):
		# increment the clock value once during a single bdcast
		self.clocks[gid].increment(int(self.uid)-1) # assume node id to be self.uid-1
		copyClock = copy.deepcopy(self.clocks[gid]) # shallow copy
		for i in self.Grp_Info[gid]:
			# if(i!=self.uid):
			self.Send_message(msg,gid,self.ClientId_IP[i][0],int(self.ClientId_IP[i][1]),True,isDeliverable,copyClock)
			time.sleep(2)

	# msg : string
	def cbcastSend_(self,gid,msg,isDeliverable=True):
		# increment the clock value once during a single bdcast
		for i in self.Grp_Info[gid]:
			if(int(i) != int(self.uid)):
				self.Send_message(msg,gid,self.ClientId_IP[i][0],int(self.ClientId_IP[i][1]),True,isDeliverable)
			# time.sleep(5)

	def abcastSend(self,gid,msg):
		if(int(self.uid) == 1): # if it has token
			self.cbcastSend(gid,msg,True)
		else:
			self.cbcastSend(gid,msg,False)

	def action(self,opt,textr=None,selected_gid=None):
		print "select option 1,2,3[create,join,chat]"
		print type(opt)
		if(opt==1):
			gid=textr.get("1.0",'end-1c')
			if(not self.RepresentsInt(gid)):
				tkMessageBox.showinfo("Error", "Enter a valid group ID")
				textr.delete("1.0",tk.END)
				return
			print "joinig Group Id ",gid
			self.Send_message('join',gid)
		elif(opt==2):
			gid=textr.get("1.0",'end-1c')
			if(not self.RepresentsInt(gid)):
				tkMessageBox.showinfo("Error", "Enter a valid group ID")
				textr.delete("1.0",tk.END)
				return
			print "joinig Group Id ",gid
			self.Send_message('join',gid)
		elif(opt==3):
			tr=self.gui.Group_list.curselection()
			if(len(tr)==0):
				print "Please select some group"
				textr.delete("1.0",tk.END)
				tkMessageBox.showinfo("Error", "Select a group before sending a message")
				return
			gid=self.gui.display_list[tr[0]][6:7]
			msg=textr.get("1.0",'end-1c')
			if(len(msg)==0):
				print "Please enter a valid message.."
				#textr.delete("1.0",tk.END)
				tkMessageBox.showinfo("Error", "Enter a valid message")
				return
			print "send message ",msg," to ",gid
			self.abcastSend(gid,msg)	
		elif(opt==4):
			gid=textr.get("1.0",'end-1c')
			if(not self.RepresentsInt(gid)):
				tkMessageBox.showinfo("Error", "Enter a valid group ID")
				textr.delete("1.0",tk.END)
				return
			print "leaving Group Id ",gid
			self.Send_message('leave',gid)
		elif(opt==5): # logout
			self.thread1=False
			self.thread2=False
			sys.exit(0)
		print textr.get("1.0",'end-1c')
		textr.delete("1.0",tk.END)		

	def execute(self):
		print "thread 1"
		root=tk.Tk()
		self.gui = Window(root,self)
		root.mainloop()
	
	def Send_message(self,msg_text,gid,host=None,port=None,Client=False,isDeliverable=True,copyClock=None):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if(Client):
			soc.connect((host, port))
			if(copyClock != None):
				soc.sendall(str(message(msg_text,0,self.uid,gid,copyClock,isDeliverable)))
			else:
				soc.sendall(str(message(msg_text,0,self.uid,gid,self.clocks[gid],isDeliverable)))
		else:
			soc.connect((self.serverIp,self.serverPort))
			soc.sendall(str(message(msg_text+'/'+self.clientIp+'/'+str(self.clientPort),1,self.uid,gid)))
			# soc.sendall("^#"+str(self.uid)+'#'+str(gid)+'#'+msg_text+'/'+self.clientIp+'/'+str(self.clientPort))
		soc.close()
	def handle_server(self,msg): # ignore uid send by server
		parsed=msg.text.split('/')
		if(parsed[0]=="InformJoin"):
			print "join"
			self.ClientId_IP[parsed[1]]=(parsed[2],int(parsed[3]))
			if(msg.Group_id in self.Grp_Info):
				self.Grp_Info[msg.Group_id][parsed[1]]=True
				print "other joined"
			else:
				print "Error"
		elif(parsed[0]=="InformLeave"):
			del self.Grp_Info[msg.Group_id][parsed[1]]
			if(parsed[1]==self.uid):
				del self.Grp_Info[msg.Group_id]
			else:
				for i in self.Grp_Info[msg.Group_id]:
					print i 
		elif(parsed[0]=="InformLogout"):
			self.Grp_Info[msg.Group_id][parsed[1]]=False
		elif(parsed[0]=="InformLogin"):
			self.ClientId_IP[msg.Group_id][parsed[1]]=(parsed[2],int(parsed[3]))
			self.Grp_Info[msg.Group_id][msg.Client_id]=True
		elif(parsed[0]=="InformJoinsuccess"):
			self.clocks[msg.Group_id]=VectorClock()
			self.Grp_Info[msg.Group_id]={}
			ip_id_list=parsed[1].split(':')
			for i in ip_id_list:
				self.ClientId_IP[i.split(',')[0]]=(i.split(',')[1],int(i.split(',')[2]))
				self.Grp_Info[msg.Group_id][i.split(',')[0]]=True
		self.gui.disp_group()		
	# msg : message type
	def cbcastReceive(self,msg):
		if(int(self.uid) == 1 and msg.isDeliverable == False):
			delay_delivery = False
			clock = self.clocks[msg.Group_id]
			if(int(msg.Client_id) == 3):
				print self.clocks[msg.Group_id].vector_clock
			if(int(msg.Client_id) != int(self.uid)):
				if(clock.vector_clock[int(msg.Client_id) - 1] != msg.clock.vector_clock[int(msg.Client_id) - 1] - 1):
					delay_delivery = True
					print "Cond 1 failed"
				else:
					for member in self.Grp_Info[msg.Group_id]:
						if(self.Grp_Info[msg.Group_id][member] == True and int(member) != int(msg.Client_id) and clock.vector_clock[int(member) - 1] < msg.clock.vector_clock[int(member) - 1]):
							delay_delivery = True
							print "Cond 2 failed"
							break
			if(delay_delivery == True or (msg.Group_id in self.delay_queue.keys() and len(self.delay_queue[msg.Group_id]) > 0)):
				self.delay_queue[msg.Group_id].append(msg)
				self.delay_queue[msg.Group_id].sort(timestamp_compare)
				print msg.text,' queued by ',msg.Client_id,msg.Group_id         
			else:
				# deliver(msg) and note the uid 
				self.uidRecord.append(msg.Client_id)
				print msg.text,' delivered by ',msg.Client_id,msg.Group_id
				if(msg.Group_id in self.ChattingTable.keys()):
					self.ChattingTable[msg.Group_id].append(msg.Client_id+" : "+msg.text)
				else:
					self.ChattingTable[msg.Group_id] = [msg.Client_id+" : "+msg.text]
				self.gui.open_group(msg.Group_id)
				if(int(msg.Client_id) != int(self.uid)):
					clock.increment(int(msg.Client_id)-1)
				for member in self.Grp_Info[msg.Group_id]:
					clock.vector_clock[int(member)-1] = max(clock.vector_clock[int(member)-1],msg.clock.vector_clock[int(member)-1])
				# print self.clocks[msg.Group_id]
				# if delivered one or more ABcast messages then send a sets-order message
				if(len(self.uidRecord) == 1):
					self.cbcastSend_(msg.Group_id,"$#"+self.uidRecord[0])
					self.uidRecord = []
		elif(int(self.uid) != 1 and msg.isDeliverable == False):
			# print "I am here ",msg.Group_id
			# print self.delay_queue
			if(msg.Group_id not in self.delay_queue.keys()):
				self.delay_queue[msg.Group_id] = [msg]
			else:	
				self.delay_queue[msg.Group_id].append(msg)
			self.delay_queue[msg.Group_id].sort(self.timestamp_compare)
			print self.delay_queue
			print msg.text,' queued by ',msg.Client_id,msg.Group_id
			# print self.delay_queue[msg.Group_id][0].text
			while(msg.Group_id in self.order_queue.keys() and len(self.order_queue[msg.Group_id]) > 0):
				clock = self.clocks[msg.Group_id]
				x = self.order_queue[msg.Group_id][0]
				status = 1
				for mesg in self.delay_queue[msg.Group_id]:
					if(int(mesg.Client_id) == int(x.Client_id)):
						status = 0
						self.delay_queue[msg.Group_id].remove(mesg)
						self.order_queue[msg.Group_id].remove(x)
						# deliver(msg) 
						print mesg.text,' delivered by ',mesg.Client_id,mesg.Group_id
						if(msg.Group_id in self.ChattingTable.keys()):
							self.ChattingTable[msg.Group_id].append(msg.Client_id+" : "+msg.text)
						else:
							self.ChattingTable[msg.Group_id] = [msg.Client_id+" : "+msg.text]						
						self.gui.open_group(msg.Group_id)	
						if(int(mesg.Client_id) != int(self.uid)):
							clock.increment(int(mesg.Client_id)-1)
						for member in self.Grp_Info[mesg.Group_id]:
							clock.vector_clock[int(member)-1] = max(clock.vector_clock[int(member)-1],msg.clock.vector_clock[int(member)-1])
						break
				if(status == 1):
					break
		else:
			delay_delivery = False
			clock = self.clocks[msg.Group_id]
			if(int(msg.Client_id) != int(self.uid)):
				if(clock.vector_clock[int(msg.Client_id) - 1] != msg.clock.vector_clock[int(msg.Client_id) - 1] - 1):
					delay_delivery = True
					print "Cond 1 failed"
				else:
					for member in self.Grp_Info[msg.Group_id]:
						if(self.Grp_Info[msg.Group_id][member] == True and int(member) != int(msg.Client_id) and clock.vector_clock[int(member) - 1] < msg.clock.vector_clock[int(member) - 1]):
							delay_delivery = True
							print "Cond 2 failed"
							break
			if(delay_delivery == True or (msg.Group_id in self.delay_queue.keys() and len(self.delay_queue[msg.Group_id]) > 0)):
				self.delay_queue[msg.Group_id].append(msg)
				self.delay_queue[msg.Group_id].sort(self.timestamp_compare)
				print msg.text,' queued by ',msg.Client_id,msg.Group_id
			else:
				# deliver(msg) 
				print msg.text,' delivered by ',msg.Client_id,msg.Group_id
				if(msg.Group_id in self.ChattingTable.keys()):
					self.ChattingTable[msg.Group_id].append(msg.Client_id+" : "+msg.text)
				else:
					self.ChattingTable[msg.Group_id] = [msg.Client_id+" : "+msg.text]				
				self.gui.open_group(msg.Group_id)
				if(int(msg.Client_id) != int(self.uid)):
					clock.increment(int(msg.Client_id)-1)
				for member in self.Grp_Info[msg.Group_id]:
					clock.vector_clock[int(member)-1] = max(clock.vector_clock[int(member)-1],msg.clock.vector_clock[int(member)-1])
				# print self.clocks[msg.Group_id]

	# msg : message type
	def abcastReceive(self,msg):
		self.cbcastReceive(msg)

	# this module handles the message from the client
	def handle_client(self,msg):
		# print "Jaigurudev :::: ",msg.text,' received from ',msg.Client_id,msg.Group_id,type(msg.clock),msg.isDeliverable
		# if(msg.Client_id != self.uid):
		# print "Msg received"
		# self.cbcastReceive_(msg)
		self.abcastReceive(msg)

	def handle(self,string):
		msg=self.ReadFromString(string)
		# print msg.msg_type	 
		if(msg.msg_type==1):
			self.handle_server(msg)
		elif(msg.msg_type==0):
			self.empty_delay_queue(msg)
			self.handle_client(msg)
			self.empty_delay_queue(msg)
		elif(msg.msg_type==-1):
			# print "Hey Gurudev help from here"
			# Order the msgs in the Cbcast queue according to the order in the msg
			# print len(self.order_queue)
			self.empty_delay_queue(msg)
			if(msg.Group_id not in self.order_queue):
				self.order_queue[msg.Group_id] = [msg]
			else:	
				self.order_queue[msg.Group_id].append(msg)
			status = 0
			while(msg.Group_id in self.order_queue.keys() and len(self.order_queue[msg.Group_id]) > 0):
				clock = self.clocks[msg.Group_id]
				x = self.order_queue[msg.Group_id][0]
				status = 1
				if(msg.Group_id not in self.delay_queue):
					break
				for mesg in self.delay_queue[msg.Group_id]:
					if(int(mesg.Client_id) == int(x.Client_id)):
						status = 0
						self.delay_queue[mesg.Group_id].remove(mesg)
						self.order_queue[mesg.Group_id].remove(x)
						print mesg.text,' delivered by ',mesg.Client_id,mesg.Group_id
						if(mesg.Group_id in self.ChattingTable.keys()):
							self.ChattingTable[msg.Group_id].append(mesg.Client_id+" : "+mesg.text)
						else:
							self.ChattingTable[mesg.Group_id] = [mesg.Client_id+" : "+mesg.text]
						self.gui.open_group(mesg.Group_id)
						if(int(mesg.Client_id) != int(self.uid)):
							clock.increment(int(mesg.Client_id)-1)
						for member in self.Grp_Info[mesg.Group_id]:
							clock.vector_clock[int(member)-1] = max(clock.vector_clock[int(member)-1],mesg.clock.vector_clock[int(member)-1])
						break
				self.empty_delay_queue(msg)
				if(status == 1):
					break
		else:
			print "I am here no one to care"		


	def RecvAndServe(self):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		soc.setblocking(0)
		soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		soc.bind((self.clientIp,self.clientPort))
		soc.listen(10)
		print "client listing at ",str(self.clientPort)
		while self.thread2:
			try:
				# print "connect"
				conn, addr = soc.accept()
				print 'Connected with ' + addr[0] + ':' + str(addr[1])
				self.handle(conn.recv(1024))
			except socket.error:
				pass
				# print "looping"
		print "server stopped"	

	def ReadFromString(self,message_string):
		msg=message_string.split('#')
		print msg
		if(len(msg) == 7): # order msg
			return message(None,-1,msg[4],msg[2],None)			
		if(msg[0]=="@"): # client-client type message
			# return message(msg[3],0,msg[1],msg[2],VectorClock(msg[4]),msg[5])
			# def __init__(self,msg,msg_type,Client_id,Group_id,time_stamp=None,isDeliverable=True)
			if(msg[5] == "False"):
				return message(msg[3],0,msg[1],msg[2],VectorClock(msg[4]),False)
			else:
				return message(msg[3],0,msg[1],msg[2],VectorClock(msg[4]))
		elif(msg[0]=="^"): # server-client type message
			return message(msg[3],1,msg[1],msg[2]) 	
	
	# assuming the active members in both the timestamps are same
	# vectorClock : list
	def timestamp_compare(self,msg1,msg2):
		vectorClock1 = msg1.clock.vector_clock
		vectorClock2 = msg2.clock.vector_clock
		ans = True # assuming vectorClock1 > vectorClock2
		for i in range(msg1.clock.Max_Clients):
			if(vectorClock1[i] < vectorClock2[i]):
				ans = False
				break
		return ans

if __name__=='__main__':
	random.seed(datetime.now())
	c=Client()
	# print message(VectorClock() ,"hi",5,1)