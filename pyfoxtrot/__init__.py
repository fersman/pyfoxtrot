import socket

BATCH_SIZE = 150

class Foxtrot:
    def __init__(self, ip, port=5010, username="", password=""):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.entities = {}
        self.groups = {}
        self.quickVariables = []
        self.allVariables = []
        self.socket = None

    def _connect(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))

    def _disconnect(self) -> None:
        self.socket.close()

    def _is_socket_closed(self) -> bool:
        try:
            if not self.socket:
                return False
            
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = self.socket.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return False  # socket was closed for some other reason
        except Exception as e:
            print(e)
            return False

        return False


    def _send(self, command: str, multiline = True) -> str:
        if not self._is_socket_closed():
            self._connect()

        self.socket.sendall(command.encode())
        result = ""
        while 1:
            data = self.socket.recv(16000)
            if not data: break
            line = data.decode("windows-1250")
            result += line
            if not multiline: break
            if (line.endswith(command)): break

        return result

    def list(self) -> str:
        return self._send("LIST:\r\n")
    
    def get(self, name: str) -> str:
        return self._send(f"GET:{name}\r\n")
    
    def set(self, name: str, value: str) -> str:
        return self._send(f"SET:{name}:{value}\r\n")
        
    def _sendAndParseGet(self, cmd: str) -> dict:
        lines = self._send(cmd, False)

        lines = lines.split("\r\n")
        variables = {}
        for line in lines:
            if line == "": continue
            line = line[line.index(":") + 1:]
            parsedLine = line.split(",")
            if len(parsedLine) < 2: continue

            split = parsedLine[0].split(".")
            name = split.pop()
            groupName = ".".join(split)
            var = parsedLine[1]

            if (self.groups[groupName][name].startswith("STRING")):
                var = var.replace("\"", "")
            elif (self.groups[groupName][name].startswith("BOOL")):
                var = var == "1"

            variables[line] = var

        print (variables)
        return variables

    """ read all entities """
    def readEntities(self):
        """ read list of variables """
        list = self._send("LIST:\r\n")
        lines = list.split("\r\n")

        groups = {}
        entities = {}
        quickVariables = []
        allVariables = []

        """ walk thru the lines """
        for line in lines:
            """ skip empty lines """
            if line == "": continue

            """ extract LIST:something,type """
            line = line[line.index(":") + 1:]

            """ split the line by comma """
            line = line.split(",")
            if len(line) < 2: continue

            """ extract name and type """
            name = line[0]
            type = line[1]

            name = name.split(".")

            if len(name) == 1:
                continue

            realName = name.pop()
            groupName = ".".join(name)
            
            if groupName not in groups:
                groups[groupName] = {}

            if groupName not in entities:
                entities[groupName] = {}

            if groupName.endswith(".LIGHT") or groupName.endswith(".LIGHT1") or groupName.endswith(".LIGHT2") or groupName.endswith(".LIGHT3"):
                entities[groupName]["type"] = "light"

            elif groupName.endswith(".PIR"):
                entities[groupName]["type"] = "pir"

            elif groupName.endswith(".JALOUSIE"):
                entities[groupName]["type"] = "jalousie"

            elif groupName.endswith(".TIMEPROGCONTROL"):
                entities[groupName]["type"] = "temp"

            elif realName == "GTSAP1_RELAY_NAME":
                entities[groupName]["type"] = "relay"

            elif realName == "GTSAP1_DISPLAY_EDIT":
                entities[groupName]["type"] = "display"

            elif realName == "GTSAP1_ACTION_EXEC":
                entities[groupName]["type"] = "action"

            groups[groupName][realName] = type

            if realName.endswith("_VALUE") or realName.endswith("_VALUESET"):
                quickVariables.append(groupName + "." + realName)

            allVariables.append(groupName + "." + realName)

        self.allVariables = allVariables
        self.entities = entities
        self.quickVariables = quickVariables
        self.groups = groups


    def _readVariables(self, variables: list, entities: dict):
        cmd = []

        """ walk thru variables """
        for vv in variables:
            cmd.append("GET:" + vv + "\r\n")

        readVariables = self._sendAndParseGet("".join(cmd))

        for name in readVariables:
            var = readVariables[name]

            if name.index(".") == -1:
                continue

            groupName = name[:name.rindex(".")]

            if groupName not in entities:
                entities[groupName] = {}


            if name.endswith("_NAME"):
                entities[groupName]["name"] = var
            elif name.endswith("_ENABLE"):
                entities[groupName]["enable"] = var
            elif name.endswith("_EDIT"):
                entities[groupName]["edit"] = var
            elif name.endswith("_UNIT"):
                entities[groupName]["unit"] = var
            elif name.endswith("_VALUE"):
                entities[groupName]["value"] = var
            elif name.endswith("_VALUESET"):
                entities[groupName]["value"] = var
                
            else:
                entities[groupName][name] = var

    def getVariablesForEntity(self, entityName: str):
        return self.entities[entityName]

    def readVariables(self):
        if len(self.allVariables) == 0:
            self.readEntities()

        batch = []
        entities = {}

        for var in self.allVariables:
            batch.append(var)

            if len(batch) == BATCH_SIZE:
                self._readVariables(batch, entities)
                batch = []

        if len(batch) > 0:
            self._readVariables(batch, entities)

        self.entities = entities
        return self.entities

    def readQuickVariables(self):
        if len(self.quickVariables) == 0:
            self.readVariables()

        batch = []

        for var in self.quickVariables:
            batch.append(var)

            if len(batch) == BATCH_SIZE:
                self._readVariables(batch, self.entities)
                batch = []

        if len(batch) > 0:
            self._readVariables(batch, self.entities)

        return self.entities
    