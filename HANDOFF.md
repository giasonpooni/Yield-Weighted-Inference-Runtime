# HANDOFF

Public siblings: Construction-State-Estimator-for-BIM,
Parameterized-Lyapunov-Stability-Runtime,
Jacobian-Sensitivity-Propagation-Testbed,
CNC-Machine-MCP, Atelier-MCP.
This repository is the admission slice. It does not import those
packages and does not absorb their domains.

## Delivered

- `ywir` package: department budgets, proposal / settlement records,
  spill classifier, composition store, decide / settle runtime,
  citeable receipts.
- Observations are declared. No embeddings. No judge model.
- Gauge spend is refused. Unglued settlement is refused and does
  not debit.
- Reference loops in examples: `pe-loop`, `mill-loop`.

## Development status

In development. Receipts carry `git_pin=in_development` until the
catalog pins a SHA. Do not treat a green pytest or a written
results file as a release.

## Not delivered

- Learned eta observer, dual-price LP solver, MPC horizon,
  Lyapunov V on budget dynamics, cascade / RouteLLM, imports of
  gat / lyapunov / sensitivity, energy-per-token accounting.

## Run

```
uv run --python 3.13 python examples/quickstart.py
uv run --python 3.13 python examples/mill_token_gate.py
uv run --python 3.13 --dev pytest
```
