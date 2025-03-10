from flask_restful import Resource, reqparse # acesso ao (GET, POST, PUT, DELETE)
from models.site import SiteModel
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required # criptografia (token)
from config.sql_alchemy import banco ### ORM (Object-Relational Mapping)
import traceback ### informações detalhadas sobre uma exceção

### Função de validação personalizada (PARÂMETRO DO USUÁRIO)
def restricao_estrelas(valor):
    valor = float(valor)
    if valor < 0.0 or valor > 5.0:  # Defina o valor mínimo e máximo aqui
        raise (f"Valor deve estar entre 0.0 e 5.0. Recebido: {valor}")
    return valor

### Função de validação personalizada (PARÂMETRO DO USUÁRIO)
def restricao_diaria(valor):
    valor = float(valor)
    if valor < 0.0:  # Defina o valor mínimo e máximo aqui
        raise (f"Valor deve ser maior que 0: {valor}")
    return valor

# rota lista Banco de Dados (TUDO): URL/hoteis?cidade=Rio de Janeiro&estrelas_min=4&diaria_max=400
class Hoteis(Resource):
     # Dados pre definidos (Construtor Local)
    meus_atributos = reqparse.RequestParser() # requerimento (extrair argumentos)
    meus_atributos.add_argument('cidade', type=str, default="",location='args') # argumentos
    meus_atributos.add_argument('estrelas_min', type=float, default=0, location='args') # argumentos
    meus_atributos.add_argument('estrelas_max', type=float, default=0, location='args') # argumentos
    meus_atributos.add_argument('diaria_min', type=float, default=0, location='args') # argumentos
    meus_atributos.add_argument('diaria_max', type=float, default=0, location='args') # argumentos
    meus_atributos.add_argument("itens",type=int, default=3, location="args") # argumentos
    meus_atributos.add_argument("pagina",type=int, default=1, location="args") # argumentos
    meus_atributos.add_argument("site", type=int, default=None , location="args") ### argumentos

    '''
    location='args': Indica que o argumento deve ser extraído dos parâmetros da ".query" na URL. 
    Ou seja, ele será lido da parte da URL que vem após o ponto de interrogação (?). 
    Por exemplo, em uma URL como http://exemplo.com/api?diaria_max=100, 
    '''

    # método de (Leitura)
    def get(self):

        # meus_filtros = (Construtor Local).(argumentos).(extrair dados)
        meus_filtros = Hoteis.meus_atributos.parse_args()

        # query = (ESCOPO Flask).consulta
        query = HotelModel.query
        
        '''
        ".query": Esse é um atributo que realizar operações de consulta no banco de dados. 
        É uma funcionalidade do SQLAlchemy que permite construir consultas SQL de maneira 
        programática. A partir do ".query", você pode filtrar, ordenar e obter resultados 
        do banco de dados.
        '''

        # filtros de consulta
        if meus_filtros["cidade"]:
            query = query.filter(HotelModel.cidade == meus_filtros["cidade"])
        if meus_filtros["estrelas_min"]:
            query = query.filter(HotelModel.estrelas >= meus_filtros["estrelas_min"])
        if meus_filtros["estrelas_max"]:
            query = query.filter(HotelModel.estrelas <= meus_filtros["estrelas_max"])
        if meus_filtros["diaria_min"]:
            query = query.filter(HotelModel.diaria >= meus_filtros["diaria_min"])
        if meus_filtros["diaria_max"]:
            query = query.filter(HotelModel.diaria <= meus_filtros["diaria_max"])
        if meus_filtros["itens"]:
            query = query.filter(meus_filtros["itens"] == meus_filtros["itens"])
        if meus_filtros["site"]:
            query = query.filter(HotelModel.site_id == meus_filtros["site"])
        
        # Paginação
        page = meus_filtros['pagina']
        per_page = meus_filtros['itens']
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        
        # resultado_hotel = [MÉTODO AUXILIAR JSON for objeto in itens_do_dicionario]
        resultado_hotel = [hotel.json() for hotel in pagination.items] # resultado

        return {
            "hotéis": resultado_hotel, # Lista de hotéis
            "quantidade de itens": pagination.total, # total de itens
            "quantidade de paginas": pagination.pages, # total de paginas
            "pagina atual": int(page) # pagina atual
        }

