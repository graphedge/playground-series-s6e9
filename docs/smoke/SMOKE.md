# Smoke gate (Spec 002) — PASS

We tried a bigger LightGBM (deeper/wider trees, and the same with simple "subsidy up / anxiety down" rules) on a random 25% slice of train.

It ran fine. Scores moved a little vs the same-slice baseline — slightly worse, not flat — so the gate passes and we can plan full experiments. Deeper trees are not free gains; tune carefully.

Numbers (3-fold OOF on the sample):
- A (depth 6, 31 leaves): 0.94076
- B (depth 8, 64 leaves): 0.94027 (−0.00049 vs A)
- C (B + monotone): 0.94060 (−0.00017 vs A)
