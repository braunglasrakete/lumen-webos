#!/usr/bin/env python3
"""Fifty-sixth patch layer: three switches in Settings > Options for features ported from samrenfrew/lumen-webos (MIT), all off by default so this build looks and behaves like before:
 - "Live blur glass"      (config.liveBlur)          html class `liveblur`, the CSS is in apply_liveblur.py
 - "New Control Center"   (config.newControlCenter) shows components/ControlCenterNew.tsx instead of the original, see apply_controlcenter2.py
 - "New home screen"     (config.newHome)           html class `homenew` and the new top-left clock block, see apply_homenew.py
This layer only adds the switches (stored in the config, listed in Options, toggled with OK, html classes kept in step); the features themselves are the three layers after it."""
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
  "	/** ported from samrenfrew/lumen-webos, each off until switched on in Settings > Options: live blur glass, the new Control Center, the new home screen look */\n"
  "	liveBlur: boolean;\n	newControlCenter: boolean;\n	newHome: boolean;\n"),
 ("	weatherPlace: null,\n", "	weatherPlace: null,\n	liveBlur: false,\n	newControlCenter: false,\n	newHome: false,\n"),
 ("				: null,\n			folders: Array.isArray(parsed.folders)",
  "				: null,\n			liveBlur: parsed.liveBlur === true,\n			newControlCenter: parsed.newControlCenter === true,\n			newHome: parsed.newHome === true,\n			folders: Array.isArray(parsed.folders)"),
])

sub('src/app.tsx', [
 ("placeSearch: 'weather-search',", "placeSearch: 'weather-search', liveBlur: 'live-blur', newCC: 'new-control-center', newHome: 'new-home',"),
 ("			valueText: 'Search'\n		},\n",
  "			valueText: 'Search'\n		},\n"
  "		{\n"
  "			id: OPTION.liveBlur,\n"
  "			label: 'Live blur glass',\n"
  "			description: 'The glass blurs what is behind it live, as on tvOS 26, instead of showing a pre-blurred copy of the wallpaper. Looks lighter and more see-through, but is heavier for the TV: switch it off if it lags.',\n"
  "			value: config.liveBlur\n"
  "		},\n"
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
 ("config.weatherCity, config.weatherPlace]);", "config.weatherCity, config.weatherPlace, config.liveBlur, config.newControlCenter, config.newHome]);"),
 ("		else if (optionId === OPTION.placeSearch) setPlaceSearch(true);\n",
  "		else if (optionId === OPTION.placeSearch) setPlaceSearch(true);\n"
  "		else if (optionId === OPTION.liveBlur) updateConfig({...config, liveBlur: !config.liveBlur});\n"
  "		else if (optionId === OPTION.newCC) updateConfig({...config, newControlCenter: !config.newControlCenter});\n"
  "		else if (optionId === OPTION.newHome) updateConfig({...config, newHome: !config.newHome});\n"),
 ("	const [placeSearch, setPlaceSearch] = useState(false);\n",
  "	const [placeSearch, setPlaceSearch] = useState(false);\n"
  "	// the CSS of the ported features keys on these html classes\n"
  "	useEffect(() => { document.documentElement.classList.toggle('liveblur', config.liveBlur); }, [config.liveBlur]);\n"
  "	useEffect(() => { document.documentElement.classList.toggle('homenew', config.newHome); }, [config.newHome]);\n"),
])
