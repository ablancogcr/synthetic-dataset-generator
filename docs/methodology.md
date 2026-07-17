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
- **Seller products:** a deterministic many-to-many marketplace catalog. Every seller and product has
  at least one listing, product listing counts stay within the configured range, and seller-weighted
  assignment gives higher-volume sellers broader catalogs. Listing price equals product base price
  adjusted by seller quality and small log-normal variation.

## Transactions

Purchase dates are sampled from daily weights. All scenarios retain ordinary variation, weekend and
promotion effects, and a Q4 uplift. Each order uses one seller and one or more products from that
seller's catalog, which keeps the order-level shipping record unambiguous. `seller_product_id` is the
authoritative item-level listing reference; duplicated seller and product IDs are validated against
it for analyst-friendly joins.

Item prices vary around seller listing prices and may receive promotion discounts. Shipping uses actual
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
  weight becomes zero and remaining sellers absorb demand. Their historical listings remain in the
  catalog with inactive period-end flags, but cannot receive post-deactivation orders.

The numeric multipliers are configuration, not hidden code, in `config/scenarios.yaml`.

## Dirty-data logic

Dirty mode runs only after the normal in-memory dataset passes clean-source validation. Each defect
category uses a stable random namespace derived from the root seed, and field groups do not overlap,
so changing one defect rate does not move the other categories' targets.

Structural defects are applied first. Missing-day selection removes the chosen dates' orders and all
dependent item, payment, shipping, and review rows while keeping the dates in `calendar.csv`. Empty
orders retain their order, payment, and shipping rows but lose their item rows. Cell defects then add
null text attributes, inconsistent or malformed date strings, non-parsable numeric/boolean tokens,
and negative prices, costs, payment values, and review scores. Derived values are not recalculated,
because the resulting inconsistencies are part of the exercise.

Seller-product relationships are protected in dirty mode. Listing prices, creation dates, and active
flags are eligible for their corresponding configured defect categories, while listing, seller, and
product identifiers remain valid. Missing-day and empty-order defects do not remove catalog rows.

The public dirty-data manifest contains counts only. Private in-memory targets are retained just long
enough to verify that each intended defect survived CSV serialization; exact locations are not
written to disk.

## Validation and limitations

Validation covers schemas, files, keys, listing uniqueness and coverage, order-item/listing
consistency, categories, states, money, date ordering, payment and shipping reconciliation, review
eligibility, scenario fields, listing availability, active states, and seller churn cutoffs.
Dirty runs report those deliberate violations as expected issues while reserving failed status for a
bad clean source, incomplete injection, missing output, or serialization mismatch.

The data is deliberately plausible rather than a statistical replica of the US ecommerce market.
Cities and state weights are simplified; taxes, returns, refunds, inventory, multi-seller shipments,
addresses, and many operational edge cases are outside the MVP. Results must not be interpreted as
real market evidence.
