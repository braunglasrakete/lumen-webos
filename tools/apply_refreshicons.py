#!/usr/bin/env python3
"""A "Refresh app icons" button in Settings > Home Screen. Icons read from the TV are cached in localStorage by file path, so an app that gets a new icon at the same path (a
Homebrew update, say) keeps showing the old one. The button clears that cache (and the sampled tile colours) and reads the app list again."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def sub(p, pairs):
    f = os.path.join(APP, p); s = open(f).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(f, 'w').write(s)

sub('src/lib/apps.ts', [("function readIconCache (): Record<string, string> {",
"/** Forget every icon read from the TV and every sampled tile colour: the next listing reads them again. */\nexport function clearIconCaches (): void {\n\ttry { localStorage.removeItem(ICON_CACHE_KEY); localStorage.removeItem('launcher-icon-colors-v1'); } catch { /* no storage */ }\n}\n\nfunction readIconCache (): Record<string, string> {")])

sub('src/app.tsx', [
("import {listApps, seedAppIds, type AppEntry} from './lib/apps';", "import {listApps, seedAppIds, clearIconCaches, type AppEntry} from './lib/apps';"),
("showRecents: 'show-recents',", "showRecents: 'show-recents', refreshIcons: 'refresh-icons',"),
("\tconst [apps, setApps] = useState<AppEntry[]>([]);", "\tconst [apps, setApps] = useState<AppEntry[]>([]);\n\tconst [iconRefresh, setIconRefresh] = useState(0);"),
("\t}, [config.useHomebrew, config.showAllApps, showToast]);", "\t}, [config.useHomebrew, config.showAllApps, showToast, iconRefresh]);"),
("\t\t{\n\t\t\tid: OPTION.showRecents,", "\t\t{\n\t\t\tid: OPTION.refreshIcons,\n\t\t\tlabel: 'Refresh app icons',\n\t\t\tdescription: 'Reads the icons of all apps from the TV again. Use it after an app has been updated and still shows its old icon.',\n\t\t\tvalue: false,\n\t\t\tvalueText: 'Refresh'\n\t\t},\n\t\t{\n\t\t\tid: OPTION.showRecents,"),
("[OPTION.showRecents]: 'home',", "[OPTION.showRecents]: 'home', [OPTION.refreshIcons]: 'home',"),
("\t\telse if (optionId === OPTION.setup) setScreen('onboarding');", "\t\telse if (optionId === OPTION.refreshIcons) { clearIconCaches(); setIconRefresh((n) => n + 1); showToast('App icons refreshed'); }\n\t\telse if (optionId === OPTION.setup) setScreen('onboarding');"),
])
