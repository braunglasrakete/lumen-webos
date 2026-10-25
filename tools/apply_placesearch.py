#!/usr/bin/env python3
"""Fifty-fifth patch layer: find the weather place by typing. Settings > Options gets "Weather place search": an on-screen keyboard (arrows + OK, or the remote's number keys /
a physical keyboard) to type a city name or a postcode, then a list of matches from Open-Meteo's geocoding service (the same free, key-less service family as the weather
itself; it takes postcodes in the same field, ignores accents, and "Paris, France" narrows by country). The chosen place overrides the country/city lists; stepping through those
lists, or choosing "Auto" in the search, takes it away again. The place is stored in the config as {name, lat, lon, detail}."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def P(p): return os.path.join(APP, p)
def sub(p, pairs):
    s = open(P(p)).read()
    for pair in pairs:
        a, b = pair[0], pair[1]
        want = pair[2] if len(pair) > 2 else 1   # how often the text must occur (and is replaced)
        assert s.count(a) == want, (p, s.count(a), a[:90])
        s = s.replace(a, b)
    open(P(p), 'w').write(s)

# ---------------------------------------------------------------- the stored place
sub('src/lib/storage.ts', [
 ("	weatherCity: string;\n", "	weatherCity: string;\n	/** a place found by typing (name or postcode): overrides the country and city above; null = not used */\n	weatherPlace: {name: string; lat: number; lon: number; detail: string} | null;\n"),
 ("	weatherCity: '',\n	folders: [],", "	weatherCity: '',\n	weatherPlace: null,\n	folders: [],"),
 ("			weatherCity: typeof parsed.weatherCity === 'string' ? parsed.weatherCity : '',\n",
  "			weatherCity: typeof parsed.weatherCity === 'string' ? parsed.weatherCity : '',\n"
  "			weatherPlace: parsed.weatherPlace && typeof parsed.weatherPlace.name === 'string' && typeof parsed.weatherPlace.lat === 'number' && typeof parsed.weatherPlace.lon === 'number'\n"
  "				? {name: parsed.weatherPlace.name, lat: parsed.weatherPlace.lat, lon: parsed.weatherPlace.lon, detail: typeof parsed.weatherPlace.detail === 'string' ? parsed.weatherPlace.detail : ''}\n"
  "				: null,\n"),
])

# (the original's weather cache key already carries the coordinates, so two places with the same name do not share a reading)

# ---------------------------------------------------------------- the search screen
open(P('src/components/PlaceSearch.tsx'), 'w').write(r"""import {useCallback, useEffect, useRef, useState} from 'preact/hooks';
import {useKeys, type NavKey} from '../hooks/useKeys';
import {t as tr} from '../lib/i18n';

/** A place found by typing; stored in the config as weatherPlace. */
export interface Place { name: string; lat: number; lon: number; detail: string; }

interface Props {
	/** two-letter language for the place names ('en', 'de' ...) */
	lang: string;
	/** a place was chosen; null = go back to Auto (found from the internet connection) */
	onPick: (place: Place | null) => void;
	onClose: () => void;
}

interface Key { id: string; label: string; ch?: string; }
interface GeoResult { name: string; latitude: number; longitude: number; country?: string; country_code?: string; admin1?: string; postcodes?: string[]; }

const chars = (s: string): Key[] => s.split('').map((c) => ({id: c, label: c.toUpperCase(), ch: c}));
const KEYS: Key[][] = [
	chars('1234567890'),
	chars('abcdefghij'),
	chars('klmnopqrst'),
	chars('uvwxyz-,.\''),
	[{id: 'space', label: 'Space'}, {id: 'delete', label: 'Delete'}, {id: 'clear', label: 'Clear'}, {id: 'auto', label: 'Use Auto'}, {id: 'search', label: 'Search'}]
];
const MAX_LENGTH = 40;

const HINT_KEYS = 'Type a city or a postcode with the arrows and OK (or the number keys). Add a country to narrow it down, like Paris, France.';
const HINT_RESULTS = 'Up and down choose · OK uses that place · Left or Back returns to the keyboard';

/** the key under the same x position in another row (the rows differ in length) */
const across = (col: number, from: number, to: number) => Math.min(to - 1, Math.floor(((col + 0.5) * to) / from));

