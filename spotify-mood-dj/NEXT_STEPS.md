# Verder werken op andere PC

## Status

De volledige Android app is aangemaakt en gecommit op branch `feature/wire-tapper-osint`.
Er is nog geen GitHub remote ingesteld — dat is de volgende stap.

---

## Stap 1: GitHub CLI installeren (als nog niet gedaan)

Open PowerShell als Administrator:

```powershell
winget install --id GitHub.cli --accept-package-agreements --accept-source-agreements
```

Na installatie, authenticeer:

```bash
gh auth login
```

---

## Stap 2: GitHub repo aanmaken + pushen

Navigeer naar de projectroot (waar alle projecten staan):

```bash
cd "C:\Users\<jouw-gebruiker>\OneDrive\Claude\projects"
```

Maak een nieuwe GitHub repo aan en push:

```bash
gh repo create spotify-mood-dj --public --source=. --remote=origin --push
```

Of als privé:

```bash
gh repo create spotify-mood-dj --private --source=. --remote=origin --push
```

---

## Stap 3: Pull Request aanmaken

```bash
gh pr create \
  --title "Add spotify-mood-dj Android app" \
  --base main \
  --head feature/wire-tapper-osint \
  --body "$(cat <<'EOF'
## Summary
- Android app (Kotlin + Jetpack Compose) met 4 mood-knoppen (Chill/Energy/Focus/Party)
- Spotify App Remote SDK voor achtergrond playback control
- Automatisch uurlijks VRT NWS nieuws via ExoPlayer (podcast RSS + live stream fallback)
- Audio transitie state machine: Spotify pause → nieuws → Spotify resume
- AlarmManager exact scheduling voor nieuws op het uur
- Foreground Service + BootReceiver voor betrouwbare achtergrondwerking

## Before building
1. Registreer app op https://developer.spotify.com/dashboard
   - Redirect URI: `spotify-djnews://callback`
   - Voeg SHA-1 fingerprint toe van je debug keystore
2. Download Spotify App Remote SDK AAR → plaats als `app/libs/spotify-app-remote-release-0.8.0.aar`
3. Zet Client ID in `local.properties`: `SPOTIFY_CLIENT_ID=jouw_client_id`

🤖 Generated with Claude Code
EOF
)"
```

---

## Projectstructuur (ter referentie)

```
spotify-mood-dj/
├── app/build.gradle.kts
├── gradle/libs.versions.toml
├── settings.gradle.kts
└── app/src/main/
    ├── AndroidManifest.xml
    └── kotlin/com/djnews/
        ├── DjNewsApplication.kt
        ├── MainActivity.kt
        ├── di/AppModule.kt
        ├── domain/model/Mood.kt          ← 4 moods + playlist URIs
        ├── domain/model/PlaybackState.kt
        ├── data/spotify/SpotifyAppRemoteManager.kt
        ├── data/news/VrtNwsRepository.kt  ← RSS + fallback stream
        ├── service/MusicPlayerService.kt  ← Foreground Service
        ├── service/NewsTransitionManager.kt
        ├── service/NewsPlayerController.kt
        ├── service/NewsScheduler.kt
        ├── receiver/NewsAlarmReceiver.kt
        ├── receiver/BootReceiver.kt
        └── ui/
            ├── mood/MoodSelectorScreen.kt
            ├── nowplaying/NowPlayingBar.kt
            ├── main/MainScreen.kt
            ├── main/MainViewModel.kt
            └── theme/Theme.kt
```
