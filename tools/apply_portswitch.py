#!/usr/bin/env python3
"""Fifty-sixth patch layer: two switches in Settings > Options for features ported from samrenfrew/lumen-webos (MIT), both off by default so this build looks and behaves like before:
 - "New Control Center"   (config.newControlCenter) shows components/ControlCenterNew.tsx instead of the original, see apply_controlcenter2.py
 - "New home screen"     (config.newHome)           html class `homenew` and the new top-left clock block, see apply_homenew.py
This layer only adds the switches (stored in the config, listed in Options, toggled with OK, html class kept in step); the features themselves are the two layers after it."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def P(p): return os.path.join(APP, p)
def sub(p, pairs):
    s = open(P(p)).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:90])
        s = s.replace(a, b, 1)
    open(P(p), 'w').write(s)

sub('src/lib/storage.ts', [
 ("	weatherPlace: {name: string; lat: number; lon: number; detail: string} | null;\n",
  "	weatherPlace: {name: string; lat: number; lon: number; detail: string} | null;\n"
  "	/** ported from samrenfrew/lumen-webos, each off until switched on in Settings > Options: the new Control Center, the new home screen look */\n"
  "	newControlCenter: boolean;\n	newHome: boolean;\n"),
 ("	weatherPlace: null,\n", "	weatherPlace: null,\n	newControlCenter: false,\n	newHome: false,\n"),
 ("				: null,\n			folders: Array.isArray(parsed.folders)",
  "				: null,\n			newControlCenter: parsed.newControlCenter === true,\n			newHome: parsed.newHome === true,\n			folders: Array.isArray(parsed.folders)"),
])

sub('src/app.tsx', [
 ("placeSearch: 'weather-search',", "placeSearch: 'weather-search', newCC: 'new-control-center', newHome: 'new-home',"),
 ("			valueText: 'Search'\n		},\n",
  "			valueText: 'Search'\n		},\n"
  "		{\n"
  "			id: OPTION.newCC,\n"
  "			label: 'New Control Center',\n"
  "			description: 'A Control Center in the tvOS 26 style: a grid of glass controls, lists that grow out of their tile, a backlight bar and Eye Comfort. Switch it off for the original one.',\n"
  "			value: config.newControlCenter\n"
  "		},\n"
  "		{\n"
  "			id: OPTION.newHome,\n"
  "			label: 'New home screen look',\n"
  "			description: 'A big clock with the date and the weather under it, tiles lit from above and a stronger focus. Switch it off for the original look.',\n"
  "			value: config.newHome\n"
  "		},\n"),
 ("config.weatherCity, config.weatherPlace]);", "config.weatherCity, config.weatherPlace, config.newControlCenter, config.newHome]);"),
 ("		else if (optionId === OPTION.placeSearch) setPlaceSearch(true);\n",
  "		else if (optionId === OPTION.placeSearch) setPlaceSearch(true);\n"
  "		else if (optionId === OPTION.newCC) updateConfig({...config, newControlCenter: !config.newControlCenter});\n"
  "		else if (optionId === OPTION.newHome) updateConfig({...config, newHome: !config.newHome});\n"),
 ("	const [placeSearch, setPlaceSearch] = useState(false);\n",
  "	const [placeSearch, setPlaceSearch] = useState(false);\n"
  "	// the CSS of the ported features keys on these html classes\n"
  "	useEffect(() => { document.documentElement.classList.toggle('homenew', config.newHome); }, [config.newHome]);\n"),
])
