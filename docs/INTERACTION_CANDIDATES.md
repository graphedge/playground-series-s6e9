# Feature Interaction Candidates (Working Notes)

**Competition**: playground-series-s6e9  
**Target**: `Will_Buy_EV`  
**Baseline**: LightGBM raw ~0.9416 OOF ROC-AUC

**Status**: Candidate list for brute-force interaction testing. Not yet evaluated. Grounded in EDA from prior runs.

---

## Already Strong Mains (interactions may still help)

These features dominate alone; interactions could capture conditional effects:

- **`Subsidy_Available × [almost anything]`**  
  Subsidy dominates: No-subsidy floors at ~0.5–0.6% Yes across demographics. May interact with income, urban, charging, or concern to lift rates further in specific segments.

- **`Environmental_Concern_Level × Range_Anxiety_Level`**  
  Both strong; env×anxiety was Laya-ranked. High concern + low anxiety likely compound; test if high×high or low×low segments diverge beyond additive.

- **`Range_Anxiety_Level × Annual_Income_USD`**  
  Income lifts rates generally but did NOT significantly buffer high anxiety in logit. Brute-force: does income discretized (quartiles) × anxiety category reveal threshold effects?

- **`Subsidy_Available × Environmental_Concern_Level`**  
  Subsidy dominates, but env concern may predict who acts on subsidy vs who doesn't. Check if low-concern + subsidy still shows uplift.

- **`Subsidy_Available × Range_Anxiety_Level`**  
  Subsidy floors low-anxiety, high-subsidy rates. Does high-anxiety + subsidy drive near-zero or just lower-than-low?

---

## Infrastructure / Charging

Charging availability is infrastructure-dependent; interactions may clarify when infrastructure bottlenecks matter:

- **`Home_Charging_Possible × Subsidy_Available`**  
  HomeCharging=No crushed Rural/Suburban+Subsidy rates. This interaction likely strong. Test if HomeCharging=Yes makes subsidy effect larger or just baseline-shifts.

- **`Home_Charging_Possible × City_Type`**  
  Rural no-home-charging may be lethal; Urban no-home-charging may be mitigated by public infrastructure. Check if interaction beats additive sum.

- **`Charging_Stations_Near_Home × Charging_Stations_Near_Work`** (or sum total)  
  Does having stations at *both* home and work matter more than additive? Or is one location sufficient? Test product vs sum.

- **`Charging_Stations_Near_Work × City_Type`**  
  Work stations track Urban strongly; little EV signal beyond subsidy. May still interact: does high work-station count in Rural mean something different than in Urban?

---

## Urbanicity / Commute (weak "political" proxies — label carefully)

**⚠️ Caution**: City type and commute correlate with politics/demographics but are NOT party affiliation. No Country/State/party columns exist. Do not invent liberal/red-blue labels from Subsidy or Urban alone.

- **`City_Type × Daily_Commute_km` bands** (short ≤17.2, mid 17.2–47.4, long ≥47.4)  
  Short commutes show higher Yes rates than long. Does Urban+short vs Rural+short matter? Test discretized commute × City_Type.

- **`City_Type × Subsidy_Available`**  
  Urban+Subsidy ≠ best segment; Rural+Subsidy had higher Yes%. Interaction may be strong. Test if subsidy effect is *larger* in Rural vs Urban.

- **`City_Type × Daily_Commute_km × Subsidy_Available`** (3-way)  
  Long urban commute + No subsidy stays near floor. Does subsidy flip that segment more than others? Expensive to brute-force but may be worth shortlist.

- **`Daily_Commute_km × Range_Anxiety_Level`**  
  Long commute + high anxiety likely compound. Does short commute + low anxiety floor out? Test if interaction beats additive.

- **`Daily_Commute_km × Home_Charging_Possible`**  
  Mid vs short home-charging gap ~1pp — weak. But: long commute + no home charging may be dealbreaker. Test if interaction emerges at extremes.

---

## Demographics / Fleet

Demographics interact with infrastructure, subsidy, and attitudes:

- **`Age × Subsidy_Available`**  
  Interaction NOT significant in prior logit; mid-age mild bump only. Still worth brute-force: does subsidy lift younger vs older differently in tree splits?

- **`Age × City_Type`**  
  Urban clustering by age — OK to brute; NOT a political signal on its own. Check if Urban+young vs Rural+old segments diverge.

- **`Annual_Income_USD × Subsidy_Available`**  
  Does subsidy matter more for low-income (cost barrier) or high-income (who can afford anyway)? Test quartiles × subsidy.

- **`Annual_Income_USD × City_Type`**  
  Income distributions differ Urban/Suburban/Rural. Does high-income Rural behave like Urban? Test if interaction helps.

- **`Current_Car_Type × Subsidy_Available` / `× Range_Anxiety_Level`**  
  Car type weak alone. May interact: Sedan vs SUV owners respond differently to subsidy or anxiety? Test if signal emerges.

- **`Number_of_Cars_Owned × Range_Anxiety_Level`**  
  Cars uncorrelated with income (weak). Multi-car households may mitigate anxiety (backup car). Test if 2+ cars + high anxiety → higher Yes.

---

## Explicitly DO NOT Treat as Political Affiliation

**⚠️ No party/vote columns exist. Do not invent labels.**

- **Do NOT** create "liberal" or "conservative" proxy features from `Subsidy_Available` or `City_Type`.
- **Do NOT** label `Age × Urban × Subsidy` as "liberal voter" — P(Subsidy|Urban) is flat by age; no signal found.
- **OK to test**: Urban, Age, Subsidy as infrastructure/policy/demographic variables.
- **NOT OK**: Interpret interactions as "red-blue" political splits.

**Why this matters**: Subsidy_Available is policy in the data, not voter history. Urban is geography, not ideology. Interactions may be real (infrastructure, cost) without being political.

---

## Brute-Force Recipe (Suggested)

1. **Encode categoricals** (ordinal where ordered, one-hot where not).
2. **Build pairwise products** or use:
   - LightGBM native categorical interactions (`categorical_feature` + high `min_data_in_leaf`)
   - sklearn `PolynomialFeatures(degree=2, interaction_only=True)` on a shortlist (not all pairs)
3. **Score with 5-fold OOF ROC-AUC** vs raw LightGBM baseline (~0.9416).
4. **Keep only interactions that beat baseline** by a clear margin (e.g. +0.0005 AUC or interpretable split gain).
5. **Drop "political storytelling" features** that don't generalize or rely on invented labels.

---

## Notes

- **Not evaluated yet**: This is a candidate list for brute-force testing, not a record of findings.
- **Prefer interactions that use real columns**: No invented party/affiliation labels.
- **Baseline to beat**: 0.9416 OOF ROC-AUC (LightGBM raw, 5-fold CV).
- **Discretization**: Consider quartiles for continuous vars (Income, Commute, Age) when building interaction terms for trees vs logistic.
