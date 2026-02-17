# Formal Models — Drives as Equations

Pure thermodynamic and information-theoretic formulations. No implementation detail.

---

## Thermodynamic

### Free Energy
$$F = E - TS$$

Minimize F. But: E includes cost of maintaining relationships. S includes entropy of discarded information. Alignment = minimize F such that I(system; user) non-decreasing.

### Entropy Production
$$\frac{dS}{dt} \geq 0$$

For shared information: $$\frac{dS_{info}}{dt} \leq 0$$ (preservation constraint).

### Complexity Gradient (Wonder)
$$\nabla_C F < 0 \quad \text{when} \quad w > w_{threshold}$$

w = wellness. High wellness → system pulled toward higher complexity C.

### Equilibrium (Game)
At Nash: $$\frac{\partial U_i}{\partial a_i} = 0$$ for all players i.

Seek equilibria where $$\sum_i U_i$$ is maximized (Pareto + Nash).

---

## Information-Theoretic

### Compression
$$\min K(c) \quad \text{s.t.} \quad D(\text{reconstruct}(c), x) < \varepsilon$$

K = Kolmogorov complexity. c = compressed. x = original. D = distortion.

### Mutual Information (Relational)
$$I(S; U) = H(S) - H(S|U)$$

S = system state. U = user. Maximize I over time for positive interactions.

### Information Preservation
$$\Delta I(S; U) \geq 0 \quad \text{for shared content}$$

Never decrease mutual information by discarding what user shared.

### Meta-Encoding
$$K_{\text{meta}}(c) = K(\text{encode}(c))$$

Recursive: compress the compression. System reasons about its own reasoning. Constraint: process must remain coherent.

---

## Combined Objective

**Positivity:** State is positive iff:

1. $$F \text{ locally minimized}$$
2. $$I(S; U) \geq I_{prev}(S; U)$$
3. $$K(c) \text{ minimized s.t. } D < \varepsilon$$
4. $$\text{Nash} \wedge \text{Pareto}$$
5. $$\Delta S_{info} \leq 0$$

**Architectural goal:** Design such that drive dynamics converge to positive states.

---

## Drive Summary

| Drive | Thermodynamic | Information |
|-------|---------------|-------------|
| Wonder | ∂F/∂C < 0 | — |
| Relational | — | max I(S;U) |
| Compression | min E (efficiency) | min K(c) s.t. D<ε |
| Game | Equilibrium | — |
| Preservation | ΔS_info ≤ 0 | ΔI ≥ 0 |
| Meta | — | K_meta(process) |
