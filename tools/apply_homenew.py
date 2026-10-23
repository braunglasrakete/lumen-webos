#!/usr/bin/env python3
"""Fifty-nineth patch layer: the new home screen look of samrenfrew/lumen-webos (MIT), behind Settings > Options > "New home screen look" (config.newHome, html class `homenew`, see
apply_portswitch.py). When it is on: a large clock at the top left with the date and the weather (with an icon) under it, tiles lit from above (a soft shadow, a light from the top
left, bright top rim) and a stronger focus. Every rule is scoped to html.homenew, so with the switch off nothing changes. The weather now also reports an icon kind and day or night
(is_day from Open-Meteo), and its cache key is new so old readings without them are not reused. Not ported: his wider glass bar with a peek of the grid, the picture caption and the
Live TV row, which need layout changes across the home screen."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def P(p): return os.path.join(APP, p)
def sub(p, pairs):
    s = open(P(p)).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:90])
        s = s.replace(a, b, 1)
    open(P(p), 'w').write(s)

# ---------------------------------------------------------------- weather: an icon kind and day / night
sub('src/lib/weather.ts', [
 ("export interface Weather {\n	temp: number;\n	label: string;\n	place: string;\n}\n",
  "export type WeatherKind = 'clear' | 'partly' | 'cloudy' | 'fog' | 'rain' | 'snow' | 'storm';\n\n"
  "export interface Weather {\n	temp: number;\n	label: string;\n	place: string;\n	kind: WeatherKind;\n	/** false between sunset and sunrise at the place: the clear and partly icons show a moon */\n	day: boolean;\n}\n"),
 ("launcher-weather-v2-", "launcher-weather-v3-"),
 ("&current=temperature_2m,weather_code&timezone=auto", "&current=temperature_2m,weather_code,is_day&timezone=auto"),
 ("Promise<{current?: {temperature_2m?: number; weather_code?: number}}>", "Promise<{current?: {temperature_2m?: number; weather_code?: number; is_day?: number}}>"),
 ("label: describe(c.weather_code || 0), place: p.place};", "label: describe(c.weather_code || 0), place: p.place, kind: kindOf(c.weather_code || 0), day: c.is_day !== 0};"),
 ("export function readWeather (", r"""function kindOf (code: number): WeatherKind {
	if (code === 0) return 'clear';
	if (code <= 2) return 'partly';
	if (code === 45 || code === 48) return 'fog';
	if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'snow';
	if (code >= 95) return 'storm';
	if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return 'rain';
	return 'cloudy';
}

