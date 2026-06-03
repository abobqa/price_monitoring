with joined as (
    select
        p.collected_date,
        pr.category,
        pr.source,
        p.price_rub
    from {{ ref('stg_prices') }} p
    join {{ ref('stg_products') }} pr on pr.product_id = p.product_id
)

select
    collected_date,
    category,
    source,
    round(avg(price_rub)::numeric, 2) as avg_price_rub,
    round(min(price_rub)::numeric, 2) as min_price_rub,
    round(max(price_rub)::numeric, 2) as max_price_rub,
    count(*) as observations
from joined
group by 1, 2, 3
