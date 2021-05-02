import hashlib
import time
import random
import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

class Transaction:
    def __init__(self, senderId, receiverId, amount):
        self.senderId = senderId
        self.receiverId = receiverId
        self.amount = amount
    
    def toString(self):
        asString = '{' + str(self.senderId) + ',' + str(self.receiverId) 
        asString = asString + ',' + str(self.amount) + '}'
        return asString
        


class Block:

    def __init__(self, index, proofOfWorkNo, prevHash, uncommittedTransactions, timestamp=None):
        self.index = index
        self.proofOfWorkNo = proofOfWorkNo
        self.prevHash = prevHash
        self.uncommittedTransactions = uncommittedTransactions
        self.timestamp = timestamp or time.time()

    @staticmethod
    def uncommittedTransactionsToString(uncommittedTransactions):
        string = ""
        for i in range(len(uncommittedTransactions)):
            transaction = uncommittedTransactions[i]
            transactionAsString = transaction.toString()
            string += transactionAsString
            if i != len(uncommittedTransactions)-1:
                string += ';'

        if string == "":
            return None
        else:
            return string


    def toString(self, delimiter = ";;", includeProofOfWorkNo = True):
        blockString = ""
        data = self.uncommittedTransactionsToString(self.uncommittedTransactions)
        blockString = blockString + str(self.index) + delimiter
        blockString = blockString + str(self.prevHash) + delimiter
        blockString = blockString + str(data) + delimiter
        blockString = blockString + str(self.timestamp)
        if includeProofOfWorkNo :
            blockString = blockString + delimiter + str(self.proofOfWorkNo)
        
        return blockString


    def calculateHash(self):
        blockString = self.toString()
        return hashlib.sha256(blockString.encode()).hexdigest()


    
class Node:

    def __init__(self, nodeId, address, balance):
        self.address = address
        self.id = nodeId
        self.balance = balance

    def makeTransaction(self, isReceiver, amount):
        if isReceiver:
            self.balance += amount
            return True
        else:
            if amount > 0 and amount >= self.balance:
                self.balance -= amount
                return True
            else:
                return False

    def toString(self, delimiter = ','):
        nodeAsString = "{" + str(self.id) + delimiter + str(self.address) + delimiter + str(self.balance) + "}"
        return nodeAsString

        