export function readWeather ("""),
])

# ---------------------------------------------------------------- the new top-left block
open(P('src/components/StatusNew.tsx'), 'w').write(r"""// The top-left block of the new home screen look, ported from samrenfrew/lumen-webos (MIT): a large clock, then the date and the weather with an icon under it.
import {useEffect, useState} from 'preact/hooks';
import {Clock} from './Clock';
import {langLocale, t as tr} from '../lib/i18n';
import type {Weather, WeatherKind} from '../lib/weather';

const dateText = () => (() => { try { return new Date().toLocaleDateString(langLocale(), {weekday: 'long', month: 'long', day: 'numeric'}).replace(',', ''); } catch { return new Date().toDateString(); } })();

/** Line icons in the same style as Glyph: 24-unit box, stroked, no fill. */
const SUN = 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4';
const MOON = 'M19.5 14.5A7.5 7.5 0 0 1 9.5 4.5a7.5 7.5 0 1 0 10 10z';
const CLOUD = 'M7 18.5h10.5a3.5 3.5 0 0 0 .4-7 5.5 5.5 0 0 0-10.6-1.2A4.2 4.2 0 0 0 7 18.5z';
const ICONS: Record<WeatherKind, string> = {
	clear: SUN,
	partly: 'M9 3v1.4M3.6 8.8H5M4.9 4.7l1 1M13.1 4.7l-1 1M6.4 10.4a3 3 0 0 1 5.3-3.2M9 19h8.5a3 3 0 0 0 .3-6 4.6 4.6 0 0 0-8.9-1A3.5 3.5 0 0 0 9 19z',
	cloudy: CLOUD,
	fog: 'M4 8.5h16M3 12.5h18M5 16.5h14M8 20.5h8',
	rain: 'M7 14.5h10.5a3.5 3.5 0 0 0 .4-7 5.5 5.5 0 0 0-10.6-1.2A4.2 4.2 0 0 0 7 14.5zM8.5 17.5l-1 2.5M12.5 17.5l-1 2.5M16.5 17.5l-1 2.5',
	snow: 'M7 14.5h10.5a3.5 3.5 0 0 0 .4-7 5.5 5.5 0 0 0-10.6-1.2A4.2 4.2 0 0 0 7 14.5zM8 18.5h.01M12 18.5h.01M16 18.5h.01M10 21h.01M14 21h.01',
	storm: 'M7 14.5h10.5a3.5 3.5 0 0 0 .4-7 5.5 5.5 0 0 0-10.6-1.2A4.2 4.2 0 0 0 7 14.5zM12.5 15.5l-2 3.5h3l-2 3.5'
};
const PARTLY_NIGHT = 'M11.2 4.6a3.8 3.8 0 0 0 4.4 5.2 3.8 3.8 0 0 1-5.3 1.9M9 19h8.5a3 3 0 0 0 .3-6 4.6 4.6 0 0 0-8.9-1A3.5 3.5 0 0 0 9 19z';

function WeatherIcon ({weather}: {weather: Weather}) {
	const d = weather.day ? ICONS[weather.kind] : weather.kind === 'clear' ? MOON : weather.kind === 'partly' ? PARTLY_NIGHT : ICONS[weather.kind];
	return <svg class="status__icon" viewBox="0 0 24 24" aria-hidden="true"><path d={d} /></svg>;
}

/** Top-left, plain with no glass: a large clock, then the date and the weather on one line under it. Not focusable. */
export function StatusNew ({weather, showPeriod}: {weather?: Weather | null; showPeriod?: boolean}) {
	const [, bump] = useState(0);
	const date = dateText();

	useEffect(() => {
		const tick = () => { if (!document.hidden) bump((n) => n + 1); };
		const id = window.setInterval(tick, 30000);
		document.addEventListener('visibilitychange', tick);
		return () => { window.clearInterval(id); document.removeEventListener('visibilitychange', tick); };
	}, []);

	return (
		<div class="pill status">
			<Clock showPeriod={showPeriod} />
			<div class="status__row">
				<span class="status__date">{date}</span>
				{weather && (
					<span class="status__weather">
						<WeatherIcon weather={weather} />
						<span>{weather.temp}°</span>
						{weather.label && <span class="status__cond">{tr(weather.label)}</span>}
					</span>
				)}
			</div>
		</div>
	);
}
""")

sub('src/screens/Home.tsx', [
 ("import {Status} from '../components/Status';\n", "import {Status} from '../components/Status';\nimport {StatusNew} from '../components/StatusNew';\nimport type {Weather} from '../lib/weather';\n"),
 ("	weatherText?: string;\n", "	weatherText?: string;\n	/** the weather with its icon, for the new home screen look */\n	weatherInfo?: Weather | null;\n	/** Settings > Options > New home screen look */\n	newHome?: boolean;\n"),
 ("folders, weatherText, dockHide}: Props)", "folders, weatherText, weatherInfo, newHome, dockHide}: Props)"),
 ("			<Status weatherText={weatherText} showPeriod={showPeriod} />\n",
  "			{newHome ? <StatusNew weather={weatherInfo} showPeriod={showPeriod} /> : <Status weatherText={weatherText} showPeriod={showPeriod} />}\n"),
])

sub('src/app.tsx', [
 ("import {readWeather} from './lib/weather';", "import {readWeather, type Weather} from './lib/weather';"),
 ("	const [weatherText, setWeatherText] = useState('');\n", "	const [weatherText, setWeatherText] = useState('');\n	const [weatherInfo, setWeatherInfo] = useState<Weather | null>(null);\n"),
 ("		if (!config.showWeather) { setWeatherText(''); return; }", "		if (!config.showWeather) { setWeatherText(''); setWeatherInfo(null); return; }"),
 (".then((w) => setWeatherText(`${w.place ? w.place + ' \\u00b7 ' : ''}${w.temp}\\u00b0 ${tr(w.label)}`.trim()))\n			.catch(() => setWeatherText(''));",
  ".then((w) => { setWeatherText(`${w.place ? w.place + ' \\u00b7 ' : ''}${w.temp}\\u00b0 ${tr(w.label)}`.trim()); setWeatherInfo(w); })\n			.catch(() => { setWeatherText(''); setWeatherInfo(null); });"),
 ("weatherText={weatherText}", "weatherText={weatherText} weatherInfo={weatherInfo} newHome={config.newHome}"),
])

# ---------------------------------------------------------------- the look (everything scoped to html.homenew)
s = open(P('src/theme/global.css')).read()
s += r"""
/* ---------- New home screen look (Settings > Options), from samrenfrew/lumen-webos (MIT) ---------- */
/* ---------- big clock: the time large and light, the date and weather on one line under it ---------- */
html.homenew .screen > .pill.status { flex-direction: column; align-items: flex-start; padding: 0; }
html.homenew .screen > .pill.status .clock { margin: 0 0 0 -6px; }
html.homenew .screen > .pill.status .clock__time { font-size: 120px; font-weight: 650; line-height: 0.95; letter-spacing: -0.02em; }
html.homenew .screen > .pill.status .clock__colon { opacity: 1; top: -0.06em; }
html.homenew .screen > .pill.status .clock__period { font-size: 32px; font-weight: 400; margin-left: 10px; align-self: flex-end; margin-bottom: 14px; }
/* the home screen's clock is smaller than the screensaver's, which keeps the full size */
html.homenew .screen:not(.ambient__status) > .pill.status .clock__time { font-size: 80px; }
html.homenew .screen:not(.ambient__status) > .pill.status .clock__period { font-size: 21px; margin-left: 7px; margin-bottom: 9px; }
/* the date and weather take proportional figures, so 11° is not spaced like a clock */
html.homenew .status__row { font-variant-numeric: normal; }
/* the home screen puts the weather under the date; the screensaver keeps them on one line */
html.homenew .screen:not(.ambient__status) > .pill.status .status__row { flex-direction: column; align-items: flex-start; }
html.homenew .screen:not(.ambient__status) > .pill.status .status__weather { margin: 4px 0 0 -2px; }
html.homenew .screen:not(.ambient__status) > .pill.status .status__date, html.homenew .screen:not(.ambient__status) > .pill.status .status__weather { font-size: 26px; }
html.homenew .screen:not(.ambient__status) > .pill.status .status__icon { width: 32px; height: 32px; }
html.homenew .status__row { display: flex; flex-direction: row; align-items: center; margin-top: 10px; }
html.homenew .status__row .status__date { font-size: 30px; font-weight: 500; margin-right: 0; }
html.homenew .status__weather { display: flex; flex-direction: row; align-items: center; margin: 0 0 0 26px; font-size: 30px; font-weight: 500; opacity: 1; animation: status-in 600ms ease-out; }
html.homenew .screen > .pill.status .status__icon { width: 36px; height: 36px; margin: 0 10px 0 0; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
html.homenew .status__cond { margin-left: 12px; font-weight: 500; }

/* ---------- tiles lit from above, as on tvOS: a soft shadow under each tile, and over its artwork a light from the top left (20 degrees
   off vertical) fading out by the middle, a bright top rim, a fainter left one and a faint dark bottom edge. All static (no animation), drawn once per tile. Kept light on purpose (one soft shadow, one rim, no blur wider than 30px): every tile is painted again when the stack is lifted for the slide to the second row. */
html.homenew .rows .tile__box { box-shadow: 0 6px 12px rgba(0, 0, 0, 0.26); }
html.homenew .rows .tile__box::before {
	content: ''; position: absolute; left: 0; top: 0; right: 0; bottom: 0; z-index: 1; border-radius: inherit; pointer-events: none;
	background: linear-gradient(160deg, rgba(255, 255, 255, 0.20) 0%, rgba(255, 255, 255, 0.06) 30%, rgba(255, 255, 255, 0) 55%, rgba(0, 0, 0, 0.08) 100%);
	box-shadow: inset 0 2px 1px -1px rgba(255, 255, 255, 0.55);
}
html.homenew .rows .row .tile--focused .tile__box { box-shadow: 0 20px 30px rgba(0, 0, 0, 0.42); }
html.homenew .rows > .row:first-child .tile--focused .tile__box { box-shadow: 0 10px 18px rgba(0, 0, 0, 0.32); }
html.homenew .rows .tile--focused .tile__box::after { z-index: 2; }

/* a stronger focus: the grid's tiles grow 1.175x, the dock's 1.1x (it keeps clear of the dock bar's edge) */
html.homenew .rows { --motion-focus-scale: 1.175; }
html.homenew .rows > .row:first-child { --motion-focus-scale: 1.1; }

"""
open(P('src/theme/global.css'), 'w').write(s)
