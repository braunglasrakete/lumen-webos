#!/usr/bin/env python3
"""Sixtieth patch layer: in dark mode the unselected top buttons (Settings, Inputs, Control Center and the clock button) can never turn light. Their glass shows the pre-blurred wallpaper
copy through a white sheen, so on a bright picture they came out nearly solid white. Now a dark veil lies between the sheen and the picture (only in dark mode, not over the video
wallpaper, which has its own dark copy); the focused and open buttons keep their bright glass."""
import os
APP = os.path.expanduser('~/Developer/webos-launcher-tvos/app')
p = os.path.join(APP, 'src/theme/global.css')
s = open(p).read()
s += r"""
/* ---------- dark mode: unselected top buttons stay dark glass on any wallpaper ---------- */
html.dark:not(.wp-video) .topbar > .pill:not(.pill--focused):not(.pill--open), html.dark:not(.wp-video) .topcap:not(.topcap--focused):not(.topcap--open) {
	background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.20) 0%, rgba(255, 255, 255, 0.05) 42%, rgba(255, 255, 255, 0.12) 100%), linear-gradient(rgba(12, 14, 24, 0.52), rgba(12, 14, 24, 0.52)), var(--wp-blur, var(--glass-fallback));
	background-size: auto, auto, 1920px 1080px;
	background-attachment: scroll, scroll, fixed;
	background-position: 0 0, 0 0, var(--dev-left, 0px) var(--dev-top, 0px);
}
"""
open(p, 'w').write(s)
