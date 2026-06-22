# Kalshi API response fields (Predictions REST)

**Generated:** 2026-06-22T22:58:41Z  
**Source:** [https://docs.kalshi.com/openapi.yaml](https://docs.kalshi.com/openapi.yaml)  
**OpenAPI:** Kalshi Trade API Manual Endpoints v3.22.0  
**Scope:** All documented REST response schemas from Kalshi's official Predictions API spec.  
**Mode:** Read-only reference — no trading.

Regenerate:

```bash
python3 ingest/scripts/generate_kalshi_api_fields_doc.py
```

Official docs: [docs.kalshi.com](https://docs.kalshi.com/welcome) · WebSocket fields are in `asyncapi.yaml` (not included here).

---

## KMIA endpoints we use

Console 2 / paper loop primarily calls:

- `GET /events`
- `GET /markets`
- `GET /markets/orderbooks`
- `GET /markets/trades`
- `GET /markets/{ticker}`
- `GET /markets/{ticker}/orderbook`
- `GET /series/{series_ticker}/markets/{ticker}/candlesticks`

---

## Endpoints by tag

### account

#### `POST /account/api_usage_level/upgrade`

Upgrade Account API Usage Level  
_operationId:_ `UpgradeAccountApiUsageLevel`  

_No JSON response schema in OpenAPI for HTTP 200._

#### `GET /account/api_usage_level/volume_progress`

Get Account API Usage Level Volume Progress  
_operationId:_ `GetAccountApiUsageLevelVolumeProgress`  
_200 schema:_ `GetAccountApiUsageLevelVolumeProgressResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `volume_progress` | array | yes | Latest cron-computed trading volume progress toward volume-based API usage tiers for the predictions (event_contract) lane. Volume-based public tiers are Expert, Premier, Paragon, Prime, and Prestige. |
| `volume_progress[].computed_ts` | integer (int64) | yes | Unix timestamp (seconds) when this progress was computed; trailing_30d_volume_fp covers the trailing 30 days ending at this time. |
| `volume_progress[].trailing_30d_volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `volume_progress[].goals` | array | yes |  |
| `volume_progress[].goals[].level` | string | yes | API usage level for this Predictions volume goal. |
| `volume_progress[].goals[].earn_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `volume_progress[].goals[].keep_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


#### `GET /account/endpoint_costs`

List Non-Default Endpoint Costs  
_operationId:_ `GetAccountEndpointCosts`  
_200 schema:_ `GetAccountEndpointCostsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `default_cost` | integer | yes | Default token cost applied to endpoints that are not listed in `endpoint_costs`. This is currently 10. |
| `endpoint_costs` | array | yes | API v2 endpoints whose configured token cost differs from `default_cost`. Endpoints that use the default cost are omitted. |
| `endpoint_costs[].method` | string | yes | HTTP method for the endpoint. |
| `endpoint_costs[].path` | string | yes | API route path for the endpoint. |
| `endpoint_costs[].cost` | integer | yes | Configured token cost for an endpoint whose cost differs from the default cost. |


#### `GET /account/limits`

Get Account API Limits  
_operationId:_ `GetAccountApiLimits`  
_200 schema:_ `GetAccountApiLimitsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `usage_tier` | string | yes | User's effective Predictions API usage tier for these limits (for example, basic, advanced, expert, premier, paragon, prime, or prestige). |
| `read.refill_rate` | integer | yes | Tokens added to the bucket per second. |
| `read.bucket_capacity` | integer | yes | Maximum tokens the bucket can hold. When equal to refill_rate the bucket holds one second of budget; larger values represent burst headroom that idle clients accumulate and can spend in a single pu… |
| `write.refill_rate` | integer | yes | Tokens added to the bucket per second. |
| `write.bucket_capacity` | integer | yes | Maximum tokens the bucket can hold. When equal to refill_rate the bucket holds one second of budget; larger values represent burst headroom that idle clients accumulate and can spend in a single pu… |
| `grants` | array | yes | The caller's active API usage level grants across exchange lanes, where each grant applies to its exchange_instance and usage_tier reflects the effective tier for the lane reported by this endpoint. |
| `grants[].exchange_instance` | enum(event_contract, margined) | yes | The exchange instance type |
| `grants[].level` | string | yes | API usage level this grant confers (for example, expert, premier, paragon, prime, or prestige). |
| `grants[].expires_ts` | integer (int64) | null |  | Unix timestamp (seconds) when the grant expires. Absent for permanent grants. |
| `grants[].source` | string | yes | How the grant was created: "volume" (earned from trading volume) or "manual" (assigned by Kalshi). |


### api-keys

#### `GET /api_keys`

Get API Keys  
_operationId:_ `GetApiKeys`  
_200 schema:_ `GetApiKeysResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_keys` | array | yes | List of all API keys associated with the user |
| `api_keys[].api_key_id` | string | yes | Unique identifier for the API key |
| `api_keys[].name` | string | yes | User-provided name for the API key |
| `api_keys[].scopes` | array | yes | List of scopes granted to this API key. |
| `api_keys[].scopes[]` | enum(read, write, read::block_trade_accept, read::portfolio_balance, write::transfer, write::block_trade_accept) |  | Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`,… |


#### `POST /api_keys`

Create API Key  
_operationId:_ `CreateApiKey`  
_200 schema:_ `CreateApiKeyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | yes | Unique identifier for the newly created API key |


#### `POST /api_keys/generate`

Generate API Key  
_operationId:_ `GenerateApiKey`  
_200 schema:_ `GenerateApiKeyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | yes | Unique identifier for the newly generated API key |
| `private_key` | string | yes | RSA private key in PEM format. This must be stored securely and cannot be retrieved again after this response |


#### `DELETE /api_keys/{api_key}`

Delete API Key  
_operationId:_ `DeleteApiKey`  

_No JSON response schema in OpenAPI for HTTP 200._

### communications

#### `GET /communications/block-trade-proposals`

Get Block Trade Proposals  
_operationId:_ `GetBlockTradeProposals`  
_200 schema:_ `GetBlockTradeProposalsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_trade_proposals` | array | yes | List of block trade proposals |
| `block_trade_proposals[].id` | string | yes | Unique identifier for the block trade proposal |
| `block_trade_proposals[].proposer_user_id` | string | yes | User ID of the proposal creator |
| `block_trade_proposals[].buyer_user_id` | string | yes | User ID of the buyer. Empty when the authenticated user is not the buyer. |
| `block_trade_proposals[].buyer_subtrader_id` | string |  | Subtrader ID of the buyer. Empty when the authenticated user is not the buyer. |
| `block_trade_proposals[].seller_user_id` | string | yes | User ID of the seller. Empty when the authenticated user is not the seller. |
| `block_trade_proposals[].seller_subtrader_id` | string |  | Subtrader ID of the seller. Empty when the authenticated user is not the seller. |
| `block_trade_proposals[].market_ticker` | string | yes | The ticker of the market for this block trade |
| `block_trade_proposals[].price_centi_cents` | integer (int64) | yes | Price in centi-cents |
| `block_trade_proposals[].centicount` | integer (int64) | yes | Number of contracts in centicounts |
| `block_trade_proposals[].maker_side` | enum(yes, no) | yes | The maker side of the trade |
| `block_trade_proposals[].expiration_ts` | string (date-time) | yes | Expiration time of the proposal |
| `block_trade_proposals[].status` | string | yes | Current status of the proposal |
| `block_trade_proposals[].created_ts` | string (date-time) | yes | Timestamp when the proposal was created |
| `block_trade_proposals[].updated_ts` | string (date-time) | yes | Timestamp when the proposal was last updated |
| `block_trade_proposals[].buyer_accepted` | boolean | yes | Whether the buyer has accepted the proposal |
| `block_trade_proposals[].seller_accepted` | boolean | yes | Whether the seller has accepted the proposal |
| `block_trade_proposals[].buyer_accepted_ts` | string (date-time) |  | Timestamp when the buyer accepted |
| `block_trade_proposals[].seller_accepted_ts` | string (date-time) |  | Timestamp when the seller accepted |
| `block_trade_proposals[].executed_ts` | string (date-time) |  | Timestamp when the proposal was executed |
| `block_trade_proposals[].buyer_order_id` | string |  | Order ID for the buyer after the proposal is executed |
| `block_trade_proposals[].seller_order_id` | string |  | Order ID for the seller after the proposal is executed |
| `cursor` | string |  | Cursor for pagination to get the next page of results |


#### `POST /communications/block-trade-proposals`

Propose Block Trade  
_operationId:_ `ProposeBlockTrade`  
_200 schema:_ `ProposeBlockTradeResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_trade_proposal_id` | string | yes | The ID of the newly created block trade proposal |


#### `POST /communications/block-trade-proposals/{block_trade_proposal_id}/accept`

Accept Block Trade Proposal  
_operationId:_ `AcceptBlockTradeProposal`  

_No JSON response schema in OpenAPI for HTTP 200._

#### `GET /communications/id`

Get Communications ID  
_operationId:_ `GetCommunicationsID`  
_200 schema:_ `GetCommunicationsIDResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `communications_id` | string | yes | A public communications ID which is used to identify the user |


#### `GET /communications/quotes`

Get Quotes  
_operationId:_ `GetQuotes`  
_200 schema:_ `GetQuotesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quotes` | array | yes | List of quotes matching the query criteria |
| `quotes[].id` | string | yes | Unique identifier for the quote |
| `quotes[].rfq_id` | string | yes | ID of the RFQ this quote is responding to |
| `quotes[].creator_id` | string | yes | Public communications ID of the quote creator |
| `quotes[].rfq_creator_id` | string | yes | Public communications ID of the RFQ creator |
| `quotes[].market_ticker` | string | yes | The ticker of the market this quote is for |
| `quotes[].contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quotes[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quotes[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quotes[].created_ts` | string (date-time) | yes | Timestamp when the quote was created |
| `quotes[].updated_ts` | string (date-time) | yes | Timestamp when the quote was last updated |
| `quotes[].status` | enum(open, accepted, confirmed, executed, cancelled) | yes | Current status of the quote |
| `quotes[].accepted_side` | enum(yes, no) |  | The side that was accepted (yes or no) |
| `quotes[].accepted_ts` | string (date-time) |  | Timestamp when the quote was accepted |
| `quotes[].confirmed_ts` | string (date-time) |  | Timestamp when the quote was confirmed |
| `quotes[].executed_ts` | string (date-time) |  | Timestamp when the quote was executed |
| `quotes[].cancelled_ts` | string (date-time) |  | Timestamp when the quote was cancelled |
| `quotes[].rest_remainder` | boolean |  | Whether to rest the remainder of the quote after execution |
| `quotes[].post_only` | boolean |  | Whether the quote creator's order is post-only (visible when the caller is the quote creator) |
| `quotes[].cancellation_reason` | string |  | Reason for quote cancellation if cancelled |
| `quotes[].creator_user_id` | string |  | User ID of the quote creator (private field) |
| `quotes[].rfq_creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `quotes[].rfq_target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quotes[].rfq_creator_order_id` | string |  | Order ID for the RFQ creator (private field) |
| `quotes[].creator_order_id` | string |  | Order ID for the quote creator (private field) |
| `quotes[].creator_subaccount` | integer |  | Subaccount number of the quote creator (visible when the caller is the quote creator) |
| `quotes[].rfq_creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `quotes[].yes_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quotes[].no_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `cursor` | string |  | Cursor for pagination to get the next page of results |


#### `POST /communications/quotes`

Create Quote  
_operationId:_ `CreateQuote`  
_200 schema:_ `CreateQuoteResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | The ID of the newly created quote |


#### `GET /communications/quotes/{quote_id}`

Get Quote  
_operationId:_ `GetQuote`  
_200 schema:_ `GetQuoteResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quote.id` | string | yes | Unique identifier for the quote |
| `quote.rfq_id` | string | yes | ID of the RFQ this quote is responding to |
| `quote.creator_id` | string | yes | Public communications ID of the quote creator |
| `quote.rfq_creator_id` | string | yes | Public communications ID of the RFQ creator |
| `quote.market_ticker` | string | yes | The ticker of the market this quote is for |
| `quote.contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quote.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quote.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quote.created_ts` | string (date-time) | yes | Timestamp when the quote was created |
| `quote.updated_ts` | string (date-time) | yes | Timestamp when the quote was last updated |
| `quote.status` | enum(open, accepted, confirmed, executed, cancelled) | yes | Current status of the quote |
| `quote.accepted_side` | enum(yes, no) |  | The side that was accepted (yes or no) |
| `quote.accepted_ts` | string (date-time) |  | Timestamp when the quote was accepted |
| `quote.confirmed_ts` | string (date-time) |  | Timestamp when the quote was confirmed |
| `quote.executed_ts` | string (date-time) |  | Timestamp when the quote was executed |
| `quote.cancelled_ts` | string (date-time) |  | Timestamp when the quote was cancelled |
| `quote.rest_remainder` | boolean |  | Whether to rest the remainder of the quote after execution |
| `quote.post_only` | boolean |  | Whether the quote creator's order is post-only (visible when the caller is the quote creator) |
| `quote.cancellation_reason` | string |  | Reason for quote cancellation if cancelled |
| `quote.creator_user_id` | string |  | User ID of the quote creator (private field) |
| `quote.rfq_creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `quote.rfq_target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quote.rfq_creator_order_id` | string |  | Order ID for the RFQ creator (private field) |
| `quote.creator_order_id` | string |  | Order ID for the quote creator (private field) |
| `quote.creator_subaccount` | integer |  | Subaccount number of the quote creator (visible when the caller is the quote creator) |
| `quote.rfq_creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `quote.yes_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quote.no_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


#### `DELETE /communications/quotes/{quote_id}`

Delete Quote  
_operationId:_ `DeleteQuote`  

_No JSON response schema in OpenAPI for HTTP 200._

#### `PUT /communications/quotes/{quote_id}/accept`

Accept Quote  
_operationId:_ `AcceptQuote`  

_No JSON response schema in OpenAPI for HTTP 200._

#### `PUT /communications/quotes/{quote_id}/confirm`

Confirm Quote  
_operationId:_ `ConfirmQuote`  

_No JSON response schema in OpenAPI for HTTP 200._

#### `GET /communications/rfqs`

Get RFQs  
_operationId:_ `GetRFQs`  
_200 schema:_ `GetRFQsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rfqs` | array | yes | List of RFQs matching the query criteria |
| `rfqs[].id` | string | yes | Unique identifier for the RFQ |
| `rfqs[].creator_id` | string | yes | Public communications ID of the RFQ creator. |
| `rfqs[].market_ticker` | string | yes | The ticker of the market this RFQ is for |
| `rfqs[].contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `rfqs[].target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfqs[].status` | enum(open, closed) | yes | Current status of the RFQ (open, closed) |
| `rfqs[].created_ts` | string (date-time) | yes | Timestamp when the RFQ was created |
| `rfqs[].mve_collection_ticker` | string |  | Ticker of the MVE collection this market belongs to |
| `rfqs[].mve_selected_legs` | array |  | Selected legs for the MVE collection |
| `rfqs[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `rfqs[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `rfqs[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `rfqs[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfqs[].rest_remainder` | boolean |  | Whether to rest the remainder of the RFQ after execution |
| `rfqs[].cancellation_reason` | string |  | Reason for RFQ cancellation if cancelled |
| `rfqs[].creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `rfqs[].creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `rfqs[].cancelled_ts` | string (date-time) |  | Timestamp when the RFQ was cancelled |
| `rfqs[].updated_ts` | string (date-time) |  | Timestamp when the RFQ was last updated |
| `cursor` | string |  | Cursor for pagination to get the next page of results |


#### `POST /communications/rfqs`

Create RFQ  
_operationId:_ `CreateRFQ`  
_200 schema:_ `CreateRFQResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | The ID of the newly created RFQ |


#### `GET /communications/rfqs/{rfq_id}`

Get RFQ  
_operationId:_ `GetRFQ`  
_200 schema:_ `GetRFQResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rfq.id` | string | yes | Unique identifier for the RFQ |
| `rfq.creator_id` | string | yes | Public communications ID of the RFQ creator. |
| `rfq.market_ticker` | string | yes | The ticker of the market this RFQ is for |
| `rfq.contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `rfq.target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfq.status` | enum(open, closed) | yes | Current status of the RFQ (open, closed) |
| `rfq.created_ts` | string (date-time) | yes | Timestamp when the RFQ was created |
| `rfq.mve_collection_ticker` | string |  | Ticker of the MVE collection this market belongs to |
| `rfq.mve_selected_legs` | array |  | Selected legs for the MVE collection |
| `rfq.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `rfq.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `rfq.mve_selected_legs[].side` | string |  | The side of the selected market |
| `rfq.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfq.rest_remainder` | boolean |  | Whether to rest the remainder of the RFQ after execution |
| `rfq.cancellation_reason` | string |  | Reason for RFQ cancellation if cancelled |
| `rfq.creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `rfq.creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `rfq.cancelled_ts` | string (date-time) |  | Timestamp when the RFQ was cancelled |
| `rfq.updated_ts` | string (date-time) |  | Timestamp when the RFQ was last updated |


#### `DELETE /communications/rfqs/{rfq_id}`

Delete RFQ  
_operationId:_ `DeleteRFQ`  

_No JSON response schema in OpenAPI for HTTP 200._

### events

#### `GET /events` **← KMIA**

Get Events  
_operationId:_ `GetEvents`  
_200 schema:_ `GetEventsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `events` | array | yes | Array of events matching the query criteria. |
| `events[].event_ticker` | string | yes | Unique identifier for this event. |
| `events[].series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `events[].sub_title` | string | yes | Shortened descriptive title for the event. |
| `events[].title` | string | yes | Full title of the event. |
| `events[].collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `events[].mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `events[].category` | string |  | Event category (deprecated, use series-level category instead). |
| `events[].strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `events[].strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `events[].markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `events[].markets[].ticker` | string | yes |  |
| `events[].markets[].event_ticker` | string | yes |  |
| `events[].markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `events[].markets[].title` | string |  |  |
| `events[].markets[].subtitle` | string |  |  |
| `events[].markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `events[].markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `events[].markets[].created_time` | string (date-time) | yes |  |
| `events[].markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `events[].markets[].open_time` | string (date-time) | yes |  |
| `events[].markets[].close_time` | string (date-time) | yes |  |
| `events[].markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `events[].markets[].expiration_time` | string (date-time) |  |  |
| `events[].markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `events[].markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `events[].markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `events[].markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `events[].markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `events[].markets[].can_close_early` | boolean | yes |  |
| `events[].markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `events[].markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `events[].markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `events[].markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `events[].markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `events[].markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `events[].markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `events[].markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `events[].markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `events[].markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `events[].markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `events[].markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `events[].markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `events[].markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `events[].markets[].mve_selected_legs` | array |  |  |
| `events[].markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `events[].markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `events[].markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `events[].markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].primary_participant_key` | string | null |  |  |
| `events[].markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `events[].markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `events[].markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `events[].markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `events[].markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `events[].markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `events[].markets[].exchange_index` | object |  |  |
| `events[].available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `events[].product_metadata` | object | null |  | Additional metadata for the event. |
| `events[].settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `events[].settlement_sources[].name` | string |  | Name of the settlement source |
| `events[].settlement_sources[].url` | string |  | URL to the settlement source |
| `events[].last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `events[].fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |

_…and 19 more fields (see schema appendix)._


#### `GET /events/fee_changes`

Get Event Fee Changes  
_operationId:_ `GetEventFeeChanges`  
_200 schema:_ `GetEventFeeChangesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_fee_changes` | array | yes |  |
| `event_fee_changes[].id` | string | yes | Unique identifier for this fee change |
| `event_fee_changes[].event_ticker` | string | yes | Event ticker this fee change applies to |
| `event_fee_changes[].series_ticker` | string | yes | Series ticker for the event |
| `event_fee_changes[].fee_type_override` | object | null | yes | New fee type override for the event. When null, the event clears any prior override and falls back to the parent series' fee structure. |
| `event_fee_changes[].fee_multiplier_override` | number (double) | null | yes | New fee multiplier override for the event. When null, the event clears any prior override and falls back to the parent series' fee multiplier. |
| `event_fee_changes[].scheduled_ts` | string (date-time) | yes | Timestamp when this fee change is scheduled to take effect |
| `cursor` | string | yes | Pagination cursor for the next page. Empty if there are no more results. |


#### `GET /events/multivariate`

Get Multivariate Events  
_operationId:_ `GetMultivariateEvents`  
_200 schema:_ `GetMultivariateEventsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `events` | array | yes | Array of multivariate events matching the query criteria. |
| `events[].event_ticker` | string | yes | Unique identifier for this event. |
| `events[].series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `events[].sub_title` | string | yes | Shortened descriptive title for the event. |
| `events[].title` | string | yes | Full title of the event. |
| `events[].collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `events[].mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `events[].category` | string |  | Event category (deprecated, use series-level category instead). |
| `events[].strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `events[].strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `events[].markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `events[].markets[].ticker` | string | yes |  |
| `events[].markets[].event_ticker` | string | yes |  |
| `events[].markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `events[].markets[].title` | string |  |  |
| `events[].markets[].subtitle` | string |  |  |
| `events[].markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `events[].markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `events[].markets[].created_time` | string (date-time) | yes |  |
| `events[].markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `events[].markets[].open_time` | string (date-time) | yes |  |
| `events[].markets[].close_time` | string (date-time) | yes |  |
| `events[].markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `events[].markets[].expiration_time` | string (date-time) |  |  |
| `events[].markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `events[].markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `events[].markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `events[].markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `events[].markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `events[].markets[].can_close_early` | boolean | yes |  |
| `events[].markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `events[].markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `events[].markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `events[].markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `events[].markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `events[].markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `events[].markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `events[].markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `events[].markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `events[].markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `events[].markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `events[].markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `events[].markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `events[].markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `events[].markets[].mve_selected_legs` | array |  |  |
| `events[].markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `events[].markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `events[].markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `events[].markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].primary_participant_key` | string | null |  |  |
| `events[].markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `events[].markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `events[].markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `events[].markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `events[].markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `events[].markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `events[].markets[].exchange_index` | object |  |  |
| `events[].available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `events[].product_metadata` | object | null |  | Additional metadata for the event. |
| `events[].settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `events[].settlement_sources[].name` | string |  | Name of the settlement source |
| `events[].settlement_sources[].url` | string |  | URL to the settlement source |
| `events[].last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `events[].fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |

_…and 3 more fields (see schema appendix)._


#### `GET /events/{event_ticker}`

Get Event  
_operationId:_ `GetEvent`  
_200 schema:_ `GetEventResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event.event_ticker` | string | yes | Unique identifier for this event. |
| `event.series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `event.sub_title` | string | yes | Shortened descriptive title for the event. |
| `event.title` | string | yes | Full title of the event. |
| `event.collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `event.mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `event.category` | string |  | Event category (deprecated, use series-level category instead). |
| `event.strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `event.strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `event.markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `event.markets[].ticker` | string | yes |  |
| `event.markets[].event_ticker` | string | yes |  |
| `event.markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `event.markets[].title` | string |  |  |
| `event.markets[].subtitle` | string |  |  |
| `event.markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `event.markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `event.markets[].created_time` | string (date-time) | yes |  |
| `event.markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `event.markets[].open_time` | string (date-time) | yes |  |
| `event.markets[].close_time` | string (date-time) | yes |  |
| `event.markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `event.markets[].expiration_time` | string (date-time) |  |  |
| `event.markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `event.markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `event.markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `event.markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `event.markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `event.markets[].can_close_early` | boolean | yes |  |
| `event.markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `event.markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `event.markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `event.markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `event.markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `event.markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `event.markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `event.markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `event.markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `event.markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `event.markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `event.markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `event.markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `event.markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `event.markets[].mve_selected_legs` | array |  |  |
| `event.markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `event.markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `event.markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `event.markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].primary_participant_key` | string | null |  |  |
| `event.markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `event.markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `event.markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `event.markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `event.markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `event.markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `event.markets[].exchange_index` | object |  |  |
| `event.available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `event.product_metadata` | object | null |  | Additional metadata for the event. |
| `event.settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `event.settlement_sources[].name` | string |  | Name of the settlement source |
| `event.settlement_sources[].url` | string |  | URL to the settlement source |
| `event.last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `event.fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |
| `event.fee_multiplier_override` | number (double) | null |  | Fee multiplier override for this event. Paired with fee_type_override. |

_…and 64 more fields (see schema appendix)._


#### `GET /events/{event_ticker}/metadata`

Get Event Metadata  
_operationId:_ `GetEventMetadata`  
_200 schema:_ `GetEventMetadataResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_url` | string | yes | A path to an image that represents this event. |
| `featured_image_url` | string |  | A path to an image that represents the image of the featured market. |
| `market_details` | array | yes | Metadata for the markets in this event. |
| `market_details[].market_ticker` | string | yes | The ticker of the market. |
| `market_details[].image_url` | string | yes | A path to an image that represents this market. |
| `market_details[].color_code` | string | yes | The color code for the market. |
| `settlement_sources` | array | yes | A list of settlement sources for this event. |
| `settlement_sources[].name` | string |  | Name of the settlement source |
| `settlement_sources[].url` | string |  | URL to the settlement source |
| `competition` | string | null |  | Event competition. |
| `competition_scope` | string | null |  | Event scope, based on the competition. |


#### `GET /series/{series_ticker}/events/{ticker}/candlesticks`

Get Event Candlesticks  
_operationId:_ `GetMarketCandlesticksByEvent`  
_200 schema:_ `GetEventCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_tickers` | array | yes | Array of market tickers in the event. |
| `market_tickers[]` | string |  |  |
| `market_candlesticks` | array | yes | Array of market candlestick arrays, one for each market in the event. |
| `market_candlesticks[][]` | array |  |  |
| `market_candlesticks[][].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `market_candlesticks[][].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market_candlesticks[][].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `adjusted_end_ts` | integer (int64) | yes | Adjusted end timestamp if the requested candlesticks would be larger than maxAggregateCandidates. |


#### `GET /series/{series_ticker}/events/{ticker}/forecast_percentile_history`

Get Event Forecast Percentile History  
_operationId:_ `GetEventForecastPercentilesHistory`  
_200 schema:_ `GetEventForecastPercentilesHistoryResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `forecast_history` | array | yes | Array of forecast percentile data points over time. |
| `forecast_history[].event_ticker` | string | yes | The event ticker this forecast is for. |
| `forecast_history[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the forecast period. |
| `forecast_history[].period_interval` | integer (int32) | yes | Length of the forecast period in minutes. |
| `forecast_history[].percentile_points` | array | yes | Array of forecast values at different percentiles. |
| `forecast_history[].percentile_points[].percentile` | integer (int32) | yes | The percentile value (0-9999). |
| `forecast_history[].percentile_points[].raw_numerical_forecast` | number | yes | The raw numerical forecast value. |
| `forecast_history[].percentile_points[].numerical_forecast` | number | yes | The processed numerical forecast value. |
| `forecast_history[].percentile_points[].formatted_forecast` | string | yes | The human-readable formatted forecast value. |


### exchange

#### `GET /exchange/announcements`

Get Exchange Announcements  
_operationId:_ `GetExchangeAnnouncements`  
_200 schema:_ `GetExchangeAnnouncementsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `announcements` | array | yes | A list of exchange-wide announcements. |
| `announcements[].type` | enum(info, warning, error) | yes | The type of the announcement. |
| `announcements[].message` | string | yes | The message contained within the announcement. |
| `announcements[].delivery_time` | string (date-time) | yes | The time the announcement was delivered. |
| `announcements[].status` | enum(active, inactive) | yes | The current status of this announcement. |


#### `GET /exchange/schedule`

Get Exchange Schedule  
_operationId:_ `GetExchangeSchedule`  
_200 schema:_ `GetExchangeScheduleResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schedule.standard_hours` | array | yes | The standard operating hours of the exchange. All times are expressed in ET. Outside of these times trading will be unavailable. |
| `schedule.standard_hours[].start_time` | string (date-time) | yes | Start date and time for when this weekly schedule is effective. |
| `schedule.standard_hours[].end_time` | string (date-time) | yes | End date and time for when this weekly schedule is no longer effective. |
| `schedule.standard_hours[].monday` | array | yes | Trading hours for Monday. May contain multiple sessions. |
| `schedule.standard_hours[].monday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].monday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].tuesday` | array | yes | Trading hours for Tuesday. May contain multiple sessions. |
| `schedule.standard_hours[].tuesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].tuesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].wednesday` | array | yes | Trading hours for Wednesday. May contain multiple sessions. |
| `schedule.standard_hours[].wednesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].wednesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].thursday` | array | yes | Trading hours for Thursday. May contain multiple sessions. |
| `schedule.standard_hours[].thursday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].thursday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].friday` | array | yes | Trading hours for Friday. May contain multiple sessions. |
| `schedule.standard_hours[].friday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].friday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].saturday` | array | yes | Trading hours for Saturday. May contain multiple sessions. |
| `schedule.standard_hours[].saturday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].saturday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].sunday` | array | yes | Trading hours for Sunday. May contain multiple sessions. |
| `schedule.standard_hours[].sunday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].sunday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.maintenance_windows` | array | yes | Scheduled maintenance windows, during which the exchange may be unavailable. |
| `schedule.maintenance_windows[].start_datetime` | string (date-time) | yes | Start date and time of the maintenance window. |
| `schedule.maintenance_windows[].end_datetime` | string (date-time) | yes | End date and time of the maintenance window. |


#### `GET /exchange/status`

Get Exchange Status  
_operationId:_ `GetExchangeStatus`  
_200 schema:_ `ExchangeStatus`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `exchange_active` | boolean | yes | False if the core Kalshi exchange is no longer taking any state changes at all. This includes but is not limited to trading, new users, and transfers. True unless we are under maintenance. |
| `trading_active` | boolean | yes | True if we are currently permitting trading on the exchange. This is true during trading hours and false outside exchange hours. Kalshi reserves the right to pause at any time in case issues are de… |
| `exchange_estimated_resume_time` | string (date-time) | null |  | Estimated downtime for the current exchange maintenance window. However, this is not guaranteed and can be extended. |


#### `GET /exchange/user_data_timestamp`

Get User Data Timestamp  
_operationId:_ `GetUserDataTimestamp`  
_200 schema:_ `GetUserDataTimestampResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `as_of_time` | string (date-time) | yes | Timestamp when user data was last updated. |