class Blockchain:

    def __init__(self, filename = None):
        self.chain = []
        self.uncommittedTransactions = []
        self.nodes = []
        
        if filename != None:
            self.loadBlockchain(filename)
        else:
            self.addNewBlock(proofOfWorkNo = 0, prevHash = "0") #Genesis Block

    def checkTransactionValidity(self, transaction):
        if transaction.senderId == transaction.receiverId:
            print("Error : Sender and receiver can't have same ID")
            return False

        flag = 1
        for node in self.nodes:
            if node.id == transaction.receiverId:
                flag = 0
        
        if flag == 1:
            print("Error : Receiver doesn't exist")
            return False

        flag = 1
        for node in self.nodes:
            if node.id == transaction.senderId:
                flag = 0
                if node.balance < transaction.amount:
                    print("Error : Not sufficient funds")
                    return False
        
        if flag == 1:
            print("Error : Sender doesn't exist")
            return False
        
        return True

        

    def addNewTransaction(self, transaction):
        transactionCanBeMade = self.checkTransactionValidity(transaction)
        if transactionCanBeMade:
            self.uncommittedTransactions.append(transaction)
            for node in self.nodes:
                if node.id == transaction.senderId:
                    node.makeTransaction(False, transaction.amount)
                if node.id == transaction.receiverId:
                    node.makeTransaction(True, transaction.amount)

            data = None
            if len(self.uncommittedTransactions) == 10:
                global myNode
                data = self.mineNewBlock(myId = myNode.id)
            return data
        else:
            print("Transaction NOT Possible")

    def addNewBlock(self, proofOfWorkNo, prevHash, timestamp = None):
        block = Block(
            index=len(self.chain),
            proofOfWorkNo=proofOfWorkNo,
            prevHash=prevHash,
            uncommittedTransactions=self.uncommittedTransactions,
            timestamp = timestamp
        )
        
        self.uncommittedTransactions = []

        self.chain.append(block)
        return block


    def validateNewBlock(self, block, prevBlock):
        if prevBlock.index + 1 != block.index:
            print(1)
            return False

        elif prevBlock.calculateHash() != block.prevHash:
            print(2)
            return False

        elif not self.verifyProof(block, prevBlock.proofOfWorkNo, block.proofOfWorkNo):
            print(3)
            return False

        elif block.timestamp <= prevBlock.timestamp:
            print(4)
            return False

        return True


    def calculateProofOfWork(self, newBlock, lastProof):
        proofOfWorkNo = 0
        while self.verifyProof(newBlock, lastProof, proofOfWorkNo) is False:
            proofOfWorkNo += 1

        return proofOfWorkNo

    
    def verifyProof(self, currentBlock, lastProof, newProof):
        blockAsString = currentBlock.toString(includeProofOfWorkNo = False)
        guess = f'{blockAsString};;{lastProof};;{newProof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


    def mineNewBlock(self, myId):

        miningTransaction = Transaction(
            senderId = "0", 
            receiverId = myId,
            amount = 1
        )

        latestBlock = self.chain[-1]
        lastHash = latestBlock.calculateHash()

        self.uncommittedTransactions.append(miningTransaction)

        

        lastProofOfWorkNo = latestBlock.proofOfWorkNo
        timestamp = time.time()
        block = Block(
                index=len(self.chain),
                proofOfWorkNo = 0,
                prevHash=lastHash,
                uncommittedTransactions=self.uncommittedTransactions,
                timestamp = timestamp
        )

        proofOfWorkNo = self.calculateProofOfWork(newBlock = block, lastProof = lastProofOfWorkNo)

        
        block = self.addNewBlock(proofOfWorkNo, lastHash, timestamp)

        return vars(block)


    def addNode(self, nodeId, address, balance):
        for node in self.nodes:
            if node.id == nodeId:
                print("Node ID already used")
                return False
            if node.address == address:
                print("Node address already used")
                return False
        newNode = Node(nodeId = nodeId, address = address, balance = balance)
        self.nodes.append(newNode)
        return True


    def toString(self):
        blockchainString = ''

        for i in range(len(self.chain)):
            block = self.chain[i]
            blockAsString = block.toString()
            blockchainString += blockAsString
            if i != len(self.chain)-1:
                blockchainString += ";;;"

        return blockchainString

    def transactionFromString(self, string):
        string = string[1:-1]
        attributes = string.split(',')
        newTransaction = Transaction(
            senderId = int(attributes[0]), 
            receiverId = int(attributes[1]), 
            amount = int(attributes[2])
        )
        return newTransaction


    def nodeFromString(self, string):
        if string == "None":
            return []
        string = string[1:-1]
        attributes = string.split(',')
        newNode = Node(
            nodeId = int(attributes[0]), 
            address = attributes[1], #TODO handle addresses
            balance = int(attributes[2])
        )
        return newNode


    def blockFromString(self, string):
        attributes = string.split(";;")
        
        dataString = attributes[2]
        transactionStrings = dataString.split(';')
        uncommittedTransactions = []

        for transactionString in transactionStrings:
            if transactionString != "None":
                transaction = self.transactionFromString(transactionString)
                uncommittedTransactions.append(transaction)
        
        block = Block(
            index = int(attributes[0]),
            prevHash = attributes[1],
            uncommittedTransactions = uncommittedTransactions,
            timestamp = float(attributes[3]),
            proofOfWorkNo = int(attributes[4]),
        )

        return block


    def loadBlockchain(self, filename = "blockchain.txt"):
        ipFile = open(filename, 'r')
        contents = ipFile.read()
        parts = contents.split(";;;;")
        
        blockchainString = parts[0]
        uncommittedTransactionsString = parts[1]
        nodesString = parts[2]
        
        if nodesString != "None":
            nodes = nodesString.split(";")
            for node in nodes:
                self.nodes.append(self.nodeFromString(node))

        uncommittedTransactions = uncommittedTransactionsString.split(';')
        for transaction in uncommittedTransactions:
            self.uncommittedTransactions.append(self.transactionFromString(transaction))

        blocks = blockchainString.split(";;;")
        for block in blocks:
            self.chain.append(self.blockFromString(block))

        ipFile.close()


    def nodesToString(self):
        nodesString = ''

        if self.nodes == [] or self.nodes == None:
            return None
        for i in range(len(self.nodes)):
            node = self.nodes[i]
            nodeAsString = node.toString()
            nodesString += nodeAsString
            if i != len(self.nodes)-1:
                nodesString += ';'

        return nodesString


    def saveBlockchain(self, filename = "blockchain.txt"):
        opFile = open(filename, 'w')
        blockchainString = str(self.toString())
        uncommittedTransactionsString = str(Block.uncommittedTransactionsToString(self.uncommittedTransactions))
        nodesString = str(self.nodesToString())

        data = blockchainString + ";;;;" + uncommittedTransactionsString + ";;;;" + nodesString

        opFile.write(data) 
        
        opFile.close()



