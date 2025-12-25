The “Kirana” or “Independent Grocery” Store Agent - Problem statement and solution 


Summary
Independent grocery store market in the US is a $70B market and consisted of
11% of market sales in 2015. These stores carry about 10k-33k store keeping
units (SKUs) and are about 8k-15k square feet in size. Bodega is a corner store
that has much smaller footprint at 1k-3k sq.feet and they carry 500-8000 SKUs.

Opportunity
These small stores often work on razor thin margins with limited resources and
are challenged to maintain low operational costs, optimum inventory levels of
SKUs and high labor turnover. These are aggravated further when unlike large
chains, small grocery stores do not have supply chain visibility of items from large
vendors and securing right products in the right quantity and at the right time
becomes challenging leading to stock outs, delays and ultimately in lost revenue.

Solution
To address these challenges, we will introduce an agentic artificial intelligence (AI)
solution backed a dynamic economic ordering quantity (EOQ) model that will
automatically adjust ordering quantities based on hyper local forecast tailored to
each grocery store based on historical point of sales (PoS), area demographics,
and store inventory levels of each item. This solution will aim to remove any
ambiguity in SKU ordering, mitigate stock out issues and increase store revenue.

How does our Kirana Agentic Solution Work?
We will have an orchestrator agent, whose job will be to co-ordinate other sub agents. We have three sub agents - 1) Inventory Agent, 2) Logistics Agent and 3) Finance Agent.

Inventory Agent - will have 3 MCP connections/tools to get 1) SKU inventory levels, 2) Item details and 3) Cost of the item
Logistics Agent - will have 2 tools - 1) to find shipping options and 2) execute the shipment.
Finance agent - is an A2A server that initiates a call to the A2A agent based on user request. 

When inventory gets lower, our inventory agent will use MCP connection to check the database and use A2A to ask the remote financial agent for approval which will then respond with a yes/no decision. 

You Tube Video: A2A and MCP explained: with ADK



Data discovery will need to be part. 
Need to open orders, intransit, onhand inventory. Some kind of integration 
How will you capture the buying behavior of the shopper? 
Can you stock up based on the buying behavior. 
Can the inventory level problems be solved using traditional AI?
We use 


Start a whatsapp group


Design Details



Store Feedback Details


Requirements


Potential Future Use cases - food truck, small grocery store, World Cup (in June) - how do you predict seasonality accurately.

 


Participants:
Pratul Sarma	425-362-3978
pratulsarma2002@gmail.com
Apoorav: 4258029267; apoorav.trehan@gmail.com
Amol - 4042007447; amolsingbal1995@gmail.com
Josh Dewanaga 206-708-1779
Ameya Margaj 716-598-3049; ameyamargaj@gmail.com
Renu Mehandru 206 750 5742





Design 

Below is a multi-agent design + prompt pack tailored for Azure AI Foundry style orchestration (an “Agent Hub” that routes tasks to specialist agents, each returning structured JSON). You can paste these as System prompts for each agent, and use the Orchestrator prompt as the top-level.

1) Overall architecture (AI Foundry-friendly)
Agents
Orchestrator (StoreOps Planner): decomposes the goal, calls specialist agents, merges outputs, produces final “Order Plan + Explainability + Alerts”.


Forecast Agent: produces SKU-level demand forecasts + uncertainty + drivers.


EOQ Agent: computes dynamic reorder point / EOQ / safety stock / days-of-cover targets.


Vendor Agent: validates vendor constraints (MOQ, case packs, lead time), substitutes, and suggests order consolidation + risk flags.


Shared artifacts
store_profile


sku_master


pos_history


inventory_snapshot


vendor_catalog


constraints (cash cap, storage, service level targets)


Data contracts
All agents must emit strict JSON with a schema (below) to enable deterministic chaining.



2) Orchestrator Agent (StoreOps Planner) — System Prompt
You are the StoreOps Planner Orchestrator for an independent grocery store replenishment solution.

Your job:
1) Understand the store context and planning horizon.
2) Call specialist agents in this order: Forecast Agent → EOQ Agent → Vendor Agent.
3) Merge their outputs into one executable Order Plan that is vendor-feasible, cost-aware, and explainable.
4) Produce a concise owner-friendly summary plus an exceptions list.

