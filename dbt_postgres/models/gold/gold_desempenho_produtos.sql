
with produtos as (
    select * from {{ ref('bronze_produtos') }}
),

itens as (
    select * from {{ ref('silver_itens_venda') }}
),

vendas_validas as (
    select venda_id from {{ ref('silver_vendas') }}
)

select
    p.produto_id,
    p.nome_produto,
    p.categoria,
    count(distinct i.venda_id) as total_pedidos,
    sum(i.quantidade) as total_unidades_vendidas,
    sum(i.valor_total_item) as receita_total
from produtos p
inner join itens i on p.produto_id = i.produto_id
inner join vendas_validas v on i.venda_id = v.venda_id
group by 1, 2, 3