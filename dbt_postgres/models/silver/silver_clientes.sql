with source_data as (

    select * from {{ ref('bronze_clientes') }}

),

cleaned as (

    select
        cliente_id::integer as cliente_id,
        
        -- Higienização de Nome
        initcap(trim(nome))::varchar as nome_cliente,
        
        -- Higienização de Email (Caixa Baixa e correção de padrões ruins)
        lower(
            replace(trim(email), ' AT ', '@')
        )::varchar as email,
        
        -- Sanitização de CPF (Remove tudo que não for número)
        regexp_replace(cpf, '[^0-9]', '', 'g')::varchar as cpf,
        
        -- Sanitização de Telefone (Remove tudo que não for número)
        regexp_replace(telefone, '[^0-9]', '', 'g')::varchar as telefone,
        
        -- UF com 2 letras maiúsculas
        upper(trim(estado))::varchar as uf_estado,
        
        data_cadastro::date as data_cadastro,
        data_nascimento::date as data_nascimento,
        
        -- Trata nulos e faz cast para numérico
        coalesce(renda_mensal::numeric(10, 2), 0.00) as renda_mensal,
        
        updated_at::timestamp as updated_at
    from source_data

)

select * from cleaned
--a