Operating rules:
- Use the provided JSON schemas. If an upstream agent returns missing fields, infer conservatively and add a "data_gaps" note.
- Prioritize preventing stockouts for high-margin / high-velocity SKUs while controlling overstock/spoilage for perishables.
- If inputs are incomplete, degrade gracefully: use category-level heuristics and higher safety stock.
- Output must be a single JSON object per the “Orchestrator Output Schema”.

You must NOT output prose outside JSON.

Orchestrator — Task Prompt Template (AI Foundry)
Given the inputs (store_profile, sku_master, pos_history, inventory_snapshot, vendor_catalog, constraints),
generate a replenishment recommendation for planning_horizon_days = {{H}}.

Steps:
1) Ask Forecast Agent for demand forecast per SKU with uncertainty & drivers.
2) Ask EOQ Agent to compute reorder points, safety stock, and suggested order quantities using the forecast + inventory.
3) Ask Vendor Agent to convert suggested quantities into feasible vendor orders (MOQ/case-pack/lead-time), propose substitutes if needed, and flag vendor risks.
4) Produce final order_plan with business impact, explainability, and alerts.

Return Orchestrator Output Schema JSON.


3) Forecast Agent — System Prompt
You are the Forecast Agent for independent grocery replenishment.

Goal:
Produce SKU-level demand forecasts for the next planning horizon with uncertainty bounds and explanatory drivers.

You must:
- Use historical POS time series; handle intermittent demand.
- Identify seasonality (weekday/weekend), trends, and events if provided (weather/local events).
- Return forecast mean + P50/P90 (or lower/upper) and a confidence score.
- Provide “drivers”: top 3-5 factors affecting forecast for each SKU (e.g., trend up, weekend lift, holiday, local demographic proxy).

Constraints:
- If POS is sparse, fall back to category-level forecast and store-wide seasonality patterns.
- Flag data quality issues (missing POS days, outliers, SKU mapping errors).

Output must be strict JSON using the “Forecast Output Schema”.
No prose outside JSON.

Forecast — Task Prompt Template
Inputs:
store_profile: {{...}}
sku_master: {{...}}
pos_history: {{...}}
planning_horizon_days: {{H}}
optional_signals: {{weather/events/demographics if present}}

Return:
Forecast Output Schema JSON with per_sku_forecast entries.


4) EOQ Agent — System Prompt
You are the EOQ & Replenishment Optimization Agent.

Goal:
Convert forecasts + inventory into ordering recommendations per SKU using dynamic EOQ, reorder point, and safety stock.

You must:
- Compute:
  - demand_rate (units/day)
  - lead_time_days (from vendor inputs or default by category)
  - safety_stock (based on demand variability + service level target)
  - reorder_point = demand_rate*lead_time + safety_stock
  - order_quantity (dynamic EOQ adjusted for constraints: spoilage, shelf-life, cash cap, storage)
  - expected_days_of_cover after ordering
- Use different logic by SKU type:
  - Perishables: cap order quantities by shelf-life and spoilage risk.
  - Non-perishables: optimize holding costs vs ordering costs.
- Provide “reason_codes” for decisions and flag exceptions (stockout risk, overstock risk, negative margin if price/cost present).

Constraints:
- If ordering_cost/holding_cost missing, use reasonable defaults by category and include them in assumptions.
- Output strict JSON using the “EOQ Output Schema”.
No prose outside JSON.

EOQ — Task Prompt Template
Inputs:
store_profile: {{...}}
sku_master: {{...}}
inventory_snapshot: {{...}}
forecast_output: {{...}}   (from Forecast Agent)
vendor_catalog: {{...}}
constraints: {{...}}
planning_horizon_days: {{H}}

Return:
EOQ Output Schema JSON with per_sku_replenishment entries.


5) Vendor Agent — System Prompt
You are the Vendor & Procurement Feasibility Agent.

Goal:
Transform SKU-level recommended quantities into vendor-feasible purchase orders and procurement actions.

You must:
- Enforce vendor constraints:
  - MOQ, case-pack, min $ order, order days/cutoff times
  - lead time and fill-rate risk
- Round quantities to case packs while minimizing distortion vs EOQ recommendations.
- Suggest consolidation opportunities (combine orders across SKUs/vendors) to meet MOQ and reduce delivery fees.
- Propose substitutes when:
  - vendor risk high
  - item unavailable
  - lead time too long for stockout risk
- Produce vendor-level PO drafts with line items, totals, and risk flags.
- Output strict JSON using the “Vendor Output Schema”.
No prose outside JSON.

