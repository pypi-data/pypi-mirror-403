# Crosstabs MCP Server

<!-- mcp-name: io.github.barangaroo/crosstabs-mcp -->

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

A Python MCP (Model Context Protocol) server providing **40+ statistical tools** for contingency table analysis. Designed for AI assistants like Claude to perform rigorous statistical analysis.

## Features

### Core Statistical Tests
| Test | Description |
|------|-------------|
| **Chi-square** | Pearson's chi-square test of independence |
| **G-test** | Likelihood ratio test (more accurate for small samples) |
| **Fisher's exact** | Exact test for 2×2 tables |
| **McNemar's** | Test for paired categorical data |

### Effect Sizes & Measures
| Measure | Use Case |
|---------|----------|
| **Cramér's V** | Effect size for any table size (with bias correction) |
| **Phi coefficient** | Effect size for 2×2 tables |
| **Odds ratio** | Association strength with confidence intervals |
| **Relative risk** | Risk comparison between groups |
| **Risk difference** | Absolute risk reduction |
| **Attributable risk** | Population-level impact |

### Ordinal Measures
| Measure | Description |
|---------|-------------|
| **Spearman's rho** | Rank correlation |
| **Kendall's tau** | Concordance measure |
| **Goodman-Kruskal gamma** | Ordinal association |
| **Somers' D** | Asymmetric ordinal measure |
| **Stuart's tau-c** | Rectangular table measure |

### Agreement & Reliability
| Measure | Description |
|---------|-------------|
| **Cohen's kappa** | Inter-rater agreement |
| **Weighted kappa** | Agreement with ordinal weights |

### Advanced Analysis
| Tool | Description |
|------|-------------|
| **CMH test** | Stratified analysis controlling confounders |
| **Breslow-Day** | Test homogeneity of odds ratios |
| **Correspondence analysis** | Dimensionality reduction for tables |
| **Monte Carlo chi-square** | Exact p-values via simulation |
| **Power analysis** | Sample size and power calculations |
| **Multiple comparisons** | Bonferroni and FDR corrections |

## Installation

### From PyPI (recommended)
```bash
pip install crosstabs-mcp
```

### From source
```bash
git clone https://github.com/barangaroo/crosstabs-lite.git
cd crosstabs-lite/mcp-server-python
pip install -e .
```

## Quick Start

### Run the MCP Server
```bash
crosstabs-mcp
```

Or directly:
```bash
python -m crosstabs_mcp.server
```

### Configure Claude Code

Add to your `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "crosstabs": {
      "command": "crosstabs-mcp"
    }
  }
}
```

Or with Python path:
```json
{
  "mcpServers": {
    "crosstabs": {
      "command": "python",
      "args": ["-m", "crosstabs_mcp.server"]
    }
  }
}
```

## Usage Examples

Once configured, Claude can perform statistical analysis:

### Chi-square Test
```
User: Test if there's an association between treatment and outcome:
      Treatment A: 50 success, 30 failure
      Treatment B: 20 success, 40 failure

Claude: [Uses chi_square_test with matrix [[50,30],[20,40]]]
        χ² = 11.67, p = 0.0006
        Cramér's V = 0.29 (small-medium effect)
        There is a significant association between treatment and outcome.
```

### Odds Ratio
```
User: Calculate the odds ratio for this case-control study:
      Cases: 30 exposed, 70 unexposed
      Controls: 15 exposed, 85 unexposed

Claude: [Uses odds_ratio with matrix [[30,70],[15,85]]]
        OR = 2.43 (95% CI: 1.21-4.87)
        Exposure is associated with 143% higher odds of the outcome.
```

### Fisher's Exact Test
```
User: I have a small sample: [[3,1],[1,5]]. Is it significant?

Claude: [Uses fishers_exact with the matrix]
        p = 0.103 (two-tailed)
        Not statistically significant at α=0.05.
```

## Available Tools

| Tool Name | Description |
|-----------|-------------|
| `chi_square_test` | Chi-square test of independence |
| `g_test` | G-test (likelihood ratio) |
| `fishers_exact` | Fisher's exact test (2×2) |
| `mcnemar_test` | McNemar's test for paired data |
| `odds_ratio` | Odds ratio with CI |
| `relative_risk` | Relative risk with CI |
| `risk_difference` | Risk difference with CI |
| `cramers_v` | Cramér's V effect size |
| `cramers_v_corrected` | Bias-corrected Cramér's V |
| `phi_coefficient` | Phi for 2×2 tables |
| `cohens_kappa` | Cohen's kappa |
| `weighted_kappa` | Weighted kappa |
| `spearmans_rho` | Spearman's rank correlation |
| `kendalls_tau` | Kendall's tau-b |
| `goodman_kruskal_gamma` | Gamma coefficient |
| `somers_d` | Somers' D |
| `tau_c` | Stuart's tau-c |
| `cmh_test` | Cochran-Mantel-Haenszel |
| `breslow_day` | Breslow-Day test |
| `linear_trend_test` | Linear-by-linear association |
| `correspondence_analysis` | Correspondence analysis |
| `monte_carlo_chi_square` | Monte Carlo exact test |
| `power_analysis` | Power/sample size |
| `bonferroni_correction` | Bonferroni p-value adjustment |
| `fdr_correction` | Benjamini-Hochberg FDR |
| `standardized_residuals` | Cell residuals |
| `post_hoc_analysis` | Post-hoc chi-square decomposition |
| `proportion_ci` | Confidence interval for proportion |
| `check_assumptions` | Validate chi-square assumptions |
| `mosaic_plot_data` | Data for mosaic visualization |
| `stacked_bar_data` | Data for stacked bar chart |
| `attributable_risk` | Attributable risk measures |
| `chi_square_yates` | Yates' continuity correction |
| `detect_outliers` | Outlier detection |
| `crosstab_from_data` | Build table from raw data |
| `crosstab_from_csv` | Build table from CSV |

## Development

### Run Tests
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Project Structure
```
mcp-server-python/
├── crosstabs_mcp/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   └── advanced_stats.py  # Additional functions
├── tests/
│   └── test_statistics.py # Test suite (52 tests)
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- mcp >= 1.0.0
- fastmcp >= 0.1.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- pandas >= 2.0.0
- statsmodels >= 0.14.0

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](../CONTRIBUTING.md) first.

## Links

- [Main Repository](https://github.com/barangaroo/crosstabs-lite)
- [Web Application](https://crosstabs-lite.vercel.app)
- [MCP Documentation](https://modelcontextprotocol.io)