function toPlace (r: GeoResult): Place {
	const area = r.admin1 && r.admin1 !== r.name ? r.admin1 : '';
	const where = [area, r.country_code || r.country || ''].filter(Boolean).join(', ');
	const code = r.postcodes && r.postcodes.length > 0 ? r.postcodes[0] : '';
	return {name: r.name, lat: Math.round(r.latitude * 1000) / 1000, lon: Math.round(r.longitude * 1000) / 1000, detail: where + (code ? ' · ' + code : '')};
}

/** Full-screen place search for the Weather option: a small on-screen keyboard on the left, the matches on the right. */
export function PlaceSearch ({lang, onPick, onClose}: Props) {
	const [query, setQuery] = useState('');
	const [zone, setZone] = useState<'keys' | 'results'>('keys');
	const [kr, setKr] = useState(1);
	const [kc, setKc] = useState(0);
	const [results, setResults] = useState<Place[]>([]);
	const [ri, setRi] = useState(0);
	const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'empty' | 'error' | 'short'>('idle');
	const request = useRef(0);

	const type = (ch: string) => setQuery((q) => (q + ch).slice(0, MAX_LENGTH));

	const search = () => {
		const q = query.trim();
		if (q.length < 2) { setStatus('short'); return; }
		const id = ++request.current;
		setStatus('loading');
		fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=8&language=${encodeURIComponent(lang || 'en')}&format=json`)
			.then((r) => { if (!r.ok) throw new Error('search failed'); return r.json() as Promise<{results?: GeoResult[]}>; })
			.then((d) => {
				if (id !== request.current) return;
				const list = (d.results || []).filter((r) => typeof r.latitude === 'number' && typeof r.longitude === 'number').map(toPlace);
				setResults(list);
				setRi(0);
				setStatus(list.length > 0 ? 'done' : 'empty');
				if (list.length > 0) setZone('results');
			})
			.catch(() => { if (id === request.current) setStatus('error'); });
	};

	const press = (k: Key) => {
		if (k.ch) type(k.ch);
		else if (k.id === 'space') type(' ');
		else if (k.id === 'delete') setQuery((q) => q.slice(0, -1));
		else if (k.id === 'clear') { setQuery(''); setResults([]); setStatus('idle'); }
		else if (k.id === 'auto') onPick(null);
		else if (k.id === 'search') search();
	};

	const handleKey = useCallback((key: NavKey): boolean => {
		if (key === 'back') { if (zone === 'results') setZone('keys'); else onClose(); return true; }
		if (zone === 'results') {
			if (key === 'up') setRi((i) => Math.max(0, i - 1));
			else if (key === 'down') setRi((i) => Math.min(results.length - 1, i + 1));
			else if (key === 'left') setZone('keys');
			else if (key === 'enter' && results[ri]) onPick(results[ri]);
			return true;
		}
		const row = KEYS[kr];
		if (key === 'left') setKc((c) => Math.max(0, c - 1));
		else if (key === 'right') { if (kc >= row.length - 1 && results.length > 0) setZone('results'); else setKc((c) => Math.min(row.length - 1, c + 1)); }
		else if (key === 'up' && kr > 0) { setKc(across(kc, row.length, KEYS[kr - 1].length)); setKr(kr - 1); }
		else if (key === 'down' && kr < KEYS.length - 1) { setKc(across(kc, row.length, KEYS[kr + 1].length)); setKr(kr + 1); }
		else if (key === 'enter') press(row[kc]);
		return true;
	}, [zone, kr, kc, ri, results, query, lang]);

	useKeys(handleKey, true);

	// the remote's number keys and a physical keyboard type straight into the box
	useEffect(() => {
		const onType = (e: KeyboardEvent) => {
			if (e.ctrlKey || e.metaKey || e.altKey) return;
			const c = e.keyCode;
			if (c >= 48 && c <= 57) type(String(c - 48));
			else if (c >= 65 && c <= 90) type(String.fromCharCode(c).toLowerCase());
			else if (c === 32) type(' ');
			else if (c === 8) setQuery((q) => q.slice(0, -1));
			else return;
			setZone('keys');
			e.preventDefault();
		};
		window.addEventListener('keydown', onType);
		return () => window.removeEventListener('keydown', onType);
	}, []);

	const message = status === 'loading' ? 'Searching...'
		: status === 'short' ? 'Type at least two characters.'
		: status === 'empty' ? 'No places found. Try another spelling, or add the country, like Paris, France.'
		: status === 'error' ? "Couldn't search. Check the internet connection." : '';

	return (
		<div class="psearch">
			<div class="psearch__panel">
				<h1 class="psearch__title">{tr('Find your place')}</h1>
				<p class="psearch__hint">{tr(zone === 'results' ? HINT_RESULTS : HINT_KEYS)}</p>
				<div class="psearch__main">
					<div class="psearch__left">
						<div class="psearch__query">{query ? <span>{query}</span> : <span class="psearch__placeholder">{tr('City or postcode')}</span>}<span class="psearch__caret" /></div>
						<div class="psearch__keys">
							{KEYS.map((row, r) => (
								<div key={r} class={`psearch__row${r === KEYS.length - 1 ? ' psearch__row--actions' : ''}`}>
									{row.map((k, c) => (
										<div
											key={k.id}
											class={`psearch__key${k.ch ? '' : ' psearch__key--action'}${zone === 'keys' && r === kr && c === kc ? ' psearch__key--focused' : ''}`}
											onMouseEnter={() => { setZone('keys'); setKr(r); setKc(c); }}
											onClick={() => press(k)}
										>{k.ch ? k.label : tr(k.label)}</div>
									))}
								</div>
							))}
						</div>
					</div>
					<div class="psearch__results">
						{message && <p class="psearch__message">{tr(message)}</p>}
						{status === 'done' && results.map((p, i) => (
							<div
								key={`${p.lat},${p.lon},${i}`}
								class={`psearch__result${zone === 'results' && i === ri ? ' psearch__result--focused' : ''}`}
								onMouseEnter={() => { setZone('results'); setRi(i); }}
								onClick={() => onPick(p)}
							>
								<div class="psearch__name">{p.name}</div>
								<div class="psearch__detail">{p.detail}</div>
							</div>
						))}
					</div>
				</div>
			</div>
		</div>
	);
}
""")

# ---------------------------------------------------------------- hooked into the app and Settings > Options
sub('src/app.tsx', [
 ("import {readWeather} from './lib/weather';\n", "import {readWeather} from './lib/weather';\nimport {PlaceSearch, type Place} from './components/PlaceSearch';\n"),
 ("city: 'weather-city',", "city: 'weather-city', placeSearch: 'weather-search',"),
 ("	const [controls, setControls] = useState(false);\n", "	const [controls, setControls] = useState(false);\n	const [placeSearch, setPlaceSearch] = useState(false);\n"),
 ("		const city = CITIES.filter((c) => c.name === config.weatherCity)[0] || null;", "		const city = config.weatherPlace || CITIES.filter((c) => c.name === config.weatherCity)[0] || null;"),
 ("	}, [config.showWeather, config.weatherCity, config.language]);", "	}, [config.showWeather, config.weatherCity, config.weatherPlace, config.language]);"),
 # the city option shows a typed place, and a new option opens the search
 ("			valueText: config.weatherCity || 'Auto'\n		},\n",
  "			valueText: config.weatherPlace ? config.weatherPlace.name : config.weatherCity || 'Auto'\n		},\n"
  "		{\n"
  "			id: OPTION.placeSearch,\n"
  "			label: 'Weather place search',\n"
  "			description: 'Type a city or a postcode, like 10115 or Paris, France. A place found this way replaces the country and city above.',\n"
  "			value: config.weatherPlace !== null,\n"
  "			valueText: 'Search'\n"
  "		},\n"),
 ("config.showAllApps, config.showWeather, config.weatherCity]);", "config.showAllApps, config.showWeather, config.weatherCity, config.weatherPlace]);"),
 # stepping through the lists drops a typed place
 ("updateConfig({...config, weatherCountry: next, weatherCity: first ? first.cities[0].name : ''});", "updateConfig({...config, weatherCountry: next, weatherCity: first ? first.cities[0].name : '', weatherPlace: null});", 2),
 ("updateConfig({...config, weatherCity: next, weatherCountry: country ? country.code : owner ? owner.code : ''});", "updateConfig({...config, weatherCity: next, weatherCountry: country ? country.code : owner ? owner.code : '', weatherPlace: null});", 2),
 ("[OPTION.city]: 'weather',", "[OPTION.city]: 'weather', [OPTION.placeSearch]: 'weather',"),
 ("		if (optionId === OPTION.useHomebrew) updateConfig(", "		if (optionId === OPTION.placeSearch) setPlaceSearch(true);\n		else if (optionId === OPTION.useHomebrew) updateConfig("),
 ("options={options} active onToggle={onToggle}", "options={options} active={!placeSearch} onToggle={onToggle}"),
 ("			{controls && <ControlCenter", """			{placeSearch && <PlaceSearch
				lang={config.language === 'auto' ? (navigator.language || 'en').slice(0, 2).toLowerCase() : config.language.slice(0, 2).toLowerCase()}
				onClose={() => setPlaceSearch(false)}
				onPick={(p: Place | null) => {
					const c = configRef.current;
					updateConfig(p ? {...c, weatherPlace: p, weatherCity: '', weatherCountry: ''} : {...c, weatherPlace: null, weatherCity: '', weatherCountry: ''});
					setPlaceSearch(false);
					showToast(p ? `Weather place: ${p.name}` : 'Weather place: Auto');
				}}
			/>}
			{controls && <ControlCenter"""),
])

# ---------------------------------------------------------------- look: a dark glass-free panel (no live blur), keys like the wallpaper chips
s = open(P('src/theme/global.css')).read()
s += """
/* ---------- place search (Settings > Options > Weather place search): a plain solid dark panel, no live blur ---------- */
.psearch { position: absolute; left: 0; top: 0; right: 0; bottom: 0; z-index: 40; display: flex; align-items: center; justify-content: center; background: #0a0c14; color: #fff; }
.psearch__panel { width: 1680px; }
.psearch__title { margin: 0 0 10px; text-align: center; font-size: 44px; font-weight: 600; }
.psearch__hint { margin: 0 0 40px; text-align: center; font-size: 22px; color: rgba(255, 255, 255, 0.62); }
.psearch__main { display: flex; flex-direction: row; justify-content: center; align-items: flex-start; }
.psearch__left { width: 1068px; margin-right: 64px; }
.psearch__query { height: 84px; padding: 0 32px; margin-bottom: 26px; display: flex; flex-direction: row; align-items: center; border-radius: 22px; background: rgba(255, 255, 255, 0.10); box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.22); font-size: 38px; letter-spacing: 0.02em; white-space: pre; overflow: hidden; }
.psearch__placeholder { color: rgba(255, 255, 255, 0.38); }
.psearch__caret { display: inline-block; width: 3px; height: 44px; margin-left: 4px; background: #fff; }
.psearch__row { display: flex; flex-direction: row; margin-bottom: 12px; }
.psearch__key { width: 96px; height: 78px; margin-right: 12px; display: flex; align-items: center; justify-content: center; border-radius: 18px; background: rgba(255, 255, 255, 0.12); font-size: 32px; font-weight: 500; }
.psearch__row .psearch__key:last-child { margin-right: 0; }
.psearch__row--actions .psearch__key { width: auto; flex: 1; font-size: 26px; }
.psearch__key--focused { background: #fff; color: #10131c; box-shadow: 0 8px 18px rgba(0, 0, 0, 0.4); }
.psearch__results { width: 548px; min-height: 420px; }
.psearch__message { margin: 24px 6px; font-size: 24px; line-height: 1.4; color: rgba(255, 255, 255, 0.66); }
.psearch__result { padding: 14px 26px 16px; margin-bottom: 10px; border-radius: 18px; background: rgba(255, 255, 255, 0.10); }
.psearch__name { font-size: 32px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.psearch__detail { margin-top: 2px; font-size: 22px; color: rgba(255, 255, 255, 0.62); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.psearch__result--focused { background: #fff; color: #10131c; }
.psearch__result--focused .psearch__detail { color: rgba(16, 19, 28, 0.66); }
"""
open(P('src/theme/global.css'), 'w').write(s)
