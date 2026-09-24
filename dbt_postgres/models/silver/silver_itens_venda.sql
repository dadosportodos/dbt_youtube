{{ config(materialized='view', schema='silver') }}

with source as (
    select * from {{ ref('bronze_itens_venda') }}
)

select
    item_id,
    venda_id,
    produto_id,
    quantidade,
    preco_unitario,
    round(cast((quantidade * preco_unitario) as numeric), 2) as valor_total_item
from source