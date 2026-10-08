{{
    config(
        materialized='incremental',
        unique_key='venda_id',
        on_schema_change='sync_all_columns'
    )
}}

with source_data as (

    select * from {{ ref('bronze_vendas') }}

),

filtered_and_cleaned as (

    select
        venda_id::integer as venda_id,
        cliente_id::integer as cliente_id,
        data_venda::timestamp as data_venda,
        upper(trim(status))::varchar as status,
        updated_at::timestamp as updated_at
    from source_data
    
    where 1=1
    {% if is_incremental() %}
        -- Compara o updated_at convertido
        and updated_at::timestamp > (select max(updated_at) from {{ this }})
    {% endif %}

)

select * from filtered_and_cleaned