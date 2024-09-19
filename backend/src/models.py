from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy.orm as so
from sqlalchemy import Enum, LargeBinary, String, Date, DateTime, Boolean, Integer, ForeignKey, Text, event, func
from typing import List
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested, fields

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: so.Mapped[str] = so.mapped_column(String(16), nullable=False)
    sobrenome: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    email: so.Mapped[str] = so.mapped_column(String(255), nullable=False, unique=True)
    telefone: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    senha: so.Mapped[str] = so.mapped_column(String(255), nullable=False)
    image: so.Mapped[bytes] = so.mapped_column(LargeBinary, nullable=True)
    img_link: so.Mapped[str] = so.mapped_column(String(250), nullable=True, default='/assets/user-no_image.png')
    tipo: so.Mapped[str] = so.mapped_column(Enum('professor', 'aluno', 'instituicao'), nullable=True)
    genero: so.Mapped[str] = so.mapped_column(Enum('masculino', 'feminino', 'outro'), nullable=True)
    nascimento: so.Mapped[Date] = so.mapped_column(Date, nullable=True)
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    update_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed: so.Mapped[bool] = so.mapped_column(Boolean, nullable=True, default=False)
    professor: so.Mapped['Professor'] = so.relationship('Professor', back_populates='usuario', uselist=False)
    aluno: so.Mapped['Aluno'] = so.relationship('Aluno', back_populates='usuario', uselist=False)
    instituicao: so.Mapped['Instituicao'] = so.relationship('Instituicao', back_populates='usuario', uselist=False)
    mensagens_enviadas = db.relationship('Mensagem', foreign_keys='Mensagem.id_remetente', back_populates='remetente')
    mensagens_recebidas = db.relationship('Mensagem', foreign_keys='Mensagem.id_destinatario', back_populates='destinatario')

    def __init__(self, nome, email, sobrenome=None, telefone=None, senha=None, image=None, img_link=None, tipo=None, genero=None, nascimento=None, confirmed=None):
        self.nome = nome
        self.sobrenome = sobrenome
        self.email = email
        self.telefone = telefone
        self.set_password(senha)
        self.image = image
        self.img_link = img_link
        self.tipo = tipo
        self.genero = genero
        self.nascimento = nascimento
        self.confirmed = confirmed

    def __repr__(self):
        return f'<Usuario {self.nome} >'

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def set_password(self, password):
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha, password)


class Professor(db.Model):
    __tablename__ = 'professores'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True)
    id_usuario: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    usuario: so.Mapped['Usuario'] = so.relationship('Usuario', back_populates='professor')
    turmas: so.Mapped[List['Turma']] = so.relationship('Turma', back_populates='professor')
    cursos: so.Mapped[List['Curso']] = so.relationship('Curso', back_populates='professor')
    unidade: so.Mapped[List['ProfessorUnidade']] = so.relationship('ProfessorUnidade', back_populates='professor')
    convites: so.Mapped[List['ConviteProfessor']] = so.relationship('ConviteProfessor', back_populates='professor')


class Aluno(db.Model):
    __tablename__ = 'alunos'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True)
    id_usuario: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    matricula: so.Mapped[str] = so.mapped_column(String(100), nullable=True)
    usuario: so.Mapped['Usuario'] = so.relationship('Usuario', back_populates='aluno')
    turmas: so.Mapped[List['TurmaAluno']] = so.relationship('TurmaAluno', back_populates='aluno')
    convites = db.relationship('ConviteAluno', back_populates='aluno')


class Turma(db.Model):
    __tablename__ = 'turmas'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: so.Mapped[str] = so.mapped_column(String(45), nullable=False)
    id_professor: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('professores.id'), nullable=False)
    inicio: so.Mapped[Date] = so.mapped_column(Date, nullable=True)
    fim: so.Mapped[Date] = so.mapped_column(Date, nullable=True)
    periodo: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    professor: so.Mapped['Professor'] = so.relationship('Professor', back_populates='turmas')
    alunos: so.Mapped[List['TurmaAluno']] = so.relationship('TurmaAluno', back_populates='turma')
    turmas_cursos: so.Mapped[List['TurmaCurso']] = so.relationship('TurmaCurso', back_populates='turma')
    convites_alunos = db.relationship('ConviteAluno', back_populates='turma')


