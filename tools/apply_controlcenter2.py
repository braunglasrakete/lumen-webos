#!/usr/bin/env python3
"""Fifty-seventh patch layer: the Control Center of samrenfrew/lumen-webos (MIT), as a second Control Center you can switch to in Settings > Options ("New Control Center").
tvOS 26 style: a grid of glass controls, Sound / Picture / Theme / Clock open a list that grows out of the tile, a backlight bar and Eye Comfort. Everything new lives in
components/ControlCenterNew.tsx, lib/tvcontrolsPlus.ts and CSS with its own class names (cn__*, panel--cn), so the original Control Center is untouched and is still shown when the
switch is off. The switch itself (config.newControlCenter) comes from apply_portswitch.py. Backlight and Eye Comfort are TV settings changed as root through the Homebrew Channel,
with fixed commands and values checked against a list (see lib/tvcontrolsPlus.ts)."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def P(p): return os.path.join(APP, p)
def sub(p, pairs):
    s = open(P(p)).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, s.count(a), a[:90])
        s = s.replace(a, b, 1)
    open(P(p), 'w').write(s)

# ---------------------------------------------------------------- three more icons (sun, eye, image)
sub('src/components/Glyph.tsx', [
 ("| 'power' | 'restart';", "| 'power' | 'restart' | 'sun' | 'eye' | 'image';"),
 ("				: name === 'screensaver'\n				? <path d=\"M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7z\" />\n",
  "				: name === 'screensaver'\n				? <path d=\"M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7z\" />\n"
  "				: name === 'sun'\n				? <path d=\"M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4\" />\n"
  "				: name === 'eye'\n				? <path d=\"M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z\" />\n"
  "				: name === 'image'\n				? <path d=\"M3.5 5h17v14h-17zM3.5 15.5l5-5 4 4 3-3 5 5M15.5 9.3a.8.8 0 1 0 0-.1\" />\n"),
])

# ---------------------------------------------------------------- backlight and Eye Comfort (root, through the Homebrew Channel)
open(P('src/lib/tvcontrolsPlus.ts'), 'w').write(r"""// Backlight and Eye Comfort for the new Control Center. Both are TV settings, changed as root through the Homebrew Channel's exec service. Nothing else builds a shell
// command here: each setting is listed with the values it may take, and a value outside the list never reaches the shell. Off the TV the values are kept in memory.

import {LUNA} from '../config/constants';
import {isWebOS, lunaCall} from './luna';
import {readControls, type Controls} from './tvcontrols';

export interface ControlsPlus extends Controls {
	/** 0-100, for the picture mode in use (the TV keeps one per mode) */
	backlight: number;
	eyeComfort: boolean;
}

const SETTINGS: Record<string, {category: string; values: string[]}> = {
	backlight: {category: 'picture', values: Array.from({length: 101}, (_, i) => String(i))},
	eyeComfortMode: {category: 'picture', values: ['on', 'off']}
};

const mock = {backlight: 100, eyeComfort: false};

const run = (command: string) => lunaCall<{stdoutString?: string}>(LUNA.homebrewExec, {command}, 6000).then((r) => r.stdoutString || '');

/** The value of one listed setting, or '' when the TV has none. */
function getSetting (key: string): Promise<string> {
	const s = SETTINGS[key];
	if (!s) return Promise.reject(new Error('unknown setting ' + key));
	const params = JSON.stringify({category: s.category, keys: [key]});
	return run(`luna-send -n 1 luna://com.webos.settingsservice/getSystemSettings '${params}'`).then((text) => {
		const m = JSON.parse(text) as {settings?: Record<string, unknown>};
		const v = m.settings && m.settings[key];
		return v === undefined || v === null ? '' : String(v);
	});
}

/** Rejects for a setting or value that is not listed, and when the TV answers returnValue:false. */
function setSetting (key: string, value: string): Promise<void> {
	const s = SETTINGS[key];
	if (!s || s.values.indexOf(value) === -1) return Promise.reject(new Error(`refused: ${key}=${value}`));
	const params = JSON.stringify({category: s.category, settings: {[key]: value}});
	return run(`luna-send -n 1 luna://com.webos.settingsservice/setSystemSettings '${params}'`).then((text) => {
		if (text.indexOf('"returnValue":false') !== -1) throw new Error(`the TV refused ${key}=${value}`);
	});
}

/** The backlight of the picture mode in use, or null when it can't be read. Read again after a picture mode change: each mode has its own. */
export function readBacklight (): Promise<number | null> {
	if (!isWebOS()) return Promise.resolve(mock.backlight);
	return getSetting('backlight').then((v) => {
		const n = Number(v);
		return v !== '' && Number.isInteger(n) && n >= 0 && n <= 100 ? n : null;
	}).catch(() => null);
}

/** 0-100, whole numbers only. */
export function setBacklight (level: number): Promise<void> {
	mock.backlight = level;
	if (!isWebOS()) return Promise.resolve();
	if (!Number.isInteger(level) || level < 0 || level > 100) return Promise.reject(new Error('bad backlight level'));
	return setSetting('backlight', String(level));
}

export function setEyeComfort (on: boolean): Promise<void> {
	mock.eyeComfort = on;
	if (!isWebOS()) return Promise.resolve();
	return setSetting('eyeComfortMode', on ? 'on' : 'off');
}