#### `GET /series/fee_changes`

Get Series Fee Changes  
_operationId:_ `GetSeriesFeeChanges`  
_200 schema:_ `GetSeriesFeeChangesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series_fee_change_arr` | array | yes |  |
| `series_fee_change_arr[].id` | string | yes | Unique identifier for this fee change |
| `series_fee_change_arr[].series_ticker` | string | yes | Series ticker this fee change applies to |
| `series_fee_change_arr[].fee_type` | object | yes | New fee type for the series |
| `series_fee_change_arr[].fee_multiplier` | number (double) | yes | New fee multiplier for the series |
| `series_fee_change_arr[].scheduled_ts` | string (date-time) | yes | Timestamp when this fee change is scheduled to take effect |


### fcm

#### `GET /fcm/orders`

Get FCM Orders  
_operationId:_ `GetFCMOrders`  
_200 schema:_ `GetOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes |  |
| `orders[].user_id` | string | yes | Unique identifier for users |
| `orders[].client_order_id` | string | yes |  |
| `orders[].ticker` | string | yes |  |
| `orders[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].type` | enum(limit, market) | yes |  |
| `orders[].status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].expiration_time` | string (date-time) | null |  |  |
| `orders[].created_time` | string (date-time) | null |  |  |
| `orders[].last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order_group_id` | string | null |  | The order group this order is part of |
| `orders[].cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


#### `GET /fcm/positions`

Get FCM Positions  
_operationId:_ `GetFCMPositions`  
_200 schema:_ `GetPositionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cursor` | string |  | The Cursor represents a pointer to the next page of records in the pagination. Use the value returned here in the cursor query parameter for this end-point to get the next page containing limit rec… |
| `market_positions` | array | yes | List of market positions |
| `market_positions[].ticker` | string | yes | Unique identifier for the market |
| `market_positions[].total_traded_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market_positions[].market_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].resting_orders_count` | integer (int32) | yes | [DEPRECATED] Aggregate size of resting orders in contract units |
| `market_positions[].fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].last_updated_ts` | string (date-time) | yes | Last time the position is updated |
| `event_positions` | array | yes | List of event positions |
| `event_positions[].event_ticker` | string | yes | Unique identifier for events |
| `event_positions[].total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].total_cost_shares_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event_positions[].event_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### historical

#### `GET /historical/cutoff`

Get Historical Cutoff Timestamps  
_operationId:_ `GetHistoricalCutoff`  
_200 schema:_ `GetHistoricalCutoffResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_settled_ts` | string (date-time) | yes | Cutoff based on **market settlement time**. Markets and their candlesticks that settled before this timestamp must be accessed via `GET /historical/markets` and `GET /historical/markets/{ticker}/ca… |
| `trades_created_ts` | string (date-time) | yes | Cutoff based on **trade fill time**. Fills that occurred before this timestamp must be accessed via `GET /historical/fills`. |
| `orders_updated_ts` | string (date-time) | yes | Cutoff based on **order cancellation or execution time**. Orders canceled or fully executed before this timestamp must be accessed via `GET /historical/orders`. Resting (active) orders are always a… |


#### `GET /historical/fills`

Get Historical Fills  
_operationId:_ `GetFillsHistorical`  
_200 schema:_ `GetFillsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fills` | array | yes |  |
| `fills[].fill_id` | string | yes | Unique identifier for this fill |
| `fills[].trade_id` | string | yes | Unique identifier for this fill (legacy field name, same as fill_id) |
| `fills[].order_id` | string | yes | Unique identifier for the order that resulted in this fill |
| `fills[].ticker` | string | yes | Unique identifier for the market |
| `fills[].market_ticker` | string | yes | Unique identifier for the market (legacy field name, same as ticker) |
| `fills[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `fills[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `fills[].outcome_side` | enum(yes, no) | yes | The outcome side this fill positioned the user for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the … |
| `fills[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `fills[].count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `fills[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].is_taker` | boolean | yes | If true, this fill was a taker (removed liquidity from the order book) |
| `fills[].created_time` | string (date-time) |  | Timestamp when this fill was executed |
| `fills[].fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). Present for direct users. |
| `fills[].ts` | integer (int64) |  | Unix timestamp when this fill was executed (legacy field name) |
| `cursor` | string | yes |  |


#### `GET /historical/markets`

Get Historical Markets  
_operationId:_ `GetHistoricalMarkets`  
_200 schema:_ `GetMarketsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markets` | array | yes |  |
| `markets[].ticker` | string | yes |  |
| `markets[].event_ticker` | string | yes |  |
| `markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `markets[].title` | string |  |  |
| `markets[].subtitle` | string |  |  |
| `markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `markets[].created_time` | string (date-time) | yes |  |
| `markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `markets[].open_time` | string (date-time) | yes |  |
| `markets[].close_time` | string (date-time) | yes |  |
| `markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `markets[].expiration_time` | string (date-time) |  |  |
| `markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `markets[].can_close_early` | boolean | yes |  |
| `markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `markets[].mve_selected_legs` | array |  |  |
| `markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].primary_participant_key` | string | null |  |  |
| `markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `markets[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


#### `GET /historical/markets/{ticker}`

Get Historical Market  
_operationId:_ `GetHistoricalMarket`  
_200 schema:_ `GetMarketResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market.ticker` | string | yes |  |
| `market.event_ticker` | string | yes |  |
| `market.market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `market.title` | string |  |  |
| `market.subtitle` | string |  |  |
| `market.yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `market.no_sub_title` | string | yes | Shortened title for the no side of this market |
| `market.created_time` | string (date-time) | yes |  |
| `market.updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `market.open_time` | string (date-time) | yes |  |
| `market.close_time` | string (date-time) | yes |  |
| `market.expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `market.expiration_time` | string (date-time) |  |  |
| `market.latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `market.settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `market.status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `market.response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `market.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.result` | enum(yes, no, scalar, ) | yes |  |
| `market.can_close_early` | boolean | yes |  |
| `market.fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `market.open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `market.expiration_value` | string | yes | The value that was considered for the settlement |
| `market.occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `market.fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `market.early_close_condition` | string | null |  | The condition under which the market can close early |
| `market.strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `market.floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `market.cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `market.functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `market.custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `market.rules_primary` | string | yes | A plain language description of the most important market terms |
| `market.rules_secondary` | string | yes | A plain language description of secondary market terms |
| `market.mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `market.mve_selected_legs` | array |  |  |
| `market.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `market.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `market.mve_selected_legs[].side` | string |  | The side of the selected market |
| `market.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.primary_participant_key` | string | null |  |  |
| `market.price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `market.price_ranges` | array | yes | Valid price ranges for orders on this market |
| `market.price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `market.price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `market.price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `market.is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `market.exchange_index` | object |  |  |


#### `GET /historical/markets/{ticker}/candlesticks`

