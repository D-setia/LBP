import hashlib
import time


class Transaction:
    def __init__(self, senderId, receiverId, quantity):
        self.senderId = senderId
        self.receiverId = receiverId
        self.quantity = quantity
    
    def toString(self):
        asString = '{' + str(self.senderId) + ',' + str(self.receiverId) 
        asString = asString + ',' + str(self.quantity) + '}'
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

    def makeTransaction(self, isReceiver, quantity):
        if isReceiver:
            self.balance += quantity
            return True
        else:
            if quantity > 0 and quantity >= self.balance:
                self.balance -= quantity
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


    def addNewTransaction(self, transaction):
        self.uncommittedTransactions.append(transaction)
        #TODO add check and change values of quantities of node balances            1
        data = None
        if len(self.uncommittedTransactions) == 10:
            global myNode
            data = self.mineNewBlock(myId = myNode.id)
            #TODO take ip if we want to mine block or not                           1
        return data

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
            quantity = 1
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
        newNode = Node(nodeId = nodeId, address = address, balance = balance)
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
            quantity = int(attributes[2])
        )
        return newTransaction


    def nodeFromString(self, string):
        if string == "None":
            return []
        string = string[1:-1]
        attributes = string.split(',')
        newNode = Node(
            id = int(attributes[0]), 
            address = int(attributes[1]), 
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
            print(i)
            node = self.nodes[i]
            print(node)
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
    nodeDetialsFile = open("my-details.txt", 'r')
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


myNode = loadMyDetails()
newChain = Blockchain()
# newChain = Blockchain("blockchain.txt")
# newChain.saveBlockchain()
# newChain2 = Blockchain("blockchain.txt")

# print(newChain.toString() == newChain2.toString())
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876329, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876328, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876327, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876326, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876325, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876324, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876323, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876322, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876321, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876320, quantity = 10))

newChain.addNode(myNode.id, myNode.address, myNode.balance)

newChain.addNewTransaction(Transaction(senderId = 2345678190, receiverId = 9876876329, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678191, receiverId = 9876876328, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678192, receiverId = 9876876327, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678193, receiverId = 9876876326, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678194, receiverId = 9876876325, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678195, receiverId = 9876876324, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678196, receiverId = 9876876323, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678197, receiverId = 9876876322, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678198, receiverId = 9876876321, quantity = 10))
newChain.addNewTransaction(Transaction(senderId = 2345678199, receiverId = 9876876320, quantity = 10))


newChain.addNewTransaction(Transaction(senderId = 2345678199, receiverId = 9876876320, quantity = 10))

# res = newChain.validateNewBlock(block = newChain.chain[2], prevBlock = newChain.chain[1])
newChain.saveBlockchain()

