# Kernel

Import `ywir`. Catalog short name **YWIR**.

The kernel owns admission. Plants own world-claims.

```text
proposer  -->  ywir.decide  -->  ADMIT | COMPOSE | REQUEST_EVIDENCE | REFUSE | CLOSE
                  |                   |
                  |                   +--> receipt (citeable, non-owning)
                  v
             ywir.settle   -->  debit budget, update eta_hat, accept morphism
```

`A`, `V`, IFC belief, and mill kinematics are inputs to *other*
kernels. This repository does not form them.

Similarity, rank-delta, glue, and plant refuses are **declared**.
The kernel does not embed the burst. A missing glue on settlement
is `H1_NO_GLUE`, not a quality footnote.

Do not import this package into `gat` or `lyapunov`. Consumers pin a
git SHA and cite receipts. They do not share a digest.
