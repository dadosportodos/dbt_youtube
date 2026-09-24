import os
import random
from datetime import datetime, timedelta
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

print(f"🚀 Verificando schema '{SCHEMA}'...")
with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))
    conn.commit()

# 1. Tabela Clientes
print("📦 Gerando Clientes...")
clientes = []
for i in range(1, 1001):
    clientes.append({
        "cliente_id": i,
        "nome": fake.name(),
        "email": fake.email(),
        "estado": fake.state_abbr(),
        "data_cadastro": fake.date_between(start_date="-3y", end_date="today")
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
    vendas.append({
        "venda_id": i,
        "cliente_id": random.randint(1, 1000),
        "data_venda": fake.date_time_between(start_date="-1y", end_date="now"),
        "status": random.choice(status_opcao)
    })
df_vendas = pd.DataFrame(vendas)

# 4. Tabela Itens da Venda
print("📦 Gerando Itens de Venda...")
itens_venda = []
item_id_counter = 1
for venda in vendas:
    # Cada venda pode ter de 1 a 4 itens
    qtd_itens = random.randint(1, 4)
    produtos_sorteados = random.sample(range(1, 101), qtd_itens)
    
    for prod_id in produtos_sorteados:
        preco_unitario = df_produtos.loc[df_produtos["produto_id"] == prod_id, "preco_base"].values[0]
        itens_venda.append({
            "item_id": item_id_counter,
            "venda_id": venda["venda_id"],
            "produto_id": prod_id,
            "quantidade": random.randint(1, 5),
            "preco_unitario": preco_unitario
        })
        item_id_counter += 1
df_itens_venda = pd.DataFrame(itens_venda)

# Inserindo dados no PostgreSQL com CASCADE para limpar tabelas com dependências
print(f"💾 Limpando tabelas existentes e inserindo novos dados no schema '{SCHEMA}'...")

with engine.connect() as conn:
    # Força a remoção das tabelas e de todas as suas dependências (Foreign Keys)
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.itens_venda CASCADE;"))
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.vendas CASCADE;"))
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.produtos CASCADE;"))
    conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.clientes CASCADE;"))
    conn.commit()

# Usamos if_exists="append" porque já limpamos as tabelas manualmente com CASCADE
df_clientes.to_sql("clientes", engine, schema=SCHEMA, if_exists="append", index=False)
df_produtos.to_sql("produtos", engine, schema=SCHEMA, if_exists="append", index=False)
df_vendas.to_sql("vendas", engine, schema=SCHEMA, if_exists="append", index=False)
df_itens_venda.to_sql("itens_venda", engine, schema=SCHEMA, if_exists="append", index=False)

print(f"✅ Carga concluída com sucesso no schema '{SCHEMA}'!")