# rota (CRUD)
class Hotel(Resource):
    # PARÂMETRO DO USUÁRIO (Construtor Local)
    atributos = reqparse.RequestParser() # parâmetros pre-definidos (argumentos)
    atributos.add_argument('nome', type=str, required=True, help="Falta nome")  # argumentos (required=True | campo obrigatório)
    atributos.add_argument('estrelas', type=restricao_estrelas, help="Número de estrelas (entre 0.0 e 5.0)") ### argumentos
    atributos.add_argument('diaria', type=restricao_diaria, help="Valor da diaria não pode ser negativo") ### argumentos
    atributos.add_argument('cidade', type=str, required=True, help="cidade") # argumentos
    atributos.add_argument('site_id', type=int, required=True, help="Falta id do site")  # argumentos (required=True | campo obrigatório)

    # Solicitar (leitura) por "id"
    def get(self, hotel_id):
        ### hotel = (ESCOPO BANCO DE DADOS).(método filtro (pesquisa por ID)).(encontrar o 1º)
        hotel = HotelModel.query.filter_by(hotel_id=hotel_id).first()

        if hotel:
            # (ESCOPO Flask).(método json)
            return hotel.json()   
        else:
            return {'mensagem': 'Hotel não existe.'}, 404
    
    # Enviar (criar)
    @jwt_required() # necessário token de acesso
    def post(self, hotel_id): 
        # hotel = (ESCOPO BANCO DE DADOS).(método filtro (pesquisa por ID)).(encontrar o 1º)
        hotel = HotelModel.query.filter_by(hotel_id=hotel_id).first()

        # Se ID existir
        if hotel:
            return {f'mensagem': 'Hotel {hotel_id} já existe.'}, 404
        else:     
            # dados = (PARÂMETRO DO USUÁRIO).(argumentos).(extrair dados)
            dados = Hotel.atributos.parse_args() 

            # novo_hotel = (ESCOPO BANCO DE DADOS (hotel_id, (PARÂMETRO DO USUÁRIO))
            novo_hotel = HotelModel(hotel_id, **dados)

            # SE não existir site_id cadastrado finalize
            # (ESCOPO BANCO DE DADOS).(método filtro (pesquisa por ID)).(encontrar o 1º)
            if not SiteModel.query.filter_by(site_id=dados['site_id']).first():
                return {'mensagem': 'Para cadastra hotel é necessário site_id valido!!!'}, 400

            try: 
                # (ESCOPO BANCO DE DADOS).(método salvar dados)
                banco.session.add(novo_hotel)
                banco.session.commit()
            except:
                '''
                traceback.print_exc() é uma função em Python usada para 
                imprimir informações detalhadas sobre uma exceção.
                '''
                traceback.print_exc()
                return {'mensagem': 'Ocorreu erro interno no servidor.'}, 500

            # (ESCOPO BANCO DE DADOS).(MÉTODO AUXILIAR JSON)
            return novo_hotel.json(), 201
            
    # Atualizar
    @jwt_required() # necessário token de acesso
    def put(self, hotel_id):
        # dados = (Construtor Local).(argumentos).(extrair dados)
        dados = Hotel.atributos.parse_args()

        ### hotel = (ESCOPO BANCO DE DADOS).(método filtro (pesquisa por ID)).(encontrar o 1º)
        hotel = HotelModel.query.filter_by(hotel_id=hotel_id).first()

        # Se ID existir: Atualizar hotel
        if hotel:

             # SE não existir site_id cadastrado finalize
            # (ESCOPO BANCO DE DADOS).(método filtro (pesquisa por ID)).(encontrar o 1º)
            if not SiteModel.query.filter_by(site_id=dados['site_id']).first():
                return {'mensagem': 'Para cadastra hotel é necessário site_id valido!!!'}, 400

            ### Atualizar os atributos do hotel
            hotel.nome = dados['nome'] # >>>>> preencher dados no Banco de Dabos <<<<<
            hotel.estrelas = dados['estrelas'] # >>>>> preencher dados no Banco de Dabos <<<<<
            hotel.diaria = dados['diaria'] # >>>>> preencher dados no Banco de Dabos <<<<<
            hotel.cidade = dados['cidade'] # >>>>> preencher dados no Banco de Dabos <<<<<
            hotel.site_id = dados['site_id'] # >>>>> preencher dados no Banco de Dabos <<<<<

            ### (ESCOPO BANCO DE DADOS).(método salvar dados)
            banco.session.add(hotel)
            banco.session.commit() 

            # (ESCOPO BANCO DE DADOS).(MÉTODO AUXILIAR JSON)
            return hotel.json(), 200        
        else: # Criar novo hotel
            # novo_hotel = (ESCOPO BANCO DE DADOS (hotel_id, (Construtor Local))
            novo_hotel = HotelModel(hotel_id, **dados) # >>>>> preencher dados no Banco de Dabos => (MÉTODO AUXILIAR CONSTRUTOR) <<<<<   

            ### SE não existir site_id cadastrado finalize
            if not SiteModel.query.filter_by(site_id=dados['site_id']).first():
                return {'mensagem': 'Para cadastra hotel é necessário site_id valido'}, 400
            
            # (ESCOPO BANCO DE DADOS).(método salvar dados)
            banco.session.add(novo_hotel)
            banco.session.commit() 

            # (ESCOPO BANCO DE DADOS).(MÉTODO AUXILIAR JSON)
            return novo_hotel.json()
        

    # Excluir
    @jwt_required() # necessário token de acesso
    def delete(self, hotel_id):

        # hotel = (ESCOPO BANCO DE DADOS).(método filtro (pesquisa por ID)).(encontrrear o 1º)
        hotel = HotelModel.query.filter_by(hotel_id=hotel_id).first()

        # Se ID existir
        if hotel:
            # (ESCOPO BANCO DE DADOS).(método delete)
            banco.session.delete(hotel)
            banco.session.commit()
            return {'mensagem': 'Hotel deletado.'}, 200   
        else:
            return {'mensagem': 'Hotel não existe.'}, 404
        
        
        