Get Historical Market Candlesticks  
_operationId:_ `GetMarketCandlesticksHistorical`  
_200 schema:_ `GetMarketCandlesticksHistoricalResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Unique identifier for the market. |
| `candlesticks` | array | yes | Array of candlestick data points for the specified time range. |
| `candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `candlesticks[].yes_bid.open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.open` | object | null | yes | Price of the first trade during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.low` | object | null | yes | Lowest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.high` | object | null | yes | Highest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.close` | object | null | yes | Price of the last trade during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.mean` | object | null | yes | Volume-weighted average price during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.previous` | object | null | yes | Close price from the previous candlestick period (in dollars). Null if this is the first candlestick or no prior trade exists. |
| `candlesticks[].volume` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `candlesticks[].open_interest` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


#### `GET /historical/orders`

Get Historical Orders  
_operationId:_ `GetHistoricalOrders`  
_200 schema:_ `GetOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes |  |
| `orders[].user_id` | string | yes | Unique identifier for users |
| `orders[].client_order_id` | string | yes |  |
| `orders[].ticker` | string | yes |  |
| `orders[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].type` | enum(limit, market) | yes |  |
| `orders[].status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].expiration_time` | string (date-time) | null |  |  |
| `orders[].created_time` | string (date-time) | null |  |  |
| `orders[].last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order_group_id` | string | null |  | The order group this order is part of |
| `orders[].cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


#### `GET /historical/trades`

Get Historical Trades  
_operationId:_ `GetTradesHistorical`  
_200 schema:_ `GetTradesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trades` | array | yes |  |
| `trades[].trade_id` | string | yes | Unique identifier for this trade |
| `trades[].ticker` | string | yes | Unique identifier for the market |
| `trades[].count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `trades[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `trades[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `trades[].taker_side` | enum(yes, no) | yes | Deprecated. Use `taker_outcome_side` (or `taker_book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `trades[].taker_outcome_side` | enum(yes, no) | yes | The outcome side the taker is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `taker_outcome_side` describes directional exposure only; it does not change the … |
| `trades[].taker_book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `trades[].created_time` | string (date-time) | yes | Timestamp when this trade was executed |
| `trades[].is_block_trade` | boolean | yes | True if this trade was matched off-book as a block trade (e.g. via RFQ / negotiated block proposal); false for trades that filled on the standard order book. |
| `cursor` | string | yes |  |


### incentive-programs

#### `GET /incentive_programs`

Get Incentives  
_operationId:_ `GetIncentivePrograms`  
_200 schema:_ `GetIncentiveProgramsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `incentive_programs` | array | yes |  |
| `incentive_programs[].id` | string | yes | Unique identifier for the incentive program |
| `incentive_programs[].market_id` | string | yes | The unique identifier of the market associated with this incentive program |
| `incentive_programs[].market_ticker` | string | yes | The ticker symbol of the market associated with this incentive program |
| `incentive_programs[].incentive_type` | enum(liquidity, volume) | yes | Type of incentive program |
| `incentive_programs[].incentive_description` | string | yes | Plain text description of the incentive program |
| `incentive_programs[].start_date` | string (date-time) | yes | Start date of the incentive program |
| `incentive_programs[].end_date` | string (date-time) | yes | End date of the incentive program |
| `incentive_programs[].period_reward` | integer (int64) | yes | Total reward for the period in centi-cents |
| `incentive_programs[].paid_out` | boolean | yes | Whether the incentive has been paid out |
| `incentive_programs[].discount_factor_bps` | integer (int32) | null |  | Discount factor in basis points (optional) |
| `incentive_programs[].target_size_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `next_cursor` | string |  | Cursor for pagination to get the next page of results |


### live-data

#### `GET /live_data/batch`

Get Multiple Live Data  
_operationId:_ `GetLiveDatas`  
_200 schema:_ `GetLiveDatasResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `live_datas` | array | yes |  |
| `live_datas[].type` | string | yes | Type of live data |
| `live_datas[].details` | object | yes | Live data details as a flexible object |
| `live_datas[].milestone_id` | string | yes | Milestone ID |


#### `GET /live_data/milestone/{milestone_id}`

Get Live Data  
_operationId:_ `GetLiveDataByMilestone`  
_200 schema:_ `GetLiveDataResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `live_data.type` | string | yes | Type of live data |
| `live_data.details` | object | yes | Live data details as a flexible object |
| `live_data.milestone_id` | string | yes | Milestone ID |


#### `GET /live_data/milestone/{milestone_id}/game_stats`

Get Game Stats  
_operationId:_ `GetGameStats`  
_200 schema:_ `GetGameStatsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pbp.periods` | array |  |  |
| `pbp.periods[].events` | array |  |  |
| `pbp.periods[].events[]` | object |  |  |


#### `GET /live_data/{type}/milestone/{milestone_id}`

Get Live Data (with type)  
_operationId:_ `GetLiveData`  
_200 schema:_ `GetLiveDataResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `live_data.type` | string | yes | Type of live data |
| `live_data.details` | object | yes | Live data details as a flexible object |
| `live_data.milestone_id` | string | yes | Milestone ID |


### market

#### `GET /markets` **← KMIA**

Get Markets  
_operationId:_ `GetMarkets`  
_200 schema:_ `GetMarketsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markets` | array | yes |  |
| `markets[].ticker` | string | yes |  |
| `markets[].event_ticker` | string | yes |  |
| `markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `markets[].title` | string |  |  |
| `markets[].subtitle` | string |  |  |
| `markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `markets[].created_time` | string (date-time) | yes |  |
| `markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `markets[].open_time` | string (date-time) | yes |  |
| `markets[].close_time` | string (date-time) | yes |  |
| `markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `markets[].expiration_time` | string (date-time) |  |  |
| `markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `markets[].can_close_early` | boolean | yes |  |
| `markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `markets[].mve_selected_legs` | array |  |  |
| `markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].primary_participant_key` | string | null |  |  |
| `markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `markets[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


#### `GET /markets/candlesticks`

Batch Get Market Candlesticks  
_operationId:_ `BatchGetMarketCandlesticks`  
_200 schema:_ `BatchGetMarketCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markets` | array | yes | Array of market candlestick data, one entry per requested market. |
| `markets[].market_ticker` | string | yes | Market ticker string (e.g., 'INXD-24JAN01'). |
| `markets[].candlesticks` | array | yes | Array of candlestick data points for the market. Includes an initial data point at the start timestamp when available. |
| `markets[].candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `markets[].candlesticks[].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].candlesticks[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


#### `GET /markets/orderbooks` **← KMIA**

Get Multiple Market Orderbooks  
_operationId:_ `GetMarketOrderbooks`  
_200 schema:_ `GetMarketOrderbooksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orderbooks` | array | yes |  |
| `orderbooks[].ticker` | string | yes |  |
| `orderbooks[].orderbook_fp.yes_dollars` | array | yes |  |
| `orderbooks[].orderbook_fp.yes_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbooks[].orderbook_fp.yes_dollars[][]` | string |  |  |
| `orderbooks[].orderbook_fp.no_dollars` | array | yes |  |
| `orderbooks[].orderbook_fp.no_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbooks[].orderbook_fp.no_dollars[][]` | string |  |  |


#### `GET /markets/trades` **← KMIA**

Get Trades  
_operationId:_ `GetTrades`  
_200 schema:_ `GetTradesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trades` | array | yes |  |
| `trades[].trade_id` | string | yes | Unique identifier for this trade |
| `trades[].ticker` | string | yes | Unique identifier for the market |
| `trades[].count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `trades[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `trades[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `trades[].taker_side` | enum(yes, no) | yes | Deprecated. Use `taker_outcome_side` (or `taker_book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `trades[].taker_outcome_side` | enum(yes, no) | yes | The outcome side the taker is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `taker_outcome_side` describes directional exposure only; it does not change the … |
| `trades[].taker_book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `trades[].created_time` | string (date-time) | yes | Timestamp when this trade was executed |
| `trades[].is_block_trade` | boolean | yes | True if this trade was matched off-book as a block trade (e.g. via RFQ / negotiated block proposal); false for trades that filled on the standard order book. |
| `cursor` | string | yes |  |


#### `GET /markets/{ticker}` **← KMIA**

Get Market  
_operationId:_ `GetMarket`  
_200 schema:_ `GetMarketResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market.ticker` | string | yes |  |
| `market.event_ticker` | string | yes |  |
| `market.market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `market.title` | string |  |  |
| `market.subtitle` | string |  |  |
| `market.yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `market.no_sub_title` | string | yes | Shortened title for the no side of this market |
| `market.created_time` | string (date-time) | yes |  |
| `market.updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `market.open_time` | string (date-time) | yes |  |
| `market.close_time` | string (date-time) | yes |  |
| `market.expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `market.expiration_time` | string (date-time) |  |  |
| `market.latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `market.settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `market.status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `market.response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `market.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.result` | enum(yes, no, scalar, ) | yes |  |
| `market.can_close_early` | boolean | yes |  |
| `market.fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `market.open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `market.expiration_value` | string | yes | The value that was considered for the settlement |
| `market.occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `market.fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `market.early_close_condition` | string | null |  | The condition under which the market can close early |
| `market.strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `market.floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `market.cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `market.functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `market.custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `market.rules_primary` | string | yes | A plain language description of the most important market terms |
| `market.rules_secondary` | string | yes | A plain language description of secondary market terms |
| `market.mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `market.mve_selected_legs` | array |  |  |
| `market.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `market.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `market.mve_selected_legs[].side` | string |  | The side of the selected market |
| `market.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.primary_participant_key` | string | null |  |  |
| `market.price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `market.price_ranges` | array | yes | Valid price ranges for orders on this market |
| `market.price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `market.price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `market.price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `market.is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `market.exchange_index` | object |  |  |


#### `GET /markets/{ticker}/orderbook` **← KMIA**

Get Market Orderbook  
_operationId:_ `GetMarketOrderbook`  
_200 schema:_ `GetMarketOrderbookResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orderbook_fp.yes_dollars` | array | yes |  |
| `orderbook_fp.yes_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbook_fp.yes_dollars[][]` | string |  |  |
| `orderbook_fp.no_dollars` | array | yes |  |
| `orderbook_fp.no_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbook_fp.no_dollars[][]` | string |  |  |


#### `GET /series`

Get Series List  
_operationId:_ `GetSeriesList`  
_200 schema:_ `GetSeriesListResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series` | array | yes |  |
| `series[].ticker` | string | yes | Ticker that identifies this series. |
| `series[].frequency` | string | yes | Description of the frequency of the series. There is no fixed value set here, but will be something human-readable like weekly, daily, one-off. |
| `series[].title` | string | yes | Title describing the series. For full context use you should use this field with the title field of the events belonging to this series. |
| `series[].category` | string | yes | Category specifies the category which this series belongs to. |
| `series[].tags` | array | yes | Tags specifies the subjects that this series relates to, multiple series from different categories can have the same tags. |
| `series[].tags[]` | string |  |  |
| `series[].settlement_sources` | array | yes | SettlementSources specifies the official sources used for the determination of markets within the series. Methodology is defined in the rulebook. |
| `series[].settlement_sources[].name` | string |  | Name of the settlement source |
| `series[].settlement_sources[].url` | string |  | URL to the settlement source |
| `series[].contract_url` | string | yes | ContractUrl provides a direct link to the original filing of the contract which underlies the series. |
| `series[].contract_terms_url` | string | yes | ContractTermsUrl is the URL to the current terms of the contract underlying the series. |
| `series[].product_metadata` | object | null |  | Internal product metadata of the series. |
| `series[].fee_type` | object | yes | FeeType is a string representing the series' fee structure. Fee structures can be found at https://kalshi.com/docs/kalshi-fee-schedule.pdf. 'quadratic' is described by the General Trading Fees Tabl… |
| `series[].fee_multiplier` | number (double) | yes | FeeMultiplier is a floating point multiplier applied to the fee calculations. |
| `series[].additional_prohibitions` | array | yes | AdditionalProhibitions is a list of additional trading prohibitions for this series. |
| `series[].additional_prohibitions[]` | string |  |  |
| `series[].volume_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `series[].last_updated_ts` | string (date-time) |  | Timestamp of when this series' metadata was last updated. |


#### `GET /series/{series_ticker}`

Get Series  
_operationId:_ `GetSeries`  
_200 schema:_ `GetSeriesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series.ticker` | string | yes | Ticker that identifies this series. |
| `series.frequency` | string | yes | Description of the frequency of the series. There is no fixed value set here, but will be something human-readable like weekly, daily, one-off. |
| `series.title` | string | yes | Title describing the series. For full context use you should use this field with the title field of the events belonging to this series. |
| `series.category` | string | yes | Category specifies the category which this series belongs to. |
| `series.tags` | array | yes | Tags specifies the subjects that this series relates to, multiple series from different categories can have the same tags. |
| `series.tags[]` | string |  |  |
| `series.settlement_sources` | array | yes | SettlementSources specifies the official sources used for the determination of markets within the series. Methodology is defined in the rulebook. |
| `series.settlement_sources[].name` | string |  | Name of the settlement source |
| `series.settlement_sources[].url` | string |  | URL to the settlement source |
| `series.contract_url` | string | yes | ContractUrl provides a direct link to the original filing of the contract which underlies the series. |
| `series.contract_terms_url` | string | yes | ContractTermsUrl is the URL to the current terms of the contract underlying the series. |
| `series.product_metadata` | object | null |  | Internal product metadata of the series. |
| `series.fee_type` | object | yes | FeeType is a string representing the series' fee structure. Fee structures can be found at https://kalshi.com/docs/kalshi-fee-schedule.pdf. 'quadratic' is described by the General Trading Fees Tabl… |
| `series.fee_multiplier` | number (double) | yes | FeeMultiplier is a floating point multiplier applied to the fee calculations. |
| `series.additional_prohibitions` | array | yes | AdditionalProhibitions is a list of additional trading prohibitions for this series. |
| `series.additional_prohibitions[]` | string |  |  |
| `series.volume_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `series.last_updated_ts` | string (date-time) |  | Timestamp of when this series' metadata was last updated. |


#### `GET /series/{series_ticker}/markets/{ticker}/candlesticks` **← KMIA**

Get Market Candlesticks  
_operationId:_ `GetMarketCandlesticks`  
_200 schema:_ `GetMarketCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Unique identifier for the market. |
| `candlesticks` | array | yes | Array of candlestick data points for the specified time range. |
| `candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `candlesticks[].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `candlesticks[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### milestone

#### `GET /milestones`

Get Milestones  
_operationId:_ `GetMilestones`  
_200 schema:_ `GetMilestonesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `milestones` | array | yes | List of milestones. |
| `milestones[].id` | string | yes | Unique identifier for the milestone. |
| `milestones[].category` | string | yes | Category of the milestone. E.g. Sports, Elections, Esports, Crypto. |
| `milestones[].type` | string | yes | Type of the milestone. E.g. football_game, basketball_game, soccer_tournament_multi_leg, baseball_game, hockey_match, golf_tournament, political_race. |
| `milestones[].start_date` | string (date-time) | yes | Start date of the milestone. |
| `milestones[].end_date` | string (date-time) | null |  | End date of the milestone, if any. |
| `milestones[].related_event_tickers` | array | yes | List of event tickers related to this milestone. |
| `milestones[].related_event_tickers[]` | string |  |  |
| `milestones[].title` | string | yes | Title of the milestone. |
| `milestones[].notification_message` | string | yes | Notification message for the milestone. |
| `milestones[].source_id` | string | null |  | Source id of milestone if available. |
| `milestones[].source_ids` | object |  | Source ids of milestone if available. |
| `milestones[].details` | object | yes | Additional details about the milestone. |
| `milestones[].primary_event_tickers` | array | yes | List of event tickers directly related to the outcome of this milestone. |
| `milestones[].primary_event_tickers[]` | string |  |  |
| `milestones[].last_updated_ts` | string (date-time) | yes | Last time this structured target was updated. |
| `cursor` | string |  | Cursor for pagination. |


#### `GET /milestones/{milestone_id}`

Get Milestone  
_operationId:_ `GetMilestone`  
_200 schema:_ `GetMilestoneResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `milestone.id` | string | yes | Unique identifier for the milestone. |
| `milestone.category` | string | yes | Category of the milestone. E.g. Sports, Elections, Esports, Crypto. |
| `milestone.type` | string | yes | Type of the milestone. E.g. football_game, basketball_game, soccer_tournament_multi_leg, baseball_game, hockey_match, golf_tournament, political_race. |
| `milestone.start_date` | string (date-time) | yes | Start date of the milestone. |
| `milestone.end_date` | string (date-time) | null |  | End date of the milestone, if any. |
| `milestone.related_event_tickers` | array | yes | List of event tickers related to this milestone. |
| `milestone.related_event_tickers[]` | string |  |  |
| `milestone.title` | string | yes | Title of the milestone. |
| `milestone.notification_message` | string | yes | Notification message for the milestone. |
| `milestone.source_id` | string | null |  | Source id of milestone if available. |
| `milestone.source_ids` | object |  | Source ids of milestone if available. |
| `milestone.details` | object | yes | Additional details about the milestone. |
| `milestone.primary_event_tickers` | array | yes | List of event tickers directly related to the outcome of this milestone. |
| `milestone.primary_event_tickers[]` | string |  |  |
| `milestone.last_updated_ts` | string (date-time) | yes | Last time this structured target was updated. |


### multivariate

#### `GET /multivariate_event_collections`

Get Multivariate Event Collections  
_operationId:_ `GetMultivariateEventCollections`  
_200 schema:_ `GetMultivariateEventCollectionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `multivariate_contracts` | array | yes | List of multivariate event collections. |
| `multivariate_contracts[].collection_ticker` | string | yes | Unique identifier for the collection. |
| `multivariate_contracts[].series_ticker` | string | yes | Series associated with the collection. Events produced in the collection will be associated with this series. |
| `multivariate_contracts[].title` | string | yes | Title of the collection. |
| `multivariate_contracts[].description` | string | yes | Short description of the collection. |
| `multivariate_contracts[].open_date` | string (date-time) | yes | The open date of the collection. Before this time, the collection cannot be interacted with. |
| `multivariate_contracts[].close_date` | string (date-time) | yes | The close date of the collection. After this time, the collection cannot be interacted with. |
| `multivariate_contracts[].associated_events` | array | yes | List of events with their individual configuration. |
| `multivariate_contracts[].associated_events[].ticker` | string | yes | The event ticker. |
| `multivariate_contracts[].associated_events[].is_yes_only` | boolean | yes | Whether only the 'yes' side can be used for this event. |
| `multivariate_contracts[].associated_events[].size_max` | integer (int32) | null |  | Maximum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contracts[].associated_events[].size_min` | integer (int32) | null |  | Minimum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contracts[].associated_events[].active_quoters` | array | yes | List of active quoters for this event. |
| `multivariate_contracts[].associated_events[].active_quoters[]` | string |  |  |
| `multivariate_contracts[].associated_event_tickers` | array | yes | [DEPRECATED - Use associated_events instead] A list of events associated with the collection. Markets in these events can be passed as inputs to the Lookup and Create endpoints. |
| `multivariate_contracts[].associated_event_tickers[]` | string |  |  |
| `multivariate_contracts[].is_ordered` | boolean | yes | Whether the collection is ordered. If true, the order of markets passed into Lookup/Create affects the output. If false, the order does not matter. |
| `multivariate_contracts[].is_single_market_per_event` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection accepts multiple markets from the same event passed into Lookup/Create. |
| `multivariate_contracts[].is_all_yes` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection requires that only the market side of 'yes' may be used. |
| `multivariate_contracts[].size_min` | integer (int32) | yes | The minimum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contracts[].size_max` | integer (int32) | yes | The maximum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contracts[].functional_description` | string | yes | A functional description of the collection describing how inputs affect the output. |
| `cursor` | string |  | The Cursor represents a pointer to the next page of records in the pagination. Use the value returned here in the cursor query parameter for this end-point to get the next page containing limit rec… |


#### `GET /multivariate_event_collections/{collection_ticker}`

Get Multivariate Event Collection  
_operationId:_ `GetMultivariateEventCollection`  
_200 schema:_ `GetMultivariateEventCollectionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `multivariate_contract.collection_ticker` | string | yes | Unique identifier for the collection. |
| `multivariate_contract.series_ticker` | string | yes | Series associated with the collection. Events produced in the collection will be associated with this series. |
| `multivariate_contract.title` | string | yes | Title of the collection. |
| `multivariate_contract.description` | string | yes | Short description of the collection. |
| `multivariate_contract.open_date` | string (date-time) | yes | The open date of the collection. Before this time, the collection cannot be interacted with. |
| `multivariate_contract.close_date` | string (date-time) | yes | The close date of the collection. After this time, the collection cannot be interacted with. |
| `multivariate_contract.associated_events` | array | yes | List of events with their individual configuration. |
| `multivariate_contract.associated_events[].ticker` | string | yes | The event ticker. |
| `multivariate_contract.associated_events[].is_yes_only` | boolean | yes | Whether only the 'yes' side can be used for this event. |
| `multivariate_contract.associated_events[].size_max` | integer (int32) | null |  | Maximum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contract.associated_events[].size_min` | integer (int32) | null |  | Minimum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contract.associated_events[].active_quoters` | array | yes | List of active quoters for this event. |
| `multivariate_contract.associated_events[].active_quoters[]` | string |  |  |
| `multivariate_contract.associated_event_tickers` | array | yes | [DEPRECATED - Use associated_events instead] A list of events associated with the collection. Markets in these events can be passed as inputs to the Lookup and Create endpoints. |
| `multivariate_contract.associated_event_tickers[]` | string |  |  |
| `multivariate_contract.is_ordered` | boolean | yes | Whether the collection is ordered. If true, the order of markets passed into Lookup/Create affects the output. If false, the order does not matter. |
| `multivariate_contract.is_single_market_per_event` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection accepts multiple markets from the same event passed into Lookup/Create. |
| `multivariate_contract.is_all_yes` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection requires that only the market side of 'yes' may be used. |
| `multivariate_contract.size_min` | integer (int32) | yes | The minimum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contract.size_max` | integer (int32) | yes | The maximum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contract.functional_description` | string | yes | A functional description of the collection describing how inputs affect the output. |


#### `POST /multivariate_event_collections/{collection_ticker}`

Create Market In Multivariate Event Collection  
_operationId:_ `CreateMarketInMultivariateEventCollection`  
_200 schema:_ `CreateMarketInMultivariateEventCollectionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Event ticker for the created market. |
| `market_ticker` | string | yes | Market ticker for the created market. |
| `market.ticker` | string | yes |  |
| `market.event_ticker` | string | yes |  |
| `market.market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `market.title` | string |  |  |
| `market.subtitle` | string |  |  |
| `market.yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `market.no_sub_title` | string | yes | Shortened title for the no side of this market |
| `market.created_time` | string (date-time) | yes |  |
| `market.updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `market.open_time` | string (date-time) | yes |  |
| `market.close_time` | string (date-time) | yes |  |
| `market.expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `market.expiration_time` | string (date-time) |  |  |
| `market.latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `market.settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `market.status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `market.response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `market.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.result` | enum(yes, no, scalar, ) | yes |  |
| `market.can_close_early` | boolean | yes |  |
| `market.fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `market.open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `market.expiration_value` | string | yes | The value that was considered for the settlement |
| `market.occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `market.fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `market.early_close_condition` | string | null |  | The condition under which the market can close early |
| `market.strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `market.floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `market.cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `market.functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `market.custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `market.rules_primary` | string | yes | A plain language description of the most important market terms |
| `market.rules_secondary` | string | yes | A plain language description of secondary market terms |
| `market.mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `market.mve_selected_legs` | array |  |  |
| `market.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `market.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `market.mve_selected_legs[].side` | string |  | The side of the selected market |
| `market.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.primary_participant_key` | string | null |  |  |
| `market.price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `market.price_ranges` | array | yes | Valid price ranges for orders on this market |
| `market.price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `market.price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `market.price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `market.is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `market.exchange_index` | object |  |  |


#### `PUT /multivariate_event_collections/{collection_ticker}/lookup`

Lookup Tickers For Market In Multivariate Event Collection  
_operationId:_ `LookupTickersForMarketInMultivariateEventCollection`  
_200 schema:_ `LookupTickersForMarketInMultivariateEventCollectionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Event ticker for the looked up market. |
| `market_ticker` | string | yes | Market ticker for the looked up market. |


#### `GET /multivariate_event_collections/{collection_ticker}/lookup`

Get Multivariate Event Collection Lookup History  
_operationId:_ `GetMultivariateEventCollectionLookupHistory`  
_200 schema:_ `GetMultivariateEventCollectionLookupHistoryResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lookup_points` | array | yes | List of recent lookup points in the collection. |
| `lookup_points[].event_ticker` | string | yes | Event ticker for the lookup point. |
| `lookup_points[].market_ticker` | string | yes | Market ticker for the lookup point. |
| `lookup_points[].selected_markets` | array | yes | Markets that were selected for this lookup. |
| `lookup_points[].selected_markets[].market_ticker` | string | yes | Market ticker identifier. |
| `lookup_points[].selected_markets[].event_ticker` | string | yes | Event ticker identifier. |
| `lookup_points[].selected_markets[].side` | enum(yes, no) | yes | Side of the market (yes or no). |
| `lookup_points[].last_queried_ts` | string (date-time) | yes | Timestamp when this lookup was last queried. |


### order-groups

#### `GET /portfolio/order_groups`

Get Order Groups  
_operationId:_ `GetOrderGroups`  
_200 schema:_ `GetOrderGroupsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_groups` | array |  |  |
| `order_groups[].id` | string | yes | Unique identifier for the order group |
| `order_groups[].contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order_groups[].is_auto_cancel_enabled` | boolean | yes | Whether auto-cancel is enabled for this order group |
| `order_groups[].exchange_index` | object |  |  |


#### `POST /portfolio/order_groups/create`

Create Order Group  
_operationId:_ `CreateOrderGroup`  
_200 schema:_ `CreateOrderGroupResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_group_id` | string | yes | The unique identifier for the created order group |
| `subaccount` | integer | yes | Subaccount number that owns the created order group (0 for primary, 1-63 for subaccounts). |
| `exchange_index` | object |  |  |


#### `GET /portfolio/order_groups/{order_group_id}`

Get Order Group  
_operationId:_ `GetOrderGroup`  
_200 schema:_ `GetOrderGroupResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_auto_cancel_enabled` | boolean | yes | Whether auto-cancel is enabled for this order group |
| `contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders` | array | yes | List of order IDs that belong to this order group |
| `orders[]` | string |  |  |
| `exchange_index` | object |  |  |


#### `DELETE /portfolio/order_groups/{order_group_id}`

Delete Order Group  
_operationId:_ `DeleteOrderGroup`  
_200 schema:_ `EmptyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | An empty response body |


#### `PUT /portfolio/order_groups/{order_group_id}/limit`

Update Order Group Limit  
_operationId:_ `UpdateOrderGroupLimit`  
_200 schema:_ `EmptyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | An empty response body |


#### `PUT /portfolio/order_groups/{order_group_id}/reset`

Reset Order Group  
_operationId:_ `ResetOrderGroup`  
_200 schema:_ `EmptyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | An empty response body |


#### `PUT /portfolio/order_groups/{order_group_id}/trigger`

Trigger Order Group  
_operationId:_ `TriggerOrderGroup`  
_200 schema:_ `EmptyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | An empty response body |


### orders

#### `POST /portfolio/events/orders`

Create Order (V2)  
_operationId:_ `CreateOrderV2`  
_200 schema:_ `CreateOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `fill_count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `remaining_count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `average_fill_price` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `average_fee_paid` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the order was processed, as Unix epoch milliseconds. |


#### `POST /portfolio/events/orders/batched`

Batch Create Orders (V2)  
_operationId:_ `BatchCreateOrdersV2`  
_200 schema:_ `BatchCreateOrdersV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string |  |  |
| `orders[].client_order_id` | string | null |  |  |
| `orders[].fill_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].remaining_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].average_fill_price` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].average_fee_paid` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].ts_ms` | integer (int64) | null |  | Matching engine timestamp at which the order was processed, as Unix epoch milliseconds. Absent when the request errored. |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


#### `DELETE /portfolio/events/orders/batched`

Batch Cancel Orders (V2)  
_operationId:_ `BatchCancelOrdersV2`  
_200 schema:_ `BatchCancelOrdersV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes | The order ID identifying which order this entry corresponds to. |
| `orders[].client_order_id` | string | null |  |  |
| `orders[].reduced_by` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].ts_ms` | integer (int64) | null |  | Matching engine timestamp at which the cancellation was processed, as Unix epoch milliseconds. Absent when the cancel errored. |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


#### `DELETE /portfolio/events/orders/{order_id}`

Cancel Order (V2)  
_operationId:_ `CancelOrderV2`  
_200 schema:_ `CancelOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `reduced_by` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the cancellation was processed, as Unix epoch milliseconds. |


#### `POST /portfolio/events/orders/{order_id}/amend`

Amend Order (V2)  
_operationId:_ `AmendOrderV2`  
_200 schema:_ `AmendOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `remaining_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `fill_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `average_fill_price` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `average_fee_paid` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the amend was processed, as Unix epoch milliseconds. |


#### `POST /portfolio/events/orders/{order_id}/decrease`

Decrease Order (V2)  
_operationId:_ `DecreaseOrderV2`  
_200 schema:_ `DecreaseOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `remaining_count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the decrease was processed, as Unix epoch milliseconds. |


#### `GET /portfolio/orders`

Get Orders  
_operationId:_ `GetOrders`  
_200 schema:_ `GetOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes |  |
| `orders[].user_id` | string | yes | Unique identifier for users |
| `orders[].client_order_id` | string | yes |  |
| `orders[].ticker` | string | yes |  |
| `orders[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].type` | enum(limit, market) | yes |  |
| `orders[].status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].expiration_time` | string (date-time) | null |  |  |
| `orders[].created_time` | string (date-time) | null |  |  |
| `orders[].last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order_group_id` | string | null |  | The order group this order is part of |
| `orders[].cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


#### `DELETE /portfolio/orders/batched`

Batch Cancel Orders  
_operationId:_ `BatchCancelOrders`  
_200 schema:_ `BatchCancelOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes | The order ID to identify which order had an error during batch cancellation |
| `orders[].order.order_id` | string | yes |  |
| `orders[].order.user_id` | string | yes | Unique identifier for users |
| `orders[].order.client_order_id` | string | yes |  |
| `orders[].order.ticker` | string | yes |  |
| `orders[].order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].order.type` | enum(limit, market) | yes |  |
| `orders[].order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.expiration_time` | string (date-time) | null |  |  |
| `orders[].order.created_time` | string (date-time) | null |  |  |
| `orders[].order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order.order_group_id` | string | null |  | The order group this order is part of |
| `orders[].order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].order.exchange_index` | object |  |  |
| `orders[].reduced_by_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


#### `GET /portfolio/orders/queue_positions`

Get Queue Positions for Orders  
_operationId:_ `GetOrderQueuePositions`  
_200 schema:_ `GetOrderQueuePositionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queue_positions` | array | yes | Queue positions for all matching orders |
| `queue_positions[].order_id` | string | yes | The order ID |
| `queue_positions[].market_ticker` | string | yes | The market ticker |
| `queue_positions[].queue_position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


#### `GET /portfolio/orders/{order_id}`

Get Order  
_operationId:_ `GetOrder`  
_200 schema:_ `GetOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |


#### `DELETE /portfolio/orders/{order_id}`

Cancel Order  
_operationId:_ `CancelOrder`  
_200 schema:_ `CancelOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |
| `reduced_by_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


#### `POST /portfolio/orders/{order_id}/decrease`

Decrease Order  
_operationId:_ `DecreaseOrder`  
_200 schema:_ `DecreaseOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |


#### `GET /portfolio/orders/{order_id}/queue_position`

Get Order Queue Position  
_operationId:_ `GetOrderQueuePosition`  
_200 schema:_ `GetOrderQueuePositionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queue_position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### portfolio

#### `GET /portfolio/balance`

Get Balance  
_operationId:_ `GetBalance`  
_200 schema:_ `GetBalanceResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `balance` | integer (int64) | yes | Member's available balance in cents. This represents the amount available for trading. |
| `balance_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `portfolio_value` | integer (int64) | yes | Member's portfolio value in cents. This is the current value of all positions held. |
| `updated_ts` | integer (int64) | yes | Unix timestamp of the last update to the balance. |
| `balance_breakdown` | array |  | Balance broken down per exchange index. |
| `balance_breakdown[].exchange_index` | integer | yes | Identifier for an exchange shard. Defaults to 0 if unspecified. Note: currently only 0 supported. |
| `balance_breakdown[].balance` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


#### `GET /portfolio/deposits`

Get Deposits  
_operationId:_ `GetDeposits`  
_200 schema:_ `GetDepositsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deposits` | array | yes |  |
| `deposits[].id` | string | yes | Unique identifier for the deposit. |
| `deposits[].status` | enum(pending, applied, failed, returned) | yes | Current status of the deposit. 'applied' means funds are reflected in balance. |
| `deposits[].type` | enum(ach, wire, crypto, debit, apm) | yes | Payment method used for the deposit. |
| `deposits[].amount_cents` | integer (int64) | yes | Deposit amount in cents. |
| `deposits[].fee_cents` | integer (int64) | yes | Fee charged for the deposit in cents. |
| `deposits[].created_ts` | integer (int64) | yes | Unix timestamp of when the deposit was created. |
| `deposits[].finalized_ts` | integer (int64) | null |  | Unix timestamp of when the deposit was finalized (applied, failed, or returned). |
| `cursor` | string |  |  |


#### `GET /portfolio/fills`

Get Fills  
_operationId:_ `GetFills`  
_200 schema:_ `GetFillsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fills` | array | yes |  |
| `fills[].fill_id` | string | yes | Unique identifier for this fill |
| `fills[].trade_id` | string | yes | Unique identifier for this fill (legacy field name, same as fill_id) |
| `fills[].order_id` | string | yes | Unique identifier for the order that resulted in this fill |
| `fills[].ticker` | string | yes | Unique identifier for the market |
| `fills[].market_ticker` | string | yes | Unique identifier for the market (legacy field name, same as ticker) |
| `fills[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `fills[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `fills[].outcome_side` | enum(yes, no) | yes | The outcome side this fill positioned the user for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the … |
| `fills[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `fills[].count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `fills[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].is_taker` | boolean | yes | If true, this fill was a taker (removed liquidity from the order book) |
| `fills[].created_time` | string (date-time) |  | Timestamp when this fill was executed |
| `fills[].fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). Present for direct users. |
| `fills[].ts` | integer (int64) |  | Unix timestamp when this fill was executed (legacy field name) |
| `cursor` | string | yes |  |


#### `GET /portfolio/positions`

Get Positions  
_operationId:_ `GetPositions`  
_200 schema:_ `GetPositionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cursor` | string |  | The Cursor represents a pointer to the next page of records in the pagination. Use the value returned here in the cursor query parameter for this end-point to get the next page containing limit rec… |
| `market_positions` | array | yes | List of market positions |
| `market_positions[].ticker` | string | yes | Unique identifier for the market |
| `market_positions[].total_traded_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market_positions[].market_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].resting_orders_count` | integer (int32) | yes | [DEPRECATED] Aggregate size of resting orders in contract units |
| `market_positions[].fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].last_updated_ts` | string (date-time) | yes | Last time the position is updated |
| `event_positions` | array | yes | List of event positions |
| `event_positions[].event_ticker` | string | yes | Unique identifier for events |
| `event_positions[].total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].total_cost_shares_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event_positions[].event_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


#### `GET /portfolio/settlements`

Get Settlements  
_operationId:_ `GetSettlements`  
_200 schema:_ `GetSettlementsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `settlements` | array | yes |  |
| `settlements[].ticker` | string | yes | The ticker symbol of the market that was settled. |
| `settlements[].event_ticker` | string | yes | The event ticker symbol of the market that was settled. |
| `settlements[].market_result` | enum(yes, no, scalar) | yes | The outcome of the market settlement. 'yes' = market resolved to YES, 'no' = market resolved to NO, 'scalar' = scalar market settled at a specific value. |
| `settlements[].yes_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `settlements[].yes_total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlements[].no_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `settlements[].no_total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlements[].revenue` | integer | yes | Total revenue earned from this settlement in cents (winning contracts pay out 100 cents each). |
| `settlements[].settled_time` | string (date-time) | yes | Timestamp when the market was settled and payouts were processed. |
| `settlements[].fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlements[].value` | integer | null |  | Payout of a single yes contract in cents. |
| `cursor` | string |  |  |


#### `POST /portfolio/subaccounts`

Create Subaccount  
_operationId:_ `CreateSubaccount`  
_200 schema:_ `CreateSubaccountResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_number` | integer | yes | The sequential number assigned to this subaccount (1-63). |


#### `GET /portfolio/subaccounts/balances`

Get All Subaccount Balances  
_operationId:_ `GetSubaccountBalances`  
_200 schema:_ `GetSubaccountBalancesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_balances` | array | yes |  |
| `subaccount_balances[].subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `subaccount_balances[].balance` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `subaccount_balances[].updated_ts` | integer (int64) | yes | Unix timestamp of last balance update. |


