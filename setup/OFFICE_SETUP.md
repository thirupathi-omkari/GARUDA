# GARUDA Office PC Setup

## First Time Only

1. Install Python 3.13+
2. Install Git
3. Clone repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd GARUDA
```

4. Create Virtual Environment

```powershell
python -m venv .venv
```

5. Activate

```powershell
.venv\Scripts\activate
```

6. Install Packages

```powershell
pip install -r requirements.txt
```

7. Copy

```
.env.example
```

to

```
.env
```

8. Fill

```
KITE_API_KEY=
KITE_API_SECRET=
```

9. Run

```powershell
python run_garuda_live_paper.py
```

GARUDA will automatically:

- Ask for Kite Login (if needed)
- Generate Access Token
- Save Access Token
- Continue
