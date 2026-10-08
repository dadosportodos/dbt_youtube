with source_data as (

    select * from {{ ref('bronze_itens_venda') }}

),

silver_vendas as (

    select venda_id from {{ ref('silver_vendas') }}

),

cleaned as (

    select
        i.item_id::integer as item_id,
        i.venda_id::integer as venda_id,
        i.produto_id::integer as produto_id,
        i.quantidade::integer as quantidade,
        i.preco_unitario::numeric(10, 2) as preco_unitario,
        
        -- Métrica calculada por linha
        (i.quantidade::integer * i.preco_unitario::numeric(10, 2))::numeric(10, 2) as valor_total_item,
        
        i.updated_at::timestamp as updated_at
    from source_data i
    -- Garante que entram apenas itens de vendas filtradas (status CONCLUIDO)
    inner join silver_vendas v on i.venda_id::integer = v.venda_id
    where i.quantidade::integer > 0 
      and i.preco_unitario::numeric(10, 2) > 0

)

select * from cleaned