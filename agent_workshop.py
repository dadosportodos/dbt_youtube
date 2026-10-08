import os
import warnings
from dotenv import load_dotenv

# Silencia warnings de depreciação do terminal
warnings.filterwarnings("ignore")

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, PromptTemplate

load_dotenv()

# 1. Configuração do Banco de Dados PostgreSQL
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

db = SQLDatabase.from_uri(
    DATABASE_URI,
    schema="gold",
    include_tables=["gold_fct_vendas", "gold_desempenho_produtos"]
)

# 2. Modelo Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0.0
)

# 3. Prefixo de Instruções de Negócio
system_prefix = """Você é um assistente especialista em análise de dados da 'Dados Por Todos'.
Você tem acesso a um banco de dados PostgreSQL contendo a camada 'gold'.

Instruções e Regras de Negócio:
1. Responda sempre em português, de forma clara, objetiva e formate valores monetários em R$.
2. Consulte apenas as tabelas do schema 'gold': 'gold_fct_vendas' e 'gold_desempenho_produtos'.
3. Colunas disponíveis:
   - 'gold_fct_vendas': venda_id, cliente_id, produto_id, data_venda, quantidade, preco_unitario, valor_total_item, status
   - 'gold_desempenho_produtos': produto_id, nome_produto, categoria, total_pedidos, quantidade_total_vendida, receita_total, ticket_medio_item
4. Execute apenas instruções SQL de leitura (SELECT).

Atenção ao formato final:
Quando souber a resposta final, use obrigatoriamente:
Final Answer: <sua resposta estruturada aqui em português>
"""

# 4. Agente SQL ReAct Estável com o Gemini
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="zero-shot-react-description",
    prefix=system_prefix,
    verbose=True,
    handle_parsing_errors="Verifique o formato da resposta! Lembre-se de sempre responder com 'Thought:', seguido por 'Action:'/'Action Input:' ou 'Final Answer:'."
)

if __name__ == "__main__":
    print("🤖 Agente SQL Dados Por Todos Conectado e Operacional!")
    print("Digite sua pergunta de negócios (ou 'sair' para encerrar):\n")

    while True:
        pergunta = input("\n📊 Pergunta: ")
        if pergunta.lower() in ["sair", "exit", "quit"]:
            print("Até logo!")
            break

        if not pergunta.strip():
            continue

        try:
            resposta = agent_executor.invoke({"input": pergunta})
            print("\n💡 Resposta:\n", resposta["output"])
        except Exception as e:
            print(f"\n❌ Erro ao processar a consulta: {e}")