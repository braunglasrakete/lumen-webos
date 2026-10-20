#!/usr/bin/env python3
"""Fifty-fourth patch layer: a smoother slide to the second row. The stack (.rows) used to slide by animating `top`, which re-lays-out the whole dock stack on every frame,
and every glass shape draws its picture with `background-attachment: fixed`, which is repainted on every frame as well. That is too much for the TV.
Now the stack jumps to its final `top` at once and a short TRANSFORM animation (FLIP: from the old place to the new one) slides it there. A transform animation is
done by the compositor alone: no layout, no repaint per frame. (While it runs the glass pictures move with the shapes instead of staying put; they are blurred and the
animation lasts 240 ms, and everything lines up again at the end.) Not used over a video wallpaper: that mode already slides with a transform."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
def P(p): return os.path.join(APP, p)

h = open(P('src/screens/Home.tsx')).read()
a = "	const rowIndex = clamp(n.rowIndex, 0, Math.max(0, rows.length - 1));\n	const overlay ="
assert h.count(a) == 1
h = h.replace(a, """	const rowIndex = clamp(n.rowIndex, 0, Math.max(0, rows.length - 1));
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
@keyframes rows-slide-down { from { transform: translateY(300px); } to { transform: translateY(0); } }
@keyframes rows-slide-up { from { transform: translateY(-300px); } to { transform: translateY(0); } }
"""
open(P('src/theme/global.css'), 'w').write(s)