/** Everything the original Control Center reads, plus the backlight and Eye Comfort. */
export function readControlsPlus (): Promise<ControlsPlus> {
	return readControls().then((base) => {
		const out: ControlsPlus = {...base, backlight: mock.backlight, eyeComfort: mock.eyeComfort};
		if (!isWebOS()) return out;
		const backlight = readBacklight().then((v) => { if (v !== null) out.backlight = v; });
		const eye = getSetting('eyeComfortMode').then((v) => { out.eyeComfort = v === 'on'; }).catch(() => undefined);
		return Promise.all([backlight, eye]).then(() => out);
	});
}
""")

# ---------------------------------------------------------------- the component
open(P('src/components/ControlCenterNew.tsx'), 'w').write(r"""// Control Center, ported from samrenfrew/lumen-webos (MIT; see THIRD_PARTY_NOTICES.md). tvOS 26 style: a grid of glass controls, pop-up lists that grow out of their tile,
// backlight bar and Eye Comfort. Classes are cn__* / panel--cn so it never clashes with the original Control Center (components/ControlCenter.tsx).
import {t as tr} from '../lib/i18n';
import {useCallback, useEffect, useLayoutEffect, useRef, useState} from 'preact/hooks';
import {Glyph, type GlyphName} from './Glyph';
import {useKeys, clamp, type NavKey} from '../hooks/useKeys';
import {PICTURE_LABEL, PICTURE_MODES, SOUND_LABEL, SOUND_MODES, setSoundMode, restartTv, screenOff, setPictureMode} from '../lib/tvcontrols';
import {readBacklight, readControlsPlus, setBacklight, setEyeComfort, type ControlsPlus} from '../lib/tvcontrolsPlus';

export type CenterAction = 'lg-home' | 'art';

interface Props {
	onClose: () => void;
	onError: (text: string) => void;
	/** buttons that leave the launcher or open another screen */
	onAction: (action: CenterAction) => void;
	darkMode: string;
	clockFormat: string;
	onDarkMode: (mode: string) => void;
	onClockFormat: (format: string) => void;
}

type CellId = 'sound' | 'picture' | 'art' | 'home' | 'screenoff' | 'restart' | 'backlight' | 'eye' | 'dark' | 'clock';
/** the tiles that open a list of choices in place of the grid, as tvOS does for Sleep Timer */
type MenuCell = 'sound' | 'picture' | 'dark' | 'clock';
const MENU_CELLS: CellId[] = ['sound', 'picture', 'dark', 'clock'];
const MENU_GLYPH: Record<MenuCell, GlyphName> = {sound: 'speaker', picture: 'picture', dark: 'screensaver', clock: 'timer'};

/** The layout, like the tvOS Control Center: a grid four squares wide, where a tile spans two squares and the backlight bar three. */
const GRID: {id: CellId; span: number}[][] = [
	[{id: 'sound', span: 2}, {id: 'picture', span: 2}],
	[{id: 'dark', span: 2}, {id: 'clock', span: 2}],
	[{id: 'home', span: 1}, {id: 'art', span: 1}, {id: 'screenoff', span: 1}, {id: 'restart', span: 1}],
	[{id: 'backlight', span: 3}, {id: 'eye', span: 1}]
];

/** The cell in a row that covers grid column x (0 to 3), and the column it starts at. */
const cellAt = (row: number, x: number) => {
	let start = 0;
	for (const c of GRID[row]) { if (x < start + c.span) return {cell: c.id, start}; start += c.span; }
	return {cell: GRID[row][GRID[row].length - 1].id, start: 4 - GRID[row][GRID[row].length - 1].span};
};
const startOf = (row: number, i: number) => GRID[row].slice(0, i).reduce((n, c) => n + c.span, 0);

/** Each backlight change is a root command (a luna-send process on the TV), so a run of presses sends only the last level, this long after. */
const BACKLIGHT_DELAY_MS = 300;

/** Opening a list, timed off the tvOS 26 Control Center frame by frame (30 fps): the tile grows into a glass pill the list's size while its text
 *  fades and the rest of the grid shrinks toward it and fades; the list fades in inside the pill, then the pill's glass clears. tvOS also
 *  darkens the pill on the way, which looked jarring here, so this keeps the tile's glass. Closing has no pill, since a big pill shrinking
 *  is heavy on the TV: the list shrinks back toward the tile as it fades out, and the grid fades back in, growing back from GRID_SHRINK. */
const OPEN_MS = 330;
const CLOSE_MS = 300;
/** keyframes per animation; enough that the pill's corners stay round between them */
const STEPS = 20;
/** how far the rest of the grid shrinks toward the tile */
const GRID_SHRINK = 0.15;
/** the space round the list inside the pill, so the options never touch its edge */
const PILL_PAD = 18;
/** how soon in the open the pill takes the list's shape (its height grows faster than its width), as a share of OPEN_MS */
const SHAPE_BY = 0.35;
/** how far past the tile the pill shrinks when closing, before it settles */
/** how far the pill has grown at each video frame (every 33 ms) of tvOS's open, measured off the frames */
const GROW = [0, 0.12, 0.35, 0.6, 0.8, 0.9, 0.94, 0.97, 0.985, 0.995, 1];
/** where the pill is: its offset and scale from the tile's own box, and its corner radius on screen */
interface End {tx: number; ty: number; sx: number; sy: number; r: number}
/** 0 before a, 1 after b, a straight line between */
const ramp = (t: number, a: number, b: number) => Math.max(0, Math.min(1, (t - a) / (b - a)));
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
/** a value read off evenly spaced samples, t from 0 to 1 */
const track = (points: number[], t: number) => {
	const at = Math.max(0, Math.min(1, t)) * (points.length - 1);
	const i = Math.min(points.length - 2, Math.floor(at));
	return points[i] + (points[i + 1] - points[i]) * (at - i);
};
/** a list choice's height and the gap between choices, as .cn__opt in global.css */
const OPT_H = 72;
const OPT_GAP = 12;
const listHeight = (count: number) => count * OPT_H + (count - 1) * OPT_GAP;

type Phase = 'grid' | 'opening' | 'list' | 'closing';
interface Morph {kind: 'open' | 'close'; cell: MenuCell; geo: {x: number; y: number; w: number; h: number; fw: number; fh: number; tile: End; list: End}}