class TurmaAluno(db.Model):
    __tablename__ = 'turmas_alunos'
    id_turma: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('turmas.id'), primary_key=True)
    id_aluno: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('alunos.id'), primary_key=True)
    turma: so.Mapped['Turma'] = so.relationship('Turma', back_populates='alunos')
    aluno: so.Mapped['Aluno'] = so.relationship('Aluno', back_populates='turmas')


class Curso(db.Model):
    __tablename__ = 'curso'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: so.Mapped[str] = so.mapped_column(String(100), nullable=False)
    id_unidade: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('unidade.id'), nullable=True)
    id_professor: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('professores.id'), nullable=True)
    descricao: so.Mapped[str] = so.mapped_column(Text, nullable=True)
    confirmed: so.Mapped[bool] = so.mapped_column(Boolean, nullable=True, default=False)
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    update_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    unidade: so.Mapped['Unidade'] = so.relationship('Unidade', back_populates='cursos')
    professor: so.Mapped['Professor'] = so.relationship('Professor', back_populates='cursos')
    turmas_cursos: so.Mapped[List['TurmaCurso']] = so.relationship('TurmaCurso', back_populates='curso')


class Unidade(db.Model):
    __tablename__ = 'unidade'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: so.Mapped[str] = so.mapped_column(String(100), nullable=False)
    id_instituicao: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('instituicao.id'), nullable=False)
    telefone: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    endereco: so.Mapped[str] = so.mapped_column(String(200), nullable=True)
    estado: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    cidade: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    bairro: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    cep: so.Mapped[str] = so.mapped_column(String(45), nullable=True)
    confirmed: so.Mapped[bool] = so.mapped_column(Boolean, nullable=True, default=False)
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    update_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cursos: so.Mapped[List['Curso']] = so.relationship('Curso', back_populates='unidade')
    instituicao: so.Mapped['Instituicao'] = so.relationship('Instituicao', back_populates='unidades')
    professores: so.Mapped[List['ProfessorUnidade']] = so.relationship('ProfessorUnidade', back_populates='unidade')
    convites: so.Mapped[List['ConviteProfessor']] = so.relationship('ConviteProfessor', back_populates='unidade')

    @classmethod
    def getPorId(cls, id):
        try:
            return db.session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None


class Instituicao(db.Model):
    __tablename__ = 'instituicao'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    nome: so.Mapped[str] = so.mapped_column(String(100), nullable=False)
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    update_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed: so.Mapped[bool] = so.mapped_column(Boolean, nullable=True, default=False)
    unidades: so.Mapped[List['Unidade']] = so.relationship('Unidade', back_populates='instituicao', uselist=True)
    usuario: so.Mapped['Usuario'] = so.relationship('Usuario', back_populates='instituicao', uselist=False)


class TurmaCurso(db.Model):
    __tablename__ = 'turmas_curso'
    id_turma: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('turmas.id'), primary_key=True)
    id_curso: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('curso.id'), primary_key=True)
    turma: so.Mapped['Turma'] = so.relationship('Turma', back_populates='turmas_cursos')
    curso: so.Mapped['Curso'] = so.relationship('Curso', back_populates='turmas_cursos')


class ProfessorUnidade(db.Model):
    __tablename__ = 'professor_unidade'
    id_unidade: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('unidade.id'), primary_key=True)
    id_professor: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('professores.id'), primary_key=True)
    unidade: so.Mapped['Unidade'] = so.relationship('Unidade', back_populates='professores')
    professor: so.Mapped['Professor'] = so.relationship('Professor', back_populates='unidade')


class ConviteProfessor(db.Model):
    __tablename__ = 'convite_professor'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    id_unidade: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('unidade.id'))
    id_professor: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('professores.id'))
    email_professor: so.Mapped[str] = so.mapped_column(String(255), nullable=False)
    status: so.Mapped[str] = so.mapped_column(Enum('pendente', 'aceito', 'recusado'), nullable=False, default='pendente')
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    data_resposta: so.Mapped[DateTime] = so.mapped_column(DateTime)
    unidade: so.Mapped['Unidade'] = so.relationship('Unidade', back_populates='convites')
    professor: so.Mapped['Professor'] = so.relationship('Professor', back_populates='convites')
    convites = db.relationship('Convite', back_populates='convite_professor')

    @classmethod
    def count_pendentes(cls):
        return db.session.query(func.count(cls.id)).filter_by(status='pendente').scalar()

    @classmethod
    def getPorId(cls, convite_id):
        try:
            return db.session.query(cls).filter_by(id=convite_id).one()
        except NoResultFound:
            return None


