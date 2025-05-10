# Model linking (OSeMOSYS & PyPSA-Eur) using Benders Decomposition

The [model_linking](https://github.com/EmiFej/WB-OEMC/tree/main/workflow/model_linking) folder includes scripts to link OSeMOSYS and PyPSA-Eur using Benders Decomposition. 

Example of how it would look when completed
```text
               (hourly load, VRE profile)         ┌───────────────┐
        ┌──────────────────────────────┐          │ PyPSA “OPF +  │   Duals
        │ OSeMOSYS master (5-year steps│───year──▶│  dispatch”    │────────┐
        │ 2020…2050)                   │          └───────────────┘        │
Cuts ───┼─ investment_vars, NPC obj    │◀──────────────────────────────────┘
        └──────────────────────────────┘
```
And the steps would then include:
1. Initial solve of OSeMOSYS with coarse op-cost proxies → invest₀
2. Build PyPSA network for 2025 (say) with invest₀ capacities, run hourly dispatch → get dual prices λᴛ
3. Generate cuts: add ∑λᴛ · capacity ≥ cost into master
4. Re-optimise master → invest₁, repeat for each planning period / scenario
5. Converge when upper- and lower-bound gap ≤ ε

### Example of structure ###

```text
benders-link/
├── data/
│   ├── tech_params.csv         # single source of truth
│   ├── demand_profiles_*.csv   # hourly demand per bus
│   └── weather_*.nc            # VRE profiles for PyPSA
├── osemosys/
│   ├── model.gms               # or .lp / .py if you use Pyomo
│   └── templates/
│       └── capacities.inc      # auto-generated each iter
├── pypsa/
│   ├── base_network.nc         # static buses/lines
│   └── scripts/
│       └── build_network.py    # fills in capacities
├── cuts/
│   └── cut_db.sqlite           # Benders cuts accumulate here
└── orchestrator.py             # <<< you’ll edit mostly this file
```


| Function               | Implementation                                                                          |
| ---------------------- | -------------------------------------------------------------------------------------- |
| `make_master_cut_file` | Reads *cuts/cut\_db.sqlite* → writes a GAMS *\$include* file with all accumulated cuts |
| `inject_capacities`    | Maps OSeMOSYS build decisions to `network.generators.p_nom` etc.                       |
| `store_cuts`           | Appends the latest cut text to SQLite (or a plain text file)                           |

## Solver & dual prerequisites ##
- PyPSA ≥ 0.30 with network.optimize(solver_name="highs", store_duals=True) gives you primal & dual values out-of-the-box when using HiGHS.
Duals appear in network.model.dual keyed by constraint names.

- OSeMOSYS needs a “dummy” variable Z in the objective so that the Benders cuts can constrain it from below (minimize Z + …).

## Gradual build-up ##
- Prototype with one year (e.g. 2030) and linear costs only.
- Log every payload you transfer (caps.to_csv("debug_iter1_caps.csv"), etc.).
- Validate: run PyPSA once with free capacities and check that it rebuilds the same mix the master proposes.
- Once the loop closes, add more years and weather scenarios (one PyPSA solve each).
- After convergence tuning, you can re-enable binaries in the master (start/stop decisions, fixed shares, etc.) if performance allows.

## Resources ##

[Pecci and Jenkins (2025)](https://zero.lab.princeton.edu/wp-content/uploads/2025/01/Pecci-Jenkins-2025-Regularized_Benders_Decomposition_for_High_Performance_Capacity_Expansion_Models.pdf) presents a multi-cut and level-set regularised Benders code.

[SpineOpt](https://github.com/spine-tools/SpineOpt.jl)→ open project showing Benders orchestration logic
