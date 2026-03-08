# Hamilton LC Explorer V2

A browser-based tool for exploring and comparing Hamilton liquid handler liquid class databases. Built for Venus software users who need search and cross-instrument comparison capabilities that the built-in Liquid Class Editor does not provide.

---

## What It Does

### Explorer Mode
Load a single `ML_STARLiquids.db` file and browse all liquid classes in a searchable, sortable table. Toggle aspiration, dispense, and detection parameter groups on and off. Useful as a replacement for the Venus Liquid Class Editor when you just need to find and inspect a class quickly.

### Cross-Audit Mode
Load two databases from two different instruments and compare them side by side. The tool identifies:

- **PARAM DIFF** -- liquid classes that exist in both systems but have different parameter values
- **SYS 1 ONLY** -- liquid classes that exist only in System 1
- **SYS 2 ONLY** -- liquid classes that exist only in System 2

Use **MISMATCHES ONLY** to filter down to anomalies only. Export findings to a formatted Excel report or print directly from the browser.

---

## Why This Exists

When two Hamilton instruments run similar methods and produce inconsistent results, liquid class parameter drift is a common culprit. Venus provides no native way to compare liquid classes across instruments -- importing one instrument's packages overwrites the other's. This tool solves that by working directly with the database files offline, with no risk of modifying anything on either instrument.

**All operations are strictly read-only. No data is ever modified or transmitted.**

---

## Prerequisites

### Mac
- Python 3 (included on modern macOS)
- mdbtools -- install via Homebrew:
  ```bash
  brew install mdbtools
  ```

### Windows
Windows support via `pyodbc` is planned. See the Windows section below.

---

## Getting Started

### 1. Get the database file from a Hamilton instrument

On the Hamilton PC, copy this file:
```
C:\Program Files (x86)\HAMILTON\Config\ML_STARLiquids.mdb
```
For a cross-audit, copy this file from both instruments and place them in separate named folders so you can tell them apart (e.g. `Site_A/ML_STARLiquids.mdb` and `Site_B/ML_STARLiquids.mdb`).

### 2. Run the launcher

```bash
python3 launch.py
```

The launcher will:
1. Ask whether you want Explorer (1 file) or Cross-Audit (2 files)
2. Open a native file picker for each `.mdb` file
3. Convert each `.mdb` to a SQLite `.db` file in the same directory as the source
4. Start a local web server and open the tool in your browser automatically

### 3. Explore or audit

The browser tool opens with your data already loaded. No manual file selection needed.

---

## Testing Without a Real Hamilton System

Two test databases are included -- `Site_A_Master.db` and `Site_B_STARlet.db`. These are SQLite files derived from a real Hamilton database with a small number of deliberate differences injected into Site B:

- `AsFlowRate` modified for all Water liquid classes
- `PressureLLDSensitivity` modified for Ethanol classes

Load them directly into the HTML tool (no conversion needed -- they are already SQLite) to verify the audit logic is working correctly. You should see those classes flagged as PARAM DIFF in Cross-Audit mode.

To regenerate the test databases from a source `.mdb` file:
```bash
python3 generate_test_dbs.py
```

---

## File Reference

| File | Purpose |
|------|---------|
| `hamilton_lc_v2.html` | Main browser tool -- Explorer and Cross-Audit modes |
| `launch.py` | Mac launcher -- converts `.mdb` to `.db`, starts server, opens browser |
| `generate_test_dbs.py` | Generates the two test databases from a source `.db` file |
| `Site_A_Master.db` | Test database -- reference instrument |
| `Site_B_STARlet.db` | Test database -- instrument with injected differences |

---

## Using the Tool Without the Launcher

If you already have `.db` (SQLite) files and don't need conversion, you can open `hamilton_lc_v2.html` directly via any local web server (e.g. VS Code Live Server) and load files manually using the file picker in the UI.

The launcher is required when starting from `.mdb` files since browsers cannot read the Access database format directly.

---

## Windows

The Windows path for this tool is planned but not yet implemented. The intended approach is:

- A Python script using `pyodbc` and the Microsoft Access ODBC driver to convert `.mdb` to SQLite
- The same `hamilton_lc_v2.html` tool works identically once the conversion is done
- A `.bat` setup validator to check Python, Access drivers, and pyodbc are installed

Contributions welcome.

---

## Notes and Limitations

- The tool loads the entire `LiquidClass` table. On a typical Hamilton system this is 400-500 classes and performs well in the browser.
- Liquid class parameter comparison normalizes numeric values before comparing, so `500`, `"500"`, and `500.0` are treated as equal.
- The `.mdb` to `.db` conversion uses `mdb-export` (mdbtools) with `latin-1` decoding to correctly handle special characters such as the µ symbol in parameter labels.
- TADM tolerance band data (`TadmToleranceBand` table) is not currently included in the comparison. This is a potential future addition.

---

## License

MIT
