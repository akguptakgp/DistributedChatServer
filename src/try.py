import socket

HOST = '10.5.16.194'    # chat server IP
PORT= 50007              # port as used by the server
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
	def __init__(self,time_stamp,msg,Client_id,Group_id, mid=1):
		self.message_id=mid
		self.clock=time_stamp
		self.text=msg 
		self.Client_id=Client_id
		self.Group_id=Group_id
	def __str__(self):
		return str(self.Client_id)+"#"+str(self.text)+"#"+str(self.Group_id)+"#"+str(self.clock)
		
class Client(object):
	def __init__(self):
		self.socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print "Please Enter your user ID"
		self.uid=raw_input()
		self.execute()

	def execute(self):
		while(1):
			print "select option 1,2,3[create,join,chat]"
			opt=int(raw_input())
			if(opt==1):
				print "Enter Group Id you wants to create"
				gid=raw_input()
				self.socket.connect((HOST, PORT))
				self.socket.sendall('join#'+gid+"#"+uid)
			elif(opt==2):
				print "Enter Group Id you wants to join"
				gid=raw_input()
				self.socket.connect((HOST, PORT))
				self.socket.sendall('join#'+gid+"#"+uid)
			elif(opt==3):
				print "Enter Group Id you wants to chat"
				gid=raw_input()	
	
	def Send_message(self,m):
		pass

if __name__=='__main__':
	# c=Client()
	print message(VectorClock() ,"hi",5,1)