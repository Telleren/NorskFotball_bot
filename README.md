# NorskFotballBot

Generator for rundetråder til Reddit (r/NorskFotball), med to måter å bruke prosjektet på:
1. Statisk webside (`index.html`) for manuell copy/paste.
2. Python-CLI for preview/post.

## Web (anbefalt for manuell posting)

`index.html` er laget for GitHub Pages og har:
- knapp: `Generer rundetråd Eliteserien`
- knapp: `Generer rundetråd OBOS-ligaen`
- knapp: `Generer rundetråd Toppserien`
- knapp: `Generer rundetråd Norgesmesterskapet`
- rundefelt ved hver knapp
- popup med ferdig tittel + markdown body, klar for kopiering
- data leses fra `data/cache.json` i samme repo

### Publiser på GitHub Pages

1. Push repoet til GitHub.
2. Gå til `Settings -> Pages`.
3. Velg `Deploy from a branch`.
4. Velg branch `main` og folder `/ (root)`.
5. Åpne URL-en GitHub Pages gir deg.

### Oppdatering av cache

Nettsiden leser fra en lokal cachefil i repoet:
- `data/cache.json`

Denne oppdateres av GitHub Actions-workflowen:
- `.github/workflows/update-cache.yml`

Workflowen kjører:
- manuelt via `Run workflow`
- automatisk hver 6. time
- automatisk når cache-scriptet eller workflowen endres

### Lokal test av websiden

Åpne `index.html` direkte i nettleser, eller via enkel lokal server:

```powershell
python -m http.server 8000
```

Deretter: `http://localhost:8000`.

## Python-CLI (alternativ)

Python-delen lager samme type markdown og kan poste direkte til Reddit via PRAW.

### Installer

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Preview

```powershell
python -m norskfotballbot.main preview
python -m norskfotballbot.main preview --season 2026 --save output.md
python -m norskfotballbot.main preview --season 2025 --round 30
```

### Post direkte til Reddit

Kopier `.env.example` til `.env`, fyll inn Reddit-nøkler, og kjør:

```powershell
python -m norskfotballbot.main post --subreddit NorskFotball
```

## Kilder

FotMob brukes som primærkilde:
- Eliteserien: league id `59`
- OBOS-ligaen (1. Divisjon): league id `203`
- Toppserien: league id `331`
- Norgesmesterskapet (Cupen): league id `206`

For webvarianten hentes data av GitHub Actions og lagres i repoet som lokal cache, slik at GitHub Pages ikke er avhengig av tredjepartsproxyer ved brukstidspunktet.
