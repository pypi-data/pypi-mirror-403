# Understanding 4PL Dose-Response Curves

## Introduction

This guide explains the **Four Parameter Logistic (4PL) model** and dose-response curves for researchers and biologists using the sprime library. You don't need to be a programmer to understand these concepts—this guide focuses on the biological and statistical meaning of dose-response analysis.

## What is a Dose-Response Curve?

A **dose-response curve** (also called a concentration-response curve) shows how a biological system responds to different concentrations of a compound (drug, chemical, etc.). The curve typically has a sigmoidal (S-shaped) appearance:

- **Low concentrations**: Minimal or baseline response
- **Intermediate concentrations**: Steep increase (or decrease) in response
- **High concentrations**: Response plateaus at maximum (or minimum) level

### Why Are Dose-Response Curves Important?

Dose-response curves are fundamental to:
- **Drug discovery**: Understanding how effective a compound is at different doses
- **Toxicology**: Determining safe concentration ranges
- **Pharmacology**: Characterizing drug potency and efficacy
- **High-throughput screening**: Ranking compounds by their biological activity

## The Four Parameter Logistic (4PL) Model

The 4PL model is a mathematical equation that describes sigmoidal dose-response relationships. It's also known as the **Hill equation**, named after Archibald Hill who developed it to describe oxygen binding to hemoglobin.

### The Mathematical Formula

The 4PL model is:

$$y = D + \frac{A - D}{1 + \left(\frac{x}{C}\right)^B}$$

Where:
- **y** = Response (what you measure: % viability, fluorescence, activity, etc.)
- **x** = Concentration (dose of compound)
- **A** = Lower asymptote (minimum response)
- **B** = Hill coefficient (steepness/slope)
- **C** = EC50 (half-maximal concentration)
- **D** = Upper asymptote (maximum response)

### The Four Parameters Explained

#### 1. Lower Asymptote (A) - Minimum Response

**What it means:**
- The response value when concentration is very low (approaching zero)
- Represents the baseline or control response
- In inhibition assays: the maximum response (no inhibition)
- In activation assays: the minimum response (no activation)

**Example:**
- If A = 5%, this means at very low concentrations, the response is 5% of maximum
- This could represent baseline cell viability or background signal

#### 2. Upper Asymptote (D) - Maximum Response

**What it means:**
- The response value when concentration is very high (approaching infinity)
- Represents the maximum achievable response
- In inhibition assays: the minimum response (maximum inhibition)
- In activation assays: the maximum response (maximum activation)

**Example:**
- If D = 95%, this means at very high concentrations, the response reaches 95% of maximum
- This could represent maximum cell death, maximum enzyme activity, etc.

#### 3. EC50 (C) - Half-Maximal Concentration

**What it means:**
- The concentration at which the response is halfway between the lower (A) and upper (D) asymptotes
- **EC50** = Effective Concentration 50% (for activation)
- **IC50** = Inhibitory Concentration 50% (for inhibition)
- A key measure of **potency**: lower EC50 = more potent compound

**Example:**
- If EC50 = 10 µM, this means at 10 micromolar concentration, the response is at 50% of the maximum range
- A compound with EC50 = 1 µM is more potent than one with EC50 = 100 µM

**Why it matters:**
- EC50 is the most commonly reported value in drug screening
- Allows comparison of compound potency across different assays
- Lower EC50 values indicate compounds that work at lower concentrations

#### 4. Hill Coefficient (B) - Steepness

**What it means:**
- Describes how steeply the curve transitions from low to high response
- Also called the "slope" or "Hill slope"
- Higher absolute values = steeper curve = more cooperative response
- Positive values = increasing curve (activation)
- Negative values = decreasing curve (inhibition)

**Example:**
- Hill coefficient = 1.5: moderate steepness, typical for many biological systems
- Hill coefficient = 3.0: very steep curve, suggests cooperative binding
- Hill coefficient = 0.5: shallow curve, suggests less cooperative response

**Biological interpretation:**
- Hill coefficient ≈ 1: Simple binding (one molecule per target)
- Hill coefficient > 1: Cooperative binding (multiple molecules work together)
- Hill coefficient < 1: Negative cooperativity or multiple binding sites

## Visualizing Dose-Response Curves

### Typical Curve Shapes

**Increasing Curve (Activation):**
```
Response
  100% |                    ╱─────── D (upper asymptote)
       |                  ╱
   50% |                ╱  ← EC50 point
       |              ╱
    0% |─────────────╱
       └────────────┴────────────┴────────────
         0.01       EC50         100
              Concentration (µM)
```

**Decreasing Curve (Inhibition):**
```
Response
  100% |─────────────╲
       |              ╲
   50% |                ╲  ← IC50 point
       |                  ╲
    0% |                    ╲─────── D (lower asymptote)
       └────────────┴────────────┴────────────
         0.01       IC50         100
              Concentration (µM)
```