/** Grows a top-bar panel in from the button that opened it (the top-bar pill with data-top={key}): a short scale and fade, as tvOS does. */
export function growFrom (panel: HTMLElement | null, key: string): void {
	const button = document.querySelector(`.topbar [data-top="${key}"]`);
	if (!panel || !button || !panel.animate || document.documentElement.classList.contains('reduce-motion')) return;
	const b = button.getBoundingClientRect();
	const p = panel.getBoundingClientRect();
	panel.style.transformOrigin = `${b.left + b.width / 2 - p.left}px ${b.top + b.height / 2 - p.top}px`;
	const opts = {duration: 260, easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)'};
	panel.animate([{transform: 'scale(0.6)'}, {transform: 'none'}], opts);
	// each control fades on its own: fading the panel would cut their live blur off from the wallpaper
	Array.from(panel.querySelectorAll<HTMLElement>('.cn__mod, .cn__caption')).forEach((el) => el.animate([{opacity: 0}, {opacity: 1}], opts));
}

/** Control Center (opened from the round button top right): sound, picture mode, appearance, clock, LG Home, Art mode (your photos), screen off,
 *  restart, backlight and Eye Comfort. Volume is left to the remote's own buttons. Arrows move between controls, OK presses one, Left/Right on
 *  the backlight bar change it, Back closes. */