def loadMyDetails():
    nodeDetialsFile = open("my-details2.txt", 'r')
    myNodeDetails = nodeDetialsFile.read()
    
    details = myNodeDetails.split(';')
    myNode = Node(nodeId = int(details[0]), address = details[1], balance = int(details[2]))

    return myNode


def saveMyDetials(myNode):
    nodeDetailsFile = open("my-details.txt", 'w')
    
    nodeString = myNode.toString(";")
    nodeString = nodeString[1:-1]
    
    
    nodeDetailsFile.write(nodeString)
    nodeDetailsFile.close()


def encrypt(pt, e, N):
    return pow(pt, e, N)

def decrypt(ct, d, N):
    return pow(ct, d, N)


def listen():
    global myNode
    global newChain
    authKeyFile = open("authKey.txt", 'r')
    contents = authKeyFile.read()
    contents = contents.split(";;")
    e = int(contents[0])
    d = int(contents[1])
    N = int(contents[2])


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr, end="\n\n")
            ct = conn.recv(2048)
            ct = int.from_bytes(ct, "big")
            pt = decrypt(ct, d, N) 
            conn.sendall(pt.to_bytes(2048, "big"))
            
            randNum = random.randint(1000000000, 9999999999)
            ct = encrypt(randNum, e, N)
            conn.sendall(ct.to_bytes(2048, "big"))

            pt = conn.recv(2048)
            if pt == b'End connection':
                print("Connection Terminated...")
                return
            else:
                pt = int.from_bytes(pt, "big")
                if pt == randNum:
                    print("User Authenticated\n")

                    typeOfReq = conn.recv(1024)
                    print("Request Type: ", typeOfReq.decode("utf-8"))
                    otherPeerId = int.from_bytes(conn.recv(1024), "big")
                    print("ID received: ", otherPeerId)
                    amount = int.from_bytes(conn.recv(1024), "big")
                    print("Amount: ", amount, end="\n\n")

                    otherPeerNode = None

                    for node in newChain.nodes:
                        if node.id == otherPeerId:
                            otherPeerNode = node


                    if otherPeerNode != None:
                        if typeOfReq == b'send':
                            if otherPeerNode.balance >= amount:
                                print("Accepted\n")
                                conn.sendall(b'Accept')
                                conn.sendall(myNode.id.to_bytes(1024, "big"))
                                transaction = Transaction(otherPeerId, myNode.id, amount)
                                newChain.addNewTransaction(transaction)
                                print("Transaction Made")
                                
                            else:
                                conn.sendall(b'Reject')
                                print("Rejected\n")

                        elif typeOfReq == b'request':
                            if myNode.balance >= amount:
                                print("Accepted\n")
                                conn.sendall(b'Accept')
                                conn.sendall(myNode.id.to_bytes(1024, "big"))
                                transaction = Transaction(myNode.id, otherPeerId, amount)
                                newChain.addNewTransaction(transaction)
                                print("Transaction Made")
                            else:
                                conn.sendall(b'Reject')
                                print("Rejected\n")
                    else:
                        print("Not matching node found")
                    
                else:
                    print("Unauthorized User")
                    print("...Disconnecting...")

        print("Connection Terminated...")

    
    #TODO send randNum, receive decypted and one diff encrypted random no, send decrypted 
    # if ptRec == randNum:
    #   ctRec = receiveNo()
    #   pt = decrypt(ctRec)
    #   send(pt)
    #   confirmation = receive()
    #   makeTransaction()



myNode = loadMyDetails()
# newChain = Blockchain()
newChain = Blockchain("blockchain.txt")

listen()

# newChain.addNode(myNode.id, myNode.address, myNode.balance)
# newChain.addNode(14, "123.123.123.132", 456)

# newChain.addNewTransaction(Transaction(senderId = 93, receiverId = 14, amount = 10))
# newChain.addNewTransaction(Transaction(senderId = 14, receiverId = 44, amount = 10))
# newChain.addNewTransaction(Transaction(senderId = 73, receiverId = 44, amount = 1))
# newChain.addNewTransaction(Transaction(senderId = 14, receiverId = 44, amount = 10))

# newChain.saveBlockchain()
