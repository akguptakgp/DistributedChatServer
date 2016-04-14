import socket,sys
from threading import Thread
import random
from datetime import datetime
import sys

class VectorClock(object):
	def __init__(self):
		self.Max_Clients=100
		self.vector_clock=[0 for i in range(self.Max_Clients)]
	def __str__(self):
		return ",".join(str(self.vector_clock[i]) for i in range(self.Max_Clients))	
	def increment(self,nodeId):
		self.vector_clock[nodeId]+=1
	
	def merge(self,b): # pass b as string
		b=b.split(',')
		for i in range(self.Max_Clients):
			self.vector_clock[i]=max(self.vector_clock[i],int(b[i]))

class message(object):
	def __init__(self,msg,msg_type,Client_id,Group_id,time_stamp=None):
		self.Client_id=Client_id         # a string value
		self.Group_id=Group_id			 # a string value
		self.clock=time_stamp			 # a VectorClock value
		self.text=msg                    # string
		self.msg_type=msg_type           # 0 or 1
	
	def __str__(self):
		if(self.msg_type==0):
			return "@#"+str(self.Client_id)+"#"+str(self.Group_id)+"#"+str(self.text)+"#"+str(self.clock) # client-client type
		else:
			return "^#"+str(self.Client_id)+"#"+str(self.Group_id)+"#"+str(self.text)

class Client(object): # for logout, login for the time assume no logout because we need to store on disk 
	def __init__(self):
		print "Please Enter your user ID"
		self.uid=raw_input()
		self.clocks={}	
		self.serverIp='localhost'
		self.serverPort=50089+int(sys.argv[1])
		self.clientPort=random.randint(10000,60000)
		self.ClientId_IP={}
		self.Grp_Info={}
		self.BufferedMsg={}
		self.ChattingTable={}
		self.delay_queue=[]	
		self.clientIp='localhost'
		# Create two threads as follows
		Thread(target=self.execute, args=()).start()
		Thread(target=self.RecvAndServe, args=()).start()	

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
				for i in self.Grp_Info[gid]:
					self.clocks[gid].increment(int(self.uid)-1) # assume node id to be self.uid-1
					if(self.Grp_Info[gid][i]!=self.uid):
						self.Send_message(msg,gid,self.ClientId_IP[i][0],int(self.ClientId_IP[i][1]),Client=True)
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
	
	def Send_message(self,msg_text,gid,host=None,port=None,Client=False):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if(Client):
			soc.connect((host, port))
			soc.sendall(str(message(msg_text,0,self.uid,gid,self.clocks[gid])))
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
				

	def handle_client(self,msg):
		print msg.text,' received from ',msg.Client_id,msg.Group_id

	def handle(self,string):
		msg=self.ReadFromString(string)
		# print msg.msg_type	 
		if(msg.msg_type==1):
			self.handle_server(msg)
		if(msg.msg_type==0):
			self.handle_client(msg)

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
		if(msg[0]=="@"): # client-client type message
			return message(msg[3],0,msg[1],msg[2],msg[4])
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


	# msg : message type
	def cbcast(self,msg):
		delay_delivery = 0
		clock = self.clocks[msg.Group_id]
		if(clock.vector_clock[msg.Client_id] != msg.clock.vector_clock[msg.Client_id] - 1):
			delay_delivery = 1
		else:
			for member in self.Grp_Info[msg.Group_id]:
				if(clock.vector_clock[member] < msg.clock.vector_clock[member]):
					delay_delivery = 1
					break
		if delay_delivery == 1:
			delay_queue.append(msg)
			delay_queue.sort(timestamp_compare)
		else:
			# deliver(msg)
			chat.append(msg.Client_id + ' says ' + msg.text)
			clock.vector_clock[self.uid] += 1
			for member in self.Grp_Info[msg.Group_id]:
				clock.vector_clock[member] = max(clock.vector_clock[member],msg.clock.vector_clock[member])		

if __name__=='__main__':
	random.seed(datetime.now())
	c=Client()
	# print message(VectorClock() ,"hi",5,1)