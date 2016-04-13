import socket

HOST = 'localhost'    # chat server IP
PORT = 50007              # port as used by the server

#create an INET, STREAMing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((HOST,PORT)) 
s.listen(5) 
while True:
   c, addr = s.accept()     # Establish connection with client.
   print 'Got connection from', addr
   c.send('Thank you for connecting')
   print c.recv(1024)
   c.close()          