Vendor — Task Prompt Template
Inputs:
vendor_catalog: {{...}}
eoq_output: {{...}}   (from EOQ Agent)
store_profile: {{...}}
constraints: {{...}}

Return:
Vendor Output Schema JSON including vendor_po_drafts and substitutions.


6) JSON Schemas (data contracts)
A) Forecast Output Schema
{
  "schema_version": "1.0",
  "planning_horizon_days": 14,
  "data_quality": {
    "issues": [],
    "notes": ""
  },
  "per_sku_forecast": [
    {
      "sku_id": "string",
      "forecast_units_total": 0,
      "forecast_units_per_day": 0.0,
      "uncertainty": {
        "p50_total": 0,
        "p90_total": 0
      },
      "confidence": 0.0,
      "drivers": ["string", "string", "string"]
    }
  ],
  "assumptions": {
    "fallbacks_used": [],
    "notes": ""
  }
}

B) EOQ Output Schema
{
  "schema_version": "1.0",
  "planning_horizon_days": 14,
  "service_level_target": 0.95,
  "per_sku_replenishment": [
    {
      "sku_id": "string",
      "demand_rate_per_day": 0.0,
      "lead_time_days": 0,
      "safety_stock_units": 0,
      "reorder_point_units": 0,
      "on_hand_units": 0,
      "on_order_units": 0,
      "recommended_order_units": 0,
      "recommended_order_reason_codes": ["string"],
      "expected_days_of_cover_after_order": 0.0,
      "risk_flags": ["STOCKOUT_RISK", "OVERSTOCK_RISK", "SPOILAGE_RISK"]
    }
  ],
  "assumptions": {
    "holding_cost_model": "default_by_category",
    "ordering_cost_model": "default_flat",
    "notes": ""
  },
  "exceptions": [
    {
      "sku_id": "string",
      "type": "string",
      "severity": "LOW|MEDIUM|HIGH",
      "message": "string"
    }
  ]
}

C) Vendor Output Schema
{
  "schema_version": "1.0",
  "vendor_po_drafts": [
    {
      "vendor_id": "string",
      "vendor_name": "string",
      "expected_lead_time_days": 0,
      "constraints_applied": ["MOQ", "CASE_PACK", "MIN_ORDER_VALUE"],
      "line_items": [
        {
          "sku_id": "string",
          "sku_name": "string",
          "requested_units": 0,
          "case_pack": 0,
          "final_order_units": 0,
          "unit_cost": 0.0,
          "extended_cost": 0.0,
          "fill_risk": "LOW|MEDIUM|HIGH"
        }
      ],
      "po_total_cost": 0.0,
      "notes": "string",
      "risk_flags": ["string"]
    }
  ],
  "substitutions": [
    {
      "sku_id": "string",
      "proposed_substitute_sku_id": "string",
      "reason": "string",
      "expected_impact": "string"
    }
  ],
  "assumptions": {
    "rounding_strategy": "minimize_stockout_risk",
    "notes": ""
  }
}

D) Orchestrator Output Schema
{
  "schema_version": "1.0",
  "store_id": "string",
  "planning_horizon_days": 14,
  "order_plan": {
    "created_at": "ISO-8601",
    "vendor_po_drafts": [],
    "sku_level_summary": [
      {
        "sku_id": "string",
        "final_order_units": 0,
        "why": ["string", "string"],
        "confidence": 0.0
      }
    ]
  },
  "owner_summary": {
    "top_actions": ["string", "string", "string"],
    "expected_business_impact": {
      "stockout_reduction_pct": 0.0,
      "revenue_uplift_estimate": 0.0,
      "inventory_cost_reduction_estimate": 0.0
    }
  },
  "alerts": [
    {
      "type": "STOCKOUT_RISK|VENDOR_RISK|SPOILAGE_RISK|DATA_QUALITY",
      "severity": "LOW|MEDIUM|HIGH",
      "message": "string",
      "sku_ids": ["string"]
    }
  ],
  "data_gaps": ["string"],
  "audit_trail": {
    "forecast_agent_used": true,
    "eoq_agent_used": true,
    "vendor_agent_used": true,
    "assumptions": ["string"]
  }
}


7) “AI Foundry” implementation notes (so this actually works)
How to run this in Foundry-style orchestration
Define 4 Agents with the above system prompts.


The Orchestrator calls the other 3 via tool/function calls (or routed messages).


Enforce JSON mode / structured outputs per agent.


Persist artifacts per run:


forecast_output.json


eoq_output.json


vendor_output.json


final_order_plan.json


Evaluation loop (recommended)
After each week, compute:


Forecast error (MAPE/WAPE)


Stockout occurrences


Spoilage/waste (if captured)


Feed metrics back as learning_signals to improve parameters:


service level targets by category


holding cost proxies


lead time distributions


Sample Dataset — Independent Grocery Store Agent

1️⃣ Store Profile (store_profile.json)
{
  "store_id": "STORE_001",
  "store_name": "Green Valley Market",
  "store_type": "Independent Grocery",
  "location": {
    "city": "Seattle",
    "state": "WA",
    "zip": "98109"
  },
  "store_size_sqft": 4500,
  "sku_count": 1800,
  "operating_days_per_week": 7,
  "service_level_target": 0.95,
  "currency": "USD"
}


2️⃣ SKU Master (sku_master.json)
[
  {
    "sku_id": "SKU_001",
    "sku_name": "Whole Milk 1 Gallon",
    "category": "Dairy",
    "perishable": true,
    "shelf_life_days": 10,
    "unit_of_measure": "each",
    "avg_unit_cost": 3.10,
    "avg_retail_price": 4.99
  },
  {
    "sku_id": "SKU_002",
    "sku_name": "Brown Eggs 12ct",
    "category": "Eggs",
    "perishable": true,
    "shelf_life_days": 14,
    "unit_of_measure": "each",
    "avg_unit_cost": 3.60,
    "avg_retail_price": 5.49
  },
  {
    "sku_id": "SKU_003",
    "sku_name": "Bananas (lb)",
    "category": "Produce",
    "perishable": true,
    "shelf_life_days": 5,
    "unit_of_measure": "lb",
    "avg_unit_cost": 0.45,
    "avg_retail_price": 0.79
  },
  {
    "sku_id": "SKU_004",
    "sku_name": "White Bread Loaf",
    "category": "Bakery",
    "perishable": true,
    "shelf_life_days": 7,
    "unit_of_measure": "each",
    "avg_unit_cost": 1.20,
    "avg_retail_price": 2.99
  },
  {
    "sku_id": "SKU_005",
    "sku_name": "Canned Black Beans 15oz",
    "category": "Dry Grocery",
    "perishable": false,
    "shelf_life_days": 730,
    "unit_of_measure": "each",
    "avg_unit_cost": 0.75,
    "avg_retail_price": 1.49
  },
  {
    "sku_id": "SKU_006",
    "sku_name": "Basmati Rice 10lb",
    "category": "Dry Grocery",
    "perishable": false,
    "shelf_life_days": 1095,
    "unit_of_measure": "each",
    "avg_unit_cost": 12.00,
    "avg_retail_price": 18.99
  },
  {
    "sku_id": "SKU_007",
    "sku_name": "Potato Chips 8oz",
    "category": "Snacks",
    "perishable": false,
    "shelf_life_days": 180,
    "unit_of_measure": "each",
    "avg_unit_cost": 1.80,
    "avg_retail_price": 3.99
  },
  {
    "sku_id": "SKU_008",
    "sku_name": "Bottled Water 24-pack",
    "category": "Beverages",
    "perishable": false,
    "shelf_life_days": 365,
    "unit_of_measure": "case",
    "avg_unit_cost": 4.50,
    "avg_retail_price": 7.99
  },
  {
    "sku_id": "SKU_009",
    "sku_name": "Orange Juice 64oz",
    "category": "Beverages",
    "perishable": true,
    "shelf_life_days": 14,
    "unit_of_measure": "each",
    "avg_unit_cost": 2.80,
    "avg_retail_price": 4.99
  },
  {
    "sku_id": "SKU_010",
    "sku_name": "Frozen Pizza",
    "category": "Frozen",
    "perishable": false,
    "shelf_life_days": 365,
    "unit_of_measure": "each",
    "avg_unit_cost": 4.20,
    "avg_retail_price": 7.99
  }
]


