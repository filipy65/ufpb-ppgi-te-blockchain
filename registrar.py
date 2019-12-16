import hashlib
# import binascii
from suds.client import Client
from bitcoinlib.transactions import Output
from bitcoinlib.wallets import wallet_create_or_open
from bitcoinlib.encoding import varstr

# Nome da carteira associada ao serviço que será utilizada para realizar as transações
imsWalletName = 'carteira-ACE'

# Rede blockchain
imsWalletNetwork = 'testnet'
# Identificador da rodada do ACE-IMS definido manualmente
imsRoundId = 10279266

# Conectar a API do serviço (ACE-IMS) para chamadas por SOAP
imsUrl = 'http://ims.umiacs.umd.edu:8080/ace-ims/IMSWebService?wsdl'
imsApi = Client(imsUrl)

# Requisitar os demais elementos (hashes) da árvore (além dos criados a partir do hash da rodada selecionado)
imsWitnessProof = imsApi.service.createWitnessProofForRound(imsRoundId)

# Calcular o hash final da árvore a partir do hash da rodada atual

# Definir o cálculo para o primeiro nível
level = 0

# Requisitar informações sobre a rodada (com foco no hash)
imsRoundSummary = imsApi.service.getRoundSummaries(imsRoundId)

# Converter o valor hash em ASCII para bytes
prevHash = bytes.fromhex(imsRoundSummary[0].hashValue)

# Iniciar o cálculo
for element in imsWitnessProof[0].proofElements:
    i = 0
    hashAlg = hashlib.sha256()
    
    # Executar de acordo com o número de elementos vizinhos nesse nível
    for strHash in element.hashes:
        # Se o hash previamente definido deve estar na posição anterior ao hash em processamento...
        if i == element.index:
            # ...colocá-lo no devido lugar
            hashAlg.update(prevHash)
        # Agregar o hash em processamento
        hashAlg.update(bytes.fromhex(strHash))
        # Incrementar o índice
        i = i + 1

    # Se o hash previamente definido deve estar na última posição...
    if i == element.index:
        #...colocá-lo no devido lugar
        hashAlg.update(prevHash)

    # Calcula o hash dos hashes agregados
    prevHash = hashAlg.digest()
    
    # Elevar o nível
    level = level + 1

# Definir valor hash topo da árvore
imsWitnessValue = prevHash.hex()

# Definir mensagem para registro
witnessMessage = 'ACE#' + str(imsWitnessProof[0].witnessId) + ':' + str(imsWitnessValue)

# Abrir carteira (Bitcoin testnet)
imsWallet = wallet_create_or_open(imsWalletName, network=imsWalletNetwork)
imsWalletKey = imsWallet.get_key()

# Atualizar situação da carteira
imsWallet.utxos_update()

# Alertar se não houver fundos disponíveis para a execução das transações
if not imsWallet.utxos():
    print("#\n#\n#\nSem recursos no endereço '%s' da carteira '%s'.\n#\n#\n#" % (imsWalletKey.address, imsWalletName))
    quit()

# Tratar mensagem a ser registrada
#lockScript = b'\x6a' + str.encode(witnessMessage)
lockScript = b'\x6a' + varstr(witnessMessage)

# Realizar registro da mensagem através de uma transação na rede 'Bitcoin testnet'
witnessRegisterTransaction = imsWallet.send([Output(0, lock_script=lockScript, network=imsWalletNetwork)])

# Mostrar informações da transação
witnessRegisterTransaction.info()