class ConviteAluno(db.Model):
    __tablename__ = 'convite_aluno'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    id_turma: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('turmas.id'), nullable=False)
    id_aluno: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('alunos.id'), nullable=True)
    email_aluno: so.Mapped[str] = so.mapped_column(String(255), nullable=False)
    status: so.Mapped[str] = so.mapped_column(Enum('pendente', 'aceito', 'recusado'), nullable=False, default='pendente')
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    data_resposta: so.Mapped[DateTime] = so.mapped_column(DateTime, nullable=True)
    turma: so.Mapped['Turma'] = so.relationship('Turma', back_populates='convites_alunos')
    aluno: so.Mapped['Aluno'] = so.relationship('Aluno', back_populates='convites')
    convites = db.relationship('Convite', back_populates='convite_aluno')


class Convite(db.Model):
    __tablename__ = 'convites'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    id_convite_professor: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('convite_professor.id'), nullable=True)
    id_convite_aluno: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('convite_aluno.id'), nullable=True)
    convite_professor: so.Mapped['ConviteProfessor'] = so.relationship('ConviteProfessor', back_populates='convites')
    convite_aluno: so.Mapped['ConviteAluno'] = so.relationship('ConviteAluno', back_populates='convites')
    mensagens: so.Mapped[List['Mensagem']] = so.relationship('Mensagem', back_populates='convite')


class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    id: so.Mapped[int] = so.mapped_column(Integer, primary_key=True, autoincrement=True)
    id_remetente: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    id_destinatario: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    status: so.Mapped[str] = so.mapped_column(Enum('enviado', 'lido', 'respondido'), nullable=False, default='enviado')
    create_time: so.Mapped[DateTime] = so.mapped_column(DateTime, default=datetime.utcnow)
    data_resposta: so.Mapped[DateTime] = so.mapped_column(DateTime, nullable=True)
    tipo: so.Mapped[str] = so.mapped_column(Enum('msg', 'convite', 'news'), nullable=False)
    id_convite: so.Mapped[int] = so.mapped_column(Integer, ForeignKey('convites.id'), nullable=True)
    text: so.Mapped[str] = so.mapped_column(Text, nullable=True)
    remetente: so.Mapped['Usuario'] = so.relationship('Usuario', foreign_keys=[id_remetente], back_populates='mensagens_enviadas')
    destinatario: so.Mapped['Usuario'] = so.relationship('Usuario', foreign_keys=[id_destinatario], back_populates='mensagens_recebidas')
    convite: so.Mapped['Convite'] = so.relationship('Convite', back_populates='mensagens')

    @classmethod
    def getPorId(cls, id):
        try:
            return db.session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None


@event.listens_for(ConviteProfessor, 'after_insert')
def create_convite_professor(mapper, connection, target):
    # Inserindo no Convite
    connection.execute(
        Convite.__table__.insert().values(id_convite_professor=target.id)
    )
    convite = connection.execute(
        Convite.__table__.select().where(Convite.id_convite_professor == target.id)
    ).first()

    if convite:
        unidade = connection.execute(
            Unidade.__table__.select().where(Unidade.id == target.id_unidade)
        ).first()

        if unidade:
            instituicao = connection.execute(
                Instituicao.__table__.select().where(Instituicao.id == unidade.id_instituicao)
            ).first()

            if instituicao:
                usuario = connection.execute(
                    Usuario.__table__.select().where(Usuario.email == target.email_professor)
                ).first()
                
                if usuario:
                    connection.execute(
                        Mensagem.__table__.insert().values(
                            id_remetente=instituicao.id_usuario,
                            id_destinatario=usuario.id,
                            id_convite=convite.id,
                            tipo='convite'
                        )
                    )

@event.listens_for(ConviteAluno, 'after_insert')
def create_convite_aluno(mapper, connection, target):
    # Inserindo no Convite
    connection.execute(
        Convite.__table__.insert().values(id_convite_aluno=target.id)
    )
    convite = connection.execute(
        Convite.__table__.select().where(Convite.id_convite_aluno == target.id)
    ).first()

    if convite:
        turma = connection.execute(
            Turma.__table__.select().where(Turma.id == target.id_turma)
        ).first()

        if turma:
            usuario = connection.execute(
                Usuario.__table__.select().where(Usuario.email == target.email_aluno)
            ).first()

            if usuario:
                connection.execute(
                    Mensagem.__table__.insert().values(
                        id_remetente=turma.id_professor,
                        id_destinatario=usuario.id,
                        id_convite=convite.id,
                        tipo='convite'
                    )
                )

