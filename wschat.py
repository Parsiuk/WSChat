import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

import threading
import re
import random
import string

clients = []
messageQueue = []
running = 1

class ConsoleThread(threading.Thread):
        def run(self):
                global running,clients
                while(running):
                        consoleInput = raw_input("> ");
                        if consoleInput=='quit':
                                print "Stopping..."
                                tornado.ioloop.IOLoop.instance().stop()
                                running = 0
                        elif consoleInput=='list':
                                for client in clients:
                                        print "    " + client.clientName
                        elif consoleInput=='help':
                                print "Available commands:"
                                print "    list - logged in clients"
                                print "    quit - stops server"
                        else:
                                print "Unknown command. Use 'help' to get a list of commands."

def broadcastMessage(message,clients):
        for client in clients:
                client.write_message(message)

def generateID(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

def duplicateUsernameExists(newUser,clients):
        for client in clients:
                if client.clientName == newUser:
                        return 1
        return 0

class WSHandler(tornado.websocket.WebSocketHandler):
        clientName = 'User'

        def open(self):
                clients.append(self)
                self.clientName += generateID()
                broadcastMessage("* " + self.clientName + " has joined chat room.\n",clients)
                print "New user joined chat from IP " + self.request.remote_ip

        def on_message(self, message):
                if re.match(r'^\/nick\ .{1,}$',message):
                        oldUser = self.clientName
                        newUser = message.split(' ')[1]
                        if re.match(r'^[a-zA-Z0-9]{1,16}$',newUser):
                                if duplicateUsernameExists(newUser,clients)==0:
                                        print self.clientName + " is changing nick to " + newUser
                                        self.clientName = newUser
                                        broadcastMessage("* " + oldUser + " has been renamed to " + self.clientName + "\n",clients);
                                else:
                                        self.write_message("* Username already taken.\n")
                        else:
                                self.write_message("* Incorrect username!\n")
                elif re.match(r'^\/list$',message):
                        self.write_message("* Logged in clients:\n")
                        for client in clients:
                                self.write_message("    " + client.clientName + "\n")
                elif re.match(r'^$',message):
                        self.write_message("* Empty message - not sending\n")
                else:
                        broadcastMessage("[" + self.clientName + "] " + message + "\n",clients)

        def on_close(self):
                clients.remove(self)
                broadcastMessage(self.clientName + " has left the chat room.\n",clients)
                print "Connection closed"

        def check_origin(self, origin):
                if origin == "http://parsiuk.net":
                        return True
                else:
                        return False

application = tornado.web.Application([
    (r'/ws', WSHandler),
])

if __name__ == "__main__":
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8080)
        consoleThread = ConsoleThread()
        consoleThread.start()
        tornado.ioloop.IOLoop.instance().start()
        consoleThread.join()
