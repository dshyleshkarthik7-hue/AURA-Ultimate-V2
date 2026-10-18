CREATE TABLE IF NOT EXISTS aura_checkout_orders (
  paypal_order_id TEXT PRIMARY KEY,
  session_hash TEXT NOT NULL,
  sku TEXT NOT NULL,
  item_name TEXT NOT NULL,
  amount TEXT NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'CREATED' CHECK (status IN ('CREATED','APPROVED','COMPLETED','CANCELLED','FAILED')),
  capture_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS aura_checkout_orders_session_created_idx
  ON aura_checkout_orders (session_hash, created_at DESC);
CREATE TABLE IF NOT EXISTS aura_checkout_rate_limits (
  rate_key TEXT NOT NULL,
  window_start TIMESTAMPTZ NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (rate_key, window_start)
);
CREATE TABLE IF NOT EXISTS aura_paypal_webhook_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  order_id TEXT,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