@event.listens_for(Usuario, 'after_insert')
def create_professor_or_aluno(mapper, connection, target):
    if target.tipo == 'professor':
        connection.execute(
            Professor.__table__.insert().values(id_usuario=target.id)
        )
    elif target.tipo == 'aluno':
        connection.execute(
            Aluno.__table__.insert().values(id_usuario=target.id)
        )


class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        include_fk = True
        load_instance = True
    senha = fields.String(load_only=True)
    professor = Nested('ProfessorSchema', exclude=('usuario',), many=False)
    aluno = Nested('AlunoSchema', exclude=('usuario',), many=False)
    instituicao = Nested('InstituicaoSchema', exclude=('usuario',), many=False)
    mensagens_enviadas = Nested('MensagemSchema', many=True, exclude=('remetente', ))
    mensagens_recebidas = Nested('MensagemSchema', many=True, exclude=('destinatario', ))


class ProfessorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Professor
        include_fk = True
        load_instance = True
    convites = Nested('ConviteSchema')
    usuario = Nested(UsuarioSchema, exclude=('professor', 'mensagens_enviadas', 'mensagens_recebidas'))
    unidades = Nested('ProfessorUnidadeSchema',many=True,exclude=('professor',))
    


class AlunoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Aluno
        include_fk = True
        load_instance = True

    usuario = Nested(UsuarioSchema, exclude=('aluno', 'mensagens_enviadas', 'mensagens_recebidas'))


class InstituicaoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Instituicao
        include_fk = True
        load_instance = True

    usuario = Nested(UsuarioSchema, exclude=('instituicao', 'mensagens_enviadas', 'mensagens_recebidas'))
    unidades = Nested('UnidadeSchema', many=True, exclude=('instituicao',))


class CursoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Curso
        include_fk = True
        load_instance = True

    unidade = Nested('UnidadeSchema', exclude=('cursos',))
    professor = Nested(ProfessorSchema, exclude=('cursos',))


class UnidadeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Unidade
        include_fk = True
        load_instance = True
    convites = Nested('ConviteProfessorSchema',many=True)
    professores = Nested('ProfessorUnidadeSchema',many=True,exclude=('unidade',))
    instituicao = Nested(InstituicaoSchema, exclude=('unidades',))
    cursos = Nested(CursoSchema, many=True, exclude=('unidade',))
    


class TurmaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Turma
        include_fk = True
        load_instance = True

    professor = Nested(ProfessorSchema, exclude=('turmas',))
    alunos = Nested('TurmaAlunoSchema', many=True, exclude=('turma',))


class TurmaAlunoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TurmaAluno
        include_fk = True
        load_instance = True

    turma = Nested(TurmaSchema, exclude=('alunos',))
    aluno = Nested(AlunoSchema, exclude=('turmas',))


class TurmaCursoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TurmaCurso
        include_fk = True
        load_instance = True

    turma = Nested(TurmaSchema, exclude=('turmas_cursos',))
    curso = Nested(CursoSchema, exclude=('turmas_cursos',))


class ProfessorUnidadeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProfessorUnidade
        include_fk = True
        load_instance = True

    unidade = Nested(UnidadeSchema, exclude=('professores',) )
    professor = Nested(ProfessorSchema, exclude=('unidades',))


class ConviteProfessorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConviteProfessor
        include_fk = True
        load_instance = True

    unidade = Nested(UnidadeSchema, exclude=('convites',))
    professor = Nested(ProfessorSchema, exclude=('convites',))


class ConviteAlunoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConviteAluno
        include_fk = True
        load_instance = True

    turma = Nested(TurmaSchema, exclude=('convites_alunos',))
    aluno = Nested(AlunoSchema, exclude=('convites',))


class ConviteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Convite
        include_fk = True
        load_instance = True

    convite_professor = Nested(ConviteProfessorSchema, )
    convite_aluno = Nested(ConviteAlunoSchema, )


class MensagemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Mensagem
        include_fk = True
        load_instance = True

    remetente = Nested(UsuarioSchema, exclude=('mensagens_enviadas', 'mensagens_recebidas'))
    destinatario = Nested(UsuarioSchema, exclude=('mensagens_recebidas', 'mensagens_enviadas'))
    convite = Nested(ConviteSchema)