{{ config(
    materialized='table',
    schema='gold'
) }}

WITH silver_vendas AS (
    SELECT * FROM {{ ref('silver_vendas') }}
),

silver_itens AS (
    SELECT * FROM {{ ref('silver_itens_venda') }}
)

SELECT
    v.venda_id,
    v.cliente_id,
    i.produto_id,
    v.data_venda,
    i.quantidade,
    i.preco_unitario,
    (i.quantidade * i.preco_unitario) AS valor_total_item,
    v.status
FROM silver_vendas v
INNER JOIN silver_itens i 
    ON v.venda_id = i.venda_id