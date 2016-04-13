import socket
print "Please Enter your user ID"
uid=raw_input()

HOST = '10.5.16.194'    # chat server IP
PORT = 50007              # port as used by the server
Grp_Info={}
Offline_Member_Message_Buffer={}
Grp_ID_chatting_table={}
ClientId_IP={}
#create an INET, STREAMing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while(1):
	print "select option 1,2,3[create,join,chat]"
	opt=int(raw_input())
	if(opt==1):
		print "Enter Group Id you wants to create"
		gid=raw_input()
		s.connect((HOST, PORT))
		s.sendall('join#'+gid+"#"+uid)
	elif(opt==2):
		print "Enter Group Id you wants to join"
		gid=raw_input()
		s.connect((HOST, PORT))
		s.sendall('join#'+gid+"#"+uid)
	elif(opt==3):
		print "Enter Group Id you wants to chat"
		gid=raw_input()
		
#now connect to the web server on port 80
# - the normal http port
s.connect(("www.mcmillan-inc.com", 80))

def cbcast():
	print "Ankit has to implement it"

def abcast():
	print "Achyuta has to implement it"
