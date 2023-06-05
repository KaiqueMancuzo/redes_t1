#!/usr/bin/env python3
import asyncio
import socket
import re

class Servidor:
    def __init__(self, porta):
        s = self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', porta))
        s.listen(5)

    def registrar_monitor_de_conexoes_aceitas(self, callback):
        asyncio.get_event_loop().add_reader(self.s, lambda: callback(Conexao(self.s.accept())))


class Conexao:
    def __init__(self, accept_tuple):
        self.s, _ = accept_tuple
        self.dados_residuais = b""  # Armazena os dados residuais

    def registrar_recebedor(self, callback):
        asyncio.get_event_loop().add_reader(self.s, lambda: callback(self, self.s.recv(8192)))

    def enviar(self, dados):
        self.s.sendall(dados)

    def fechar(self):
        asyncio.get_event_loop().remove_reader(self.s)
        self.s.close()

def validar_nome(nome):
    return re.match(br'^[a-zA-Z][a-zA-Z0-9_-]*$', nome) is not None


def sair(conexao):
    print(conexao, 'conexão fechada')
    conexao.fechar()


def dados_recebidos(conexao, dados):
    dados = conexao.dados_residuais + dados
    conexao.dados_residuais = b''

    if not dados.endswith(b'\r\n'):
        dados = list(filter((b'').__ne__, dados.split(b'\r\n')))
        conexao.dados_residuais += dados.pop(-1)
    
    else:
        dados = list(filter((b'').__ne__, dados.split(b'\r\n')))   
        
    if dados:
        for message in dados:   
            request, text = message.split(b' ', 1)
            
            # Passo 1: tratando mensagens do tipo 'PING'
            if request.upper() == b'PING':
                conexao.enviar(b':server PONG server :' + text + b'\r\n')

# Tratamento de mensagens do tipo 'NICK'
            elif request.upper() == b'NICK':
                nickname = text.strip()
                if validar_nome(nickname):
                    conexao.enviar(b':server 001 %s :Welcome\r\n' % nickname)
                    conexao.enviar(b':server 422 %s :MOTD File is missing\r\n' % nickname)
                else:
                    conexao.enviar(b':server 432 * %s :Erroneous nickname\r\n' % nickname)

                    
        print(conexao, dados)




def conexao_aceita(conexao):
    print(conexao, 'nova conexão')
    conexao.registrar_recebedor(dados_recebidos)


servidor = Servidor(6667)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()
