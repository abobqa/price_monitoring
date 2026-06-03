select
    product_id,
    history_date,
    min_price,
    max_price,
    avg_price,
    availability_status,
    observations_count,
    avg_price - lag(avg_price) over (
        partition by product_id order by history_date
    ) as avg_price_day_over_day
from {{ source('public', 'price_history') }}
