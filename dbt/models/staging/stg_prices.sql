select
    price_id,
    product_id,
    price,
    coalesce(price_rub, price) as price_rub,
    upper(currency) as currency,
    collected_at::date as collected_date,
    collected_at,
    availability
from {{ source('public', 'prices') }}
