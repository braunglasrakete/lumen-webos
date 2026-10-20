#!/usr/bin/env python3
"""Fifty-fourth patch layer: a smoother slide to the second row. The stack (.rows) used to slide by animating `top`, which re-lays-out the whole dock stack on every frame,
and every glass shape draws its picture with `background-attachment: fixed`, which is repainted on every frame as well. That is too much for the TV.
Now the stack jumps to its final `top` at once and a short TRANSFORM animation (FLIP: from the old place to the new one) slides it there. A transform animation is
done by the compositor alone: no layout, no repaint per frame. (While it runs the glass pictures move with the shapes instead of staying put; they are blurred and the
animation lasts 240 ms, and everything lines up again at the end.) Not used over a video wallpaper: that mode already slides with a transform.
A transformed ancestor also turns `background-attachment: fixed` into a plain local background, so the glass bars showed the wrong part of the (blue-ish) wallpaper for a split
second. While the slide runs, each row gets the offset of its glass bar (--gx/--gy, measured once from the final layout) and the bar's picture is positioned with it."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def P(p): return os.path.join(APP, p)

h = open(P('src/screens/Home.tsx')).read()
imp = "import {useCallback, useEffect, useRef, useState} from 'preact/hooks';"
assert h.count(imp) == 1
h = h.replace(imp, "import {useCallback, useEffect, useLayoutEffect, useRef, useState} from 'preact/hooks';", 1)
a = "	const rowIndex = clamp(n.rowIndex, 0, Math.max(0, rows.length - 1));\n	const overlay ="
assert h.count(a) == 1
h = h.replace(a, r"""	const rowIndex = clamp(n.rowIndex, 0, Math.max(0, rows.length - 1));
	// going between the dock and the second row: remember the direction for the length of the slide (it styles the stack, see global.css)
	const lowerNow = n.zone === 'rows' && rowIndex >= 1;
	const slide = useRef({lower: false, dir: '', until: 0});
	if (slide.current.lower !== lowerNow) {
		slide.current.lower = lowerNow;
		slide.current.dir = lowerNow ? 'down' : 'up';
		slide.current.until = Date.now() + 320;
		window.setTimeout(render, 340);
	}
	const sliding = Date.now() < slide.current.until ? ` screen--slide-${slide.current.dir}` : '';
	// the glass bar of each row keeps its picture lined up with the screen during the slide: tell the CSS where the bar will be when the slide is over
	useLayoutEffect(() => {
		if (!sliding) return;
		const stack = document.querySelector('.rows') as HTMLElement | null;
		if (!stack) return;
		let x = 0, y = 0, p: HTMLElement | null = stack;
		while (p) { x += p.offsetLeft; y += p.offsetTop; p = p.offsetParent as HTMLElement | null; }
		Array.prototype.forEach.call(stack.children, (r: HTMLElement) => {
			const bar = getComputedStyle(r, '::before');
			// the second row's bar is `left: calc(50% - 538px)`, which the browser may hand back unresolved: work the percentage out from the row's width
			const px = (v: string, of: number) => { const m = /^calc\(\s*([\d.]+)%\s*([+-])\s*([\d.]+)px\s*\)$/.exec(v); return m ? of * parseFloat(m[1]) / 100 + (m[2] === '-' ? -1 : 1) * parseFloat(m[3]) : (parseFloat(v) || 0); };
			r.style.setProperty('--gx', (x + r.offsetLeft + px(bar.left, r.offsetWidth)) + 'px');
			r.style.setProperty('--gy', (y + r.offsetTop + px(bar.top, r.offsetHeight)) + 'px');
		});
	}, [sliding]);
	const overlay =""", 1)
b = "${n.dockHidden ? ' screen--dockhidden' : ''}`}>"
assert h.count(b) == 1
h = h.replace(b, "${n.dockHidden ? ' screen--dockhidden' : ''}${sliding}`}>", 1)
open(P('src/screens/Home.tsx'), 'w').write(h)

s = open(P('src/theme/global.css')).read()
s += """
/* dock <-> second row: `top` jumps, a transform animation does the sliding (compositor only; no layout or repaint per frame) */
html:not(.wp-video) .rows { transition: transform 260ms cubic-bezier(0.2, 0.7, 0.2, 1), opacity 220ms ease; }
html:not(.wp-video) .screen--slide-down .rows:not(.rows--hidden) { animation: rows-slide-down 240ms cubic-bezier(0.2, 0.7, 0.2, 1); will-change: transform; }
html:not(.wp-video) .screen--slide-up .rows:not(.rows--hidden) { animation: rows-slide-up 240ms cubic-bezier(0.2, 0.7, 0.2, 1); will-change: transform; }
html:not(.wp-video) .screen--slide-down .row:not(.row--dock)::before, html:not(.wp-video) .screen--slide-up .row:not(.row--dock)::before { background-attachment: scroll, scroll; background-position: 0 0, calc(-1 * var(--gx, 0px)) calc(-1 * var(--gy, 0px)); }
@keyframes rows-slide-down { from { transform: translateY(300px); } to { transform: translateY(0); } }
@keyframes rows-slide-up { from { transform: translateY(-300px); } to { transform: translateY(0); } }
"""
open(P('src/theme/global.css'), 'w').write(s)