export function ControlCenterNew ({onClose, onError, onAction, darkMode, clockFormat, onDarkMode, onClockFormat}: Props) {
	const outer = useRef({darkMode, clockFormat, onDarkMode, onClockFormat});
	outer.current = {darkMode, clockFormat, onDarkMode, onClockFormat};
	const [values, setValues] = useState<ControlsPlus>({volume: 0, muted: false, picture: 'normal', sound: 'standard', sleepMinutes: 0, screensaver: 10, backlight: 100, eyeComfort: false});
	// x is the grid column the remote is on, kept when moving up and down, so Down from Restart lands on Eye Comfort
	const [pos, setPos] = useState({row: 0, x: 0});
	const [confirm, setConfirm] = useState(false);
	// the open list: which tile it belongs to and the focused choice
	const [menu, setMenu] = useState<{cell: MenuCell; idx: number} | null>(null);
	const [phase, setPhase] = useState<Phase>('grid');
	// the pill that stands in for the tile while the list opens or closes; the tile itself is hidden meanwhile
	const [morph, setMorph] = useState<Morph | null>(null);
	const state = useRef({values, pos, confirm, menu, phase});
	state.current = {values, pos, confirm, menu, phase};
	const tiles = useRef<Partial<Record<CellId, HTMLElement | null>>>({});
	const panel = useRef<HTMLDivElement>(null);
	const timers = useRef<number[]>([]);
	useEffect(() => () => timers.current.forEach((id) => window.clearTimeout(id)), []);
	const still = () => document.documentElement.classList.contains('reduce-motion');
	const after = (ms: number, fn: () => void) => { timers.current.push(window.setTimeout(fn, still() ? 0 : ms)); };

	useLayoutEffect(() => growFrom(panel.current, 'controls'), []);

	// read the TV's values a moment after the panel is on screen, so opening it is never held up by the TV answering
	useEffect(() => {
		const id = window.setTimeout(() => { readControlsPlus().then(setValues); }, 250);
		return () => window.clearTimeout(id);
	}, []);

	const fail = (what: string) => () => onError(`Couldn't change ${what}`);
	const patch = (p: Partial<ControlsPlus>) => setValues((v) => ({...v, ...p}));

	// the backlight level waiting to be sent; sent at once if the panel closes first
	const pendingBacklight = useRef<{id: number; level: number} | null>(null);
	const sendBacklight = () => {
		const p = pendingBacklight.current;
		if (!p) return;
		window.clearTimeout(p.id);
		pendingBacklight.current = null;
		setBacklight(p.level).catch(() => onError("Couldn't change the backlight"));
	};
	useEffect(() => sendBacklight, []);
	const backlight = (next: number) => {
		const level = clamp(next, 0, 100);
		patch({backlight: level});
		if (pendingBacklight.current) window.clearTimeout(pendingBacklight.current.id);
		pendingBacklight.current = {id: window.setTimeout(sendBacklight, BACKLIGHT_DELAY_MS), level};
	};

	const press = (cell: CellId) => {
		if (state.current.phase !== 'grid') return;
		const v = state.current.values;
		if (cell === 'eye') {
			const on = !v.eyeComfort;
			patch({eyeComfort: on}); setEyeComfort(on).catch(() => { patch({eyeComfort: !on}); onError("Couldn't change Eye Comfort"); });
		}
		else if (MENU_CELLS.indexOf(cell) >= 0) openMenu(cell as MenuCell);
		else if (cell === 'art') onAction('art');
		else if (cell === 'home') onAction('lg-home');
		else if (cell === 'screenoff') { onClose(); screenOff().catch(() => onError("Couldn't turn the screen off (it needs the Homebrew Channel)")); }
		else if (cell === 'restart') {
			if (!state.current.confirm) { setConfirm(true); return; }
			onClose(); restartTv().catch(() => onError("Couldn't restart the TV (it needs the Homebrew Channel)"));
		}
	};

	const options = (cell: MenuCell): {value: string; label: string}[] =>
		cell === 'sound' ? SOUND_MODES.map((m) => ({value: m, label: SOUND_LABEL[m] || m}))
			: cell === 'picture' ? PICTURE_MODES.map((m) => ({value: m, label: PICTURE_LABEL[m] || m}))
				: cell === 'dark' ? [{value: 'off', label: tr('Light')}, {value: 'on', label: tr('Dark')}, {value: 'auto', label: tr('Auto')}]
					: [{value: 'auto', label: tr('Auto')}, {value: '12h', label: tr('12-hour')}, {value: '24h', label: tr('24-hour')}];
	const chosen = (cell: MenuCell): string => {
		const v = state.current.values;
		const o = outer.current;
		return cell === 'sound' ? v.sound : cell === 'picture' ? v.picture : cell === 'dark' ? o.darkMode : o.clockFormat;
	};

	const apply = (cell: MenuCell, value: string) => {
		if (value === chosen(cell)) return;
		const v = state.current.values;
		if (cell === 'sound') {
			const before = v.sound;
			patch({sound: value}); setSoundMode(value).catch(() => { patch({sound: before}); onError("This TV didn't accept that sound mode"); });
		}
		else if (cell === 'picture') {
			// each picture mode has its own backlight, so show the new mode's
			patch({picture: value}); setPictureMode(value).then(readBacklight).then((b) => { if (b !== null) patch({backlight: b}); }).catch(fail('the picture mode'));
		}
		else if (cell === 'dark') outer.current.onDarkMode(value);
		else outer.current.onClockFormat(value);
	};

	/** Where the copy sits (the tile's own box, so its corners match) and the transforms for its two ends: the focused tile (scaled 1.1 about
	 *  its centre) and the whole list. */
	/** The pill's geometry for a tile and a list of count choices. The pill is laid out in the tile's own box, so its ends match the tile. */
	const geometry = (cell: MenuCell, count: number) => {
		const el = tiles.current[cell];
		const w = el ? el.offsetWidth : 1;
		const h = el ? el.offsetHeight : 1;
		const x = el ? el.offsetLeft : 0;
		const y = el ? el.offsetTop : 0;
		const full = panel.current ? panel.current.offsetWidth : w;
		const grown = (s: number): End => ({tx: ((1 - s) * w) / 2, ty: ((1 - s) * h) / 2, sx: s, sy: s, r: (h / 2) * s});
		return {
			x, y, w, h, fw: full, fh: listHeight(count),
			tile: grown(1.1), // focused tiles are drawn at 1.1
			// the pill ends PILL_PAD bigger than the list all round, with an option's corners
			list: {tx: -x - PILL_PAD, ty: -y - PILL_PAD, sx: (full + 2 * PILL_PAD) / w, sy: (listHeight(count) + 2 * PILL_PAD) / h, r: OPT_H / 2}
		};
	};

	/** The pill partway through opening. Its size follows tvOS's measured growth, but its height grows faster than its width, so it has the
	 *  list's shape by SHAPE_BY and the list fills it from early on. Each edge moves in step with its own growth, so the pill stays between the
	 *  tile and the list. */
	const opening = (g: Morph['geo'], t: number): End => {
		const k = track(GROW, t);
		const l0 = g.x + g.tile.tx, t0 = g.y + g.tile.ty, w0 = g.w * g.tile.sx, h0 = g.h * g.tile.sy;
		const l1 = g.x + g.list.tx, t1 = g.y + g.list.ty, w1 = g.w * g.list.sx, h1 = g.h * g.list.sy;
		const h = h0 + (h1 - h0) * k;
		const shape = w0 / h0 + (w1 / h1 - w0 / h0) * easeOut(ramp(t, 0, SHAPE_BY));
		const w = Math.max(Math.min(w0, w1), Math.min(Math.max(w0, w1), h * shape));
		const px = w1 === w0 ? k : (w - w0) / (w1 - w0);
		const left = l0 + (l1 - l0) * px;
		const top = t0 + (t1 - t0) * k;
		return {tx: left - g.x, ty: top - g.y, sx: w / g.w, sy: h / g.h, r: g.tile.r + (g.list.r - g.tile.r) * k};
	};

	/** Every layer's keyframes for one open or close, sampled from the same timeline. */
	const timeline = (m: Morph) => {
		const g = m.geo;
		const pill: Keyframe[] = [], glass: Keyframe[] = [], rim: Keyframe[] = [], text: Keyframe[] = [], list: Keyframe[] = [], listFade: Keyframe[] = [], grid: Keyframe[] = [], gridFade: Keyframe[] = [];
		for (let i = 0; i <= STEPS; i++) {
			const t = i / STEPS;
			const open = m.kind === 'open';
			// closing has no pill: the list shrinks back toward the tile as it fades, and the grid, tile included, fades back in
			const at = open ? opening(g, t) : opening(g, 1 - easeOut(ramp(t, 0, 0.7)));
			// the corners ease from the tile's round ends to an option's radius as the pill grows
			const r = at.r;
			pill.push({transform: `translate(${at.tx}px, ${at.ty}px) scale(${at.sx}, ${at.sy})`, borderRadius: `${r / at.sx}px / ${r / at.sy}px`});
			// the tile's text follows the pill's centre at its own size
			const dx = at.tx + (g.w * at.sx) / 2 - g.w / 2;
			const dy = at.ty + (g.h * at.sy) / 2 - g.h / 2;
			text.push({transform: `translate(${dx}px, ${dy}px) scale(1.1)`, opacity: 1 - ramp(t, 0.06, 0.27)});
			// opening: the glass is gone by 167 ms, while the list is still fading in and growing
			glass.push({opacity: 1 - ramp(t, 0.2, 0.5)});
			// the edge highlight and shadow grow with the pill's scale, so they go before it grows
			rim.push({opacity: 1 - ramp(t, 0, 0.1)});
			// the list sits inside the pill at the pill's size, as tvOS's does: scaled evenly to fit inside its padding, and centred
			const pw = g.w * at.sx;
			const ph = g.h * at.sy;
			const fit = Math.max(0, Math.min(1, (pw - 2 * PILL_PAD) / g.fw, (ph - 2 * PILL_PAD) / g.fh));
			const lx = g.x + at.tx + (pw - fit * g.fw) / 2;
			const ly = g.y + at.ty + (ph - fit * g.fh) / 2;
			// opacity goes on each piece of glass, not the list or grid: a fading parent would cut its live blur off from the wallpaper
			list.push({transform: `translate(${lx}px, ${ly}px) scale(${fit})`});
			listFade.push({opacity: open ? easeOut(ramp(t, 0.08, 0.8)) : 1 - ramp(t, 0.1, 0.7)});
			grid.push({transform: open ? `scale(${1 - GRID_SHRINK * easeOut(ramp(t, 0, 0.4))})` : `scale(${1 - GRID_SHRINK + GRID_SHRINK * easeOut(ramp(t, 0.2, 1))})`});
			gridFade.push({opacity: open ? 1 - ramp(t, 0.08, 0.4) : ramp(t, 0.25, 0.85)});
		}
		return {pill, glass, rim, text, list, listFade, grid, gridFade};
	};

	const pillEl = useRef<HTMLDivElement>(null);
	const glassEl = useRef<HTMLDivElement>(null);
	const rimEl = useRef<HTMLDivElement>(null);
	const textEl = useRef<HTMLDivElement>(null);
	const listEl = useRef<HTMLDivElement>(null);
	const gridEl = useRef<HTMLDivElement>(null);
	const running = useRef<Animation[]>([]);
	// start every layer in the same frame the pill is drawn, before the browser paints it
	useLayoutEffect(() => {
		if (!morph) return;
		running.current.forEach((a) => a.cancel());
		const k = timeline(morph);
		const ms = still() ? 0 : morph.kind === 'open' ? OPEN_MS : CLOSE_MS;
		const opts: KeyframeAnimationOptions = {duration: ms, easing: 'linear', fill: 'both'};
		const each = (root: HTMLElement | null, sel: string, frames: Keyframe[]) => (root ? Array.from(root.querySelectorAll<HTMLElement>(sel)) : []).map((el): [HTMLElement, Keyframe[]] => [el, frames]);
		const pairs: [HTMLElement | null, Keyframe[]][] = [[pillEl.current, k.pill], [glassEl.current, k.glass], [rimEl.current, k.rim], [textEl.current, k.text], [listEl.current, k.list], [gridEl.current, k.grid],
			...each(listEl.current, '.cn__opt', k.listFade), ...each(gridEl.current, '.cn__mod:not(.cn__mod--gone), .cn__caption', k.gridFade)];
		running.current = pairs.filter(([el]) => el && el.animate).map(([el, frames]) => (el as HTMLElement).animate(frames, opts));
		const grid = gridEl.current;
		if (grid) grid.style.transformOrigin = `${morph.geo.x + morph.geo.w / 2}px ${morph.geo.y + morph.geo.h / 2}px`;
		after(ms + 20, () => {
			if (morph.kind === 'open') { setPhase('list'); setMorph(null); }
			else { setMorph(null); setMenu(null); setPhase('grid'); }
			// the classes now hold each layer's end state
			running.current.forEach((a) => a.cancel());
			running.current = [];
		});
	}, [morph]);

	const openMenu = (cell: MenuCell) => {
		if (state.current.phase !== 'grid') return;
		const list = options(cell);
		const idx = Math.max(0, list.map((o) => o.value).indexOf(chosen(cell)));
		setConfirm(false); setMenu({cell, idx}); setPhase('opening');
		setMorph({kind: 'open', cell, geo: geometry(cell, list.length)});
	};

	/** Back to the grid, after applying the choice if one was picked. */
	const closeMenu = (pick: boolean, idx?: number) => {
		const {menu: m, phase: ph} = state.current;
		if (!m || ph !== 'list') return;
		if (pick) apply(m.cell, options(m.cell)[idx === undefined ? m.idx : idx].value);
		setPhase('closing');
		setMorph({kind: 'close', cell: m.cell, geo: geometry(m.cell, options(m.cell).length)});
	};

	const move = (row: number, x: number) => { setPos({row, x}); setConfirm(false); };

	const handleKey = useCallback((key: NavKey): boolean => {
		const {pos: p, values: v, menu: m, phase: ph} = state.current;
		if (ph === 'opening' || ph === 'closing') return true;
		if (m) {
			if (key === 'back') closeMenu(false);
			else if (key === 'enter') closeMenu(true);
			else if (key === 'up' || key === 'down') setMenu({cell: m.cell, idx: clamp(m.idx + (key === 'up' ? -1 : 1), 0, options(m.cell).length - 1)});
			return true;
		}
		const {cell, start} = cellAt(p.row, p.x);
		if (key === 'back') { onClose(); return true; }
		if (key === 'enter') { press(cell); return true; }
		if (cell === 'backlight' && (key === 'left' || key === 'right')) { backlight(v.backlight + (key === 'left' ? -5 : 5)); return true; }
		if (key === 'left' || key === 'right') {
			const i = GRID[p.row].map((c) => c.id).indexOf(cell);
			const j = clamp(i + (key === 'left' ? -1 : 1), 0, GRID[p.row].length - 1);
			if (j !== i) move(p.row, startOf(p.row, j));
		}
		else if (key === 'up' && p.row === 0) onClose();   // Up past the top row closes, back to the top buttons
		else if (key === 'up' || key === 'down') move(clamp(p.row + (key === 'up' ? -1 : 1), 0, GRID.length - 1), start);
		return true;
	}, []);
	useKeys(handleKey, true);

	const current = cellAt(pos.row, pos.x).cell;
	const focus = (cell: CellId) => () => {
		for (let r = 0; r < GRID.length; r++) { const i = GRID[r].map((c) => c.id).indexOf(cell); if (i >= 0) { setPos({row: r, x: startOf(r, i)}); return; } }
	};

	/** What a list tile shows: icon, name, current choice, and whether it shows as on. */
	const info = (cell: MenuCell): {glyph: GlyphName; title: string; sub: string; on: boolean} =>
		cell === 'sound' ? {glyph: 'speaker', title: tr('Sound'), sub: SOUND_LABEL[values.sound] || values.sound, on: false}
			: cell === 'picture' ? {glyph: 'picture', title: tr('Picture'), sub: PICTURE_LABEL[values.picture] || values.picture, on: false}
				: cell === 'dark' ? {glyph: 'screensaver', title: tr('Theme'), sub: darkMode === 'on' ? tr('Dark') : darkMode === 'auto' ? tr('Auto') : tr('Light'), on: darkMode === 'on'}
					: {glyph: 'timer', title: tr('Clock'), sub: clockFormat === '12h' ? tr('12-hour') : clockFormat === '24h' ? tr('24-hour') : tr('Auto'), on: clockFormat !== 'auto'};
	const tileInside = (i: {glyph: GlyphName; title: string; sub: string}) => [
		<div key="i" class="cn__icon"><Glyph name={i.glyph} /></div>,
		<div key="t" class="cn__text"><div class="cn__name">{i.title}</div><div class="cn__sub">{i.sub}</div></div>
	];
	const wide = (cell: MenuCell) => {
		const i = info(cell);
		return (
			<div
				key={cell}
				ref={(el) => { tiles.current[cell] = el; }}
				class={`cn__mod cn__tile${current === cell ? ' cn__mod--focused' : ''}${morph && morph.kind === 'open' && morph.cell === cell ? ' cn__mod--gone' : ''}${i.on ? ' cn__mod--on' : ''}`}
				onMouseEnter={focus(cell)}
				onClick={() => press(cell)}
			>
				{tileInside(i)}
			</div>
		);
	};
	// icon-only circles, as on tvOS; the focused one is named in the caption under the panel
	const CIRCLES: {cell: CellId; glyph: GlyphName; label: string}[] = [
		{cell: 'home', glyph: 'house', label: 'LG Home'}, {cell: 'art', glyph: 'image', label: 'Art mode'},
		{cell: 'screenoff', glyph: 'power', label: 'Screen off'}, {cell: 'restart', glyph: 'restart', label: 'Restart'},
		{cell: 'eye', glyph: 'eye', label: 'Eye Comfort'}
	];
	const circle = (cell: CellId, on = false) => {
		const c = CIRCLES.filter((q) => q.cell === cell)[0];
		return <div key={cell} class={`cn__mod cn__circle${current === cell ? ' cn__mod--focused' : ''}${on ? ' cn__mod--on' : ''}`} onMouseEnter={focus(cell)} onClick={() => press(cell)}><Glyph name={c.glyph} /></div>;
	};
	const named = CIRCLES.filter((q) => q.cell === current)[0];
	const caption = !named || menu ? '' : named.cell === 'restart' && confirm ? tr('Press OK again') : named.cell === 'eye' ? `${tr(named.label)}: ${tr(values.eyeComfort ? 'On' : 'Off')}` : tr(named.label);
	// the backlight label, drawn twice: light over the glass, dark over the filled part, so it reads at any level
	const sliderText = <div class="cn__slidertext"><Glyph name="sun" /><span>{tr('Backlight')}</span><span class="cn__num">{values.backlight}</span></div>;

	return (
		<>
			<div class="panel-backdrop panel-backdrop--clear" onClick={onClose} />
			<div class="panel panel--cn" ref={panel}>
				<div ref={gridEl} class={`cn__grid${phase === 'grid' || phase === 'closing' ? '' : ' cn__grid--leaving'}`}>
				<div class="cn__row">
					{wide('sound')}
					{wide('picture')}
				</div>
				<div class="cn__row">
					{wide('dark')}
					{wide('clock')}
				</div>
				<div class="cn__row">{circle('home')}{circle('art')}{circle('screenoff')}{circle('restart')}</div>
				<div class="cn__row">
					<div
						class={`cn__mod cn__slider${current === 'backlight' ? ' cn__mod--focused' : ''}`}
						onMouseEnter={focus('backlight')}
						onClick={(e: MouseEvent) => { const box = (e.currentTarget as HTMLElement).getBoundingClientRect(); backlight(Math.round(((e.clientX - box.left) / box.width) * 100)); }}
					>
						{sliderText}
						<div class="cn__fill" style={`width:${values.backlight}%`}>{sliderText}</div>
					</div>
					{circle('eye', values.eyeComfort)}
				</div>
				<div class="cn__caption">{caption}</div>
				</div>
				{morph && morph.kind === 'open' && (() => {
					const box = `left:${morph.geo.x}px;top:${morph.geo.y}px;width:${morph.geo.w}px;height:${morph.geo.h}px`;
					const i = info(morph.cell);
					return [
						<div key="pill" ref={pillEl} class="cn__morph" style={box}>
							<div ref={glassEl} class="cn__mod cn__mod--focused cn__morph__glass" />
							<div ref={rimEl} class="cn__morph__rim" />
						</div>,
						<div key="text" ref={textEl} class={`cn__tile cn__morph__text${i.on ? ' cn__mod--on' : ''}`} style={box}>{tileInside(i)}</div>
					];
				})()}
				{menu && (
					<div ref={listEl} class={`cn__list${phase === 'closing' || phase === 'grid' ? '' : ' cn__list--shown'}`}>
						{options(menu.cell).map((o, i) => (
							<div
								key={o.value}
								class={`cn__mod cn__tile cn__opt${menu.idx === i ? ' cn__mod--focused' : ''}${o.value === chosen(menu.cell) ? ' cn__mod--on' : ''}`}
								onMouseEnter={() => setMenu({cell: menu.cell, idx: i})}
								onClick={() => closeMenu(true, i)}
							>
								<div class="cn__icon"><Glyph name={MENU_GLYPH[menu.cell]} /></div>
								<div class="cn__text"><div class="cn__name">{o.label}</div></div>
							</div>
						))}
					</div>
				)}
			</div>
		</>
	);
}
""")

# ---------------------------------------------------------------- the glass, own class names
s = open(P('src/theme/global.css')).read()
s += r"""
/* ---------- New Control Center (components/ControlCenterNew.tsx), from samrenfrew/lumen-webos (MIT): no panel, each control its own piece of glass ---------- */
.panel-backdrop--clear { background: none; }
/* :root lifts this above the light panel rules */
html:root body .panel.panel--cn {
	--cn-u: 90px; --cn-gap: 18px; --cn-on: rgb(64, 196, 255);
	background: none !important; box-shadow: none !important; -webkit-backdrop-filter: none !important; backdrop-filter: none !important;
	width: calc(4 * var(--cn-u) + 3 * var(--cn-gap)); padding: 0; top: 196px; border-radius: 0;
}
.cn__row { display: flex; flex-direction: row; margin-bottom: var(--cn-gap); }
.cn__row > * + * { margin-left: var(--cn-gap); }
.cn__mod {
	position: relative; flex: 0 0 auto; height: var(--cn-u); border-radius: calc(var(--cn-u) / 2); box-sizing: border-box; color: #fff;
	background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.26) 0%, rgba(255, 255, 255, 0.07) 42%, rgba(255, 255, 255, 0.16) 100%), var(--wp-blur, var(--glass-fallback));
	background-size: auto, 1920px 1080px; background-attachment: scroll, fixed; background-position: 0 0, var(--dev-left, 0px) var(--dev-top, 0px); background-repeat: no-repeat;
	background-color: rgba(30, 36, 50, 0.30);
	box-shadow: inset 2px 2px 1.5px -1px rgba(255, 255, 255, 0.9), inset -2px -2px 1.5px -1px rgba(255, 255, 255, 0.42), inset 0 0 14px rgba(255, 255, 255, 0.10), 0 8px 18px rgba(0, 0, 0, 0.25);
	text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35);
	transition: transform var(--motion-focus-ms) ease-out;
}
.cn__mod--focused { transform: scale(1.1); background-image: linear-gradient(145deg, rgba(255, 255, 255, 0.50), rgba(255, 255, 255, 0.20) 55%, rgba(255, 255, 255, 0.34)), var(--wp-blur, var(--glass-fallback)); }
.cn__mod svg { position: static; width: 44px; height: 44px; fill: none; stroke: rgba(255, 255, 255, 0.9); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.cn__mod--on svg { stroke: var(--cn-on); }

.cn__tile { width: calc(2 * var(--cn-u) + var(--cn-gap)); display: flex; flex-direction: row; align-items: center; padding: 0 14px 0 20px; }
.cn__icon { flex: 0 0 auto; display: flex; margin-right: 14px; }
.cn__icon svg { width: 40px; height: 40px; }
.cn__text { min-width: 0; }
.cn__name { font-size: 21px; font-weight: 600; white-space: nowrap; line-height: 1.2; }
.cn__sub { font-size: 21px; opacity: 0.7; white-space: nowrap; line-height: 1.2; }

.cn__circle { width: var(--cn-u); display: flex; align-items: center; justify-content: center; }

.cn__slider { width: calc(3 * var(--cn-u) + 2 * var(--cn-gap)); overflow: hidden; }
/* the fill is a second sheet of frost on the slider's glass: a brighter tint and its own rim, no second blur (the slider's glass already blurs) */
.cn__fill {
	position: absolute; left: 0; top: 0; bottom: 0; overflow: hidden;
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.34) 0%, rgba(255, 255, 255, 0.14) 45%, rgba(255, 255, 255, 0.24) 100%);
	box-shadow: inset 2px 2px 1.5px -1px rgba(255, 255, 255, 0.95), inset -2px -2px 1.5px -1px rgba(255, 255, 255, 0.5), inset 0 0 16px rgba(255, 255, 255, 0.16), 4px 0 14px rgba(0, 0, 0, 0.18);
}
.cn__mod--focused .cn__fill { background: linear-gradient(135deg, rgba(255, 255, 255, 0.52) 0%, rgba(255, 255, 255, 0.26) 45%, rgba(255, 255, 255, 0.40) 100%); }
.cn__slidertext { position: absolute; left: 0; top: 0; bottom: 0; width: calc(3 * var(--cn-u) + 2 * var(--cn-gap)); display: flex; flex-direction: row; align-items: center; padding: 0 26px 0 22px; box-sizing: border-box; font-size: 21px; font-weight: 600; white-space: nowrap; }
.cn__slidertext svg { width: 34px; height: 34px; margin-right: 12px; }
.cn__num { margin-left: auto; font-weight: 500; }