#### `PUT /portfolio/subaccounts/netting`

Update Subaccount Netting  
_operationId:_ `UpdateSubaccountNetting`  

_No JSON response schema in OpenAPI for HTTP 200._

#### `GET /portfolio/subaccounts/netting`

Get Subaccount Netting  
_operationId:_ `GetSubaccountNetting`  
_200 schema:_ `GetSubaccountNettingResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `netting_configs` | array | yes |  |
| `netting_configs[].subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `netting_configs[].enabled` | boolean | yes | Whether netting is enabled for this subaccount. |


#### `POST /portfolio/subaccounts/transfer`

Transfer Between Subaccounts  
_operationId:_ `ApplySubaccountTransfer`  
_200 schema:_ `ApplySubaccountTransferResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | Empty response indicating successful transfer. |


#### `GET /portfolio/subaccounts/transfers`

Get Subaccount Transfers  
_operationId:_ `GetSubaccountTransfers`  
_200 schema:_ `GetSubaccountTransfersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transfers` | array | yes |  |
| `transfers[].transfer_id` | string | yes | Unique identifier for this transfer. |
| `transfers[].from_subaccount` | integer | yes | Source subaccount number (0 for primary, 1-63 for subaccounts). |
| `transfers[].to_subaccount` | integer | yes | Destination subaccount number (0 for primary, 1-63 for subaccounts). |
| `transfers[].amount_cents` | integer (int64) | yes | Transfer amount in cents. |
| `transfers[].created_ts` | integer (int64) | yes | Unix timestamp when the transfer was created. |
| `cursor` | string |  | Cursor for the next page of results. |


#### `GET /portfolio/summary/total_resting_order_value`

Get Total Resting Order Value  
_operationId:_ `GetPortfolioRestingOrderTotalValue`  
_200 schema:_ `GetPortfolioRestingOrderTotalValueResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_resting_order_value` | integer | yes | Total value of resting orders in cents |


#### `GET /portfolio/withdrawals`

Get Withdrawals  
_operationId:_ `GetWithdrawals`  
_200 schema:_ `GetWithdrawalsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `withdrawals` | array | yes |  |
| `withdrawals[].id` | string | yes | Unique identifier for the withdrawal. |
| `withdrawals[].status` | enum(pending, applied, failed, returned) | yes | Current status of the withdrawal. 'applied' means funds have been deducted from balance. |
| `withdrawals[].type` | enum(ach, wire, crypto, debit, apm) | yes | Payment type used for the withdrawal. |
| `withdrawals[].amount_cents` | integer (int64) | yes | Withdrawal amount in cents. |
| `withdrawals[].fee_cents` | integer (int64) | yes | Fee charged for the withdrawal in cents. |
| `withdrawals[].created_ts` | integer (int64) | yes | Unix timestamp of when the withdrawal was created. |
| `withdrawals[].finalized_ts` | integer (int64) | null |  | Unix timestamp of when the withdrawal was finalized (applied, failed, or returned). |
| `cursor` | string |  |  |


### search

#### `GET /search/filters_by_sport`

Get Filters for Sports  
_operationId:_ `GetFiltersForSports`  
_200 schema:_ `GetFiltersBySportsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filters_by_sports` | object | yes | Mapping of sports to their filter details |
| `sport_ordering` | array | yes | Ordered list of sports for display |
| `sport_ordering[]` | string |  |  |


#### `GET /search/tags_by_categories`

Get Tags for Series Categories  
_operationId:_ `GetTagsForSeriesCategories`  
_200 schema:_ `GetTagsForSeriesCategoriesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tags_by_categories` | object | yes | Mapping of series categories to their associated tags |


### structured-targets

#### `GET /structured_targets`

Get Structured Targets  
_operationId:_ `GetStructuredTargets`  
_200 schema:_ `GetStructuredTargetsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `structured_targets` | array |  |  |
| `structured_targets[].id` | string |  | Unique identifier for the structured target. |
| `structured_targets[].name` | string |  | Name of the structured target. |
| `structured_targets[].type` | string |  | Type of the structured target. |
| `structured_targets[].details` | object |  | Additional details about the structured target. Contains flexible JSON data specific to the target type. |
| `structured_targets[].source_id` | string |  | External source identifier for the structured target, if available (e.g., third-party data provider ID). |
| `structured_targets[].source_ids` | object |  | Source ids of structured target if available. |
| `structured_targets[].last_updated_ts` | string (date-time) |  | Timestamp when this structured target was last updated. |
| `cursor` | string |  | Pagination cursor for the next page. Empty if there are no more results. |


#### `GET /structured_targets/{structured_target_id}`

Get Structured Target  
_operationId:_ `GetStructuredTarget`  
_200 schema:_ `GetStructuredTargetResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `structured_target.id` | string |  | Unique identifier for the structured target. |
| `structured_target.name` | string |  | Name of the structured target. |
| `structured_target.type` | string |  | Type of the structured target. |
| `structured_target.details` | object |  | Additional details about the structured target. Contains flexible JSON data specific to the target type. |
| `structured_target.source_id` | string |  | External source identifier for the structured target, if available (e.g., third-party data provider ID). |
| `structured_target.source_ids` | object |  | Source ids of structured target if available. |
| `structured_target.last_updated_ts` | string (date-time) |  | Timestamp when this structured target was last updated. |


---

## Schema appendix (all response types)

### `AcceptBlockTradeProposalRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subtrader_id` | string |  | Subtrader ID to accept as. Provide either this or subaccount, not both. |
| `subaccount` | integer |  | User-managed subaccount number to accept as (0 for primary, 1-63 for numbered subaccounts). Provide either this or subtrader_id, not both. |


### `AcceptQuoteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `accepted_side` | enum(yes, no) | yes | The side of the quote to accept (yes or no) |


### `AccountApiUsageLevelVolumeGoal`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | string | yes | API usage level for this Predictions volume goal. |
| `earn_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `keep_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `AccountApiUsageLevelVolumeProgress`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `computed_ts` | integer (int64) | yes | Unix timestamp (seconds) when this progress was computed; trailing_30d_volume_fp covers the trailing 30 days ending at this time. |
| `trailing_30d_volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `goals` | array | yes |  |
| `goals[].level` | string | yes | API usage level for this Predictions volume goal. |
| `goals[].earn_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `goals[].keep_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `AmendOrderRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount` | integer |  | Optional subaccount number to use for this amendment (0 for primary, 1-63 for subaccounts) |
| `ticker` | string | yes | Market ticker |
| `side` | enum(yes, no) | yes | Side of the order |
| `action` | enum(buy, sell) | yes | Action of the order |
| `client_order_id` | string |  | The original client-specified order ID to be amended |
| `updated_client_order_id` | string |  | The new client-specified order ID after amendment |
| `yes_price` | integer |  | Updated yes price for the order in cents |
| `no_price` | integer |  | Updated no price for the order in cents |
| `yes_price_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_price_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `count` | integer |  | Updated quantity for the order (whole contracts only). If updating quantity, provide count or count_fp; if both provided they must match. |
| `count_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `exchange_index` | object |  |  |


### `AmendOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `old_order.order_id` | string | yes |  |
| `old_order.user_id` | string | yes | Unique identifier for users |
| `old_order.client_order_id` | string | yes |  |
| `old_order.ticker` | string | yes |  |
| `old_order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `old_order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `old_order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `old_order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `old_order.type` | enum(limit, market) | yes |  |
| `old_order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `old_order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `old_order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `old_order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `old_order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `old_order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `old_order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `old_order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `old_order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `old_order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `old_order.expiration_time` | string (date-time) | null |  |  |
| `old_order.created_time` | string (date-time) | null |  |  |
| `old_order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `old_order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `old_order.order_group_id` | string | null |  | The order group this order is part of |
| `old_order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `old_order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `old_order.exchange_index` | object |  |  |
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |


### `AmendOrderV2Request`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Market ticker |
| `side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `price` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `client_order_id` | string |  | The original client-specified order ID to be amended |
| `updated_client_order_id` | string |  | The new client-specified order ID after amendment |
| `exchange_index` | object |  |  |


### `AmendOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `remaining_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `fill_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `average_fill_price` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `average_fee_paid` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the amend was processed, as Unix epoch milliseconds. |


### `Announcement`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum(info, warning, error) | yes | The type of the announcement. |
| `message` | string | yes | The message contained within the announcement. |
| `delivery_time` | string (date-time) | yes | The time the announcement was delivered. |
| `status` | enum(active, inactive) | yes | The current status of this announcement. |


### `ApiKey`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | yes | Unique identifier for the API key |
| `name` | string | yes | User-provided name for the API key |
| `scopes` | array | yes | List of scopes granted to this API key. |
| `scopes[]` | enum(read, write, read::block_trade_accept, read::portfolio_balance, write::transfer, write::block_trade_accept) |  | Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`,… |


### `ApiKeyScope`

Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`, `read::portfolio_balance`, `write::transfer`, and `write::block_trade_accept` grant only their specific endpoint group and can be granted without the parent scope.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(read, write, read::block_trade_accept, read::portfolio_balance, write::transfer, write::block_trade_accept) |  | Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`,… |


### `ApiUsageLevelGrant`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `exchange_instance` | enum(event_contract, margined) | yes | The exchange instance type |
| `level` | string | yes | API usage level this grant confers (for example, expert, premier, paragon, prime, or prestige). |
| `expires_ts` | integer (int64) | null |  | Unix timestamp (seconds) when the grant expires. Absent for permanent grants. |
| `source` | string | yes | How the grant was created: "volume" (earned from trading volume) or "manual" (assigned by Kalshi). |


### `ApplySubaccountTransferRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_transfer_id` | string (uuid) | yes | Unique client-provided transfer ID for idempotency. |
| `from_subaccount` | integer | yes | Source subaccount number (0 for primary, 1-63 for numbered subaccounts). |
| `to_subaccount` | integer | yes | Destination subaccount number (0 for primary, 1-63 for numbered subaccounts). |
| `amount_cents` | integer (int64) | yes | Amount to transfer in cents. |


### `ApplySubaccountTransferResponse`

Empty response indicating successful transfer.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | Empty response indicating successful transfer. |


### `AssociatedEvent`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | The event ticker. |
| `is_yes_only` | boolean | yes | Whether only the 'yes' side can be used for this event. |
| `size_max` | integer (int32) | null |  | Maximum number of markets from this event (inclusive). Null means no limit. |
| `size_min` | integer (int32) | null |  | Minimum number of markets from this event (inclusive). Null means no limit. |
| `active_quoters` | array | yes | List of active quoters for this event. |
| `active_quoters[]` | string |  |  |


### `BatchCancelOrdersIndividualResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes | The order ID to identify which order had an error during batch cancellation |
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |
| `reduced_by_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `error.code` | string |  | Error code |
| `error.message` | string |  | Human-readable error message |
| `error.details` | string |  | Additional details about the error, if available |
| `error.service` | string |  | The name of the service that generated the error |


### `BatchCancelOrdersRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ids` | array |  | An array of order IDs to cancel |
| `ids[]` | string |  |  |
| `orders` | array |  | An array of orders to cancel, each optionally specifying a subaccount |
| `orders[].order_id` | string | yes | Order ID to cancel |
| `orders[].subaccount` | integer |  | Optional subaccount number to use for this cancellation (0 for primary, 1-63 for subaccounts) |
| `orders[].exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |
| `orders[].market_ticker` | string |  | Market ticker. Required when exchange_index is -1 (auto). |


### `BatchCancelOrdersRequestOrder`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes | Order ID to cancel |
| `subaccount` | integer |  | Optional subaccount number to use for this cancellation (0 for primary, 1-63 for subaccounts) |
| `exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |
| `market_ticker` | string |  | Market ticker. Required when exchange_index is -1 (auto). |


### `BatchCancelOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes | The order ID to identify which order had an error during batch cancellation |
| `orders[].order.order_id` | string | yes |  |
| `orders[].order.user_id` | string | yes | Unique identifier for users |
| `orders[].order.client_order_id` | string | yes |  |
| `orders[].order.ticker` | string | yes |  |
| `orders[].order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].order.type` | enum(limit, market) | yes |  |
| `orders[].order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.expiration_time` | string (date-time) | null |  |  |
| `orders[].order.created_time` | string (date-time) | null |  |  |
| `orders[].order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order.order_group_id` | string | null |  | The order group this order is part of |
| `orders[].order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].order.exchange_index` | object |  |  |
| `orders[].reduced_by_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


### `BatchCancelOrdersV2Request`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes | An array of orders to cancel, each optionally specifying a subaccount. |
| `orders[].order_id` | string | yes | Order ID to cancel. |
| `orders[].subaccount` | integer |  | Optional subaccount number to use for this cancellation (0 for primary, 1-63 for subaccounts). |
| `orders[].exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |
| `orders[].market_ticker` | string |  | Market ticker. Required when exchange_index is -1 (auto). |


### `BatchCancelOrdersV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes | The order ID identifying which order this entry corresponds to. |
| `orders[].client_order_id` | string | null |  |  |
| `orders[].reduced_by` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].ts_ms` | integer (int64) | null |  | Matching engine timestamp at which the cancellation was processed, as Unix epoch milliseconds. Absent when the cancel errored. |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


### `BatchCreateOrdersIndividualResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_order_id` | string | null |  |  |
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |
| `error.code` | string |  | Error code |
| `error.message` | string |  | Human-readable error message |
| `error.details` | string |  | Additional details about the error, if available |
| `error.service` | string |  | The name of the service that generated the error |


### `BatchCreateOrdersRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].ticker` | string | yes |  |
| `orders[].client_order_id` | string |  |  |
| `orders[].side` | enum(yes, no) | yes |  |
| `orders[].action` | enum(buy, sell) | yes |  |
| `orders[].count` | integer |  | Order quantity in contracts (whole contracts only). Provide count or count_fp; if both provided they must match. |
| `orders[].count_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].yes_price` | integer |  |  |
| `orders[].no_price` | integer |  |  |
| `orders[].yes_price_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].no_price_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].expiration_ts` | integer (int64) |  | Optional Unix timestamp in seconds for when the order expires. To place an expiring order, set `time_in_force` to `good_till_canceled` and provide this `expiration_ts`. `GTT` is an internal executi… |
| `orders[].time_in_force` | enum(fill_or_kill, good_till_canceled, immediate_or_cancel) |  | Specifies how long the order remains active. Use `good_till_canceled` with `expiration_ts` for an order that should rest until a specific expiration time; without `expiration_ts`, `good_till_cancel… |
| `orders[].buy_max_cost` | integer |  | Maximum cost in cents. When specified, the order will automatically have Fill-or-Kill (FoK) behavior. |
| `orders[].post_only` | boolean |  |  |
| `orders[].reduce_only` | boolean |  |  |
| `orders[].sell_position_floor` | integer |  | Deprecated: Use reduce_only instead. Only accepts value of 0. |
| `orders[].self_trade_prevention_type` | object |  |  |
| `orders[].order_group_id` | string |  | The order group this order is part of |
| `orders[].cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].subaccount` | integer |  | The subaccount number to use for this order. 0 is the primary subaccount. |
| `orders[].exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |


### `BatchCreateOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].client_order_id` | string | null |  |  |
| `orders[].order.order_id` | string | yes |  |
| `orders[].order.user_id` | string | yes | Unique identifier for users |
| `orders[].order.client_order_id` | string | yes |  |
| `orders[].order.ticker` | string | yes |  |
| `orders[].order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].order.type` | enum(limit, market) | yes |  |
| `orders[].order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].order.expiration_time` | string (date-time) | null |  |  |
| `orders[].order.created_time` | string (date-time) | null |  |  |
| `orders[].order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order.order_group_id` | string | null |  | The order group this order is part of |
| `orders[].order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].order.exchange_index` | object |  |  |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


### `BatchCreateOrdersV2Request`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].ticker` | string | yes |  |
| `orders[].client_order_id` | string |  |  |
| `orders[].side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].price` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].expiration_time` | integer (int64) |  | Optional Unix timestamp in seconds for when the order expires. To place an expiring order, set `time_in_force` to `good_till_canceled` and provide this `expiration_time`. `GTT` is an internal execu… |
| `orders[].time_in_force` | enum(fill_or_kill, good_till_canceled, immediate_or_cancel) | yes | Specifies how long the order remains active. Use `good_till_canceled` with `expiration_time` for an order that should rest until a specific expiration time; without `expiration_time`, `good_till_ca… |
| `orders[].post_only` | boolean |  |  |
| `orders[].self_trade_prevention_type` | object | yes |  |
| `orders[].cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].reduce_only` | boolean |  | Specifies whether the order place count should be capped by the member's current position. |
| `orders[].subaccount` | integer |  | The subaccount number to use for this order. 0 is the primary subaccount. |
| `orders[].order_group_id` | string |  | The order group this order is part of |
| `orders[].exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |


### `BatchCreateOrdersV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string |  |  |
| `orders[].client_order_id` | string | null |  |  |
| `orders[].fill_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].remaining_count` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].average_fill_price` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].average_fee_paid` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].ts_ms` | integer (int64) | null |  | Matching engine timestamp at which the order was processed, as Unix epoch milliseconds. Absent when the request errored. |
| `orders[].error.code` | string |  | Error code |
| `orders[].error.message` | string |  | Human-readable error message |
| `orders[].error.details` | string |  | Additional details about the error, if available |
| `orders[].error.service` | string |  | The name of the service that generated the error |


### `BatchGetMarketCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markets` | array | yes | Array of market candlestick data, one entry per requested market. |
| `markets[].market_ticker` | string | yes | Market ticker string (e.g., 'INXD-24JAN01'). |
| `markets[].candlesticks` | array | yes | Array of candlestick data points for the market. Includes an initial data point at the start timestamp when available. |
| `markets[].candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `markets[].candlesticks[].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].candlesticks[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].candlesticks[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `BidAskDistribution`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `BidAskDistributionHistorical`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `BlockTradeProposal`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the block trade proposal |
| `proposer_user_id` | string | yes | User ID of the proposal creator |
| `buyer_user_id` | string | yes | User ID of the buyer. Empty when the authenticated user is not the buyer. |
| `buyer_subtrader_id` | string |  | Subtrader ID of the buyer. Empty when the authenticated user is not the buyer. |
| `seller_user_id` | string | yes | User ID of the seller. Empty when the authenticated user is not the seller. |
| `seller_subtrader_id` | string |  | Subtrader ID of the seller. Empty when the authenticated user is not the seller. |
| `market_ticker` | string | yes | The ticker of the market for this block trade |
| `price_centi_cents` | integer (int64) | yes | Price in centi-cents |
| `centicount` | integer (int64) | yes | Number of contracts in centicounts |
| `maker_side` | enum(yes, no) | yes | The maker side of the trade |
| `expiration_ts` | string (date-time) | yes | Expiration time of the proposal |
| `status` | string | yes | Current status of the proposal |
| `created_ts` | string (date-time) | yes | Timestamp when the proposal was created |
| `updated_ts` | string (date-time) | yes | Timestamp when the proposal was last updated |
| `buyer_accepted` | boolean | yes | Whether the buyer has accepted the proposal |
| `seller_accepted` | boolean | yes | Whether the seller has accepted the proposal |
| `buyer_accepted_ts` | string (date-time) |  | Timestamp when the buyer accepted |
| `seller_accepted_ts` | string (date-time) |  | Timestamp when the seller accepted |
| `executed_ts` | string (date-time) |  | Timestamp when the proposal was executed |
| `buyer_order_id` | string |  | Order ID for the buyer after the proposal is executed |
| `seller_order_id` | string |  | Order ID for the seller after the proposal is executed |


### `BookSide`

Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - price`, but this endpoint quotes everything from the YES side.)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(bid, ask) |  | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |


### `BucketLimit`

Token-bucket budget for one rate-limit bucket. Each request deducts
tokens equal to its endpoint cost; the bucket refills at refill_rate
tokens per second up to bucket_capacity. A request is allowed if the
bucket holds enough tokens to cover its cost; otherwise the request
is rejected with HTTP 429.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refill_rate` | integer | yes | Tokens added to the bucket per second. |
| `bucket_capacity` | integer | yes | Maximum tokens the bucket can hold. When equal to refill_rate the bucket holds one second of budget; larger values represent burst headroom that idle clients accumulate and can spend in a single pu… |


### `CancelOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |
| `reduced_by_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `CancelOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `reduced_by` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the cancellation was processed, as Unix epoch milliseconds. |


### `CreateApiKeyRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Name for the API key. This helps identify the key's purpose |
| `public_key` | string | yes | RSA public key in PEM format. This will be used to verify signatures on API requests |
| `scopes` | array |  | List of scopes to grant to the API key. If the broad `write` parent scope is included, `read` must also be included. Child scopes may be granted without the broad parent scope. Defaults to full acc… |
| `scopes[]` | enum(read, write, read::block_trade_accept, read::portfolio_balance, write::transfer, write::block_trade_accept) |  | Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`,… |


### `CreateApiKeyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | yes | Unique identifier for the newly created API key |


### `CreateMarketInMultivariateEventCollectionRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selected_markets` | array | yes | List of selected markets that act as parameters to determine which market is created. |
| `selected_markets[].market_ticker` | string | yes | Market ticker identifier. |
| `selected_markets[].event_ticker` | string | yes | Event ticker identifier. |
| `selected_markets[].side` | enum(yes, no) | yes | Side of the market (yes or no). |
| `with_market_payload` | boolean |  | Whether to include the market payload in the response. |


### `CreateMarketInMultivariateEventCollectionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Event ticker for the created market. |
| `market_ticker` | string | yes | Market ticker for the created market. |
| `market.ticker` | string | yes |  |
| `market.event_ticker` | string | yes |  |
| `market.market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `market.title` | string |  |  |
| `market.subtitle` | string |  |  |
| `market.yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `market.no_sub_title` | string | yes | Shortened title for the no side of this market |
| `market.created_time` | string (date-time) | yes |  |
| `market.updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `market.open_time` | string (date-time) | yes |  |
| `market.close_time` | string (date-time) | yes |  |
| `market.expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `market.expiration_time` | string (date-time) |  |  |
| `market.latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `market.settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `market.status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `market.response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `market.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.result` | enum(yes, no, scalar, ) | yes |  |
| `market.can_close_early` | boolean | yes |  |
| `market.fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `market.open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `market.expiration_value` | string | yes | The value that was considered for the settlement |
| `market.occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `market.fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `market.early_close_condition` | string | null |  | The condition under which the market can close early |
| `market.strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `market.floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `market.cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `market.functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `market.custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `market.rules_primary` | string | yes | A plain language description of the most important market terms |
| `market.rules_secondary` | string | yes | A plain language description of secondary market terms |
| `market.mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `market.mve_selected_legs` | array |  |  |
| `market.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `market.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `market.mve_selected_legs[].side` | string |  | The side of the selected market |
| `market.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.primary_participant_key` | string | null |  |  |
| `market.price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `market.price_ranges` | array | yes | Valid price ranges for orders on this market |
| `market.price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `market.price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `market.price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `market.is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `market.exchange_index` | object |  |  |


### `CreateOrderGroupRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount` | integer |  | Optional subaccount number to use for this order group (0 for primary, 1-63 for subaccounts) |
| `contracts_limit` | integer (int64) |  | Specifies the maximum number of contracts that can be matched within this group over a rolling 15-second window. Whole contracts only. Provide contracts_limit or contracts_limit_fp; if both provide… |
| `contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `exchange_index` | object |  |  |


### `CreateOrderGroupResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_group_id` | string | yes | The unique identifier for the created order group |
| `subaccount` | integer | yes | Subaccount number that owns the created order group (0 for primary, 1-63 for subaccounts). |
| `exchange_index` | object |  |  |


### `CreateOrderRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes |  |
| `client_order_id` | string |  |  |
| `side` | enum(yes, no) | yes |  |
| `action` | enum(buy, sell) | yes |  |
| `count` | integer |  | Order quantity in contracts (whole contracts only). Provide count or count_fp; if both provided they must match. |
| `count_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `yes_price` | integer |  |  |
| `no_price` | integer |  |  |
| `yes_price_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_price_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `expiration_ts` | integer (int64) |  | Optional Unix timestamp in seconds for when the order expires. To place an expiring order, set `time_in_force` to `good_till_canceled` and provide this `expiration_ts`. `GTT` is an internal executi… |
| `time_in_force` | enum(fill_or_kill, good_till_canceled, immediate_or_cancel) |  | Specifies how long the order remains active. Use `good_till_canceled` with `expiration_ts` for an order that should rest until a specific expiration time; without `expiration_ts`, `good_till_cancel… |
| `buy_max_cost` | integer |  | Maximum cost in cents. When specified, the order will automatically have Fill-or-Kill (FoK) behavior. |
| `post_only` | boolean |  |  |
| `reduce_only` | boolean |  |  |
| `sell_position_floor` | integer |  | Deprecated: Use reduce_only instead. Only accepts value of 0. |
| `self_trade_prevention_type` | object |  |  |
| `order_group_id` | string |  | The order group this order is part of |
| `cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `subaccount` | integer |  | The subaccount number to use for this order. 0 is the primary subaccount. |
| `exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |


### `CreateOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |


### `CreateOrderV2Request`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes |  |
| `client_order_id` | string |  |  |
| `side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `price` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `expiration_time` | integer (int64) |  | Optional Unix timestamp in seconds for when the order expires. To place an expiring order, set `time_in_force` to `good_till_canceled` and provide this `expiration_time`. `GTT` is an internal execu… |
| `time_in_force` | enum(fill_or_kill, good_till_canceled, immediate_or_cancel) | yes | Specifies how long the order remains active. Use `good_till_canceled` with `expiration_time` for an order that should rest until a specific expiration time; without `expiration_time`, `good_till_ca… |
| `post_only` | boolean |  |  |
| `self_trade_prevention_type` | object | yes |  |
| `cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `reduce_only` | boolean |  | Specifies whether the order place count should be capped by the member's current position. |
| `subaccount` | integer |  | The subaccount number to use for this order. 0 is the primary subaccount. |
| `order_group_id` | string |  | The order group this order is part of |
| `exchange_index` | object |  | Exchange shard index. Defaults to 0. Use -1 to auto-route by market ticker. |


### `CreateOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `fill_count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `remaining_count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `average_fill_price` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `average_fee_paid` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the order was processed, as Unix epoch milliseconds. |


### `CreateQuoteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rfq_id` | string | yes | The ID of the RFQ to quote on |
| `yes_bid` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_bid` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rest_remainder` | boolean | yes | Whether to rest the remainder of the quote after execution |
| `post_only` | boolean |  | If true, the quote creator's resting order will be cancelled rather than crossed if it would take liquidity. Defaults to false. |
| `subaccount` | integer |  | Optional subaccount number to place the quote under (0 for primary, 1-63 for subaccounts) |


### `CreateQuoteResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | The ID of the newly created quote |


### `CreateRFQRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_ticker` | string | yes | The ticker of the market for which to create an RFQ |
| `contracts` | integer |  | Whole-contract count for the RFQ. Use contracts_fp for partial contract values; if both are provided, they must match. |
| `contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `target_cost_centi_cents` | integer (int64) |  | DEPRECATED: The target cost for the RFQ in centi-cents. Use target_cost_dollars instead. |
| `target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rest_remainder` | boolean | yes | Whether to rest the remainder of the RFQ after execution |
| `replace_existing` | boolean |  | Whether to delete existing RFQs as part of this RFQ's creation |
| `subtrader_id` | string |  | The subtrader to create the RFQ for (FCM members only) |
| `subaccount` | integer |  | The subaccount number to create the RFQ for (direct members only; 0 for primary, 1-63 for subaccounts) |


### `CreateRFQResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | The ID of the newly created RFQ |


### `CreateSubaccountResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_number` | integer | yes | The sequential number assigned to this subaccount (1-63). |


### `DailySchedule`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |


### `DecreaseOrderRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount` | integer |  | Optional subaccount number to use for this decrease (0 for primary, 1-63 for subaccounts) |
| `reduce_by` | integer |  | Number of contracts to reduce by (whole contracts only). Reduce-by may be provided via reduce_by or reduce_by_fp; if both provided they must match. Exactly one of reduce_by(/reduce_by_fp) or reduce… |
| `reduce_by_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `reduce_to` | integer |  | Number of contracts to reduce to (whole contracts only). Reduce-to may be provided via reduce_to or reduce_to_fp; if both provided they must match. Exactly one of reduce_by(/reduce_by_fp) or reduce… |
| `reduce_to_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `exchange_index` | object |  |  |


### `DecreaseOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |


### `DecreaseOrderV2Request`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reduce_by` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `reduce_to` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `exchange_index` | object |  |  |


### `DecreaseOrderV2Response`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `client_order_id` | string |  |  |
| `remaining_count` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `ts_ms` | integer (int64) | yes | Matching engine timestamp at which the decrease was processed, as Unix epoch milliseconds. |


### `Deposit`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the deposit. |
| `status` | enum(pending, applied, failed, returned) | yes | Current status of the deposit. 'applied' means funds are reflected in balance. |
| `type` | enum(ach, wire, crypto, debit, apm) | yes | Payment method used for the deposit. |
| `amount_cents` | integer (int64) | yes | Deposit amount in cents. |
| `fee_cents` | integer (int64) | yes | Fee charged for the deposit in cents. |
| `created_ts` | integer (int64) | yes | Unix timestamp of when the deposit was created. |
| `finalized_ts` | integer (int64) | null |  | Unix timestamp of when the deposit was finalized (applied, failed, or returned). |


### `EmptyResponse`

An empty response body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | object |  | An empty response body |


### `EndpointTokenCost`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `method` | string | yes | HTTP method for the endpoint. |
| `path` | string | yes | API route path for the endpoint. |
| `cost` | integer | yes | Configured token cost for an endpoint whose cost differs from the default cost. |


### `ErrorResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string |  | Error code |
| `message` | string |  | Human-readable error message |
| `details` | string |  | Additional details about the error, if available |
| `service` | string |  | The name of the service that generated the error |


### `EventData`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Unique identifier for this event. |
| `series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `sub_title` | string | yes | Shortened descriptive title for the event. |
| `title` | string | yes | Full title of the event. |
| `collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `category` | string |  | Event category (deprecated, use series-level category instead). |
| `strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `markets[].ticker` | string | yes |  |
| `markets[].event_ticker` | string | yes |  |
| `markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `markets[].title` | string |  |  |
| `markets[].subtitle` | string |  |  |
| `markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `markets[].created_time` | string (date-time) | yes |  |
| `markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `markets[].open_time` | string (date-time) | yes |  |
| `markets[].close_time` | string (date-time) | yes |  |
| `markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `markets[].expiration_time` | string (date-time) |  |  |
| `markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `markets[].can_close_early` | boolean | yes |  |
| `markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `markets[].mve_selected_legs` | array |  |  |
| `markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].primary_participant_key` | string | null |  |  |
| `markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `markets[].exchange_index` | object |  |  |
| `available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `product_metadata` | object | null |  | Additional metadata for the event. |
| `settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `settlement_sources[].name` | string |  | Name of the settlement source |
| `settlement_sources[].url` | string |  | URL to the settlement source |
| `last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |
| `fee_multiplier_override` | number (double) | null |  | Fee multiplier override for this event. Paired with fee_type_override. |
| `exchange_index` | object |  |  |


### `EventFeeChange`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for this fee change |
| `event_ticker` | string | yes | Event ticker this fee change applies to |
| `series_ticker` | string | yes | Series ticker for the event |
| `fee_type_override` | object | null | yes | New fee type override for the event. When null, the event clears any prior override and falls back to the parent series' fee structure. |
| `fee_multiplier_override` | number (double) | null | yes | New fee multiplier override for the event. When null, the event clears any prior override and falls back to the parent series' fee multiplier. |
| `scheduled_ts` | string (date-time) | yes | Timestamp when this fee change is scheduled to take effect |


### `EventPosition`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Unique identifier for events |
| `total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `total_cost_shares_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `ExchangeIndex`

Identifier for an exchange shard. Defaults to 0 if unspecified. Note: currently only 0 supported.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | integer |  | Identifier for an exchange shard. Defaults to 0 if unspecified. Note: currently only 0 supported. |


### `ExchangeInstance`

The exchange instance type

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(event_contract, margined) |  | The exchange instance type |


### `ExchangeStatus`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `exchange_active` | boolean | yes | False if the core Kalshi exchange is no longer taking any state changes at all. This includes but is not limited to trading, new users, and transfers. True unless we are under maintenance. |
| `trading_active` | boolean | yes | True if we are currently permitting trading on the exchange. This is true during trading hours and false outside exchange hours. Kalshi reserves the right to pause at any time in case issues are de… |
| `exchange_estimated_resume_time` | string (date-time) | null |  | Estimated downtime for the current exchange maintenance window. However, this is not guaranteed and can be extended. |


### `FeeType`

Fee type for a series or scheduled fee override.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(quadratic, quadratic_with_maker_fees, flat) |  | Fee type for a series or scheduled fee override. |


### `Fill`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fill_id` | string | yes | Unique identifier for this fill |
| `trade_id` | string | yes | Unique identifier for this fill (legacy field name, same as fill_id) |
| `order_id` | string | yes | Unique identifier for the order that resulted in this fill |
| `ticker` | string | yes | Unique identifier for the market |
| `market_ticker` | string | yes | Unique identifier for the market (legacy field name, same as ticker) |
| `side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `outcome_side` | enum(yes, no) | yes | The outcome side this fill positioned the user for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the … |
| `book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `is_taker` | boolean | yes | If true, this fill was a taker (removed liquidity from the order book) |
| `created_time` | string (date-time) |  | Timestamp when this fill was executed |
| `fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). Present for direct users. |
| `ts` | integer (int64) |  | Unix timestamp when this fill was executed (legacy field name) |


### `FixedPointCount`

Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals. Fractional contract values (e.g., "2.50") are supported on markets with fractional trading enabled; the minimum granularity is 0.01 contracts. Integer contract count fields are legacy and will be deprecated; when both integer and fp fields are provided, they must match.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `FixedPointDollars`

US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that market's price level structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `ForecastPercentilesPoint`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | The event ticker this forecast is for. |
| `end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the forecast period. |
| `period_interval` | integer (int32) | yes | Length of the forecast period in minutes. |
| `percentile_points` | array | yes | Array of forecast values at different percentiles. |
| `percentile_points[].percentile` | integer (int32) | yes | The percentile value (0-9999). |
| `percentile_points[].raw_numerical_forecast` | number | yes | The raw numerical forecast value. |
| `percentile_points[].numerical_forecast` | number | yes | The processed numerical forecast value. |
| `percentile_points[].formatted_forecast` | string | yes | The human-readable formatted forecast value. |


### `GenerateApiKeyRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Name for the API key. This helps identify the key's purpose |
| `scopes` | array |  | List of scopes to grant to the API key. If the broad `write` parent scope is included, `read` must also be included. Child scopes may be granted without the broad parent scope. Defaults to full acc… |
| `scopes[]` | enum(read, write, read::block_trade_accept, read::portfolio_balance, write::transfer, write::block_trade_accept) |  | Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`,… |


### `GenerateApiKeyResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key_id` | string | yes | Unique identifier for the newly generated API key |
| `private_key` | string | yes | RSA private key in PEM format. This must be stored securely and cannot be retrieved again after this response |


### `GetAccountApiLimitsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `usage_tier` | string | yes | User's effective Predictions API usage tier for these limits (for example, basic, advanced, expert, premier, paragon, prime, or prestige). |
| `read.refill_rate` | integer | yes | Tokens added to the bucket per second. |
| `read.bucket_capacity` | integer | yes | Maximum tokens the bucket can hold. When equal to refill_rate the bucket holds one second of budget; larger values represent burst headroom that idle clients accumulate and can spend in a single pu… |
| `write.refill_rate` | integer | yes | Tokens added to the bucket per second. |
| `write.bucket_capacity` | integer | yes | Maximum tokens the bucket can hold. When equal to refill_rate the bucket holds one second of budget; larger values represent burst headroom that idle clients accumulate and can spend in a single pu… |
| `grants` | array | yes | The caller's active API usage level grants across exchange lanes, where each grant applies to its exchange_instance and usage_tier reflects the effective tier for the lane reported by this endpoint. |
| `grants[].exchange_instance` | enum(event_contract, margined) | yes | The exchange instance type |
| `grants[].level` | string | yes | API usage level this grant confers (for example, expert, premier, paragon, prime, or prestige). |
| `grants[].expires_ts` | integer (int64) | null |  | Unix timestamp (seconds) when the grant expires. Absent for permanent grants. |
| `grants[].source` | string | yes | How the grant was created: "volume" (earned from trading volume) or "manual" (assigned by Kalshi). |


### `GetAccountApiUsageLevelVolumeProgressResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `volume_progress` | array | yes | Latest cron-computed trading volume progress toward volume-based API usage tiers for the predictions (event_contract) lane. Volume-based public tiers are Expert, Premier, Paragon, Prime, and Prestige. |
| `volume_progress[].computed_ts` | integer (int64) | yes | Unix timestamp (seconds) when this progress was computed; trailing_30d_volume_fp covers the trailing 30 days ending at this time. |
| `volume_progress[].trailing_30d_volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `volume_progress[].goals` | array | yes |  |
| `volume_progress[].goals[].level` | string | yes | API usage level for this Predictions volume goal. |
| `volume_progress[].goals[].earn_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `volume_progress[].goals[].keep_volume_goal_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `GetAccountEndpointCostsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `default_cost` | integer | yes | Default token cost applied to endpoints that are not listed in `endpoint_costs`. This is currently 10. |
| `endpoint_costs` | array | yes | API v2 endpoints whose configured token cost differs from `default_cost`. Endpoints that use the default cost are omitted. |
| `endpoint_costs[].method` | string | yes | HTTP method for the endpoint. |
| `endpoint_costs[].path` | string | yes | API route path for the endpoint. |
| `endpoint_costs[].cost` | integer | yes | Configured token cost for an endpoint whose cost differs from the default cost. |


### `GetApiKeysResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_keys` | array | yes | List of all API keys associated with the user |
| `api_keys[].api_key_id` | string | yes | Unique identifier for the API key |
| `api_keys[].name` | string | yes | User-provided name for the API key |
| `api_keys[].scopes` | array | yes | List of scopes granted to this API key. |
| `api_keys[].scopes[]` | enum(read, write, read::block_trade_accept, read::portfolio_balance, write::transfer, write::block_trade_accept) |  | Scope granted to an API key. Parent scopes grant broad access; for example, `read` grants all read endpoints and `write` grants all write endpoints. Child scopes such as `read::block_trade_accept`,… |


### `GetBalanceResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `balance` | integer (int64) | yes | Member's available balance in cents. This represents the amount available for trading. |
| `balance_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `portfolio_value` | integer (int64) | yes | Member's portfolio value in cents. This is the current value of all positions held. |
| `updated_ts` | integer (int64) | yes | Unix timestamp of the last update to the balance. |
| `balance_breakdown` | array |  | Balance broken down per exchange index. |
| `balance_breakdown[].exchange_index` | integer | yes | Identifier for an exchange shard. Defaults to 0 if unspecified. Note: currently only 0 supported. |
| `balance_breakdown[].balance` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `GetBlockTradeProposalsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_trade_proposals` | array | yes | List of block trade proposals |
| `block_trade_proposals[].id` | string | yes | Unique identifier for the block trade proposal |
| `block_trade_proposals[].proposer_user_id` | string | yes | User ID of the proposal creator |
| `block_trade_proposals[].buyer_user_id` | string | yes | User ID of the buyer. Empty when the authenticated user is not the buyer. |
| `block_trade_proposals[].buyer_subtrader_id` | string |  | Subtrader ID of the buyer. Empty when the authenticated user is not the buyer. |
| `block_trade_proposals[].seller_user_id` | string | yes | User ID of the seller. Empty when the authenticated user is not the seller. |
| `block_trade_proposals[].seller_subtrader_id` | string |  | Subtrader ID of the seller. Empty when the authenticated user is not the seller. |
| `block_trade_proposals[].market_ticker` | string | yes | The ticker of the market for this block trade |
| `block_trade_proposals[].price_centi_cents` | integer (int64) | yes | Price in centi-cents |
| `block_trade_proposals[].centicount` | integer (int64) | yes | Number of contracts in centicounts |
| `block_trade_proposals[].maker_side` | enum(yes, no) | yes | The maker side of the trade |
| `block_trade_proposals[].expiration_ts` | string (date-time) | yes | Expiration time of the proposal |
| `block_trade_proposals[].status` | string | yes | Current status of the proposal |
| `block_trade_proposals[].created_ts` | string (date-time) | yes | Timestamp when the proposal was created |
| `block_trade_proposals[].updated_ts` | string (date-time) | yes | Timestamp when the proposal was last updated |
| `block_trade_proposals[].buyer_accepted` | boolean | yes | Whether the buyer has accepted the proposal |
| `block_trade_proposals[].seller_accepted` | boolean | yes | Whether the seller has accepted the proposal |
| `block_trade_proposals[].buyer_accepted_ts` | string (date-time) |  | Timestamp when the buyer accepted |
| `block_trade_proposals[].seller_accepted_ts` | string (date-time) |  | Timestamp when the seller accepted |
| `block_trade_proposals[].executed_ts` | string (date-time) |  | Timestamp when the proposal was executed |
| `block_trade_proposals[].buyer_order_id` | string |  | Order ID for the buyer after the proposal is executed |
| `block_trade_proposals[].seller_order_id` | string |  | Order ID for the seller after the proposal is executed |
| `cursor` | string |  | Cursor for pagination to get the next page of results |


### `GetCommunicationsIDResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `communications_id` | string | yes | A public communications ID which is used to identify the user |


### `GetDepositsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deposits` | array | yes |  |
| `deposits[].id` | string | yes | Unique identifier for the deposit. |
| `deposits[].status` | enum(pending, applied, failed, returned) | yes | Current status of the deposit. 'applied' means funds are reflected in balance. |
| `deposits[].type` | enum(ach, wire, crypto, debit, apm) | yes | Payment method used for the deposit. |
| `deposits[].amount_cents` | integer (int64) | yes | Deposit amount in cents. |
| `deposits[].fee_cents` | integer (int64) | yes | Fee charged for the deposit in cents. |
| `deposits[].created_ts` | integer (int64) | yes | Unix timestamp of when the deposit was created. |
| `deposits[].finalized_ts` | integer (int64) | null |  | Unix timestamp of when the deposit was finalized (applied, failed, or returned). |
| `cursor` | string |  |  |


### `GetEventCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_tickers` | array | yes | Array of market tickers in the event. |
| `market_tickers[]` | string |  |  |
| `market_candlesticks` | array | yes | Array of market candlestick arrays, one for each market in the event. |
| `market_candlesticks[][]` | array |  |  |
| `market_candlesticks[][].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `market_candlesticks[][].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_candlesticks[][].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market_candlesticks[][].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `adjusted_end_ts` | integer (int64) | yes | Adjusted end timestamp if the requested candlesticks would be larger than maxAggregateCandidates. |


### `GetEventFeeChangesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_fee_changes` | array | yes |  |
| `event_fee_changes[].id` | string | yes | Unique identifier for this fee change |
| `event_fee_changes[].event_ticker` | string | yes | Event ticker this fee change applies to |
| `event_fee_changes[].series_ticker` | string | yes | Series ticker for the event |
| `event_fee_changes[].fee_type_override` | object | null | yes | New fee type override for the event. When null, the event clears any prior override and falls back to the parent series' fee structure. |
| `event_fee_changes[].fee_multiplier_override` | number (double) | null | yes | New fee multiplier override for the event. When null, the event clears any prior override and falls back to the parent series' fee multiplier. |
| `event_fee_changes[].scheduled_ts` | string (date-time) | yes | Timestamp when this fee change is scheduled to take effect |
| `cursor` | string | yes | Pagination cursor for the next page. Empty if there are no more results. |


### `GetEventForecastPercentilesHistoryResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `forecast_history` | array | yes | Array of forecast percentile data points over time. |
| `forecast_history[].event_ticker` | string | yes | The event ticker this forecast is for. |
| `forecast_history[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the forecast period. |
| `forecast_history[].period_interval` | integer (int32) | yes | Length of the forecast period in minutes. |
| `forecast_history[].percentile_points` | array | yes | Array of forecast values at different percentiles. |
| `forecast_history[].percentile_points[].percentile` | integer (int32) | yes | The percentile value (0-9999). |
| `forecast_history[].percentile_points[].raw_numerical_forecast` | number | yes | The raw numerical forecast value. |
| `forecast_history[].percentile_points[].numerical_forecast` | number | yes | The processed numerical forecast value. |
| `forecast_history[].percentile_points[].formatted_forecast` | string | yes | The human-readable formatted forecast value. |


### `GetEventMetadataResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_url` | string | yes | A path to an image that represents this event. |
| `featured_image_url` | string |  | A path to an image that represents the image of the featured market. |
| `market_details` | array | yes | Metadata for the markets in this event. |
| `market_details[].market_ticker` | string | yes | The ticker of the market. |
| `market_details[].image_url` | string | yes | A path to an image that represents this market. |
| `market_details[].color_code` | string | yes | The color code for the market. |
| `settlement_sources` | array | yes | A list of settlement sources for this event. |
| `settlement_sources[].name` | string |  | Name of the settlement source |
| `settlement_sources[].url` | string |  | URL to the settlement source |
| `competition` | string | null |  | Event competition. |
| `competition_scope` | string | null |  | Event scope, based on the competition. |


### `GetEventResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event.event_ticker` | string | yes | Unique identifier for this event. |
| `event.series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `event.sub_title` | string | yes | Shortened descriptive title for the event. |
| `event.title` | string | yes | Full title of the event. |
| `event.collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `event.mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `event.category` | string |  | Event category (deprecated, use series-level category instead). |
| `event.strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `event.strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `event.markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `event.markets[].ticker` | string | yes |  |
| `event.markets[].event_ticker` | string | yes |  |
| `event.markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `event.markets[].title` | string |  |  |
| `event.markets[].subtitle` | string |  |  |
| `event.markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `event.markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `event.markets[].created_time` | string (date-time) | yes |  |
| `event.markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `event.markets[].open_time` | string (date-time) | yes |  |
| `event.markets[].close_time` | string (date-time) | yes |  |
| `event.markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `event.markets[].expiration_time` | string (date-time) |  |  |
| `event.markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `event.markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `event.markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `event.markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `event.markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `event.markets[].can_close_early` | boolean | yes |  |
| `event.markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `event.markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event.markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `event.markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `event.markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `event.markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `event.markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `event.markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `event.markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `event.markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `event.markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `event.markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `event.markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `event.markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `event.markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `event.markets[].mve_selected_legs` | array |  |  |
| `event.markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `event.markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `event.markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `event.markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event.markets[].primary_participant_key` | string | null |  |  |
| `event.markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `event.markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `event.markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `event.markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `event.markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `event.markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `event.markets[].exchange_index` | object |  |  |
| `event.available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `event.product_metadata` | object | null |  | Additional metadata for the event. |
| `event.settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `event.settlement_sources[].name` | string |  | Name of the settlement source |
| `event.settlement_sources[].url` | string |  | URL to the settlement source |
| `event.last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `event.fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |
| `event.fee_multiplier_override` | number (double) | null |  | Fee multiplier override for this event. Paired with fee_type_override. |
| `event.exchange_index` | object |  |  |
| `markets` | array | yes | Data for the markets in this event. This field is deprecated in favour of the "markets" field inside the event. Which will be filled with the same value if you use the query parameter "with_nested_… |
| `markets[].ticker` | string | yes |  |
| `markets[].event_ticker` | string | yes |  |
| `markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `markets[].title` | string |  |  |
| `markets[].subtitle` | string |  |  |
| `markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `markets[].created_time` | string (date-time) | yes |  |
| `markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `markets[].open_time` | string (date-time) | yes |  |
| `markets[].close_time` | string (date-time) | yes |  |
| `markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `markets[].expiration_time` | string (date-time) |  |  |
| `markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `markets[].can_close_early` | boolean | yes |  |
| `markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `markets[].mve_selected_legs` | array |  |  |
| `markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].primary_participant_key` | string | null |  |  |
| `markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `markets[].exchange_index` | object |  |  |


### `GetEventsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `events` | array | yes | Array of events matching the query criteria. |
| `events[].event_ticker` | string | yes | Unique identifier for this event. |
| `events[].series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `events[].sub_title` | string | yes | Shortened descriptive title for the event. |
| `events[].title` | string | yes | Full title of the event. |
| `events[].collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `events[].mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `events[].category` | string |  | Event category (deprecated, use series-level category instead). |
| `events[].strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `events[].strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `events[].markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `events[].markets[].ticker` | string | yes |  |
| `events[].markets[].event_ticker` | string | yes |  |
| `events[].markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `events[].markets[].title` | string |  |  |
| `events[].markets[].subtitle` | string |  |  |
| `events[].markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `events[].markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `events[].markets[].created_time` | string (date-time) | yes |  |
| `events[].markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `events[].markets[].open_time` | string (date-time) | yes |  |
| `events[].markets[].close_time` | string (date-time) | yes |  |
| `events[].markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `events[].markets[].expiration_time` | string (date-time) |  |  |
| `events[].markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `events[].markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `events[].markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `events[].markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `events[].markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `events[].markets[].can_close_early` | boolean | yes |  |
| `events[].markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `events[].markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `events[].markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `events[].markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `events[].markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `events[].markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `events[].markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `events[].markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `events[].markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `events[].markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `events[].markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `events[].markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `events[].markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `events[].markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `events[].markets[].mve_selected_legs` | array |  |  |
| `events[].markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `events[].markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `events[].markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `events[].markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].primary_participant_key` | string | null |  |  |
| `events[].markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `events[].markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `events[].markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `events[].markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `events[].markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `events[].markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `events[].markets[].exchange_index` | object |  |  |
| `events[].available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `events[].product_metadata` | object | null |  | Additional metadata for the event. |
| `events[].settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `events[].settlement_sources[].name` | string |  | Name of the settlement source |
| `events[].settlement_sources[].url` | string |  | URL to the settlement source |
| `events[].last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `events[].fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |
| `events[].fee_multiplier_override` | number (double) | null |  | Fee multiplier override for this event. Paired with fee_type_override. |
| `events[].exchange_index` | object |  |  |
| `milestones` | array |  | Array of milestones related to the events. |
| `milestones[].id` | string | yes | Unique identifier for the milestone. |
| `milestones[].category` | string | yes | Category of the milestone. E.g. Sports, Elections, Esports, Crypto. |
| `milestones[].type` | string | yes | Type of the milestone. E.g. football_game, basketball_game, soccer_tournament_multi_leg, baseball_game, hockey_match, golf_tournament, political_race. |
| `milestones[].start_date` | string (date-time) | yes | Start date of the milestone. |
| `milestones[].end_date` | string (date-time) | null |  | End date of the milestone, if any. |
| `milestones[].related_event_tickers` | array | yes | List of event tickers related to this milestone. |
| `milestones[].related_event_tickers[]` | string |  |  |
| `milestones[].title` | string | yes | Title of the milestone. |
| `milestones[].notification_message` | string | yes | Notification message for the milestone. |
| `milestones[].source_id` | string | null |  | Source id of milestone if available. |
| `milestones[].source_ids` | object |  | Source ids of milestone if available. |
| `milestones[].details` | object | yes | Additional details about the milestone. |
| `milestones[].primary_event_tickers` | array | yes | List of event tickers directly related to the outcome of this milestone. |
| `milestones[].primary_event_tickers[]` | string |  |  |
| `milestones[].last_updated_ts` | string (date-time) | yes | Last time this structured target was updated. |
| `cursor` | string | yes | Pagination cursor for the next page. Empty if there are no more results. |


### `GetExchangeAnnouncementsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `announcements` | array | yes | A list of exchange-wide announcements. |
| `announcements[].type` | enum(info, warning, error) | yes | The type of the announcement. |
| `announcements[].message` | string | yes | The message contained within the announcement. |
| `announcements[].delivery_time` | string (date-time) | yes | The time the announcement was delivered. |
| `announcements[].status` | enum(active, inactive) | yes | The current status of this announcement. |


