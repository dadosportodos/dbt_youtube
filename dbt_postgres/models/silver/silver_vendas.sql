{{ config(materialized='view', schema='silver') }}

with source as (
    select * from {{ ref('bronze_vendas') }}
)

select
    venda_id,
    cliente_id,
    cast(data_venda as timestamp) as data_venda,
    lower(status) as status_venda
from source
where status = 'CONCLUIDO'