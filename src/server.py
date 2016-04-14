import socket
import sys

class message(object):
	def __init__(self,msg,msg_type,Client_id,Group_id,time_stamp=None):
		self.Client_id=Client_id         # a str value
		self.Group_id=Group_id		 # a str value
		self.clock=time_stamp			 # a VectorClock value
		self.text=msg                    # string
		self.msg_type=msg_type           # 0 or 1
	
	def __str__(self):
		if(self.msg_type==0):
			return "@#"+str(self.Client_id)+"#"+str(self.Group_id)+"#"+str(self.text)+"#"+str(self.clock) # client-client type
		else:
			return "^#"+str(self.Client_id)+"#"+str(self.Group_id)+"#"+str(self.text)

class Server(object):
	def __init__(self):
		self.socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serverIp='localhost'
		self.serverPort=50089+int(sys.argv[1])
		self.ClientId_IP={}   # int key
		self.Grp_Info={}      # int key
		self.execute()

	def execute(self):
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((self.serverIp,self.serverPort))
		self.socket.listen(10)
		print "server listing at ",str(self.serverPort)
		while True:
			conn, addr = self.socket.accept()
			print 'Connected with ' + addr[0] + ':' + str(addr[1])
			self.handle(conn.recv(1024)) 
	
	def handle(self,string):
		msg=self.ReadFromString(string)
		parsed=msg.text.split('/')
		# self.Send_message('fun','fg',self.ClientId_IP[msg.Group_id][0],int(self.ClientId_IP[msg.Group_id][1]))
		if(parsed[0]=="join"):
			print "join"
			self.ClientId_IP[msg.Client_id]=(parsed[1],int(parsed[2]))
			if(msg.Group_id in self.Grp_Info):
				self.Grp_Info[msg.Group_id][msg.Client_id]=True
			else:
				self.Grp_Info[msg.Group_id]={}
				self.Grp_Info[msg.Group_id][msg.Client_id]=True
			for i in self.Grp_Info[msg.Group_id]:
				if(i!=msg.Client_id and self.Grp_Info[msg.Group_id][i]): # not same client and online
					self.Send_message('InformJoin'+'/'+str(msg.Client_id)+'/'+parsed[1]+'/'+parsed[2],msg.Group_id,self.ClientId_IP[i][0],int(self.ClientId_IP[i][1]))
				elif(i==msg.Client_id):
					id_ip_list=''
					for j in self.Grp_Info[msg.Group_id]:
						if(self.Grp_Info[msg.Group_id][i]): # if client online
							id_ip_list+=':'+str(j)+','+self.ClientId_IP[j][0]+','+str(self.ClientId_IP[j][1])
					self.Send_message('InformJoinsuccess'+'/'+id_ip_list[1:],msg.Group_id,self.ClientId_IP[msg.Client_id][0],int(self.ClientId_IP[msg.Client_id][1]))
						
		elif(parsed[0]=="leave"):
			for i in self.Grp_Info[msg.Group_id]:
				if(self.Grp_Info[msg.Group_id][i]):
					self.Send_message('InformLeave'+'/'+str(msg.Client_id),msg.Group_id,self.ClientId_IP[i][0],int(self.ClientId_IP[i][1]))
			del self.Grp_Info[msg.Group_id][msg.Client_id]
			# for i in self.Grp_Info[msg.Group_id]:
				# print i			
		elif(parsed[0]=="logout"):
			self.Grp_Info[msg.Group_id][msg.Client_id]=False
			for i in self.Grp_Info[msg.Group_id]:
				if(self.Grp_Info[msg.Group_id][i]!=msg.Client_id):
					self.Send_message('InformLogout'+'/'+str(msg.Client_id),msg.Group_id,self.ClientId_IP[msg.Group_id][0],int(self.ClientId_IP[msg.Group_id][1]))
		elif(parsed[0]=="login"):
			self.Grp_Info[msg.Group_id][msg.Client_id]=True
			for i in self.Grp_Info[msg.Group_id]:
				if(self.Grp_Info[msg.Group_id][i]!=msg.Client_id):
					self.Send_message('InformLogin'+'/'+str(msg.Client_id)+'/'+parsed[1]+'/'+parsed[2],msg.Group_id,self.ClientId_IP[msg.Group_id][0],int(self.ClientId_IP[msg.Group_id][1]))
	
	def Send_message(self,msg_text,gid,host=None,port=None,Client=False):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		soc.connect((host,int(port)))
		soc.sendall(str(message(msg_text,1,'ignre',gid)))
		# soc.sendall("^#"+str("ignre")+'#'+str(gid)+'#'+msg_text)
		soc.close()	

	def ReadFromString(self,message_string):
		msg=message_string.split('#')
		print msg
		if(msg[0]=="@"): # client-client type message
			return message(msg[3],0,msg[1],msg[2],msg[4])
		elif(msg[0]=="^"): # server-client type message
			return message(msg[3],1,msg[1],msg[2])

if __name__=='__main__':
	c=Server()