{{ config(
    materialized='table',
    schema='gold'
) }}

WITH fct_vendas AS (
    SELECT * FROM {{ ref('gold_fct_vendas') }}
),

silver_produtos AS (
    SELECT * FROM {{ ref('silver_produtos') }}
)

SELECT
    p.produto_id,
    p.nome_produto,
    p.categoria,
    COUNT(DISTINCT f.venda_id) AS total_pedidos,
    SUM(f.quantidade) AS quantidade_total_vendida,
    SUM(f.valor_total_item) AS receita_total,
    ROUND(AVG(f.valor_total_item), 2) AS ticket_medio_item
FROM fct_vendas f
INNER JOIN silver_produtos p 
    ON f.produto_id = p.produto_id
GROUP BY 
    p.produto_id,
    p.nome_produto,
    p.categoria