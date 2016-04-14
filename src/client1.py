import socket,sys
from threading import Thread
import random
from datetime import datetime
import sys
import time

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

class Client(object): # for logout, login for the time assume no logout because we need to store on disk 
	def __init__(self):
		print "Please Enter your user ID"
		self.uid=raw_input()
		self.clocks={}	 # map of gid to VectorClock
		self.serverIp='localhost'
		self.serverPort=50089+int(sys.argv[1])
		self.clientPort=random.randint(10000,60000)
		self.ClientId_IP={}
		self.Grp_Info={}
		self.BufferedMsg={}
		self.ChattingTable={}
		self.delay_queue={}	 # map of gid to list of delayed messages
		self.order_queue={}	 # map of gid to list of delayed messages
		self.uidRecord = []
		self.clientIp='localhost'
		# Create two threads as follows
		Thread(target=self.execute, args=()).start()
		Thread(target=self.RecvAndServe, args=()).start()	

	# msg : string
	def cbcastSend(self,gid,msg,isDeliverable=True):
		# increment the clock value once during a single bdcast
		self.clocks[gid].increment(int(self.uid)-1) # assume node id to be self.uid-1
		for i in self.Grp_Info[gid]:
			# if(i!=self.uid):
			self.Send_message(msg,gid,self.ClientId_IP[i][0],int(self.ClientId_IP[i][1]),True,isDeliverable)
			time.sleep(5)

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



	def execute(self):
		print "thread 1"
		while(1):
			print "select option 1,2,3[create,join,chat]"
			opt=int(raw_input())
			if(opt==1):
				print "Enter Group Id you wants to create"
				gid=raw_input()
				self.Send_message('join',gid)
			elif(opt==2):
				print "Enter Group Id you wants to join"
				gid=raw_input()
				self.Send_message('join',gid)
			elif(opt==3):
				print "Enter Group Id you wants to chat"
				gid=raw_input()
				print "Enter message"
				msg=raw_input()
				self.abcastSend(gid,msg)
			elif(opt==5):
				print "Enter Group Id you wants to leave"
				gid=raw_input()
				self.Send_message('leave',gid)
			elif(opt==6): # logout
				print "Enter Group Id you wants to join"
				gid=raw_input()
				self.Send_message('join',gid)	
			elif(opt==4):
				sys.exit(0)
	
	def Send_message(self,msg_text,gid,host=None,port=None,Client=False,isDeliverable=True):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if(Client):
			soc.connect((host, port))
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

	# msg : message type
	def cbcastReceive(self,msg):
		if(int(self.uid) == 1 and msg.isDeliverable == False):
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
			if delay_delivery == True:
				self.delay_queue[msg.Group_id].append(msg)
				self.delay_queue[msg.Group_id].sort(timestamp_compare)
			else:
				# deliver(msg) and note the uid 
				self.uidRecord.append(msg.Client_id)
				print msg.text,' delivered by ',msg.Client_id,msg.Group_id
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
			if(len(self.delay_queue) == 0):
				self.delay_queue[msg.Group_id] = [msg]
			else:	
				self.delay_queue[msg.Group_id].append(msg)
			self.delay_queue[msg.Group_id].sort(self.timestamp_compare)
			# print self.delay_queue[msg.Group_id][0].text
			while(len(self.order_queue[msg.Group_id]) > 0):
				clock = self.clocks[msg.Group_id]
				x = self.order_queue[msg.Group_id][0]
				for mesg in self.delay_queue[msg.Group_id]:
					if(mesg.Client_id == x.Client_id):
						self.delay_queue[msg.Group_id].remove(mesg)
						self.order_queue[msg.Group_id].remove(x)
						# deliver(msg) 
						print mesg.text,' delivered by ',mesg.Client_id,mesg.Group_id
						if(int(mesg.Client_id) != int(self.uid)):
							clock.increment(int(mesg.Client_id)-1)
						for member in self.Grp_Info[mesg.Group_id]:
							clock.vector_clock[int(member)-1] = max(clock.vector_clock[int(member)-1],msg.clock.vector_clock[int(member)-1])
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
			if delay_delivery == True:
				self.delay_queue[msg.Group_id].append(msg)
				self.delay_queue[msg.Group_id].sort(self.timestamp_compare)
			else:
				# deliver(msg) 
				print msg.text,' delivered by ',msg.Client_id,msg.Group_id
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
			self.handle_client(msg)
		elif(msg.msg_type==-1):
			# print "Hey Gurudev help from here"
			# Order the msgs in the Cbcast queue according to the order in the msg
			# print len(self.order_queue)
			if(len(self.order_queue) == 0):
				self.order_queue[msg.Group_id] = [msg]
			else:	
				self.order_queue[msg.Group_id].append(msg)


	def RecvAndServe(self):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		soc.bind((self.clientIp,self.clientPort))
		soc.listen(10)
		print "client listing at ",str(self.clientPort)
		while True:
			conn, addr = soc.accept()
			print 'Connected with ' + addr[0] + ':' + str(addr[1])
			self.handle(conn.recv(1024))

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
	def timestamp_compare(msg1,msg2):
		vectorClock1 = msg1.clock
		vectorClock2 = msg2.clock
		ans = True # assuming vectorClock1 > vectorClock2
		for i in vectorClock1.Max_Clients:
			if(vectorClock1[i] < vectorClock2[i]):
				ans = False
				break
		return ans


			

if __name__=='__main__':
	random.seed(datetime.now())
	c=Client()
	# print message(VectorClock() ,"hi",5,1)