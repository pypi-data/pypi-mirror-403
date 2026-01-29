# Example Configurations

Quick reference catalog for **general-purpose** MDP configurations (manufacturing, DevOps, finance, etc.).

**👉 New to this?** Read the [Practical Guide](../../docs/PRACTICAL_GUIDE.md) for detailed explanations and real-world context.

---

## 📁 Available Configurations

### 🏢 **General Purpose Examples**

#### `manufacturing_process.json` - Multi-Stage Production

- **Application**: Manufacturing quality control
- **Expected Cost**: $103.46
- **States**: Raw material → Stage 1 → Stage 2 → QC → Finished
- **Decision**: Standard process (fast, 10% defect) vs Careful process (slow, 2% defect)

**Optimal Strategy**: Standard process at both stages  
**Key Insight**: Careful process not worth the extra time for marginal improvement

---

#### `deployment_pipeline.json` - Software CI/CD

- **Application**: Software deployment with testing strategies
- **Expected Cost**: 52 person-hours
- **States**: Development → Staging → Production
- **Decision**: Minimal testing (fast, risky) vs Standard vs Comprehensive (slow, safe)

**Optimal Strategy**: Standard testing (not minimal, not comprehensive!)  
**Key Insight**: Balance between speed and safety; extremes rarely optimal

---

#### `investment_strategy.json` - Portfolio Management

- **Application**: Investment rebalancing with transaction costs
- **Expected Cost**: 1.17 basis points
- **States**: Cash → Low/Medium/High risk → Target return
- **Decision**: Hold vs Rebalance to different risk levels

**Optimal Strategy**: Start low-risk, never rebalance!  
**Key Insight**: Transaction costs kill returns; buy-and-hold wins

---

---

## 🆚 Quick Comparison

| Config        | Application     | Expected Cost   | Key Decision                |
| ------------- | --------------- | --------------- | --------------------------- |
| Manufacturing | Quality control | $103.46         | Standard vs careful process |
| Deployment    | CI/CD pipeline  | 52 person-hours | Testing level               |
| Investment    | Portfolio       | 1.17 bps        | Rebalance vs hold           |

---

## 💡 Tips for Choosing

### Start Here:

- **Manufacturing/Operations**: `manufacturing_process.json`
- **Software/DevOps**: `deployment_pipeline.json`
- **Finance/Investment**: `investment_strategy.json`

---

## 🎯 Key Differences Between Configs

### Manufacturing vs DevOps

- **Manufacturing**: Multi-stage production with quality control
- **DevOps**: Software deployment with testing strategies
- Both demonstrate cost vs quality trade-offs

### Investment Strategy

- Shows how transaction costs affect optimal strategy
- Demonstrates when "buy and hold" beats active rebalancing

---

## 📚 **More Information**

- **[Practical Guide](../../docs/PRACTICAL_GUIDE.md)** - Detailed explanations of each example
- **[JSON Guide](../../docs/JSON_GUIDE.md)** - Complete format reference and customization
- **[Main README](../../README.md)** - Library overview and API reference
