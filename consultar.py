import hashlib
import re
import requests
from suds.client import Client

# Identificador da transação definido manualmente
transactionId = 'c8a79922de56dd46ce5d5e621d8eda69c0f7b119470cbd679d19c92b8f93e26e'
#transactionId = ''

# API de consulta (formatado para consulta da transação definida em 'transactionId')
transactionUrl = 'https://tbtc.bitaps.com/' + transactionId
#transactionUrl = 'https://live.blockcypher.com/btc-testnet/tx/' + transactionId

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

# Definir mensagem para consulta
witnessMessage = 'ACE#' + str(imsWitnessProof[0].witnessId) + ':' + str(imsWitnessValue)

# Requisitar as informações da transação na blockchain (em HTML e string)
blockchainWitnessRequest = requests.session().get(transactionUrl)
blockchainWitnessInfo = str(blockchainWitnessRequest.content)

# Procurar pela prova na transação da blockchain
righteousWitnessValue = re.search(witnessMessage, blockchainWitnessInfo)

if righteousWitnessValue:
    print("#\n#\n#\nValor de referência íntegro e apto para auditoria.\n#\n#")
else:
    print("#\n#\n#\nValor de referência inconsistente!\n#\nPode ser que o valor tenha sido corrompido ou adulterado.\n#\n#")
