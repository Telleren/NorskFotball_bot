# NorskFotballBot

Generator for rundetråder til Reddit (norsk fotball), med to måter å bruke prosjektet på:
1. Statisk webside (`index.html`) for manuell copy/paste.
2. Python-CLI for preview/post.

## Web (anbefalt for manuell posting)

`index.html` er laget for GitHub Pages og har:
- knapp: `Generer rundetråd Eliteserien`
- knapp: `Generer rundetråd OBOS-ligaen`
- knapp: `Generer rundetråd Norgesmesterskapet`
- runde-felt ved hver knapp
- popup med ferdig tittel + markdown body, klar for kopiering

Merk:
- Cupen (Norgesmesterskapet) bruker runder `1-7`.
- Cup-output inkluderer kun kampliste (ingen tabellseksjon).

### Publiser på GitHub Pages

1. Push repoet til GitHub.
2. Gå til `Settings -> Pages`.
3. Velg `Deploy from a branch`.
4. Velg branch `main` og folder `/ (root)`.
5. Åpne URL-en GitHub Pages gir deg.

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
- Norgesmesterskapet (Cupen): league id `206`

For webvarianten hentes data via CORS-proxy (primært `api.codetabs.com`, fallback `r.jina.ai`) slik at det fungerer fra en statisk GitHub Pages-side.
