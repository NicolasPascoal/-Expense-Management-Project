"""
Modelos SQLAlchemy (Tarefa 3.1 — introdução gradual, ver STATUS.md).

Espelham exatamente o schema hoje criado por app/database/model*.py — mesmos
nomes de tabela/coluna, mesmos tipos, mesmo ON DELETE por FK (não é uniforme:
a maioria é CASCADE, mas empresa_id em Projeto/Usuario não tem ON DELETE
explícito no SQL original, e Auditoria.usuario_id é o único SET NULL).

`colunas`/`dados` continuam Text (não JSONB) — essa conversão é a Tarefa 3.2,
separada. `is_admin` continua Integer — evita mudar comparações espalhadas
pelo código (`is_admin == 1`).

A tabela legada `lancamentos` (não-`_v2`) não tem modelo aqui: confirmado via
grep que não é referenciada em nenhum controller/rota, fora de escopo.
"""
from app.extensions import db


class Empresa(db.Model):
    __tablename__ = "empresas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)

    usuarios = db.relationship("Usuario", back_populates="empresa")
    projetos = db.relationship("Projeto", back_populates="empresa")


class Projeto(db.Model):
    __tablename__ = "projetos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    colunas = db.Column(db.Text, nullable=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)

    empresa = db.relationship("Empresa", back_populates="projetos")
    categorias = db.relationship("Categoria", back_populates="projeto")
    contas = db.relationship("Conta", back_populates="projeto")
    lancamentos = db.relationship("LancamentoV2", back_populates="projeto")
    orcamentos = db.relationship("Orcamento", back_populates="projeto")
    entradas = db.relationship("Entrada", back_populates="projeto")


class LancamentoV2(db.Model):
    __tablename__ = "lancamentos_v2"

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False)
    dados = db.Column(db.Text, nullable=False)

    projeto = db.relationship("Projeto", back_populates="lancamentos")


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Integer, default=0)
    role = db.Column(db.String(50), default="prestador")
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)

    empresa = db.relationship("Empresa", back_populates="usuarios")
    tarefas = db.relationship("Tarefa", back_populates="prestador")
    requisicoes = db.relationship("RequisicaoMaterial", back_populates="usuario")


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id", ondelete="CASCADE"), nullable=True)

    projeto = db.relationship("Projeto", back_populates="categorias")


class Conta(db.Model):
    __tablename__ = "contas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id", ondelete="CASCADE"), nullable=True)

    projeto = db.relationship("Projeto", back_populates="contas")


class RequisicaoMaterial(db.Model):
    __tablename__ = "requisicoes_materiais"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    funcao = db.Column(db.String(255), nullable=False)
    material = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Pendente")
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    usuario = db.relationship("Usuario", back_populates="requisicoes")


class Tarefa(db.Model):
    __tablename__ = "tarefas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    prestador_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True)
    status = db.Column(db.String(50), default="Pendente")
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    prestador = db.relationship("Usuario", back_populates="tarefas")


class Orcamento(db.Model):
    __tablename__ = "orcamentos"
    __table_args__ = (db.UniqueConstraint("projeto_id", "categoria_id"),)

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False)
    valor_orcado = db.Column(db.Numeric, nullable=False)

    projeto = db.relationship("Projeto", back_populates="orcamentos")


class Entrada(db.Model):
    __tablename__ = "entradas"

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric, nullable=False)
    data = db.Column(db.String(50), nullable=True)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    projeto = db.relationship("Projeto", back_populates="entradas")


class Auditoria(db.Model):
    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    entidade = db.Column(db.String(50), nullable=False)
    entidade_id = db.Column(db.Integer, nullable=True)
    acao = db.Column(db.String(20), nullable=False)
    detalhes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
