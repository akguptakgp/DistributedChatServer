from functools import partial
import tkMessageBox
import Tkinter as tk

def action(atm,textr):
		print atm
		print textr.get("1.0",'end-1c')

		textr.delete("1.0",tk.END)

def disp_group(groups):
	data=get_group_list()
	for item in data:
		groups.insert(tk.END, item)

	return


class Window(tk.Frame):
	def __init__(self,parent):
		tk.Frame.__init__(self, parent)

		self.frame1=tk.Frame(parent)
		self.frame1.pack(side=tk.TOP)
		self.frame2=tk.Frame(parent)
		self.frame2.pack(side=tk.BOTTOM)

		self.text_show=tk.Text(self.frame1,height=40,width=20)
		self.text_show.pack(side=tk.LEFT,pady=15,padx=15)
		self.Group_list=tk.Listbox(self.frame1)
		self.Group_list.pack(padx=15,pady=30)
		self.refresh=tk.Button(self.frame1,text="Refresh",command=partial(disp_group,self.Group_list))
		self.refresh.pack(pady=30)

		
		self.logout=tk.Button(self.frame1,text="Logout",command=partial(action,5))
		self.logout.pack(side=tk.BOTTOM)

		self.text_type=tk.Text(self.frame2,height=2,width=20)
		self.text_type.pack(side=tk.LEFT,pady=15,padx=15)
		self.send=tk.Button(self.frame2,text="Send",command=partial(action,1,self.text_type))
		self.send.pack(side=tk.LEFT)
		self.join=tk.Button(self.frame2,text="Join",command=partial(action,2,self.text_type))
		self.join.pack(side=tk.LEFT)
		self.Make=tk.Button(self.frame2,text="Make Group",command=partial(action,3,self.text_type))
		self.Make.pack(side=tk.LEFT)
		self.leave=tk.Button(self.frame1,text="Leave",command=partial(action,4,self.text_type))
		self.leave.pack(side=tk.BOTTOM)
		

	def fetch_data(self):
		return self.text_type.get()

	def print_list(self,datalist):
		for items in datalist:
			self.text_show.insert(tk.END, items+'\n')
		return
	def print_line(self,data):
		self.text_show.insert(tk.END,data+'\n')

	def disp_list(self,groups_data):
		for item in groups_data:
			self.Group_list.insert(tk.END, item)



root=tk.Tk()
app = Window(root)
list=["akash","gourav","achutya","ankit"]
app.print_list(list)
root.mainloop()

# class Application(tk.Frame):
#     def __init__(self, master=None):
#         tk.Frame.__init__(self, master)
#         self.pack()
#         self.createWidgets()

#     def createWidgets(self):
#         self.hi_there = tk.Button(self)
#         self.hi_there["text"] = "Hello World\n(click me)"
#         self.hi_there["command"] = self.say_hi
#         self.hi_there.pack(side="top")

#         self.QUIT = tk.Button(self, text="QUIT", fg="red",
#                                             command=root.destroy)
#         self.QUIT.pack(side="bottom")

#     def say_hi(self):
#         print("hi there, everyone!")

# root = tk.Tk()
# app = Application(master=root)
# app.mainloop()