{{ config(materialized='table', schema='gold') }}

with vendas as (
    select * from {{ ref('silver_vendas') }}
),

itens as (
    select * from {{ ref('silver_itens_venda') }}
),

clientes as (
    select * from {{ ref('bronze_clientes') }}
),

totais_venda as (
    select
        venda_id,
        sum(quantidade) as total_itens,
        sum(valor_total_item) as valor_total_venda
    from itens
    group by 1
)

select
    v.venda_id,
    v.data_venda,
    c.cliente_id,
    c.nome as nome_cliente,
    c.estado as estado_cliente,
    coalesce(t.total_itens, 0) as quantidade_itens,
    coalesce(t.valor_total_venda, 0) as valor_total
from vendas v
left join clientes c on v.cliente_id = c.cliente_id
left join totais_venda t on v.venda_id = t.venda_id