### `GetExchangeScheduleResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schedule.standard_hours` | array | yes | The standard operating hours of the exchange. All times are expressed in ET. Outside of these times trading will be unavailable. |
| `schedule.standard_hours[].start_time` | string (date-time) | yes | Start date and time for when this weekly schedule is effective. |
| `schedule.standard_hours[].end_time` | string (date-time) | yes | End date and time for when this weekly schedule is no longer effective. |
| `schedule.standard_hours[].monday` | array | yes | Trading hours for Monday. May contain multiple sessions. |
| `schedule.standard_hours[].monday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].monday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].tuesday` | array | yes | Trading hours for Tuesday. May contain multiple sessions. |
| `schedule.standard_hours[].tuesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].tuesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].wednesday` | array | yes | Trading hours for Wednesday. May contain multiple sessions. |
| `schedule.standard_hours[].wednesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].wednesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].thursday` | array | yes | Trading hours for Thursday. May contain multiple sessions. |
| `schedule.standard_hours[].thursday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].thursday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].friday` | array | yes | Trading hours for Friday. May contain multiple sessions. |
| `schedule.standard_hours[].friday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].friday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].saturday` | array | yes | Trading hours for Saturday. May contain multiple sessions. |
| `schedule.standard_hours[].saturday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].saturday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].sunday` | array | yes | Trading hours for Sunday. May contain multiple sessions. |
| `schedule.standard_hours[].sunday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `schedule.standard_hours[].sunday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `schedule.maintenance_windows` | array | yes | Scheduled maintenance windows, during which the exchange may be unavailable. |
| `schedule.maintenance_windows[].start_datetime` | string (date-time) | yes | Start date and time of the maintenance window. |
| `schedule.maintenance_windows[].end_datetime` | string (date-time) | yes | End date and time of the maintenance window. |


