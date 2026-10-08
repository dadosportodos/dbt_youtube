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

print(f"🚀 Verificando tabelas no schema '{SCHEMA}'...")

# 1. Identificar Watermark (Maior data_venda existente)
query_watermark = text(f"""
    SELECT MAX(data_venda), MAX(venda_id) 
    FROM {SCHEMA}.vendas;
""")

max_data_venda = None
max_venda_id = 0

with engine.connect() as conn:
    try:
        result = conn.execute(query_watermark).fetchone()
        if result and result[0] is not None:
            max_data_venda = result[0]
            max_venda_id = result[1]
            print(f"📌 Watermark encontrada: Última venda id={max_venda_id} em {max_data_venda}")
        else:
            print("ℹ️ Tabela de vendas vazia. Realizando carga inicial (Backfill)...")
    except Exception:
        print("ℹ️ Tabela de vendas não encontrada. Realizando carga inicial (Backfill)...")

# 2. Definir janela de tempo para a nova carga incremental
if max_data_venda:
    # Carga Incremental: Gera registros a partir do último checkpoint até agora
    start_date = max_data_venda + timedelta(seconds=1)
    end_date = datetime.now()
    qtd_novas_vendas = random.randint(50, 200) # Lote incremental menor
    print(f"🔄 Gerando {qtd_novas_vendas} NOVAS vendas entre {start_date} e {end_date}...")
else:
    # Carga Inicial (Backfill): 1 ano de histórico
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    qtd_novas_vendas = 10000
    print(f"📦 Gerando histórico inicial de {qtd_novas_vendas} vendas...")

if start_date >= end_date:
    print("✅ Os dados já estão atualizados até o momento atual! Nenhuma venda nova gerada.")
    exit()

# 3. Buscar produtos ativos para pegar o preço e montar os itens da venda
df_produtos = pd.read_sql(f"SELECT produto_id, preco_base FROM {SCHEMA}.produtos;", engine)
if df_produtos.empty:
    raise ValueError("⚠️ A tabela de produtos precisa estar populada antes de gerar as vendas!")

# 4. Gerar Novas Vendas
novas_vendas = []
status_opcao = ["CONCLUIDO", "CONCLUIDO", "CONCLUIDO", "CANCELADO", "PENDENTE"]

# Buscar o último item_id gerado
query_max_item = text(f"SELECT COALESCE(MAX(item_id), 0) FROM {SCHEMA}.itens_venda;")
with engine.connect() as conn:
    try:
        max_item_id = conn.execute(query_max_item).scalar()
    except Exception:
        max_item_id = 0

novos_itens_venda = []
current_venda_id = max_venda_id + 1
current_item_id = max_item_id + 1

for _ in range(qtd_novas_vendas):
    data_venda_gerada = fake.date_time_between(start_date=start_date, end_date=end_date)
    
    # Registro de Venda
    venda_dict = {
        "venda_id": current_venda_id,
        "cliente_id": random.randint(1, 1000), # Aponta para a dimensão de clientes
        "data_venda": data_venda_gerada,
        "status": random.choice(status_opcao),
        "updated_at": data_venda_gerada # Útil para controlar o incremental no dbt
    }
    novas_vendas.append(venda_dict)

    # Registro de Itens da Venda (1 a 4 itens por venda)
    qtd_itens = random.randint(1, 4)
    produtos_sorteados = random.sample(list(df_produtos["produto_id"]), qtd_itens)

    for prod_id in produtos_sorteados:
        preco_unitario = df_produtos.loc[df_produtos["produto_id"] == prod_id, "preco_base"].values[0]
        novos_itens_venda.append({
            "item_id": current_item_id,
            "venda_id": current_venda_id,
            "produto_id": prod_id,
            "quantidade": random.randint(1, 5),
            "preco_unitario": preco_unitario,
            "updated_at": data_venda_gerada
        })
        current_item_id += 1

    current_venda_id += 1

df_novas_vendas = pd.DataFrame(novas_vendas)
df_novos_itens = pd.DataFrame(novos_itens_venda)

# 5. Inserir lote incremental via APPEND
print(f"💾 Inserindo {len(df_novas_vendas)} novas vendas e {len(df_novos_itens)} itens no schema '{SCHEMA}'...")

df_novas_vendas.to_sql("vendas", engine, schema=SCHEMA, if_exists="append", index=False)
df_novos_itens.to_sql("itens_venda", engine, schema=SCHEMA, if_exists="append", index=False)

print(f"✅ Incremental concluído com sucesso!")