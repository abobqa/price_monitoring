select
    product_id,
    external_id,
    trim(name) as name,
    lower(trim(category)) as category,
    lower(trim(brand)) as brand,
    lower(trim(source)) as source,
    created_at,
    updated_at
from {{ source('public', 'products') }}
