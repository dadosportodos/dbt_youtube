import os
import random
from datetime import datetime
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Conexão com o PostgreSQL
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
SCHEMA = os.getenv("DB_SCHEMA", "public")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

fake = Faker("pt_BR")
Faker.seed(42)
random.seed(42)

print(f"🚀 Verificando schema '{SCHEMA}'...")
with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))
    conn.commit()


# --- FUNÇÕES DE INJEÇÃO DE INCONSISTÊNCIAS (DADOS BRUTOS BRONZE) ---

def aplicar_sujeira_nome(nome):
    prob = random.random()
    if prob < 0.05:
        return nome.upper()
    elif prob < 0.10:
        return nome.lower()
    elif prob < 0.15:
        return f"  {nome}   "
    return nome

def aplicar_sujeira_email(email):
    prob = random.random()
    if prob < 0.05:
        return None
    elif prob < 0.10:
        return email.replace("@", " AT ")
    elif prob < 0.13:
        return f" {email} "
    return email

def aplicar_sujeira_cpf(cpf_raw):
    prob = random.random()
    if prob < 0.08:
        return None
    elif prob < 0.25:
        return cpf_raw.replace(".", "").replace("-", "")
    elif prob < 0.30:
        return cpf_raw.replace(".", "")
    return cpf_raw

def aplicar_sujeira_telefone(tel_raw):
    prob = random.random()
    if prob < 0.10:
        return None
    if random.random() < 0.30:
        return tel_raw.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    return tel_raw

def aplicar_sujeira_estado(estado):
    prob = random.random()
    if prob < 0.05:
        return None
    elif prob < 0.10:
        return estado.lower()
    elif prob < 0.12:
        return f"{estado} "
    return estado


# 1. Tabela Clientes (Com sujeiras e histórico de mutação para SCD Tipo 2 no dbt)
print("📦 Gerando Clientes...")
clientes = []

for i in range(1, 1001):
    nome_base = fake.name()
    email_base = fake.email()
    cpf_base = fake.cpf()
    tel_base = fake.phone_number()
    estado_base = fake.state_abbr()
    
    data_cadastro_inicial = fake.date_between(start_date="-3y", end_date="-1y")
    data_nasc = None if random.random() < 0.05 else fake.date_of_birth(minimum_age=16, maximum_age=80)
    renda_base = None if random.random() < 0.12 else round(random.uniform(1500.0, 25000.0), 2)

    # Registro V1 (Cadastro Inicial)
    clientes.append({
        "cliente_id": i,
        "nome": aplicar_sujeira_nome(nome_base),
        "email": aplicar_sujeira_email(email_base),
        "cpf": aplicar_sujeira_cpf(cpf_base),
        "telefone": aplicar_sujeira_telefone(tel_base),
        "estado": aplicar_sujeira_estado(estado_base),
        "data_cadastro": data_cadastro_inicial,
        "updated_at": datetime.combine(data_cadastro_inicial, datetime.min.time()),
        "data_nascimento": data_nasc,
        "renda_mensal": renda_base
    })

    # Registro V2 (Mutação cadastral para ~25% dos clientes)
    if random.random() < 0.25:
        data_alteracao = fake.date_between(start_date=data_cadastro_inicial, end_date="today")
        novo_estado = fake.state_abbr() if random.random() < 0.50 else estado_base
        novo_tel = fake.phone_number() if random.random() < 0.50 else tel_base
        nova_renda = round(renda_base * random.uniform(1.1, 1.3), 2) if renda_base else round(random.uniform(2500.0, 28000.0), 2)

        clientes.append({
            "cliente_id": i,
            "nome": aplicar_sujeira_nome(nome_base),
            "email": aplicar_sujeira_email(email_base),
            "cpf": aplicar_sujeira_cpf(cpf_base),
            "telefone": aplicar_sujeira_telefone(novo_tel),
            "estado": aplicar_sujeira_estado(novo_estado),
            "data_cadastro": data_cadastro_inicial,
            "updated_at": datetime.combine(data_alteracao, datetime.min.time()),
            "data_nascimento": data_nasc,
            "renda_mensal": nova_renda
        })

df_clientes = pd.DataFrame(clientes)

# 2. Tabela Produtos
print("📦 Gerando Produtos...")
categorias = ["Eletrônicos", "Roupas", "Casa", "Livros", "Esportes"]
produtos = []
for i in range(1, 101):
    produtos.append({
        "produto_id": i,
        "nome_produto": f"Produto {fake.word().capitalize()}",
        "categoria": random.choice(categorias),
        "preco_base": round(random.uniform(20.0, 1500.0), 2)
    })
df_produtos = pd.DataFrame(produtos)

# 3. Tabela Vendas
print("📦 Gerando Vendas...")
vendas = []
status_opcao = ["CONCLUIDO", "CONCLUIDO", "CONCLUIDO", "CANCELADO", "PENDENTE"]
for i in range(1, 10001):
    dt_venda = fake.date_time_between(start_date="-1y", end_date="now")
    vendas.append({
        "venda_id": i,
        "cliente_id": random.randint(1, 1000),
        "data_venda": dt_venda,
        "status": random.choice(status_opcao),
        "updated_at": dt_venda  # Coluna necessária para o dbt incremental
    })
df_vendas = pd.DataFrame(vendas)

# 4. Tabela Itens da Venda
print("📦 Gerando Itens de Venda...")
itens_venda = []
item_id_counter = 1
for venda in vendas:
    qtd_itens = random.randint(1, 4)
    produtos_sorteados = random.sample(range(1, 101), qtd_itens)
    
    for prod_id in produtos_sorteados:
        preco_unitario = df_produtos.loc[df_produtos["produto_id"] == prod_id, "preco_base"].values[0]
        itens_venda.append({
            "item_id": item_id_counter,
            "venda_id": venda["venda_id"],
            "produto_id": prod_id,
            "quantidade": random.randint(1, 5),
            "preco_unitario": preco_unitario,
            "updated_at": venda["data_venda"]
        })
        item_id_counter += 1
df_itens_venda = pd.DataFrame(itens_venda)

# Reconstrução das tabelas no PostgreSQL
print(f"💾 Limpando e recriando tabelas no schema '{SCHEMA}'...")

with engine.connect() as conn:
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.itens_venda CASCADE;"))
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.vendas CASCADE;"))
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.produtos CASCADE;"))
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.clientes CASCADE;"))
    conn.commit()

df_clientes.to_sql("clientes", engine, schema=SCHEMA, if_exists="append", index=False)
df_produtos.to_sql("produtos", engine, schema=SCHEMA, if_exists="append", index=False)
df_vendas.to_sql("vendas", engine, schema=SCHEMA, if_exists="append", index=False)
df_itens_venda.to_sql("itens_venda", engine, schema=SCHEMA, if_exists="append", index=False)

print(f"✅ Carga base concluída com sucesso no schema '{SCHEMA}'!")