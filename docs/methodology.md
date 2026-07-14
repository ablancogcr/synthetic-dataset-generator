# Generation Methodology

## Approach

The generator uses explicit probability distributions and business rules rather than learned models.
Every generator stage receives a stable seed derived from the configured root seed and its namespace.
This makes analytical tables reproducible while keeping modules independent.

All data is synthetic. Geographic names provide a US-like context, but no addresses, people,
companies, brands, transactions, or performance figures describe real activity.

## Dimensions

- **Calendar:** one row per configured date with ISO week, season, weekend, holiday, and promotion flags.
- **Customers:** weighted state geography, behavioral segments, lifecycle stages, and segment-based
  purchase propensity. Repeat purchases reuse the same customer identifier.
- **Sellers:** weighted logistics-hub geography, quality and capacity scores, and Pareto-like selection
  weights that create realistic concentration.
- **Products:** generic category/name combinations with category-specific log-normal price and physical
  attribute distributions.

## Transactions

Purchase dates are sampled from daily weights. All scenarios retain ordinary variation, weekend and
promotion effects, and a Q4 uplift. Each order uses one seller and one or more products, which keeps
the order-level shipping record unambiguous.

Item prices vary around product base prices and may receive promotion discounts. Shipping uses actual
and volumetric weight, seller/customer distance, holiday pressure, and scenario multipliers. Payment
rows can split an order across methods; the final component is adjusted so payments reconcile to the
item-plus-shipping total to the cent.

Fulfillment time depends on route band, seller capacity, holiday pressure, and scenario. Delivered
orders have ordered purchase, approval, carrier, and customer timestamps. Open and cancelled orders
use nullable fulfillment fields. Reviews are sampled only from delivered orders and their score is
driven by delay, seller quality, shipping burden, holiday pressure, and scenario.

## Scenario logic

- `baseline` provides the reference distribution.
- `holiday_spike` increases November/December and selected category weights, shipping cost, transit
  pressure, delay probability, and negative review pressure.
- `logistics_improvement` lowers transit time, cost, and delay probability and raises satisfaction.
- `seller_churn` deactivates the top 5% of sellers 60% through the period. Their post-churn selection
  weight becomes zero and remaining sellers absorb demand.

The numeric multipliers are configuration, not hidden code, in `config/scenarios.yaml`.

## Validation and limitations

Validation covers schemas, files, keys, relationships, categories, states, money, date ordering,
payment and shipping reconciliation, review eligibility, scenario fields, and seller churn cutoffs.

The data is deliberately plausible rather than a statistical replica of the US ecommerce market.
Cities and state weights are simplified; taxes, returns, refunds, inventory, multi-seller shipments,
addresses, and many operational edge cases are outside the MVP. Results must not be interpreted as
real market evidence.