## R-Squared: How Well Does the Curve Fit?

**R² (R-squared)** is a statistical measure that tells you how well your experimental data points match the fitted 4PL curve.

- **R² = 1.0**: Perfect fit (all data points lie exactly on the curve)
- **R² = 0.9**: Very good fit (90% of variance explained)
- **R² = 0.7**: Moderate fit (70% of variance explained)
- **R² < 0.5**: Poor fit (data may not follow sigmoidal pattern)

**What affects R²?**
- **Data quality**: Noisy or scattered data → lower R²
- **Data range**: Need concentrations spanning the full response range
- **Outliers**: Single bad data points can reduce R²
- **Biological variability**: Some assays are inherently more variable

**When is R² acceptable?**
- **R² > 0.9**: Excellent, publishable quality
- **R² > 0.8**: Good, reliable for most purposes
- **R² > 0.7**: Acceptable, but may want to investigate data quality
- **R² < 0.7**: Consider re-running assay or checking for issues

## How sprime Uses 4PL Fitting

When you use sprime to analyze your screening data:

1. **Input**: You provide raw dose-response data (concentrations and responses)

2. **Fitting**: sprime automatically fits a 4PL curve to your data using mathematical optimization

3. **Output**: You get:
   - **EC50**: Potency value
   - **Upper and Lower asymptotes**: Response range
   - **Hill coefficient**: Curve steepness
   - **R²**: Fit quality

4. **S' Calculation**: sprime then calculates the **S' (S prime)** metric from these parameters, which provides a single value summarizing the entire dose-response profile

## Common Questions

### Why use 4PL instead of simpler models?

The 4PL model captures the full sigmoidal shape of biological dose-response relationships. Simpler models (like linear) don't account for:
- Baseline responses at low concentrations
- Maximum achievable responses at high concentrations
- The S-shaped transition between these extremes

### What if my data doesn't look sigmoidal?

If your data doesn't follow a sigmoidal pattern, the 4PL fit may have low R². Possible reasons:
- **Insufficient concentration range**: Need data from baseline to plateau
- **Non-sigmoidal biology**: Some responses are linear or have different shapes
- **Data quality issues**: Outliers, experimental errors, or assay problems

### Can I compare EC50 values across different assays?

Yes, but be cautious:
- EC50 values are comparable within the same assay type
- Different readouts (viability vs. activity) may have different scales
- Always consider the biological context and assay conditions

### What's a "good" EC50 value?

It depends on your context:
- **Drug discovery**: Often looking for EC50 < 1 µM (nanomolar range is ideal)
- **Toxicology**: May be interested in higher concentrations
- **Research**: Depends on your specific question

The important thing is comparing EC50 values **within your screening assay** to rank compounds.

## Real-World Example

Imagine you're screening compounds for anti-cancer activity:

**Compound A:**
- EC50 = 0.5 µM (very potent!)
- R² = 0.95 (excellent fit)
- Upper asymptote = 90% (strong maximum effect)

**Compound B:**
- EC50 = 50 µM (less potent)
- R² = 0.88 (good fit)
- Upper asymptote = 75% (moderate maximum effect)

**Interpretation:**
- Compound A is **100x more potent** than Compound B (0.5 vs 50 µM)
- Compound A also has a **stronger maximum effect** (90% vs 75%)
- Both have good curve fits (R² > 0.85)
- **Conclusion**: Compound A is the better candidate

## Further Reading

For more information:
- **Configuration options**: See [Hill Curve Fitting Configuration](usage/hill_curve_fitting_configuration.md)
- **Background and concepts**: See [Background and Concepts](background_and_concepts.md) for qHTS and assay terminology
- **Theoretical foundations**: See references below

## References

1. **Hill, A. V.** (1910). The possible effects of the aggregation of the molecules of haemoglobin on its dissociation curves. *J. Physiol.*, 40, iv-vii.

2. **De Lean, A., Munson, P. J., & Rodbard, D.** (1978). Simultaneous analysis of families of sigmoidal curves: application to bioassay, radioligand assay, and physiological dose-response curves. *Am. J. Physiol.*, 235(2), E97-E102.

3. **Gottschalk, P. G., & Dunn, J. R.** (2005). The five-parameter logistic: a characterization and comparison with the four-parameter logistic. *Anal. Biochem.*, 343(1), 54-65.

4. **Cardillo, G.** (2012). Four parameters logistic regression - There and back again. MATLAB Central File Exchange. Retrieved from https://it.mathworks.com/matlabcentral/fileexchange/38122

5. **AAT Bioquest, Inc.** (2024). Quest Graph™ Four Parameter Logistic (4PL) Curve Calculator. Retrieved from https://www.aatbio.com/tools/four-parameter-logistic-4pl-curve-regression-online-calculator