### `GetFillsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fills` | array | yes |  |
| `fills[].fill_id` | string | yes | Unique identifier for this fill |
| `fills[].trade_id` | string | yes | Unique identifier for this fill (legacy field name, same as fill_id) |
| `fills[].order_id` | string | yes | Unique identifier for the order that resulted in this fill |
| `fills[].ticker` | string | yes | Unique identifier for the market |
| `fills[].market_ticker` | string | yes | Unique identifier for the market (legacy field name, same as ticker) |
| `fills[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `fills[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `fills[].outcome_side` | enum(yes, no) | yes | The outcome side this fill positioned the user for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the … |
| `fills[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `fills[].count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `fills[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].is_taker` | boolean | yes | If true, this fill was a taker (removed liquidity from the order book) |
| `fills[].created_time` | string (date-time) |  | Timestamp when this fill was executed |
| `fills[].fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fills[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). Present for direct users. |
| `fills[].ts` | integer (int64) |  | Unix timestamp when this fill was executed (legacy field name) |
| `cursor` | string | yes |  |


### `GetFiltersBySportsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filters_by_sports` | object | yes | Mapping of sports to their filter details |
| `sport_ordering` | array | yes | Ordered list of sports for display |
| `sport_ordering[]` | string |  |  |


### `GetGameStatsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pbp.periods` | array |  |  |
| `pbp.periods[].events` | array |  |  |
| `pbp.periods[].events[]` | object |  |  |


### `GetHistoricalCutoffResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_settled_ts` | string (date-time) | yes | Cutoff based on **market settlement time**. Markets and their candlesticks that settled before this timestamp must be accessed via `GET /historical/markets` and `GET /historical/markets/{ticker}/ca… |
| `trades_created_ts` | string (date-time) | yes | Cutoff based on **trade fill time**. Fills that occurred before this timestamp must be accessed via `GET /historical/fills`. |
| `orders_updated_ts` | string (date-time) | yes | Cutoff based on **order cancellation or execution time**. Orders canceled or fully executed before this timestamp must be accessed via `GET /historical/orders`. Resting (active) orders are always a… |


### `GetIncentiveProgramsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `incentive_programs` | array | yes |  |
| `incentive_programs[].id` | string | yes | Unique identifier for the incentive program |
| `incentive_programs[].market_id` | string | yes | The unique identifier of the market associated with this incentive program |
| `incentive_programs[].market_ticker` | string | yes | The ticker symbol of the market associated with this incentive program |
| `incentive_programs[].incentive_type` | enum(liquidity, volume) | yes | Type of incentive program |
| `incentive_programs[].incentive_description` | string | yes | Plain text description of the incentive program |
| `incentive_programs[].start_date` | string (date-time) | yes | Start date of the incentive program |
| `incentive_programs[].end_date` | string (date-time) | yes | End date of the incentive program |
| `incentive_programs[].period_reward` | integer (int64) | yes | Total reward for the period in centi-cents |
| `incentive_programs[].paid_out` | boolean | yes | Whether the incentive has been paid out |
| `incentive_programs[].discount_factor_bps` | integer (int32) | null |  | Discount factor in basis points (optional) |
| `incentive_programs[].target_size_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `next_cursor` | string |  | Cursor for pagination to get the next page of results |


### `GetLiveDataResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `live_data.type` | string | yes | Type of live data |
| `live_data.details` | object | yes | Live data details as a flexible object |
| `live_data.milestone_id` | string | yes | Milestone ID |


### `GetLiveDatasResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `live_datas` | array | yes |  |
| `live_datas[].type` | string | yes | Type of live data |
| `live_datas[].details` | object | yes | Live data details as a flexible object |
| `live_datas[].milestone_id` | string | yes | Milestone ID |


### `GetMarketCandlesticksHistoricalResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Unique identifier for the market. |
| `candlesticks` | array | yes | Array of candlestick data points for the specified time range. |
| `candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `candlesticks[].yes_bid.open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.open` | object | null | yes | Price of the first trade during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.low` | object | null | yes | Lowest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.high` | object | null | yes | Highest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.close` | object | null | yes | Price of the last trade during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.mean` | object | null | yes | Volume-weighted average price during the candlestick period (in dollars). Null if no trades occurred. |
| `candlesticks[].price.previous` | object | null | yes | Close price from the previous candlestick period (in dollars). Null if this is the first candlestick or no prior trade exists. |
| `candlesticks[].volume` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `candlesticks[].open_interest` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `GetMarketCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Unique identifier for the market. |
| `candlesticks` | array | yes | Array of candlestick data points for the specified time range. |
| `candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `candlesticks[].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `candlesticks[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `GetMarketOrderbookResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orderbook_fp.yes_dollars` | array | yes |  |
| `orderbook_fp.yes_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbook_fp.yes_dollars[][]` | string |  |  |
| `orderbook_fp.no_dollars` | array | yes |  |
| `orderbook_fp.no_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbook_fp.no_dollars[][]` | string |  |  |


### `GetMarketOrderbooksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orderbooks` | array | yes |  |
| `orderbooks[].ticker` | string | yes |  |
| `orderbooks[].orderbook_fp.yes_dollars` | array | yes |  |
| `orderbooks[].orderbook_fp.yes_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbooks[].orderbook_fp.yes_dollars[][]` | string |  |  |
| `orderbooks[].orderbook_fp.no_dollars` | array | yes |  |
| `orderbooks[].orderbook_fp.no_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbooks[].orderbook_fp.no_dollars[][]` | string |  |  |


### `GetMarketResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market.ticker` | string | yes |  |
| `market.event_ticker` | string | yes |  |
| `market.market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `market.title` | string |  |  |
| `market.subtitle` | string |  |  |
| `market.yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `market.no_sub_title` | string | yes | Shortened title for the no side of this market |
| `market.created_time` | string (date-time) | yes |  |
| `market.updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `market.open_time` | string (date-time) | yes |  |
| `market.close_time` | string (date-time) | yes |  |
| `market.expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `market.expiration_time` | string (date-time) |  |  |
| `market.latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `market.settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `market.status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `market.response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `market.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.result` | enum(yes, no, scalar, ) | yes |  |
| `market.can_close_early` | boolean | yes |  |
| `market.fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `market.open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market.notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `market.expiration_value` | string | yes | The value that was considered for the settlement |
| `market.occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `market.fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `market.early_close_condition` | string | null |  | The condition under which the market can close early |
| `market.strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `market.floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `market.cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `market.functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `market.custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `market.rules_primary` | string | yes | A plain language description of the most important market terms |
| `market.rules_secondary` | string | yes | A plain language description of secondary market terms |
| `market.mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `market.mve_selected_legs` | array |  |  |
| `market.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `market.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `market.mve_selected_legs[].side` | string |  | The side of the selected market |
| `market.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market.primary_participant_key` | string | null |  |  |
| `market.price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `market.price_ranges` | array | yes | Valid price ranges for orders on this market |
| `market.price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `market.price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `market.price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `market.is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `market.exchange_index` | object |  |  |


### `GetMarketsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markets` | array | yes |  |
| `markets[].ticker` | string | yes |  |
| `markets[].event_ticker` | string | yes |  |
| `markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `markets[].title` | string |  |  |
| `markets[].subtitle` | string |  |  |
| `markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `markets[].created_time` | string (date-time) | yes |  |
| `markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `markets[].open_time` | string (date-time) | yes |  |
| `markets[].close_time` | string (date-time) | yes |  |
| `markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `markets[].expiration_time` | string (date-time) |  |  |
| `markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `markets[].can_close_early` | boolean | yes |  |
| `markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `markets[].mve_selected_legs` | array |  |  |
| `markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `markets[].primary_participant_key` | string | null |  |  |
| `markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `markets[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


### `GetMilestoneResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `milestone.id` | string | yes | Unique identifier for the milestone. |
| `milestone.category` | string | yes | Category of the milestone. E.g. Sports, Elections, Esports, Crypto. |
| `milestone.type` | string | yes | Type of the milestone. E.g. football_game, basketball_game, soccer_tournament_multi_leg, baseball_game, hockey_match, golf_tournament, political_race. |
| `milestone.start_date` | string (date-time) | yes | Start date of the milestone. |
| `milestone.end_date` | string (date-time) | null |  | End date of the milestone, if any. |
| `milestone.related_event_tickers` | array | yes | List of event tickers related to this milestone. |
| `milestone.related_event_tickers[]` | string |  |  |
| `milestone.title` | string | yes | Title of the milestone. |
| `milestone.notification_message` | string | yes | Notification message for the milestone. |
| `milestone.source_id` | string | null |  | Source id of milestone if available. |
| `milestone.source_ids` | object |  | Source ids of milestone if available. |
| `milestone.details` | object | yes | Additional details about the milestone. |
| `milestone.primary_event_tickers` | array | yes | List of event tickers directly related to the outcome of this milestone. |
| `milestone.primary_event_tickers[]` | string |  |  |
| `milestone.last_updated_ts` | string (date-time) | yes | Last time this structured target was updated. |


### `GetMilestonesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `milestones` | array | yes | List of milestones. |
| `milestones[].id` | string | yes | Unique identifier for the milestone. |
| `milestones[].category` | string | yes | Category of the milestone. E.g. Sports, Elections, Esports, Crypto. |
| `milestones[].type` | string | yes | Type of the milestone. E.g. football_game, basketball_game, soccer_tournament_multi_leg, baseball_game, hockey_match, golf_tournament, political_race. |
| `milestones[].start_date` | string (date-time) | yes | Start date of the milestone. |
| `milestones[].end_date` | string (date-time) | null |  | End date of the milestone, if any. |
| `milestones[].related_event_tickers` | array | yes | List of event tickers related to this milestone. |
| `milestones[].related_event_tickers[]` | string |  |  |
| `milestones[].title` | string | yes | Title of the milestone. |
| `milestones[].notification_message` | string | yes | Notification message for the milestone. |
| `milestones[].source_id` | string | null |  | Source id of milestone if available. |
| `milestones[].source_ids` | object |  | Source ids of milestone if available. |
| `milestones[].details` | object | yes | Additional details about the milestone. |
| `milestones[].primary_event_tickers` | array | yes | List of event tickers directly related to the outcome of this milestone. |
| `milestones[].primary_event_tickers[]` | string |  |  |
| `milestones[].last_updated_ts` | string (date-time) | yes | Last time this structured target was updated. |
| `cursor` | string |  | Cursor for pagination. |


### `GetMultivariateEventCollectionLookupHistoryResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lookup_points` | array | yes | List of recent lookup points in the collection. |
| `lookup_points[].event_ticker` | string | yes | Event ticker for the lookup point. |
| `lookup_points[].market_ticker` | string | yes | Market ticker for the lookup point. |
| `lookup_points[].selected_markets` | array | yes | Markets that were selected for this lookup. |
| `lookup_points[].selected_markets[].market_ticker` | string | yes | Market ticker identifier. |
| `lookup_points[].selected_markets[].event_ticker` | string | yes | Event ticker identifier. |
| `lookup_points[].selected_markets[].side` | enum(yes, no) | yes | Side of the market (yes or no). |
| `lookup_points[].last_queried_ts` | string (date-time) | yes | Timestamp when this lookup was last queried. |


### `GetMultivariateEventCollectionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `multivariate_contract.collection_ticker` | string | yes | Unique identifier for the collection. |
| `multivariate_contract.series_ticker` | string | yes | Series associated with the collection. Events produced in the collection will be associated with this series. |
| `multivariate_contract.title` | string | yes | Title of the collection. |
| `multivariate_contract.description` | string | yes | Short description of the collection. |
| `multivariate_contract.open_date` | string (date-time) | yes | The open date of the collection. Before this time, the collection cannot be interacted with. |
| `multivariate_contract.close_date` | string (date-time) | yes | The close date of the collection. After this time, the collection cannot be interacted with. |
| `multivariate_contract.associated_events` | array | yes | List of events with their individual configuration. |
| `multivariate_contract.associated_events[].ticker` | string | yes | The event ticker. |
| `multivariate_contract.associated_events[].is_yes_only` | boolean | yes | Whether only the 'yes' side can be used for this event. |
| `multivariate_contract.associated_events[].size_max` | integer (int32) | null |  | Maximum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contract.associated_events[].size_min` | integer (int32) | null |  | Minimum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contract.associated_events[].active_quoters` | array | yes | List of active quoters for this event. |
| `multivariate_contract.associated_events[].active_quoters[]` | string |  |  |
| `multivariate_contract.associated_event_tickers` | array | yes | [DEPRECATED - Use associated_events instead] A list of events associated with the collection. Markets in these events can be passed as inputs to the Lookup and Create endpoints. |
| `multivariate_contract.associated_event_tickers[]` | string |  |  |
| `multivariate_contract.is_ordered` | boolean | yes | Whether the collection is ordered. If true, the order of markets passed into Lookup/Create affects the output. If false, the order does not matter. |
| `multivariate_contract.is_single_market_per_event` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection accepts multiple markets from the same event passed into Lookup/Create. |
| `multivariate_contract.is_all_yes` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection requires that only the market side of 'yes' may be used. |
| `multivariate_contract.size_min` | integer (int32) | yes | The minimum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contract.size_max` | integer (int32) | yes | The maximum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contract.functional_description` | string | yes | A functional description of the collection describing how inputs affect the output. |


### `GetMultivariateEventCollectionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `multivariate_contracts` | array | yes | List of multivariate event collections. |
| `multivariate_contracts[].collection_ticker` | string | yes | Unique identifier for the collection. |
| `multivariate_contracts[].series_ticker` | string | yes | Series associated with the collection. Events produced in the collection will be associated with this series. |
| `multivariate_contracts[].title` | string | yes | Title of the collection. |
| `multivariate_contracts[].description` | string | yes | Short description of the collection. |
| `multivariate_contracts[].open_date` | string (date-time) | yes | The open date of the collection. Before this time, the collection cannot be interacted with. |
| `multivariate_contracts[].close_date` | string (date-time) | yes | The close date of the collection. After this time, the collection cannot be interacted with. |
| `multivariate_contracts[].associated_events` | array | yes | List of events with their individual configuration. |
| `multivariate_contracts[].associated_events[].ticker` | string | yes | The event ticker. |
| `multivariate_contracts[].associated_events[].is_yes_only` | boolean | yes | Whether only the 'yes' side can be used for this event. |
| `multivariate_contracts[].associated_events[].size_max` | integer (int32) | null |  | Maximum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contracts[].associated_events[].size_min` | integer (int32) | null |  | Minimum number of markets from this event (inclusive). Null means no limit. |
| `multivariate_contracts[].associated_events[].active_quoters` | array | yes | List of active quoters for this event. |
| `multivariate_contracts[].associated_events[].active_quoters[]` | string |  |  |
| `multivariate_contracts[].associated_event_tickers` | array | yes | [DEPRECATED - Use associated_events instead] A list of events associated with the collection. Markets in these events can be passed as inputs to the Lookup and Create endpoints. |
| `multivariate_contracts[].associated_event_tickers[]` | string |  |  |
| `multivariate_contracts[].is_ordered` | boolean | yes | Whether the collection is ordered. If true, the order of markets passed into Lookup/Create affects the output. If false, the order does not matter. |
| `multivariate_contracts[].is_single_market_per_event` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection accepts multiple markets from the same event passed into Lookup/Create. |
| `multivariate_contracts[].is_all_yes` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection requires that only the market side of 'yes' may be used. |
| `multivariate_contracts[].size_min` | integer (int32) | yes | The minimum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contracts[].size_max` | integer (int32) | yes | The maximum number of markets that must be passed into Lookup/Create (inclusive). |
| `multivariate_contracts[].functional_description` | string | yes | A functional description of the collection describing how inputs affect the output. |
| `cursor` | string |  | The Cursor represents a pointer to the next page of records in the pagination. Use the value returned here in the cursor query parameter for this end-point to get the next page containing limit rec… |


### `GetMultivariateEventsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `events` | array | yes | Array of multivariate events matching the query criteria. |
| `events[].event_ticker` | string | yes | Unique identifier for this event. |
| `events[].series_ticker` | string | yes | Unique identifier for the series this event belongs to. |
| `events[].sub_title` | string | yes | Shortened descriptive title for the event. |
| `events[].title` | string | yes | Full title of the event. |
| `events[].collateral_return_type` | string | yes | Specifies how collateral is returned when markets settle (e.g., 'binary' for standard yes/no markets). |
| `events[].mutually_exclusive` | boolean | yes | If true, only one market in this event can resolve to 'yes'. If false, multiple markets can resolve to 'yes'. |
| `events[].category` | string |  | Event category (deprecated, use series-level category instead). |
| `events[].strike_date` | string (date-time) | null |  | The specific date this event is based on. Only filled when the event uses a date strike (mutually exclusive with strike_period). |
| `events[].strike_period` | string | null |  | The time period this event covers (e.g., 'week', 'month'). Only filled when the event uses a period strike (mutually exclusive with strike_date). |
| `events[].markets` | array |  | Array of markets associated with this event. Only populated when 'with_nested_markets=true' is specified in the request. |
| `events[].markets[].ticker` | string | yes |  |
| `events[].markets[].event_ticker` | string | yes |  |
| `events[].markets[].market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `events[].markets[].title` | string |  |  |
| `events[].markets[].subtitle` | string |  |  |
| `events[].markets[].yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `events[].markets[].no_sub_title` | string | yes | Shortened title for the no side of this market |
| `events[].markets[].created_time` | string (date-time) | yes |  |
| `events[].markets[].updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `events[].markets[].open_time` | string (date-time) | yes |  |
| `events[].markets[].close_time` | string (date-time) | yes |  |
| `events[].markets[].expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `events[].markets[].expiration_time` | string (date-time) |  |  |
| `events[].markets[].latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `events[].markets[].settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `events[].markets[].status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `events[].markets[].response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `events[].markets[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].result` | enum(yes, no, scalar, ) | yes |  |
| `events[].markets[].can_close_early` | boolean | yes |  |
| `events[].markets[].fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `events[].markets[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `events[].markets[].notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `events[].markets[].expiration_value` | string | yes | The value that was considered for the settlement |
| `events[].markets[].occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `events[].markets[].fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `events[].markets[].early_close_condition` | string | null |  | The condition under which the market can close early |
| `events[].markets[].strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `events[].markets[].floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `events[].markets[].cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `events[].markets[].functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `events[].markets[].custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `events[].markets[].rules_primary` | string | yes | A plain language description of the most important market terms |
| `events[].markets[].rules_secondary` | string | yes | A plain language description of secondary market terms |
| `events[].markets[].mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `events[].markets[].mve_selected_legs` | array |  |  |
| `events[].markets[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `events[].markets[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `events[].markets[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `events[].markets[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `events[].markets[].primary_participant_key` | string | null |  |  |
| `events[].markets[].price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `events[].markets[].price_ranges` | array | yes | Valid price ranges for orders on this market |
| `events[].markets[].price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `events[].markets[].price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `events[].markets[].price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `events[].markets[].is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `events[].markets[].exchange_index` | object |  |  |
| `events[].available_on_brokers` | boolean | yes | Whether this event is available to trade on brokers. |
| `events[].product_metadata` | object | null |  | Additional metadata for the event. |
| `events[].settlement_sources` | array | yes | The official sources used for the determination of markets within this event. Methodology is defined in the rulebook. |
| `events[].settlement_sources[].name` | string |  | Name of the settlement source |
| `events[].settlement_sources[].url` | string |  | URL to the settlement source |
| `events[].last_updated_ts` | string (date-time) |  | Timestamp of when this event's metadata was last updated. |
| `events[].fee_type_override` | string | null |  | Fee type override for this event. When present, takes precedence over the series-level fee for this event's markets. |
| `events[].fee_multiplier_override` | number (double) | null |  | Fee multiplier override for this event. Paired with fee_type_override. |
| `events[].exchange_index` | object |  |  |
| `cursor` | string | yes | Pagination cursor for the next page. Empty if there are no more results. |


### `GetOrderGroupResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_auto_cancel_enabled` | boolean | yes | Whether auto-cancel is enabled for this order group |
| `contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders` | array | yes | List of order IDs that belong to this order group |
| `orders[]` | string |  |  |
| `exchange_index` | object |  |  |


### `GetOrderGroupsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_groups` | array |  |  |
| `order_groups[].id` | string | yes | Unique identifier for the order group |
| `order_groups[].contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order_groups[].is_auto_cancel_enabled` | boolean | yes | Whether auto-cancel is enabled for this order group |
| `order_groups[].exchange_index` | object |  |  |


### `GetOrderQueuePositionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queue_position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `GetOrderQueuePositionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queue_positions` | array | yes | Queue positions for all matching orders |
| `queue_positions[].order_id` | string | yes | The order ID |
| `queue_positions[].market_ticker` | string | yes | The market ticker |
| `queue_positions[].queue_position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `GetOrderResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order.order_id` | string | yes |  |
| `order.user_id` | string | yes | Unique identifier for users |
| `order.client_order_id` | string | yes |  |
| `order.ticker` | string | yes |  |
| `order.side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `order.outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `order.book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `order.type` | enum(limit, market) | yes |  |
| `order.status` | enum(resting, canceled, executed) | yes | The status of an order |
| `order.yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `order.taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `order.expiration_time` | string (date-time) | null |  |  |
| `order.created_time` | string (date-time) | null |  |  |
| `order.last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `order.self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order.order_group_id` | string | null |  | The order group this order is part of |
| `order.cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `order.subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `order.exchange_index` | object |  |  |


### `GetOrdersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `orders` | array | yes |  |
| `orders[].order_id` | string | yes |  |
| `orders[].user_id` | string | yes | Unique identifier for users |
| `orders[].client_order_id` | string | yes |  |
| `orders[].ticker` | string | yes |  |
| `orders[].side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `orders[].outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `orders[].book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `orders[].type` | enum(limit, market) | yes |  |
| `orders[].status` | enum(resting, canceled, executed) | yes | The status of an order |
| `orders[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `orders[].taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `orders[].expiration_time` | string (date-time) | null |  |  |
| `orders[].created_time` | string (date-time) | null |  |  |
| `orders[].last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `orders[].self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `orders[].order_group_id` | string | null |  | The order group this order is part of |
| `orders[].cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `orders[].subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `orders[].exchange_index` | object |  |  |
| `cursor` | string | yes |  |


### `GetPortfolioRestingOrderTotalValueResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_resting_order_value` | integer | yes | Total value of resting orders in cents |


### `GetPositionsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cursor` | string |  | The Cursor represents a pointer to the next page of records in the pagination. Use the value returned here in the cursor query parameter for this end-point to get the next page containing limit rec… |
| `market_positions` | array | yes | List of market positions |
| `market_positions[].ticker` | string | yes | Unique identifier for the market |
| `market_positions[].total_traded_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market_positions[].market_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].resting_orders_count` | integer (int32) | yes | [DEPRECATED] Aggregate size of resting orders in contract units |
| `market_positions[].fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `market_positions[].last_updated_ts` | string (date-time) | yes | Last time the position is updated |
| `event_positions` | array | yes | List of event positions |
| `event_positions[].event_ticker` | string | yes | Unique identifier for events |
| `event_positions[].total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].total_cost_shares_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `event_positions[].event_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `event_positions[].fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `GetQuoteResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quote.id` | string | yes | Unique identifier for the quote |
| `quote.rfq_id` | string | yes | ID of the RFQ this quote is responding to |
| `quote.creator_id` | string | yes | Public communications ID of the quote creator |
| `quote.rfq_creator_id` | string | yes | Public communications ID of the RFQ creator |
| `quote.market_ticker` | string | yes | The ticker of the market this quote is for |
| `quote.contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quote.yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quote.no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quote.created_ts` | string (date-time) | yes | Timestamp when the quote was created |
| `quote.updated_ts` | string (date-time) | yes | Timestamp when the quote was last updated |
| `quote.status` | enum(open, accepted, confirmed, executed, cancelled) | yes | Current status of the quote |
| `quote.accepted_side` | enum(yes, no) |  | The side that was accepted (yes or no) |
| `quote.accepted_ts` | string (date-time) |  | Timestamp when the quote was accepted |
| `quote.confirmed_ts` | string (date-time) |  | Timestamp when the quote was confirmed |
| `quote.executed_ts` | string (date-time) |  | Timestamp when the quote was executed |
| `quote.cancelled_ts` | string (date-time) |  | Timestamp when the quote was cancelled |
| `quote.rest_remainder` | boolean |  | Whether to rest the remainder of the quote after execution |
| `quote.post_only` | boolean |  | Whether the quote creator's order is post-only (visible when the caller is the quote creator) |
| `quote.cancellation_reason` | string |  | Reason for quote cancellation if cancelled |
| `quote.creator_user_id` | string |  | User ID of the quote creator (private field) |
| `quote.rfq_creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `quote.rfq_target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quote.rfq_creator_order_id` | string |  | Order ID for the RFQ creator (private field) |
| `quote.creator_order_id` | string |  | Order ID for the quote creator (private field) |
| `quote.creator_subaccount` | integer |  | Subaccount number of the quote creator (visible when the caller is the quote creator) |
| `quote.rfq_creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `quote.yes_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quote.no_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `GetQuotesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quotes` | array | yes | List of quotes matching the query criteria |
| `quotes[].id` | string | yes | Unique identifier for the quote |
| `quotes[].rfq_id` | string | yes | ID of the RFQ this quote is responding to |
| `quotes[].creator_id` | string | yes | Public communications ID of the quote creator |
| `quotes[].rfq_creator_id` | string | yes | Public communications ID of the RFQ creator |
| `quotes[].market_ticker` | string | yes | The ticker of the market this quote is for |
| `quotes[].contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quotes[].yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quotes[].no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quotes[].created_ts` | string (date-time) | yes | Timestamp when the quote was created |
| `quotes[].updated_ts` | string (date-time) | yes | Timestamp when the quote was last updated |
| `quotes[].status` | enum(open, accepted, confirmed, executed, cancelled) | yes | Current status of the quote |
| `quotes[].accepted_side` | enum(yes, no) |  | The side that was accepted (yes or no) |
| `quotes[].accepted_ts` | string (date-time) |  | Timestamp when the quote was accepted |
| `quotes[].confirmed_ts` | string (date-time) |  | Timestamp when the quote was confirmed |
| `quotes[].executed_ts` | string (date-time) |  | Timestamp when the quote was executed |
| `quotes[].cancelled_ts` | string (date-time) |  | Timestamp when the quote was cancelled |
| `quotes[].rest_remainder` | boolean |  | Whether to rest the remainder of the quote after execution |
| `quotes[].post_only` | boolean |  | Whether the quote creator's order is post-only (visible when the caller is the quote creator) |
| `quotes[].cancellation_reason` | string |  | Reason for quote cancellation if cancelled |
| `quotes[].creator_user_id` | string |  | User ID of the quote creator (private field) |
| `quotes[].rfq_creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `quotes[].rfq_target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `quotes[].rfq_creator_order_id` | string |  | Order ID for the RFQ creator (private field) |
| `quotes[].creator_order_id` | string |  | Order ID for the quote creator (private field) |
| `quotes[].creator_subaccount` | integer |  | Subaccount number of the quote creator (visible when the caller is the quote creator) |
| `quotes[].rfq_creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `quotes[].yes_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `quotes[].no_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `cursor` | string |  | Cursor for pagination to get the next page of results |


### `GetRFQResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rfq.id` | string | yes | Unique identifier for the RFQ |
| `rfq.creator_id` | string | yes | Public communications ID of the RFQ creator. |
| `rfq.market_ticker` | string | yes | The ticker of the market this RFQ is for |
| `rfq.contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `rfq.target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfq.status` | enum(open, closed) | yes | Current status of the RFQ (open, closed) |
| `rfq.created_ts` | string (date-time) | yes | Timestamp when the RFQ was created |
| `rfq.mve_collection_ticker` | string |  | Ticker of the MVE collection this market belongs to |
| `rfq.mve_selected_legs` | array |  | Selected legs for the MVE collection |
| `rfq.mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `rfq.mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `rfq.mve_selected_legs[].side` | string |  | The side of the selected market |
| `rfq.mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfq.rest_remainder` | boolean |  | Whether to rest the remainder of the RFQ after execution |
| `rfq.cancellation_reason` | string |  | Reason for RFQ cancellation if cancelled |
| `rfq.creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `rfq.creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `rfq.cancelled_ts` | string (date-time) |  | Timestamp when the RFQ was cancelled |
| `rfq.updated_ts` | string (date-time) |  | Timestamp when the RFQ was last updated |


### `GetRFQsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rfqs` | array | yes | List of RFQs matching the query criteria |
| `rfqs[].id` | string | yes | Unique identifier for the RFQ |
| `rfqs[].creator_id` | string | yes | Public communications ID of the RFQ creator. |
| `rfqs[].market_ticker` | string | yes | The ticker of the market this RFQ is for |
| `rfqs[].contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `rfqs[].target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfqs[].status` | enum(open, closed) | yes | Current status of the RFQ (open, closed) |
| `rfqs[].created_ts` | string (date-time) | yes | Timestamp when the RFQ was created |
| `rfqs[].mve_collection_ticker` | string |  | Ticker of the MVE collection this market belongs to |
| `rfqs[].mve_selected_legs` | array |  | Selected legs for the MVE collection |
| `rfqs[].mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `rfqs[].mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `rfqs[].mve_selected_legs[].side` | string |  | The side of the selected market |
| `rfqs[].mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfqs[].rest_remainder` | boolean |  | Whether to rest the remainder of the RFQ after execution |
| `rfqs[].cancellation_reason` | string |  | Reason for RFQ cancellation if cancelled |
| `rfqs[].creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `rfqs[].creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `rfqs[].cancelled_ts` | string (date-time) |  | Timestamp when the RFQ was cancelled |
| `rfqs[].updated_ts` | string (date-time) |  | Timestamp when the RFQ was last updated |
| `cursor` | string |  | Cursor for pagination to get the next page of results |


### `GetSeriesFeeChangesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series_fee_change_arr` | array | yes |  |
| `series_fee_change_arr[].id` | string | yes | Unique identifier for this fee change |
| `series_fee_change_arr[].series_ticker` | string | yes | Series ticker this fee change applies to |
| `series_fee_change_arr[].fee_type` | object | yes | New fee type for the series |
| `series_fee_change_arr[].fee_multiplier` | number (double) | yes | New fee multiplier for the series |
| `series_fee_change_arr[].scheduled_ts` | string (date-time) | yes | Timestamp when this fee change is scheduled to take effect |


### `GetSeriesListResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series` | array | yes |  |
| `series[].ticker` | string | yes | Ticker that identifies this series. |
| `series[].frequency` | string | yes | Description of the frequency of the series. There is no fixed value set here, but will be something human-readable like weekly, daily, one-off. |
| `series[].title` | string | yes | Title describing the series. For full context use you should use this field with the title field of the events belonging to this series. |
| `series[].category` | string | yes | Category specifies the category which this series belongs to. |
| `series[].tags` | array | yes | Tags specifies the subjects that this series relates to, multiple series from different categories can have the same tags. |
| `series[].tags[]` | string |  |  |
| `series[].settlement_sources` | array | yes | SettlementSources specifies the official sources used for the determination of markets within the series. Methodology is defined in the rulebook. |
| `series[].settlement_sources[].name` | string |  | Name of the settlement source |
| `series[].settlement_sources[].url` | string |  | URL to the settlement source |
| `series[].contract_url` | string | yes | ContractUrl provides a direct link to the original filing of the contract which underlies the series. |
| `series[].contract_terms_url` | string | yes | ContractTermsUrl is the URL to the current terms of the contract underlying the series. |
| `series[].product_metadata` | object | null |  | Internal product metadata of the series. |
| `series[].fee_type` | object | yes | FeeType is a string representing the series' fee structure. Fee structures can be found at https://kalshi.com/docs/kalshi-fee-schedule.pdf. 'quadratic' is described by the General Trading Fees Tabl… |
| `series[].fee_multiplier` | number (double) | yes | FeeMultiplier is a floating point multiplier applied to the fee calculations. |
| `series[].additional_prohibitions` | array | yes | AdditionalProhibitions is a list of additional trading prohibitions for this series. |
| `series[].additional_prohibitions[]` | string |  |  |
| `series[].volume_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `series[].last_updated_ts` | string (date-time) |  | Timestamp of when this series' metadata was last updated. |


### `GetSeriesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `series.ticker` | string | yes | Ticker that identifies this series. |
| `series.frequency` | string | yes | Description of the frequency of the series. There is no fixed value set here, but will be something human-readable like weekly, daily, one-off. |
| `series.title` | string | yes | Title describing the series. For full context use you should use this field with the title field of the events belonging to this series. |
| `series.category` | string | yes | Category specifies the category which this series belongs to. |
| `series.tags` | array | yes | Tags specifies the subjects that this series relates to, multiple series from different categories can have the same tags. |
| `series.tags[]` | string |  |  |
| `series.settlement_sources` | array | yes | SettlementSources specifies the official sources used for the determination of markets within the series. Methodology is defined in the rulebook. |
| `series.settlement_sources[].name` | string |  | Name of the settlement source |
| `series.settlement_sources[].url` | string |  | URL to the settlement source |
| `series.contract_url` | string | yes | ContractUrl provides a direct link to the original filing of the contract which underlies the series. |
| `series.contract_terms_url` | string | yes | ContractTermsUrl is the URL to the current terms of the contract underlying the series. |
| `series.product_metadata` | object | null |  | Internal product metadata of the series. |
| `series.fee_type` | object | yes | FeeType is a string representing the series' fee structure. Fee structures can be found at https://kalshi.com/docs/kalshi-fee-schedule.pdf. 'quadratic' is described by the General Trading Fees Tabl… |
| `series.fee_multiplier` | number (double) | yes | FeeMultiplier is a floating point multiplier applied to the fee calculations. |
| `series.additional_prohibitions` | array | yes | AdditionalProhibitions is a list of additional trading prohibitions for this series. |
| `series.additional_prohibitions[]` | string |  |  |
| `series.volume_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `series.last_updated_ts` | string (date-time) |  | Timestamp of when this series' metadata was last updated. |


### `GetSettlementsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `settlements` | array | yes |  |
| `settlements[].ticker` | string | yes | The ticker symbol of the market that was settled. |
| `settlements[].event_ticker` | string | yes | The event ticker symbol of the market that was settled. |
| `settlements[].market_result` | enum(yes, no, scalar) | yes | The outcome of the market settlement. 'yes' = market resolved to YES, 'no' = market resolved to NO, 'scalar' = scalar market settled at a specific value. |
| `settlements[].yes_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `settlements[].yes_total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlements[].no_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `settlements[].no_total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlements[].revenue` | integer | yes | Total revenue earned from this settlement in cents (winning contracts pay out 100 cents each). |
| `settlements[].settled_time` | string (date-time) | yes | Timestamp when the market was settled and payouts were processed. |
| `settlements[].fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlements[].value` | integer | null |  | Payout of a single yes contract in cents. |
| `cursor` | string |  |  |


### `GetStructuredTargetResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `structured_target.id` | string |  | Unique identifier for the structured target. |
| `structured_target.name` | string |  | Name of the structured target. |
| `structured_target.type` | string |  | Type of the structured target. |
| `structured_target.details` | object |  | Additional details about the structured target. Contains flexible JSON data specific to the target type. |
| `structured_target.source_id` | string |  | External source identifier for the structured target, if available (e.g., third-party data provider ID). |
| `structured_target.source_ids` | object |  | Source ids of structured target if available. |
| `structured_target.last_updated_ts` | string (date-time) |  | Timestamp when this structured target was last updated. |


### `GetStructuredTargetsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `structured_targets` | array |  |  |
| `structured_targets[].id` | string |  | Unique identifier for the structured target. |
| `structured_targets[].name` | string |  | Name of the structured target. |
| `structured_targets[].type` | string |  | Type of the structured target. |
| `structured_targets[].details` | object |  | Additional details about the structured target. Contains flexible JSON data specific to the target type. |
| `structured_targets[].source_id` | string |  | External source identifier for the structured target, if available (e.g., third-party data provider ID). |
| `structured_targets[].source_ids` | object |  | Source ids of structured target if available. |
| `structured_targets[].last_updated_ts` | string (date-time) |  | Timestamp when this structured target was last updated. |
| `cursor` | string |  | Pagination cursor for the next page. Empty if there are no more results. |


### `GetSubaccountBalancesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_balances` | array | yes |  |
| `subaccount_balances[].subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `subaccount_balances[].balance` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `subaccount_balances[].updated_ts` | integer (int64) | yes | Unix timestamp of last balance update. |


### `GetSubaccountNettingResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `netting_configs` | array | yes |  |
| `netting_configs[].subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `netting_configs[].enabled` | boolean | yes | Whether netting is enabled for this subaccount. |


### `GetSubaccountTransfersResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transfers` | array | yes |  |
| `transfers[].transfer_id` | string | yes | Unique identifier for this transfer. |
| `transfers[].from_subaccount` | integer | yes | Source subaccount number (0 for primary, 1-63 for subaccounts). |
| `transfers[].to_subaccount` | integer | yes | Destination subaccount number (0 for primary, 1-63 for subaccounts). |
| `transfers[].amount_cents` | integer (int64) | yes | Transfer amount in cents. |
| `transfers[].created_ts` | integer (int64) | yes | Unix timestamp when the transfer was created. |
| `cursor` | string |  | Cursor for the next page of results. |


### `GetTagsForSeriesCategoriesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tags_by_categories` | object | yes | Mapping of series categories to their associated tags |


### `GetTradesResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trades` | array | yes |  |
| `trades[].trade_id` | string | yes | Unique identifier for this trade |
| `trades[].ticker` | string | yes | Unique identifier for the market |
| `trades[].count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `trades[].yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `trades[].no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `trades[].taker_side` | enum(yes, no) | yes | Deprecated. Use `taker_outcome_side` (or `taker_book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `trades[].taker_outcome_side` | enum(yes, no) | yes | The outcome side the taker is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `taker_outcome_side` describes directional exposure only; it does not change the … |
| `trades[].taker_book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `trades[].created_time` | string (date-time) | yes | Timestamp when this trade was executed |
| `trades[].is_block_trade` | boolean | yes | True if this trade was matched off-book as a block trade (e.g. via RFQ / negotiated block proposal); false for trades that filled on the standard order book. |
| `cursor` | string | yes |  |


### `GetUserDataTimestampResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `as_of_time` | string (date-time) | yes | Timestamp when user data was last updated. |


### `GetWithdrawalsResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `withdrawals` | array | yes |  |
| `withdrawals[].id` | string | yes | Unique identifier for the withdrawal. |
| `withdrawals[].status` | enum(pending, applied, failed, returned) | yes | Current status of the withdrawal. 'applied' means funds have been deducted from balance. |
| `withdrawals[].type` | enum(ach, wire, crypto, debit, apm) | yes | Payment type used for the withdrawal. |
| `withdrawals[].amount_cents` | integer (int64) | yes | Withdrawal amount in cents. |
| `withdrawals[].fee_cents` | integer (int64) | yes | Fee charged for the withdrawal in cents. |
| `withdrawals[].created_ts` | integer (int64) | yes | Unix timestamp of when the withdrawal was created. |
| `withdrawals[].finalized_ts` | integer (int64) | null |  | Unix timestamp of when the withdrawal was finalized (applied, failed, or returned). |
| `cursor` | string |  |  |


### `IncentiveProgram`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the incentive program |
| `market_id` | string | yes | The unique identifier of the market associated with this incentive program |
| `market_ticker` | string | yes | The ticker symbol of the market associated with this incentive program |
| `incentive_type` | enum(liquidity, volume) | yes | Type of incentive program |
| `incentive_description` | string | yes | Plain text description of the incentive program |
| `start_date` | string (date-time) | yes | Start date of the incentive program |
| `end_date` | string (date-time) | yes | End date of the incentive program |
| `period_reward` | integer (int64) | yes | Total reward for the period in centi-cents |
| `paid_out` | boolean | yes | Whether the incentive has been paid out |
| `discount_factor_bps` | integer (int32) | null |  | Discount factor in basis points (optional) |
| `target_size_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `IndexedBalance`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `exchange_index` | integer | yes | Identifier for an exchange shard. Defaults to 0 if unspecified. Note: currently only 0 supported. |
| `balance` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `IntraExchangeInstanceTransferRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | enum(event_contract, margined) | yes | The exchange instance type |
| `destination` | enum(event_contract, margined) | yes | The exchange instance type |
| `amount` | integer (int64) | yes | The amount to transfer in centicents |
| `source_exchange_shard` | integer |  | Source exchange shard index (default 0) |
| `destination_exchange_shard` | integer |  | Destination exchange shard index (default 0) |


### `IntraExchangeInstanceTransferResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transfer_id` | string | yes | The ID of the transfer that was created |


### `LiveData`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | Type of live data |
| `details` | object | yes | Live data details as a flexible object |
| `milestone_id` | string | yes | Milestone ID |


### `LookupPoint`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Event ticker for the lookup point. |
| `market_ticker` | string | yes | Market ticker for the lookup point. |
| `selected_markets` | array | yes | Markets that were selected for this lookup. |
| `selected_markets[].market_ticker` | string | yes | Market ticker identifier. |
| `selected_markets[].event_ticker` | string | yes | Event ticker identifier. |
| `selected_markets[].side` | enum(yes, no) | yes | Side of the market (yes or no). |
| `last_queried_ts` | string (date-time) | yes | Timestamp when this lookup was last queried. |


### `LookupTickersForMarketInMultivariateEventCollectionRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selected_markets` | array | yes | List of selected markets that act as parameters to determine which market is produced. |
| `selected_markets[].market_ticker` | string | yes | Market ticker identifier. |
| `selected_markets[].event_ticker` | string | yes | Event ticker identifier. |
| `selected_markets[].side` | enum(yes, no) | yes | Side of the market (yes or no). |


### `LookupTickersForMarketInMultivariateEventCollectionResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string | yes | Event ticker for the looked up market. |
| `market_ticker` | string | yes | Market ticker for the looked up market. |


### `MaintenanceWindow`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_datetime` | string (date-time) | yes | Start date and time of the maintenance window. |
| `end_datetime` | string (date-time) | yes | End date and time of the maintenance window. |


### `Market`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes |  |
| `event_ticker` | string | yes |  |
| `market_type` | enum(binary, scalar) | yes | Identifies the type of market |
| `title` | string |  |  |
| `subtitle` | string |  |  |
| `yes_sub_title` | string | yes | Shortened title for the yes side of this market |
| `no_sub_title` | string | yes | Shortened title for the no side of this market |
| `created_time` | string (date-time) | yes |  |
| `updated_time` | string (date-time) | yes | Time of the last non-trading metadata update. |
| `open_time` | string (date-time) | yes |  |
| `close_time` | string (date-time) | yes |  |
| `expected_expiration_time` | string (date-time) | null |  | Time when this market is expected to expire |
| `expiration_time` | string (date-time) |  |  |
| `latest_expiration_time` | string (date-time) | yes | Latest possible time for this market to expire |
| `settlement_timer_seconds` | integer | yes | The amount of time after determination that the market settles |
| `status` | enum(initialized, inactive, active, closed, determined, disputed, amended, finalized) | yes | The current status of the market in its lifecycle. |
| `response_price_units` | enum(usd_cent) |  | DEPRECATED: Use price_level_structure and price_ranges instead. |
| `yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask_size_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `last_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `volume_24h_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `result` | enum(yes, no, scalar, ) | yes |  |
| `can_close_early` | boolean | yes |  |
| `fractional_trading_enabled` | boolean | yes | Deprecated. This flag is always `true` and carries no information. Will be removed after a pre-announcement with the removal date. |
| `open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `notional_value_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `previous_yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `previous_yes_ask_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `previous_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `liquidity_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `settlement_ts` | string (date-time) | null |  | Timestamp when the market was settled. Only filled for settled markets |
| `expiration_value` | string | yes | The value that was considered for the settlement |
| `occurrence_datetime` | string (date-time) | null |  | The recorded datetime when the underlying event occurred, if available |
| `fee_waiver_expiration_time` | string (date-time) | null |  | Time when this market's fee waiver expires |
| `early_close_condition` | string | null |  | The condition under which the market can close early |
| `strike_type` | enum(greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured) |  | Strike type defines how the market strike is defined and evaluated |
| `floor_strike` | number (double) | null |  | Minimum expiration value that leads to a YES settlement |
| `cap_strike` | number (double) | null |  | Maximum expiration value that leads to a YES settlement |
| `functional_strike` | string | null |  | Mapping from expiration values to settlement values |
| `custom_strike` | object | null |  | Expiration value for each target that leads to a YES settlement |
| `rules_primary` | string | yes | A plain language description of the most important market terms |
| `rules_secondary` | string | yes | A plain language description of secondary market terms |
| `mve_collection_ticker` | string |  | The ticker of the multivariate event collection |
| `mve_selected_legs` | array |  |  |
| `mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `mve_selected_legs[].side` | string |  | The side of the selected market |
| `mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `primary_participant_key` | string | null |  |  |
| `price_level_structure` | string | yes | Price level structure for this market, defining price ranges and tick sizes |
| `price_ranges` | array | yes | Valid price ranges for orders on this market |
| `price_ranges[].start` | string | yes | Starting price for this range in dollars |
| `price_ranges[].end` | string | yes | Ending price for this range in dollars |
| `price_ranges[].step` | string | yes | Price step/tick size for this range in dollars |
| `is_provisional` | boolean |  | If true, the market may be removed after determination if there is no activity on it |
| `exchange_index` | object |  |  |


### `MarketCandlestick`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `MarketCandlestickHistorical`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `yes_bid.open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid.low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid.high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_bid.close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.open` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.low` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.high` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `yes_ask.close` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `price.open` | object | null | yes | Price of the first trade during the candlestick period (in dollars). Null if no trades occurred. |
| `price.low` | object | null | yes | Lowest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `price.high` | object | null | yes | Highest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `price.close` | object | null | yes | Price of the last trade during the candlestick period (in dollars). Null if no trades occurred. |
| `price.mean` | object | null | yes | Volume-weighted average price during the candlestick period (in dollars). Null if no trades occurred. |
| `price.previous` | object | null | yes | Close price from the previous candlestick period (in dollars). Null if this is the first candlestick or no prior trade exists. |
| `volume` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `open_interest` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `MarketCandlesticksResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_ticker` | string | yes | Market ticker string (e.g., 'INXD-24JAN01'). |
| `candlesticks` | array | yes | Array of candlestick data points for the market. Includes an initial data point at the start timestamp when available. |
| `candlesticks[].end_period_ts` | integer (int64) | yes | Unix timestamp for the inclusive end of the candlestick period. |
| `candlesticks[].yes_bid.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_bid.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.open_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.low_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.high_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].yes_ask.close_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].price.max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `candlesticks[].volume_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `candlesticks[].open_interest_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `MarketMetadata`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_ticker` | string | yes | The ticker of the market. |
| `image_url` | string | yes | A path to an image that represents this market. |
| `color_code` | string | yes | The color code for the market. |


### `MarketOrderbookFp`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes |  |
| `orderbook_fp.yes_dollars` | array | yes |  |
| `orderbook_fp.yes_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbook_fp.yes_dollars[][]` | string |  |  |
| `orderbook_fp.no_dollars` | array | yes |  |
| `orderbook_fp.no_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `orderbook_fp.no_dollars[][]` | string |  |  |


### `MarketPosition`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Unique identifier for the market |
| `total_traded_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `market_exposure_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `realized_pnl_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `resting_orders_count` | integer (int32) | yes | [DEPRECATED] Aggregate size of resting orders in contract units |
| `fees_paid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `last_updated_ts` | string (date-time) | yes | Last time the position is updated |


### `Milestone`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the milestone. |
| `category` | string | yes | Category of the milestone. E.g. Sports, Elections, Esports, Crypto. |
| `type` | string | yes | Type of the milestone. E.g. football_game, basketball_game, soccer_tournament_multi_leg, baseball_game, hockey_match, golf_tournament, political_race. |
| `start_date` | string (date-time) | yes | Start date of the milestone. |
| `end_date` | string (date-time) | null |  | End date of the milestone, if any. |
| `related_event_tickers` | array | yes | List of event tickers related to this milestone. |
| `related_event_tickers[]` | string |  |  |
| `title` | string | yes | Title of the milestone. |
| `notification_message` | string | yes | Notification message for the milestone. |
| `source_id` | string | null |  | Source id of milestone if available. |
| `source_ids` | object |  | Source ids of milestone if available. |
| `details` | object | yes | Additional details about the milestone. |
| `primary_event_tickers` | array | yes | List of event tickers directly related to the outcome of this milestone. |
| `primary_event_tickers[]` | string |  |  |
| `last_updated_ts` | string (date-time) | yes | Last time this structured target was updated. |


### `MultivariateEventCollection`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_ticker` | string | yes | Unique identifier for the collection. |
| `series_ticker` | string | yes | Series associated with the collection. Events produced in the collection will be associated with this series. |
| `title` | string | yes | Title of the collection. |
| `description` | string | yes | Short description of the collection. |
| `open_date` | string (date-time) | yes | The open date of the collection. Before this time, the collection cannot be interacted with. |
| `close_date` | string (date-time) | yes | The close date of the collection. After this time, the collection cannot be interacted with. |
| `associated_events` | array | yes | List of events with their individual configuration. |
| `associated_events[].ticker` | string | yes | The event ticker. |
| `associated_events[].is_yes_only` | boolean | yes | Whether only the 'yes' side can be used for this event. |
| `associated_events[].size_max` | integer (int32) | null |  | Maximum number of markets from this event (inclusive). Null means no limit. |
| `associated_events[].size_min` | integer (int32) | null |  | Minimum number of markets from this event (inclusive). Null means no limit. |
| `associated_events[].active_quoters` | array | yes | List of active quoters for this event. |
| `associated_events[].active_quoters[]` | string |  |  |
| `associated_event_tickers` | array | yes | [DEPRECATED - Use associated_events instead] A list of events associated with the collection. Markets in these events can be passed as inputs to the Lookup and Create endpoints. |
| `associated_event_tickers[]` | string |  |  |
| `is_ordered` | boolean | yes | Whether the collection is ordered. If true, the order of markets passed into Lookup/Create affects the output. If false, the order does not matter. |
| `is_single_market_per_event` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection accepts multiple markets from the same event passed into Lookup/Create. |
| `is_all_yes` | boolean | yes | [DEPRECATED - Use associated_events instead] Whether the collection requires that only the market side of 'yes' may be used. |
| `size_min` | integer (int32) | yes | The minimum number of markets that must be passed into Lookup/Create (inclusive). |
| `size_max` | integer (int32) | yes | The maximum number of markets that must be passed into Lookup/Create (inclusive). |
| `functional_description` | string | yes | A functional description of the collection describing how inputs affect the output. |


### `MveSelectedLeg`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_ticker` | string |  | Unique identifier for the selected event |
| `market_ticker` | string |  | Unique identifier for the selected market |
| `side` | string |  | The side of the selected market |
| `yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `Order`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes |  |
| `user_id` | string | yes | Unique identifier for users |
| `client_order_id` | string | yes |  |
| `ticker` | string | yes |  |
| `side` | enum(yes, no) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `action` | enum(buy, sell) | yes | Deprecated. Use `outcome_side` (or `book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `outcome_side` | enum(yes, no) | yes | The outcome side this order is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `outcome_side` describes directional exposure only; it does not change the order… |
| `book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `type` | enum(limit, market) | yes |  |
| `status` | enum(resting, canceled, executed) | yes | The status of an order |
| `yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `fill_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `remaining_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `initial_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `taker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `maker_fill_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `taker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `maker_fees_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `expiration_time` | string (date-time) | null |  |  |
| `created_time` | string (date-time) | null |  |  |
| `last_update_time` | string (date-time) | null |  | The last update to an order (modify, cancel, fill) |
| `self_trade_prevention_type` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |
| `order_group_id` | string | null |  | The order group this order is part of |
| `cancel_order_on_pause` | boolean |  | If this flag is set to true, the order will be canceled if the order is open and trading on the exchange is paused for any reason. |
| `subaccount_number` | integer | null |  | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `exchange_index` | object |  |  |


### `OrderGroup`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the order group |
| `contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `is_auto_cancel_enabled` | boolean | yes | Whether auto-cancel is enabled for this order group |
| `exchange_index` | object |  |  |


### `OrderQueuePosition`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | yes | The order ID |
| `market_ticker` | string | yes | The market ticker |
| `queue_position_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `OrderStatus`

The status of an order

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(resting, canceled, executed) |  | The status of an order |


### `OrderbookCountFp`

Orderbook with fixed-point contract counts (fp) in all dollar price levels.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `yes_dollars` | array | yes |  |
| `yes_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `yes_dollars[][]` | string |  |  |
| `no_dollars` | array | yes |  |
| `no_dollars[][]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `no_dollars[][]` | string |  |  |


### `PercentilePoint`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `percentile` | integer (int32) | yes | The percentile value (0-9999). |
| `raw_numerical_forecast` | number | yes | The raw numerical forecast value. |
| `numerical_forecast` | number | yes | The processed numerical forecast value. |
| `formatted_forecast` | string | yes | The human-readable formatted forecast value. |


### `PlayByPlay`

Play-by-play data organized by period.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `periods` | array |  |  |
| `periods[].events` | array |  |  |
| `periods[].events[]` | object |  |  |


### `PriceDistribution`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `open_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `low_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `high_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `close_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `mean_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `previous_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `min_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `max_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |


### `PriceDistributionHistorical`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `open` | object | null | yes | Price of the first trade during the candlestick period (in dollars). Null if no trades occurred. |
| `low` | object | null | yes | Lowest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `high` | object | null | yes | Highest trade price during the candlestick period (in dollars). Null if no trades occurred. |
| `close` | object | null | yes | Price of the last trade during the candlestick period (in dollars). Null if no trades occurred. |
| `mean` | object | null | yes | Volume-weighted average price during the candlestick period (in dollars). Null if no trades occurred. |
| `previous` | object | null | yes | Close price from the previous candlestick period (in dollars). Null if this is the first candlestick or no prior trade exists. |


### `PriceLevelDollarsCountFp`

Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract quantity (not price).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `[]` | array |  | Price level in dollars represented as [dollars_string, fp] where dollars_string is like "0.1500" and fp is a FixedPointCount string (fixed-point contract count). The second element is the contract … |
| `[]` | string |  |  |


### `PriceRange`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | string | yes | Starting price for this range in dollars |
| `end` | string | yes | Ending price for this range in dollars |
| `step` | string | yes | Price step/tick size for this range in dollars |


### `ProposeBlockTradeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `buyer_user_id` | string | yes | User ID of the buyer |
| `buyer_subtrader_id` | string |  | Subtrader ID of the buyer. Provide either this or buyer_subaccount, not both. |
| `buyer_subaccount` | integer |  | User-managed subaccount number of the buyer (0 for primary, 1-63 for numbered subaccounts). Provide either this or buyer_subtrader_id, not both. |
| `seller_user_id` | string | yes | User ID of the seller |
| `seller_subtrader_id` | string |  | Subtrader ID of the seller. Provide either this or seller_subaccount, not both. |
| `seller_subaccount` | integer |  | User-managed subaccount number of the seller (0 for primary, 1-63 for numbered subaccounts). Provide either this or seller_subtrader_id, not both. |
| `market_ticker` | string | yes | The ticker of the market for this block trade |
| `price_centi_cents` | integer (int64) | yes | Price in centi-cents |
| `centicount` | integer (int64) | yes | Number of contracts in centicounts |
| `maker_side` | enum(yes, no) | yes | The maker side of the trade |
| `expiration_ts` | string (date-time) | yes | Expiration time of the proposal |


### `ProposeBlockTradeResponse`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_trade_proposal_id` | string | yes | The ID of the newly created block trade proposal |


### `Quote`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the quote |
| `rfq_id` | string | yes | ID of the RFQ this quote is responding to |
| `creator_id` | string | yes | Public communications ID of the quote creator |
| `rfq_creator_id` | string | yes | Public communications ID of the RFQ creator |
| `market_ticker` | string | yes | The ticker of the market this quote is for |
| `contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `yes_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_bid_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `created_ts` | string (date-time) | yes | Timestamp when the quote was created |
| `updated_ts` | string (date-time) | yes | Timestamp when the quote was last updated |
| `status` | enum(open, accepted, confirmed, executed, cancelled) | yes | Current status of the quote |
| `accepted_side` | enum(yes, no) |  | The side that was accepted (yes or no) |
| `accepted_ts` | string (date-time) |  | Timestamp when the quote was accepted |
| `confirmed_ts` | string (date-time) |  | Timestamp when the quote was confirmed |
| `executed_ts` | string (date-time) |  | Timestamp when the quote was executed |
| `cancelled_ts` | string (date-time) |  | Timestamp when the quote was cancelled |
| `rest_remainder` | boolean |  | Whether to rest the remainder of the quote after execution |
| `post_only` | boolean |  | Whether the quote creator's order is post-only (visible when the caller is the quote creator) |
| `cancellation_reason` | string |  | Reason for quote cancellation if cancelled |
| `creator_user_id` | string |  | User ID of the quote creator (private field) |
| `rfq_creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `rfq_target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rfq_creator_order_id` | string |  | Order ID for the RFQ creator (private field) |
| `creator_order_id` | string |  | Order ID for the quote creator (private field) |
| `creator_subaccount` | integer |  | Subaccount number of the quote creator (visible when the caller is the quote creator) |
| `rfq_creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `yes_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `no_contracts_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `RFQ`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the RFQ |
| `creator_id` | string | yes | Public communications ID of the RFQ creator. |
| `market_ticker` | string | yes | The ticker of the market this RFQ is for |
| `contracts_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `target_cost_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `status` | enum(open, closed) | yes | Current status of the RFQ (open, closed) |
| `created_ts` | string (date-time) | yes | Timestamp when the RFQ was created |
| `mve_collection_ticker` | string |  | Ticker of the MVE collection this market belongs to |
| `mve_selected_legs` | array |  | Selected legs for the MVE collection |
| `mve_selected_legs[].event_ticker` | string |  | Unique identifier for the selected event |
| `mve_selected_legs[].market_ticker` | string |  | Unique identifier for the selected market |
| `mve_selected_legs[].side` | string |  | The side of the selected market |
| `mve_selected_legs[].yes_settlement_value_dollars` | string |  | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `rest_remainder` | boolean |  | Whether to rest the remainder of the RFQ after execution |
| `cancellation_reason` | string |  | Reason for RFQ cancellation if cancelled |
| `creator_user_id` | string |  | User ID of the RFQ creator (private field) |
| `creator_subaccount` | integer |  | Subaccount number of the RFQ creator (visible when the caller is the RFQ creator) |
| `cancelled_ts` | string (date-time) |  | Timestamp when the RFQ was cancelled |
| `updated_ts` | string (date-time) |  | Timestamp when the RFQ was last updated |


### `Schedule`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `standard_hours` | array | yes | The standard operating hours of the exchange. All times are expressed in ET. Outside of these times trading will be unavailable. |
| `standard_hours[].start_time` | string (date-time) | yes | Start date and time for when this weekly schedule is effective. |
| `standard_hours[].end_time` | string (date-time) | yes | End date and time for when this weekly schedule is no longer effective. |
| `standard_hours[].monday` | array | yes | Trading hours for Monday. May contain multiple sessions. |
| `standard_hours[].monday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].monday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].tuesday` | array | yes | Trading hours for Tuesday. May contain multiple sessions. |
| `standard_hours[].tuesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].tuesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].wednesday` | array | yes | Trading hours for Wednesday. May contain multiple sessions. |
| `standard_hours[].wednesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].wednesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].thursday` | array | yes | Trading hours for Thursday. May contain multiple sessions. |
| `standard_hours[].thursday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].thursday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].friday` | array | yes | Trading hours for Friday. May contain multiple sessions. |
| `standard_hours[].friday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].friday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].saturday` | array | yes | Trading hours for Saturday. May contain multiple sessions. |
| `standard_hours[].saturday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].saturday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].sunday` | array | yes | Trading hours for Sunday. May contain multiple sessions. |
| `standard_hours[].sunday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `standard_hours[].sunday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `maintenance_windows` | array | yes | Scheduled maintenance windows, during which the exchange may be unavailable. |
| `maintenance_windows[].start_datetime` | string (date-time) | yes | Start date and time of the maintenance window. |
| `maintenance_windows[].end_datetime` | string (date-time) | yes | End date and time of the maintenance window. |


### `ScopeList`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scopes` | array | yes | List of scopes |
| `scopes[]` | string |  |  |


### `SelfTradePreventionType`

The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already matched are executed. `maker` cancels the resting maker order and continues matching.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(taker_at_cross, maker) |  | The self-trade prevention type for orders. `taker_at_cross` cancels the taker order when it would trade against another order from the same user; execution stops and any partial fills already match… |


### `Series`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | Ticker that identifies this series. |
| `frequency` | string | yes | Description of the frequency of the series. There is no fixed value set here, but will be something human-readable like weekly, daily, one-off. |
| `title` | string | yes | Title describing the series. For full context use you should use this field with the title field of the events belonging to this series. |
| `category` | string | yes | Category specifies the category which this series belongs to. |
| `tags` | array | yes | Tags specifies the subjects that this series relates to, multiple series from different categories can have the same tags. |
| `tags[]` | string |  |  |
| `settlement_sources` | array | yes | SettlementSources specifies the official sources used for the determination of markets within the series. Methodology is defined in the rulebook. |
| `settlement_sources[].name` | string |  | Name of the settlement source |
| `settlement_sources[].url` | string |  | URL to the settlement source |
| `contract_url` | string | yes | ContractUrl provides a direct link to the original filing of the contract which underlies the series. |
| `contract_terms_url` | string | yes | ContractTermsUrl is the URL to the current terms of the contract underlying the series. |
| `product_metadata` | object | null |  | Internal product metadata of the series. |
| `fee_type` | object | yes | FeeType is a string representing the series' fee structure. Fee structures can be found at https://kalshi.com/docs/kalshi-fee-schedule.pdf. 'quadratic' is described by the General Trading Fees Tabl… |
| `fee_multiplier` | number (double) | yes | FeeMultiplier is a floating point multiplier applied to the fee calculations. |
| `additional_prohibitions` | array | yes | AdditionalProhibitions is a list of additional trading prohibitions for this series. |
| `additional_prohibitions[]` | string |  |  |
| `volume_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `last_updated_ts` | string (date-time) |  | Timestamp of when this series' metadata was last updated. |


### `SeriesFeeChange`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for this fee change |
| `series_ticker` | string | yes | Series ticker this fee change applies to |
| `fee_type` | object | yes | New fee type for the series |
| `fee_multiplier` | number (double) | yes | New fee multiplier for the series |
| `scheduled_ts` | string (date-time) | yes | Timestamp when this fee change is scheduled to take effect |


### `Settlement`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | yes | The ticker symbol of the market that was settled. |
| `event_ticker` | string | yes | The event ticker symbol of the market that was settled. |
| `market_result` | enum(yes, no, scalar) | yes | The outcome of the market settlement. 'yes' = market resolved to YES, 'no' = market resolved to NO, 'scalar' = scalar market settled at a specific value. |
| `yes_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `yes_total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `no_total_cost_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `revenue` | integer | yes | Total revenue earned from this settlement in cents (winning contracts pay out 100 cents each). |
| `settled_time` | string (date-time) | yes | Timestamp when the market was settled and payouts were processed. |
| `fee_cost` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `value` | integer | null |  | Payout of a single yes contract in cents. |


### `SettlementSource`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string |  | Name of the settlement source |
| `url` | string |  | URL to the settlement source |


### `SportFilterDetails`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scopes` | array | yes | List of scopes available for this sport |
| `scopes[]` | string |  |  |
| `competitions` | object | yes | Mapping of competitions to their scope lists |


### `StructuredTarget`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string |  | Unique identifier for the structured target. |
| `name` | string |  | Name of the structured target. |
| `type` | string |  | Type of the structured target. |
| `details` | object |  | Additional details about the structured target. Contains flexible JSON data specific to the target type. |
| `source_id` | string |  | External source identifier for the structured target, if available (e.g., third-party data provider ID). |
| `source_ids` | object |  | Source ids of structured target if available. |
| `last_updated_ts` | string (date-time) |  | Timestamp when this structured target was last updated. |


### `SubaccountBalance`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `balance` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `updated_ts` | integer (int64) | yes | Unix timestamp of last balance update. |


### `SubaccountNettingConfig`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `enabled` | boolean | yes | Whether netting is enabled for this subaccount. |


### `SubaccountTransfer`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transfer_id` | string | yes | Unique identifier for this transfer. |
| `from_subaccount` | integer | yes | Source subaccount number (0 for primary, 1-63 for subaccounts). |
| `to_subaccount` | integer | yes | Destination subaccount number (0 for primary, 1-63 for subaccounts). |
| `amount_cents` | integer (int64) | yes | Transfer amount in cents. |
| `created_ts` | integer (int64) | yes | Unix timestamp when the transfer was created. |


### `TickerPair`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market_ticker` | string | yes | Market ticker identifier. |
| `event_ticker` | string | yes | Event ticker identifier. |
| `side` | enum(yes, no) | yes | Side of the market (yes or no). |


### `Trade`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trade_id` | string | yes | Unique identifier for this trade |
| `ticker` | string | yes | Unique identifier for the market |
| `count_fp` | string | yes | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |
| `yes_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `no_price_dollars` | string | yes | US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision. This is the maximum supported precision; valid quote intervals for a given market are constrained by that … |
| `taker_side` | enum(yes, no) | yes | Deprecated. Use `taker_outcome_side` (or `taker_book_side`) instead. See [Order direction](/getting_started/order_direction). This field will not be removed before May 14, 2026. |
| `taker_outcome_side` | enum(yes, no) | yes | The outcome side the taker is positioned for. buy-yes and sell-no produce 'yes'; buy-no and sell-yes produce 'no'.  `taker_outcome_side` describes directional exposure only; it does not change the … |
| `taker_book_side` | enum(bid, ask) | yes | Side of the book for an order or trade. For event markets, this refers to the YES leg only: `bid` means buy YES, `ask` means sell YES. (Selling YES is economically equivalent to buying NO at `1 - p… |
| `created_time` | string (date-time) | yes | Timestamp when this trade was executed |
| `is_block_trade` | boolean | yes | True if this trade was matched off-book as a block trade (e.g. via RFQ / negotiated block proposal); false for trades that filled on the standard order book. |


### `UpdateOrderGroupLimitRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contracts_limit` | integer (int64) |  | New maximum number of contracts that can be matched within this group over a rolling 15-second window. Whole contracts only. Provide contracts_limit or contracts_limit_fp; if both provided they mus… |
| `contracts_limit_fp` | string |  | Fixed-point contract count string (2 decimals, e.g., "10.00"; referred to as "fp" in field names). Requests accept 0–2 decimal places (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals… |


### `UpdateSubaccountNettingRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subaccount_number` | integer | yes | Subaccount number (0 for primary, 1-63 for subaccounts). |
| `enabled` | boolean | yes | Whether netting is enabled for this subaccount. |


### `UserFilter`

Omit or leave empty to return all results. Use `self` to filter by the authenticated user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `(root)` | enum(self) |  | Omit or leave empty to return all results. Use `self` to filter by the authenticated user. |


### `WeeklySchedule`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_time` | string (date-time) | yes | Start date and time for when this weekly schedule is effective. |
| `end_time` | string (date-time) | yes | End date and time for when this weekly schedule is no longer effective. |
| `monday` | array | yes | Trading hours for Monday. May contain multiple sessions. |
| `monday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `monday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `tuesday` | array | yes | Trading hours for Tuesday. May contain multiple sessions. |
| `tuesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `tuesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `wednesday` | array | yes | Trading hours for Wednesday. May contain multiple sessions. |
| `wednesday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `wednesday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `thursday` | array | yes | Trading hours for Thursday. May contain multiple sessions. |
| `thursday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `thursday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `friday` | array | yes | Trading hours for Friday. May contain multiple sessions. |
| `friday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `friday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `saturday` | array | yes | Trading hours for Saturday. May contain multiple sessions. |
| `saturday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `saturday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |
| `sunday` | array | yes | Trading hours for Sunday. May contain multiple sessions. |
| `sunday[].open_time` | string | yes | Opening time in ET (Eastern Time) format HH:MM. |
| `sunday[].close_time` | string | yes | Closing time in ET (Eastern Time) format HH:MM. |


### `Withdrawal`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier for the withdrawal. |
| `status` | enum(pending, applied, failed, returned) | yes | Current status of the withdrawal. 'applied' means funds have been deducted from balance. |
| `type` | enum(ach, wire, crypto, debit, apm) | yes | Payment type used for the withdrawal. |
| `amount_cents` | integer (int64) | yes | Withdrawal amount in cents. |
| `fee_cents` | integer (int64) | yes | Fee charged for the withdrawal in cents. |
| `created_ts` | integer (int64) | yes | Unix timestamp of when the withdrawal was created. |
| `finalized_ts` | integer (int64) | null |  | Unix timestamp of when the withdrawal was finalized (applied, failed, or returned). |


---

## Notes

- **Fixed-point strings:** Many price/size fields use `*_fp` or `*_dollars` string types (e.g. `"0.4200"`, `"13.00"`). See [Fixed-Point Migration](https://docs.kalshi.com/getting_started/fixed_point_migration).
- **Orderbook:** API returns bids only; YES ask = 100¢ − NO bid (see orderbook docs).
- **Not in this file:** Perps API (`perps_openapi.yaml`), WebSocket (`asyncapi.yaml`), undocumented endpoints, or fields absent from the published spec.
- **Vendor snapshot:** `docs/specs/kalshi_openapi.yaml`
