#!/usr/bin/env python3
"""Fifty-eighth patch layer: live blur glass, ported from samrenfrew/lumen-webos (MIT). When Settings > Options > "Live blur glass" is on (html class `liveblur`, set by apply_portswitch.py),
the glass shapes (the dock bar of the second row, the top buttons, the panels and the new Control Center's controls) blur what is behind them live (backdrop-filter) instead of showing the
pre-blurred copy of the wallpaper. A very light blur with extra colour and a dark tint, closer to tvOS 26 Liquid Glass; the rims do the rest. Heavier for the TV's graphics chip than the
pre-blurred copy, which is why it is a switch. The full-screen backdrops stay as they are. His optional Liquid glass dock (an SVG displacement) is not part of this."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
s = open(os.path.join(APP, 'src/theme/global.css')).read()
s += r"""
html.liveblur, html.liveblur * { --wp-blur: linear-gradient(transparent, transparent) !important; }
/* closer to tvOS 26 Liquid Glass: a very light blur so the picture reads through, extra colour and a dark tint; the rims do the rest */
html.liveblur { --live-glass: blur(2px) saturate(1.5) brightness(1.1); --live-tint: rgba(0, 0, 0, 0.3); }
html.liveblur .row:not(.row--dock)::before, html.liveblur .topcap, html.liveblur .topbar > .pill, html.liveblur .panel {
	-webkit-backdrop-filter: var(--live-glass);
	backdrop-filter: var(--live-glass);
	background-attachment: scroll !important;
	background-color: var(--live-tint) !important;
	background-blend-mode: normal !important;
	opacity: 1;
}
html.liveblur.light .row:not(.row--dock)::before, html.liveblur.light .topcap, html.liveblur.light .topbar > .pill, html.liveblur.light .panel {
	background-color: rgba(255, 255, 255, 0.34) !important;
}

/* dark live glass: the sheen and rim lights at about half strength, so the glass reads dark like Liquid Glass. On the wide glass bar the
   sheen stops 200px in from each end, or it would spread across hundreds of pixels and look like a focused button. */
html.liveblur:not(.light) .topbar > .pill:not(.pill--focused):not(.pill--open), html.liveblur:not(.light) .topcap:not(.topcap--focused):not(.topcap--open),
html.liveblur:not(.light) .cn__mod:not(.cn__mod--focused), html.liveblur:not(.light) .panel:not(.panel--cn) {
	background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.13) 0%, rgba(255, 255, 255, 0.03) 42%, rgba(255, 255, 255, 0.08) 100%) !important;
	box-shadow: inset 2px 2px 1.5px -1px rgba(255, 255, 255, 0.55), inset -2px -2px 1.5px -1px rgba(255, 255, 255, 0.25), inset 0 0 14px rgba(255, 255, 255, 0.05), 0 8px 18px rgba(0, 0, 0, 0.25) !important;
}
html.liveblur:not(.light) .topbar > .pill.pill--focused, html.liveblur:not(.light) .topbar > .pill.pill--open, html.liveblur:not(.light) .topcap--focused,
html.liveblur:not(.light) .topcap--open, html.liveblur:not(.light) .cn__mod--focused {
	background-image: linear-gradient(145deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.12) 55%, rgba(255, 255, 255, 0.22)) !important;
}
html.liveblur:not(.light) .cn__fill {
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0.08) 45%, rgba(255, 255, 255, 0.15) 100%) !important;
	box-shadow: inset 2px 2px 1.5px -1px rgba(255, 255, 255, 0.6), inset -2px -2px 1.5px -1px rgba(255, 255, 255, 0.3), inset 0 0 16px rgba(255, 255, 255, 0.1), 4px 0 14px rgba(0, 0, 0, 0.18) !important;
}
html.liveblur:not(.light) .cn__mod--focused .cn__fill { background: linear-gradient(135deg, rgba(255, 255, 255, 0.36) 0%, rgba(255, 255, 255, 0.16) 45%, rgba(255, 255, 255, 0.26) 100%) !important; }
html.liveblur:not(.light) .row:not(.row--dock)::before {
	background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.13) 0, rgba(255, 255, 255, 0.03) 200px, rgba(255, 255, 255, 0.03) calc(100% - 200px), rgba(255, 255, 255, 0.08) 100%) !important;
	box-shadow: inset 2px 2px 1.5px -1px rgba(255, 255, 255, 0.55), inset -2px -2px 1.5px -1px rgba(255, 255, 255, 0.25), inset 0 0 14px rgba(255, 255, 255, 0.05), 0 20px 44px rgba(0, 0, 0, 0.28) !important;
}
html.liveblur:not(.light) .row:not(.row--dock)::after { opacity: 0.6; }
"""
open(os.path.join(APP, 'src/theme/global.css'), 'w').write(s)