/* A tile's list of choices (Sound, Picture, Theme, Clock), as tvOS's Sleep Timer. ControlCenter.tsx animates every layer with keyframes; these
   classes hold the states between. The pill stands in for the tile: its focused glass, with the tile's text on top. */
/* the fade sits on each control, never the grid or list: a parent below full opacity cuts its children's live blur off from the wallpaper */
.cn__grid--leaving { pointer-events: none; }
.cn__grid--leaving .cn__mod, .cn__grid--leaving .cn__caption, .cn__mod--gone { opacity: 0; }
.cn__list { position: absolute; left: 0; top: 0; width: 100%; transform-origin: 0 0; }
.cn__list:not(.cn__list--shown) { pointer-events: none; }
.cn__list:not(.cn__list--shown) .cn__opt { opacity: 0; }
.panel--cn .cn__morph { position: absolute; transform-origin: 0 0; pointer-events: none; }
.panel--cn .cn__morph > * { position: absolute; left: 0; top: 0; width: 100%; height: 100%; border-radius: inherit; transform: none; transition: none; }
/* the pill's fill without its edge highlight and shadow, which would swell as it scales; .cn__morph__rim draws those, on its own timing */
html body .panel--cn .cn__morph__glass { box-shadow: none !important; }
.cn__morph__rim { box-shadow: inset 2px 2px 1.5px -1px rgba(255, 255, 255, 0.9), inset -2px -2px 1.5px -1px rgba(255, 255, 255, 0.42), inset 0 0 14px rgba(255, 255, 255, 0.10), 0 8px 18px rgba(0, 0, 0, 0.25); }
html.light .cn__morph__rim { box-shadow: 0 8px 18px rgba(20, 24, 40, 0.30); }
.panel--cn .cn__morph__text { position: absolute; pointer-events: none; color: #fff; text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35); }
.cn__morph__text svg { position: static; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.cn__morph__text:not(.cn__mod--on) svg { stroke: rgba(255, 255, 255, 0.9); }
html.light .cn__morph__text { text-shadow: none; }
/* height and gap match OPT_H and OPT_GAP in ControlCenter.tsx */
.panel--cn .cn__opt { width: 100%; height: 72px; border-radius: 36px; margin-bottom: 12px; }
.panel--cn .cn__opt.cn__mod--focused { transform: scale(1.05); }
.cn__opt .cn__icon svg { width: 34px; height: 34px; }

.cn__caption { height: 30px; line-height: 30px; text-align: center; font-size: 20px; font-weight: 600; color: #fff; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6); }

/* light look: the top buttons' light glass, and focus turns dark as theirs does */
html.light .cn__mod { color: #14151b; text-shadow: none; background-color: rgb(120, 128, 148); background-blend-mode: normal, screen; box-shadow: inset 0 0 0 1.5px rgba(255, 255, 255, 0.8), 0 4px 12px rgba(20, 24, 40, 0.12); }
html.light.wp-video .cn__mod { background-color: transparent; background-blend-mode: normal; }
html.light .cn__mod svg { stroke: rgba(20, 22, 32, 0.72); }
html.light .cn__mod--on svg { stroke: rgb(0, 122, 255); }
html.light body .panel--cn .cn__mod--focused:not(.cn__slider) { background: #14151b !important; color: #fff; box-shadow: 0 8px 18px rgba(20, 24, 40, 0.30); }
html.light .cn__mod--focused:not(.cn__slider) svg { stroke: #fff; }
html.light .cn__mod--focused.cn__mod--on svg { stroke: var(--cn-on); }
html.light .cn__fill { background: rgba(20, 21, 27, 0.72); }
html.light .cn__fill .cn__slidertext { color: #fff; }
html.light .cn__fill .cn__slidertext svg { stroke: #fff; }
html.light .cn__mod--focused .cn__fill { background: #14151b; }
html.light .cn__mod--focused .cn__fill .cn__slidertext { color: #fff; }
html.light .cn__mod--focused .cn__fill .cn__slidertext svg { stroke: #fff; }
"""
open(P('src/theme/global.css'), 'w').write(s)

# ---------------------------------------------------------------- shown instead of the original when Settings > Options > New Control Center is on
OLD = """			{controls && <ControlCenter
				darkMode={config.darkMode}
				clockFormat={config.clockFormat}
				onDarkMode={() => updateConfig({...configRef.current, darkMode: nextDark(configRef.current.darkMode)})}
				onClockFormat={() => { const modes = ['auto', '12h', '24h']; const c = configRef.current; updateConfig({...c, clockFormat: modes[(modes.indexOf(c.clockFormat) + 1) % modes.length]}); }}
				onClose={() => setControls(false)}
				onError={(text) => showToast(text, 'error')}
				onAction={(a: CenterAction) => { setControls(false); onActivate('menu', a === 'settings' ? {key: MISC.settings, label: 'Settings'} : a === 'lg-home' ? {key: MISC.lgHome, label: 'LG Home'} : a === 'art' ? {key: 'com.ammar027.lumen.gallery', label: 'Frame'} : {key: 'screensaver', label: 'Screensaver'}); }}
			/>}
"""
NEW = """			{controls && (config.newControlCenter ? <ControlCenterNew {...centerProps} /> : <ControlCenter {...centerProps} />)}
"""
PROPS = """	// what both Control Centers are given (the original cycles a choice when it is called with none, the new one is told which choice was picked)
	const centerProps = {
		darkMode: config.darkMode,
		clockFormat: config.clockFormat,
		onDarkMode: (mode?: string) => updateConfig({...configRef.current, darkMode: mode || nextDark(configRef.current.darkMode)}),
		onClockFormat: (format?: string) => { const modes = ['auto', '12h', '24h']; const c = configRef.current; updateConfig({...c, clockFormat: format || modes[(modes.indexOf(c.clockFormat) + 1) % modes.length]}); },
		onClose: () => setControls(false),
		onError: (text: string) => showToast(text, 'error'),
		onAction: (a: CenterAction) => { setControls(false); onActivate('menu', a === 'settings' ? {key: MISC.settings, label: 'Settings'} : a === 'lg-home' ? {key: MISC.lgHome, label: 'LG Home'} : a === 'art' ? {key: 'com.ammar027.lumen.gallery', label: 'Frame'} : {key: 'screensaver', label: 'Screensaver'}); }
	};

"""
RET = "	return (\n		<>\n			{/* Home stays mounted under Settings so it keeps its focus position. */}"
sub('src/app.tsx', [
 ("import {ControlCenter, type CenterAction} from './components/ControlCenter';\n", "import {ControlCenter, type CenterAction} from './components/ControlCenter';\nimport {ControlCenterNew} from './components/ControlCenterNew';\n"),
 (OLD, NEW),
 (RET, PROPS + RET),
 ("topItems={TOP_ITEMS}", "topItems={config.newControlCenter ? [{key: MISC.settings, label: 'Settings', glyph: 'gear'}, ...TOP_ITEMS] : TOP_ITEMS}"),
])
