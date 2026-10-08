with source_data as (

    select * from {{ ref('bronze_produtos') }}

),

cleaned as (

    select
        produto_id::integer as produto_id,
        initcap(trim(nome_produto))::varchar as nome_produto,
        initcap(trim(categoria))::varchar as categoria,
        preco_base::numeric(10, 2) as preco_base,
        --a
        -- Atributo derivado de faixa de preço
        case 
            when preco_base::numeric(10, 2) < 100 then 'Baixo'
            when preco_base::numeric(10, 2) between 100 and 500 then 'Médio'
            else 'Alto'
        end::varchar as faixa_preco
    from source_data
    where preco_base::numeric(10, 2) > 0

)

select * from cleaned