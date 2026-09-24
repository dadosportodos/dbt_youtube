{{ config(materialized='view', schema='bronze') }}

select * from {{ source('public_raw', 'vendas') }}