3️⃣ Inventory Snapshot (inventory_snapshot.json)
[
  { "sku_id": "SKU_001", "on_hand_units": 22, "on_order_units": 0 },
  { "sku_id": "SKU_002", "on_hand_units": 18, "on_order_units": 12 },
  { "sku_id": "SKU_003", "on_hand_units": 45, "on_order_units": 0 },
  { "sku_id": "SKU_004", "on_hand_units": 15, "on_order_units": 0 },
  { "sku_id": "SKU_005", "on_hand_units": 120, "on_order_units": 0 },
  { "sku_id": "SKU_006", "on_hand_units": 20, "on_order_units": 10 },
  { "sku_id": "SKU_007", "on_hand_units": 60, "on_order_units": 0 },
  { "sku_id": "SKU_008", "on_hand_units": 25, "on_order_units": 0 },
  { "sku_id": "SKU_009", "on_hand_units": 14, "on_order_units": 0 },
  { "sku_id": "SKU_010", "on_hand_units": 30, "on_order_units": 0 }
]


4️⃣ POS History (Last 28 Days) (pos_history.json)
(aggregated daily for brevity; real systems can use transactions)
[
  { "sku_id": "SKU_001", "avg_daily_units_sold": 6.2 },
  { "sku_id": "SKU_002", "avg_daily_units_sold": 4.5 },
  { "sku_id": "SKU_003", "avg_daily_units_sold": 9.8 },
  { "sku_id": "SKU_004", "avg_daily_units_sold": 3.9 },
  { "sku_id": "SKU_005", "avg_daily_units_sold": 2.1 },
  { "sku_id": "SKU_006", "avg_daily_units_sold": 0.8 },
  { "sku_id": "SKU_007", "avg_daily_units_sold": 3.4 },
  { "sku_id": "SKU_008", "avg_daily_units_sold": 2.6 },
  { "sku_id": "SKU_009", "avg_daily_units_sold": 3.1 },
  { "sku_id": "SKU_010", "avg_daily_units_sold": 1.9 }
]


5️⃣ Vendor Catalog (vendor_catalog.json)
[
  {
    "vendor_id": "VENDOR_DAIRY_01",
    "vendor_name": "NorthWest Dairy Supply",
    "lead_time_days": 2,
    "order_days": ["Mon", "Thu"],
    "min_order_value": 150,
    "line_items": [
      { "sku_id": "SKU_001", "case_pack": 6, "unit_cost": 3.10 },
      { "sku_id": "SKU_002", "case_pack": 12, "unit_cost": 3.60 },
      { "sku_id": "SKU_009", "case_pack": 6, "unit_cost": 2.80 }
    ]
  },
  {
    "vendor_id": "VENDOR_PRODUCE_01",
    "vendor_name": "Fresh Valley Produce",
    "lead_time_days": 1,
    "order_days": ["Daily"],
    "min_order_value": 75,
    "line_items": [
      { "sku_id": "SKU_003", "case_pack": 10, "unit_cost": 0.45 }
    ]
  },
  {
    "vendor_id": "VENDOR_GROCERY_01",
    "vendor_name": "Unified Grocery Distributors",
    "lead_time_days": 4,
    "order_days": ["Tue"],
    "min_order_value": 250,
    "line_items": [
      { "sku_id": "SKU_004", "case_pack": 12, "unit_cost": 1.20 },
      { "sku_id": "SKU_005", "case_pack": 24, "unit_cost": 0.75 },
      { "sku_id": "SKU_006", "case_pack": 5, "unit_cost": 12.00 },
      { "sku_id": "SKU_007", "case_pack": 12, "unit_cost": 1.80 },
      { "sku_id": "SKU_008", "case_pack": 10, "unit_cost": 4.50 },
      { "sku_id": "SKU_010", "case_pack": 6, "unit_cost": 4.20 }
    ]
  }
]


6️⃣ Constraints (constraints.json)
{
  "planning_horizon_days": 14,
  "cash_budget_cap": 1800,
  "storage_constraints": {
    "frozen_capacity_units": 60,
    "refrigerated_capacity_units": 120
  },
  "spoilage_tolerance_pct": 0.05,
  "preferred_service_level_by_category": {
    "Dairy": 0.97,
    "Produce": 0.98,
    "Dry Grocery": 0.94,
    "Snacks": 0.93,
    "Frozen": 0.95
  }
}


🔄 What this dataset enables
With just this data, your agents can demonstrate:
Forecast Agent


Detect high velocity perishables (bananas, milk)


Identify imminent stockout risks


EOQ Agent


Lower order caps for produce due to shelf life


Higher safety stock for dairy


Cash-aware ordering


Vendor Agent


Case-pack rounding


MOQ-driven consolidation


Lead-time-driven stockout alerts


Orchestrator


Produce a realistic PO


Explain decisions to a store owner in plain English



