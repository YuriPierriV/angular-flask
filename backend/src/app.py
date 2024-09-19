from flask import Flask, render_template, redirect, request, flash, url_for, session, abort, jsonify, send_file
import io
import traceback
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import *
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime
import secrets
import base64
from dotenv import load_dotenv
import os
from flask_cors import CORS
import jwt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt

#.env variaveis
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
CLIENT_ID = os.getenv('CLIENT_ID')

#configurações app
app = Flask(__name__) 
app.config.from_object(Config) 
app.config['JWT_SECRET_KEY'] = SECRET_KEY
CORS(app, resources={r"/*": {"origins": "*"}})
db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# Função que verifica token da google
def verify_jwt(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        return idinfo
    except ValueError:
        return None

# Função para retornar os dados do usuário logado
def get_current_user():
    user_id = get_jwt_identity()
    return Usuario.query.get(user_id)

@app.route('/usuarios', methods=['POST'])
def create_or_update_usuario():
    data = request.get_json()

    # Função para criar um novo usuário
    def create_new_user(user_data):
        novo_usuario = Usuario(
            nome=user_data.get('nome'),
            sobrenome=user_data.get('sobrenome'),
            email=user_data.get('email'),
            telefone=user_data.get('telefone'),
            senha=user_data.get('senha'),
            genero=user_data.get('genero'),
            nascimento=datetime.strptime(user_data.get('nasc'), '%Y-%m-%d') if user_data.get('nasc') else None,
            tipo=user_data.get('tipo'),
            confirmed=True
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return novo_usuario

    # Função para criar token de acesso
    def generate_access_token(user):
        return create_access_token(identity=user.id)

    # Função para verificar e decodificar token JWT
    def decode_google_token(token):
        return verify_jwt(token)

    # Verificar o método solicitado
    method = data.get('method')

    # Caso: Criando um novo usuário
    if method == 'Comecando um novo usuario!':
        user = data.get('user')
        email = user.get('email')

        # Verificar se o usuário já existe
        usuario = Usuario.find_by_email(email)
        if usuario:
            if usuario.confirmed:
                return jsonify({'message': 'Email já existe!'}), 409
            return jsonify({'message': 'User nao confirmado!', 'user': UsuarioSchema().dump(usuario)})

        # Criar novo usuário
        novo_usuario = Usuario(nome=user.get('nome'), email=email)
        db.session.add(novo_usuario)
        db.session.commit()

        # Gerar token de acesso
        access_token = generate_access_token(novo_usuario)
        return jsonify({'message': 'User created!', 'token': access_token, 'user': UsuarioSchema().dump(novo_usuario)}), 201

    # Caso: Atualizando usuário existente
    if method == 'Cadastrando um novo usuário!':
        user = data.get('user')
        email = user.get('email')

        # Verificar se o usuário já existe
        usuario_existente = Usuario.find_by_email(email)
        if usuario_existente:
            if not usuario_existente.confirmed:
                usuario_existente.nome = user.get('nome')
                usuario_existente.sobrenome = user.get('sobrenome')
                usuario_existente.telefone = user.get('telefone')
                usuario_existente.senha = user.get('senha')
                usuario_existente.genero = user.get('genero')
                usuario_existente.nascimento = datetime.strptime(user.get('nasc'), '%Y-%m-%d') if user.get('nasc') else None
                usuario_existente.tipo = user.get('tipo')
                usuario_existente.confirmed = True
                db.session.commit()

                # Gerar token de acesso
                access_token = generate_access_token(usuario_existente)
                return jsonify({"msg": "Usuário atualizado com sucesso", "token": access_token, "user": UsuarioSchema().dump(usuario_existente)}), 200

            return jsonify({"msg": "Usuário já existe"}), 400

        # Criar novo usuário
        novo_usuario = create_new_user(user)
        access_token = generate_access_token(novo_usuario)
        return jsonify({"msg": "Usuário criado com sucesso", "token": access_token, "user": UsuarioSchema().dump(novo_usuario)}), 201

    # Caso: Acesso via Google
    if method == 'Google acess':
        user = data.get('user')
        token = user.get('credential')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 400

        decoded_token = decode_google_token(token)
        if not decoded_token:
            return jsonify({'error': 'Invalid token!'}), 400

        email = decoded_token['email']

        # Verificar se o usuário já existe
        usuario = Usuario.find_by_email(email)
        if usuario:
            if usuario.confirmed:
                access_token = generate_access_token(usuario)
                return jsonify({'message': 'Login successful!', 'token': access_token, 'user': UsuarioSchema().dump(usuario)})

            return jsonify({'message': 'User nao confirmado!', 'user': UsuarioSchema().dump(usuario)})

        # Criar novo usuário
        novo_usuario = Usuario(
            nome=decoded_token.get('given_name'),
            sobrenome=decoded_token.get('family_name'),
            email=email,
            img_link=decoded_token.get('picture')
        )
        db.session.add(novo_usuario)
        db.session.commit()

        access_token = generate_access_token(novo_usuario)
        return jsonify({'message': 'User created!', 'token': access_token, 'user': UsuarioSchema().dump(novo_usuario)}), 201

    return jsonify({'error': 'Invalid method!'}), 400

@app.route('/login', methods=['POST'])
def login():
    #recebe email e senha
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    #verifica usuario e senha corretos
    usuario = Usuario.find_by_email(email)
    if not usuario:
        return jsonify({"msg": "Bad email or password"}), 401
    if not usuario.check_password(senha):
        return jsonify({"msg": "Bad password"}), 401

    #passa token para acessar o usuario
    access_token = create_access_token(identity=usuario.id)
    return jsonify(access_token=access_token), 200

@app.route('/usuarios', methods=['GET'])
@jwt_required()
def get_usuarios():
    usuario = get_current_user()

    if usuario.tipo == "aluno":
        aluno_schema = AlunoSchema()
        return jsonify({
            'usuario': UsuarioSchema().dump(usuario),
            'aluno': aluno_schema.dump(usuario.aluno)
        })
    elif usuario.tipo == "professor":
        professor_schema = ProfessorSchema()
        return jsonify({
            'usuario': UsuarioSchema().dump(usuario),
            'professor': professor_schema.dump(usuario.professor)
        })
    elif usuario.tipo == 'instituicao':
        instituicao_schema = InstituicaoSchema()
        return jsonify({
            'usuario': UsuarioSchema().dump(usuario),
            'instituicao': instituicao_schema.dump(usuario.instituicao),

        })
    else:
        return jsonify({"msg": "User not found"}), 404

@app.route('/instituicao', methods=['POST'])
@jwt_required() #solicita o jwt
def add_instituicao():
    # Verifica qual é o usuário
    usuario = get_current_user()

    if not usuario:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = request.get_json()
        nome_instituicao = data.get('instituicao')
        if not nome_instituicao:
            return jsonify({"msg": "Nome da instituição é obrigatório"}), 400

        instituicao_created = Instituicao(
            id_usuario=usuario.id,
            nome=nome_instituicao,
            confirmed=True
        )

        db.session.add(instituicao_created)
        db.session.commit()

        return jsonify({'msg' : "Insituição criada", 'instituicao': InstituicaoSchema().dump(instituicao_created)}), 201
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        return jsonify({"msg": "Erro ao adicionar instituição"}), 500

@app.route('/instituicao/unidade', methods=['POST'])
@jwt_required() #solicita o jwt
def add_unidade():
    # Verifica qual é o usuário
    usuario = get_current_user()

    if not usuario:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = request.get_json()
        unidade = data.get('unidade')

        unidade_created = Unidade(
            id_instituicao=usuario.instituicao.id,
            nome=unidade.get('nome_unidade'),
            confirmed=True,
            telefone= unidade.get('telefone_unidade'),
            endereco= unidade.get('endereco_unidade'),
            estado=unidade.get('estado_unidade'),
            cidade=unidade.get('cidade_unidade'),
            bairro=unidade.get('bairro_unidade'),
            cep=unidade.get('cep_unidade'),
        )

        db.session.add(unidade_created)
        db.session.commit()

        return jsonify({'msg' : "Unidade criada", 'unidade': UnidadeSchema().dump(unidade_created)}), 201
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        return jsonify({"msg": "Erro ao adicionar unidade"}), 500

@app.route('/curso', methods=['POST'])
@jwt_required() #solicita o jwt
def add_curso():
    # Verifica qual é o usuário
    usuario = get_current_user()

    if not usuario:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = request.get_json()
        curso = data.get('curso')
        if not curso:
            return jsonify({"msg": "Curso não recebido"}), 400

        new_curso = Curso(
            id_unidade=curso.get('id_unidade'),
            nome=curso.get('nome'),
            descricao=curso.get('desc'),
            confirmed=True
        )

        db.session.add(new_curso)
        db.session.commit()

        return jsonify({'msg' : "Curso criado", 'curso': CursoSchema().dump(new_curso)}), 201
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        return jsonify({"msg": "Erro ao adicionar curso"}), 500

@app.route('/convite', methods=['POST'])
@jwt_required() #solicita o jwt
def add_convite():
    # Verifica qual é o usuário
    usuario = get_current_user()

    if not usuario:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = request.get_json()
        convite = data.get('convite')
        email_professor = convite.get('email_professor')
        usuario_convidado = Usuario.find_by_email(email_professor)

        if not usuario_convidado:
            return jsonify({"msg": "Email não corresponde a nenhum professor"}), 400

        if not usuario_convidado.professor:
            return jsonify({"msg": "Não é professor"}), 400

        if not convite:
            return jsonify({"msg": "Convite não recebido"}), 400

        # Verifica se o professor já foi convidado pela unidade
        convite_existente = db.session.query(ConviteProfessor).filter_by(
            id_unidade=convite.get('id_unidade'),
            email_professor=email_professor
        ).first()

        if convite_existente:
            return jsonify({
                "msg": "Professor já foi convidado para esta unidade",
                "id": convite_existente.professor.id
                }), 400

        new_convite = ConviteProfessor(
            id_unidade=convite.get('id_unidade'),
            id_professor=usuario_convidado.professor.id,
            email_professor=email_professor,
        )

        db.session.add(new_convite)
        db.session.commit()

        return jsonify({'msg' : "Convite criado", 'convite': ConviteProfessorSchema().dump(new_convite)}), 201
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        return jsonify({"msg": "Erro ao adicionar convite"}), 500

@app.route('/convite', methods=['PUT'])
@jwt_required() #solicita o jwt
def change_convite():
    # Verifica qual é o usuário
    usuario = get_current_user()

    if not usuario:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = request.get_json()
        convite_data = data.get('convite')
        convite = convite_data.get('convite')
        convite_professor = convite.get('convite_professor')
        mode = data.get('mode')
        print(convite_professor)
        if not convite_data:
            return jsonify({"msg": "Dados do convite não fornecidos"}), 400

        convite = ConviteProfessor.getPorId(convite_professor.get('id'))

        if not convite:
            return jsonify({"msg": "Convite não encontrado"}), 400

        if mode == 'aceitar':
            if convite.status == "aceito":
                return jsonify({"msg": "Convite já aceito"}), 400
            if convite.status == "recusado":
                return jsonify({"msg": "Convite já recusado"}), 400
            if convite.status == "pendente":
                professor_unidade = ProfessorUnidade(
                    id_unidade=convite.id_unidade,
                    id_professor=convite.id_professor
                )
                
                convite.status = "aceito"
                #mudar mensagem
                db.session.add(professor_unidade)
                db.session.commit()
                return jsonify({"msg": "Convite aceito com sucesso", 'convite': ConviteProfessorSchema().dump(convite)}), 200

        if mode == 'recusar':
            if convite.status == "recusado":
                return jsonify({"msg": "Convite já recusado"}), 400
            if convite.status == "aceito":
                return jsonify({"msg": "Convite já aceito"}), 400
            if convite.status == "pendente":
                convite.status = "recusado"
                db.session.commit()
                return jsonify({"msg": "Convite recusado com sucesso", 'convite': ConviteProfessorSchema().dump(convite)}), 200

        return jsonify({"msg": "Modo inválido"}), 400
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        return jsonify({"msg": "Erro ao atualizar convite"}), 500



@app.route('/msg/status', methods=['PUT'])
@jwt_required() #solicita o jwt
def change_status_msg():
    # Verifica qual é o usuário
    usuario = get_current_user()

    if not usuario:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = request.get_json()
        mensagem_id = data.get('msg')
        status = data.get('status')

        if not mensagem_id:
            return jsonify({"msg": "Dados do convite não fornecidos"}), 400

        msg = Mensagem.getPorId(mensagem_id)

        if not msg:
            return jsonify({"msg": "Mensagem não encontrada"}), 400

        if status == 'lido':
            if msg.status == "lido":
                return jsonify({"msg": "msg já lida"}), 400
            if msg.status == "respondido":
                return jsonify({"msg": "msg já respondido"}), 400
            if msg.status == "enviado":
                msg.status = "lido"
                db.session.commit()
                return jsonify({"msg": "Msg lida com sucesso"}), 200


        return jsonify({"msg": "Modo inválido"}), 400
    except Exception as e:
        print(f"Erro: {e}")
        db.session.rollback()
        return jsonify({"msg": "Erro ao atualizar convite"}), 500

@app.route('/getall', methods=['GET'])
def get_all():
    try:
        usuarios = Usuario.query.all()
        alunos = Aluno.query.all()
        professores = Professor.query.all()
        instituicoes = Instituicao.query.all()
        unidades = Unidade.query.all()
        cursos = Curso.query.all()
        convites_professores = ConviteProfessor.query.all()
        turmas = Turma.query.all()
        turmas_alunos = TurmaAluno.query.all()
        turmas_cursos = TurmaCurso.query.all()
        professores_unidades = ProfessorUnidade.query.all()

        return jsonify({
            "usuarios": UsuarioSchema(many=True).dump(usuarios),
            "alunos": AlunoSchema(many=True).dump(alunos),
            "professores": ProfessorSchema(many=True).dump(professores),
            "instituicoes": InstituicaoSchema(many=True).dump(instituicoes),
            "unidades": UnidadeSchema(many=True).dump(unidades),
            "cursos": CursoSchema(many=True).dump(cursos),
            "convites_professores": ConviteProfessorSchema(many=True).dump(convites_professores),
            "turmas": TurmaSchema(many=True).dump(turmas),
            "turmas_alunos": TurmaAlunoSchema(many=True).dump(turmas_alunos),
            "turmas_cursos": TurmaCursoSchema(many=True).dump(turmas_cursos),
            "professores_unidades": ProfessorUnidadeSchema(many=True).dump(professores_unidades),
        }), 200
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"msg": "Erro ao buscar dados"}), 500

# Manipulador de erros 404
@app.errorhandler(404)
def not_found(error):
    return redirect("http://localhost:4200"), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
