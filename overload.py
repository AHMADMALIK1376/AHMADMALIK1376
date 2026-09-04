# -*- coding: utf-8 -*-
"""
A server being pushed past what it can do, cut open so you can see where.

Every number on this panel is solved, not invented. The system is an M/M/c/K
queue: c database connections in the pool, K worker threads in the server. A
request holds a thread for the whole time it is in the system — while it waits
for a connection as much as while it is querying — so when all K threads are
held there is nothing left to accept with and the server sheds.

The load ramps across the loop and the state equations are solved at every step,
so what the panel shows at any moment is the real steady state for that arrival
rate.

What it is built to show, and what the arithmetic actually says:

  - THE POOL IS THE CEILING. Ten connections at 25 ms each is 400 requests a
    second, and no amount of load makes it 401. Throughput climbs, reaches 400,
    and then simply stops.
  - THE SERVER LOOKS BUSY DOING NOTHING. Past the knee, 46 of 48 threads are
    occupied while only 10 are actually querying. The other 36 are blocked on
    the pool. A thread count is not a measure of work being done, and this is
    why adding threads to a server in this state makes it worse: more threads
    means more requests accepted to wait, not more requests served.
  - LATENCY DOES NOT RISE IN A LINE. It is flat at 25 ms all the way to half
    capacity, still only 40 ms at ninety percent, and then it goes vertical.
    That knee is the whole reason queueing theory is worth knowing.
  - SHEDDING IS NOT FAILURE. Once the threads are gone the server rejects work
    immediately rather than accepting it and timing out later. Throughput stays
    at 400 rather than collapsing.

Colour carries the argument: a thread actually running a query is blue, a thread
blocked waiting for a connection is coral. The server filling with coral while
ten blue slots do all the work is the point of the whole picture.

House style: solid fills, no gradients, no filters.
"""
import math

AEGEAN, CORAL = "#0077C8", "#F88379"
BROWN, TEAMIST, CRIMSON = "#D4A373", "#AAC832", "#D41F26"
SKY = "#F2EDE6"
GRID = "#E6DBCA"
CARD = "#FBF7F0"
INK = "#2E2A24"
INK_2 = "#5E5349"
MUTED = "#7D7266"
FAINT = "#A2988A"
RULE = "#D9D0C1"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W, H = 1240, 536
DUR = 30.0
RAMP_FROM, RAMP_TO = 5.0, 88.0      # the rest of the loop holds the overloaded state
STEPS = 48

CONNS = 10                          # database connections in the pool
THREADS = 48                        # worker threads in the server
SERVICE = 0.025                     # seconds of database time per request
MU = 1.0 / SERVICE
CAPACITY = CONNS * MU               # 400 requests a second, and no more
LAM_MIN, LAM_MAX = 40.0, 700.0

LX0, LX1 = 44.0, 790.0              # the cutaway
RX0, RX1 = 820.0, 1196.0            # the instruments


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _txt(x, y, s, size, fill, weight="700", anchor="start", ls="0", cls=None):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%s" '
            'fill="%s" text-anchor="%s" letter-spacing="%s"%s>%s</text>'
            % (x, y, MONO, size, weight, fill, anchor, ls,
               (' class="%s"' % cls) if cls else "", _esc(s)))


def _rr(x, y, w, h, r, fill, extra=""):
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s"%s/>'
            % (x, y, w, h, r, fill, (" " + extra) if extra else ""))


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#%02X%02X%02X" % tuple(
        max(0, min(255, int(round(ra[i] + (rb[i] - ra[i]) * t)))) for i in range(3))


def _kf(name, stops):
    return ("@keyframes " + name + "{"
            + "".join("%.3f" % p + "%{" + body + "}" for p, body in stops) + "}")


def solve(lam):
    """Steady state of M/M/c/K, worked out exactly rather than simulated.

    A request occupies a thread from arrival to departure, so the number in the
    system is the number of threads held; when that reaches K the server has
    nothing to accept with and the arrival is rejected.
    """
    a = lam / MU
    terms = []
    for n in range(THREADS + 1):
        if n < CONNS:
            terms.append(a ** n / math.factorial(n))
        else:
            terms.append(a ** n / (math.factorial(CONNS) * CONNS ** (n - CONNS)))
    tot = sum(terms)
    p = [t / tot for t in terms]
    block = p[THREADS]
    lam_eff = lam * (1.0 - block)
    in_system = sum(n * p[n] for n in range(THREADS + 1))
    queued = sum((n - CONNS) * p[n] for n in range(CONNS + 1, THREADS + 1))
    busy_conns = sum(min(n, CONNS) * p[n] for n in range(THREADS + 1))
    wait = queued / lam_eff if lam_eff else 0.0
    return {"lam": lam, "threads": in_system, "conns": busy_conns, "queue": queued,
            "latency": (wait + SERVICE) * 1000.0, "shed": lam * block, "tput": lam_eff}


def _pct(step):
    """When in the loop a given step of the ramp is reached."""
    return RAMP_FROM + (step / float(STEPS - 1)) * (RAMP_TO - RAMP_FROM)


def build(path_out="assets/overload.svg"):
    states = [solve(LAM_MIN + (LAM_MAX - LAM_MIN) * s / float(STEPS - 1))
              for s in range(STEPS)]
    lat_max = max(s["latency"] for s in states)

    css = ["@keyframes blip{0%,100%{opacity:1}50%{opacity:.25}}",
           ".blip{animation:blip 1.6s steps(1,end) infinite}"]

    def latch(name, step):
        """Turn something on at a step of the ramp and leave it on."""
        at = _pct(step)
        css.append(_kf(name, [(0.0, "opacity:0"), (max(0.0, at - 0.01), "opacity:0"),
                              (at, "opacity:1"), (100.0, "opacity:1")]))
        css.append("." + name + "{animation:" + name + " " + "%.1f" % DUR
                   + "s linear infinite}")

    def only(name, step):
        """Show a readout for exactly its own step of the ramp."""
        a, b = _pct(step), _pct(step + 1) if step + 1 < STEPS else 100.0
        # the ramp starts at RAMP_FROM, so without this the first step holds the
        # readouts blank for the opening seconds of every loop
        if step == 0:
            stops = [(0.0, "opacity:1")]
        else:
            stops = [(0.0, "opacity:0"), (max(0.0, a - 0.001), "opacity:0"), (a, "opacity:1")]
        if step + 1 < STEPS:
            stops += [(max(a, b - 0.001), "opacity:1"), (b, "opacity:0"), (100.0, "opacity:0")]
        else:
            stops += [(100.0, "opacity:1")]
        css.append(_kf(name, stops))
        css.append("." + name + "{animation:" + name + " " + "%.1f" % DUR
                   + "s linear infinite}")

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="A server under rising load, cut open: %d worker threads fill '
           'up while only %d database connections do the work, throughput stops at %d requests '
           'a second, latency goes vertical past the knee, and the server begins shedding">'
           % (W, H, W, H, THREADS, CONNS, int(CAPACITY)),
           "<title>A Server Under Load</title>",
           '<defs><pattern id="og" width="26" height="26" patternUnits="userSpaceOnUse">'
           '<circle cx="1.5" cy="1.5" r="1" fill="%s"/></pattern>__STYLE__</defs>' % GRID,
           '<rect width="%d" height="%d" fill="%s"/>' % (W, H, SKY),
           '<rect width="%d" height="%d" fill="url(#og)"/>' % (W, H)]

    out.append(_txt(48, 44, "A SERVER UNDER LOAD", 14, INK, "800", "start", "3.4"))
    out.append(_txt(W - 66, 44, "SOLVED, NOT MIMED", 12.5, FAINT, "600", "end", "2.2"))
    out.append('<circle cx="%d" cy="40" r="5" fill="%s" class="blip"/>' % (W - 48, TEAMIST))
    out.append('<path d="M48,58 H%d" stroke="%s" stroke-width="1.4" fill="none"/>' % (W - 48, RULE))
    out.append(_txt(48, 80, "%d WORKER THREADS · %d DATABASE CONNECTIONS · WATCH WHICH ONE "
                            "RUNS OUT FIRST" % (THREADS, CONNS), 10.5, MUTED, "600", "start", "1.5"))

    # ══ the cutaway ══════════════════════════════════════════════════════
    # ── arrivals ─────────────────────────────────────────────────────────
    out.append(_rr(LX0, 100, LX1 - LX0, 40, 5, CARD, 'stroke="%s" stroke-width="1.2"' % RULE))
    out.append(_txt(LX0 + 14, 125, "ARRIVING", 9, MUTED, "800", "start", "1.8"))
    bar_x, bar_w = LX0 + 96, LX1 - LX0 - 210
    out.append(_rr(bar_x, 112, bar_w, 16, 3, _mix(CARD, INK, 0.06)))
    css.append(_kf("rate", [(0.0, "transform:scaleX(%.4f)" % (LAM_MIN / LAM_MAX)),
                            (RAMP_FROM, "transform:scaleX(%.4f)" % (LAM_MIN / LAM_MAX)),
                            (RAMP_TO, "transform:scaleX(1)"), (100.0, "transform:scaleX(1)")]))
    css.append(".rate{transform-box:fill-box;transform-origin:left center;"
               "animation:rate " + "%.1f" % DUR + "s linear infinite}")
    out.append(_rr(bar_x, 112, bar_w, 16, 3, _mix(AEGEAN, CARD, 0.35), 'class="rate"'))
    cap_x = bar_x + bar_w * (CAPACITY / LAM_MAX)
    out.append('<path d="M%.1f,106 V134" stroke="%s" stroke-width="1.4" '
               'stroke-dasharray="3 3"/>' % (cap_x, CRIMSON))
    out.append(_txt(cap_x + 5, 111, "CAPACITY %d/s" % int(CAPACITY), 7.4, CRIMSON,
                    "800", "start", "0.8"))
    for s in range(STEPS):
        only("lam%d" % s, s)
        out.append(_txt(LX1 - 14, 125, "%d REQ/S" % round(states[s]["lam"]), 11.5, INK,
                        "800", "end", "0.8", "lam%d" % s))

    # ── the server, and what its threads are actually doing ──────────────
    out.append(_rr(LX0, 150, LX1 - LX0, 148, 6, CARD, 'stroke="%s" stroke-width="1.3"' % RULE))
    out.append(_txt(LX0 + 14, 172, "APPLICATION SERVER", 9.5, INK, "800", "start", "1.8"))
    out.append(_txt(LX0 + 172, 172, "ONE THREAD PER REQUEST, HELD UNTIL IT IS DONE",
                    8, FAINT, "600", "start", "1.1"))
    cols, sw, sh, gx, gy = 12, 54.0, 18.0, 8.0, 6.0
    tx0, ty0 = LX0 + 14, 182.0
    for i in range(THREADS):
        c, r = i % cols, i // cols
        x, y = tx0 + c * (sw + gx), ty0 + r * (sh + gy)
        out.append(_rr(x, y, sw, sh, 3, _mix(CARD, INK, 0.05)))
        # a thread is blue only while it is really running a query; the rest are
        # blocked on the pool, and that is the whole argument of the panel
        # a mean occupancy of 9.9998 is a full pool of ten; testing against
        # the whole number leaves the last slot dark forever
        work = next((s for s in range(STEPS) if states[s]["conns"] >= i + 0.95), None)
        blocked = next((s for s in range(STEPS)
                        if states[s]["threads"] >= i + 0.95), None)
        if work is not None:
            latch("tw%d" % i, work)
            out.append(_rr(x, y, sw, sh, 3, AEGEAN, 'class="tw%d"' % i))
        elif blocked is not None:
            latch("tb%d" % i, blocked)
            out.append(_rr(x, y, sw, sh, 3, CORAL, 'class="tb%d"' % i))
    lg = LX0 + 14
    for lab, col in (("RUNNING A QUERY", AEGEAN), ("BLOCKED ON THE POOL", CORAL),
                     ("IDLE", _mix(CARD, INK, 0.05))):
        out.append(_rr(lg, 278, 10, 10, 2, col))
        out.append(_txt(lg + 15, 287, lab, 7.6, MUTED, "700", "start", "1"))
        lg += 30 + len(lab) * 5.6

    # ── the queue in front of the pool ───────────────────────────────────
    out.append(_txt(LX0, 322, "WAITING FOR A CONNECTION", 9, MUTED, "800", "start", "1.6"))
    qn = THREADS - CONNS
    qw = (LX1 - LX0 - 250) / float(qn)
    out.append(_rr(LX0 + 205, 326, LX1 - LX0 - 240, 26, 4, CARD,
                   'stroke="%s" stroke-width="1.1"' % RULE))
    for i in range(qn):
        x = LX0 + 210 + i * qw
        out.append(_rr(x, 330, qw - 2.5, 18, 2, _mix(CARD, INK, 0.05)))
        at = next((s for s in range(STEPS) if states[s]["queue"] >= i + 0.95), None)
        if at is not None:
            latch("q%d" % i, at)
            out.append(_rr(x, 330, qw - 2.5, 18, 2, _mix(CORAL, INK, 0.12), 'class="q%d"' % i))
    shed_at = next((s for s in range(STEPS) if states[s]["shed"] >= 1.0), None)
    if shed_at is not None:
        latch("shed", shed_at)
        out.append('<g class="shed">')
        out.append("  " + _txt(LX1 - 2, 344, "503", 12, CRIMSON, "800", "end", "1"))
        out.append("  " + _txt(LX1 - 2, 356, "SHED", 7, CRIMSON, "700", "end", "1.2"))
        out.append("</g>")

    # ── the database, and the door into it ───────────────────────────────
    out.append(_rr(LX0, 372, LX1 - LX0, 98, 6, _mix(CARD, BROWN, 0.16),
                   'stroke="%s" stroke-width="1.3"' % _mix(RULE, BROWN, 0.4)))
    out.append(_txt(LX0 + 14, 394, "DATABASE", 9.5, INK, "800", "start", "1.8"))
    out.append(_txt(LX0 + 100, 394, "CONNECTION POOL · %d SLOTS · %d ms A QUERY"
                    % (CONNS, int(SERVICE * 1000)), 8, _mix(FAINT, INK, 0.2), "600", "start", "1.1"))
    pw, pg = 62.0, 10.0
    px0 = LX0 + (LX1 - LX0 - (CONNS * pw + (CONNS - 1) * pg)) / 2.0
    for i in range(CONNS):
        x = px0 + i * (pw + pg)
        out.append(_rr(x, 406, pw, 26, 3, _mix(CARD, BROWN, 0.30)))
        at = next((s for s in range(STEPS) if states[s]["conns"] >= i + 0.95), None)
        if at is not None:
            latch("c%d" % i, at)
            out.append(_rr(x, 406, pw, 26, 3, AEGEAN, 'class="c%d"' % i))
    out.append(_txt((LX0 + LX1) / 2.0, 454, "%d CONNECTIONS / %d ms = %d REQUESTS A SECOND, "
                    "AND NO AMOUNT OF LOAD MAKES IT %d"
                    % (CONNS, int(SERVICE * 1000), int(CAPACITY), int(CAPACITY) + 1),
                    8.4, _mix(FAINT, INK, 0.25), "700", "middle", "1"))

    # ══ the instruments ══════════════════════════════════════════════════
    reads = [("LATENCY", "latency", "%.0f ms", CRIMSON),
             ("THROUGHPUT", "tput", "%.0f/s", AEGEAN),
             ("THREADS HELD", "threads", "%.0f / " + str(THREADS), CORAL),
             ("SHED", "shed", "%.0f/s", CRIMSON)]
    for k, (lab, key, fmt, col) in enumerate(reads):
        x = RX0 + (k % 2) * 194
        y = 108 + (k // 2) * 74
        out.append(_txt(x, y, lab, 8.4, MUTED, "800", "start", "1.6"))
        out.append('<path d="M%.1f,%.1f H%.1f" stroke="%s" stroke-width="1.1"/>'
                   % (x, y + 8, x + 168, RULE))
        for s in range(STEPS):
            cls = "r%d_%d" % (k, s)
            only(cls, s)
            out.append(_txt(x, y + 36, fmt % states[s][key], 19, col, "800", "start", "-0.5", cls))

    # ── the knee ─────────────────────────────────────────────────────────
    cx0, cx1, cy0, cy1 = RX0, RX1, 268.0, 442.0
    out.append(_rr(cx0, cy0, cx1 - cx0, cy1 - cy0, 5, CARD,
                   'stroke="%s" stroke-width="1.2"' % RULE))
    out.append(_txt(cx0, cy0 - 10, "AS LOAD RISES", 8.4, MUTED, "800", "start", "1.6"))
    for gy_ in range(1, 4):
        y = cy0 + (cy1 - cy0) * gy_ / 4.0
        out.append('<path d="M%.1f,%.1f H%.1f" stroke="%s" stroke-width="0.8"/>'
                   % (cx0, y, cx1, _mix(CARD, INK, 0.07)))

    def px(lam):
        return cx0 + 8 + (cx1 - cx0 - 16) * (lam - LAM_MIN) / (LAM_MAX - LAM_MIN)

    def py(v, hi):
        return cy1 - 10 - (cy1 - cy0 - 20) * (v / hi)

    capx = px(CAPACITY)
    out.append('<path d="M%.1f,%.1f V%.1f" stroke="%s" stroke-width="1.2" '
               'stroke-dasharray="3 3"/>' % (capx, cy0 + 6, cy1 - 6, _mix(CRIMSON, CARD, 0.45)))
    out.append(_txt(capx - 5, cy0 + 18, "CAPACITY", 7.2, _mix(CRIMSON, INK, 0.2),
                    "800", "end", "0.8"))
    for key, hi, col, lab in (("latency", lat_max, CRIMSON, "LATENCY"),
                              ("tput", CAPACITY, AEGEAN, "THROUGHPUT")):
        d = "M" + " L".join("%.1f,%.1f" % (px(s["lam"]), py(s[key], hi)) for s in states)
        cls = "k_" + key
        css.append(_kf(cls, [(0.0, "stroke-dashoffset:1"), (RAMP_FROM, "stroke-dashoffset:1"),
                             (RAMP_TO, "stroke-dashoffset:0"), (100.0, "stroke-dashoffset:0")]))
        css.append("." + cls + "{stroke-dasharray:1;animation:" + cls + " "
                   + "%.1f" % DUR + "s linear infinite}")
        out.append('<path class="%s" pathLength="1" d="%s" fill="none" stroke="%s" '
                   'stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
                   % (cls, d, col))
    for li, (col, lab) in enumerate(
            ((AEGEAN, "THROUGHPUT  0-%d/s" % int(CAPACITY)),
             (CRIMSON, "LATENCY  %d-%d ms" % (round(states[0]["latency"]), round(lat_max))))):
        ly = cy0 + 16 + li * 13
        out.append(_rr(cx0 + 12, ly - 7, 9, 9, 2, col))
        out.append(_txt(cx0 + 26, ly + 1, lab, 7.2, _mix(FAINT, INK, 0.25),
                        "700", "start", "0.8"))
    stops = [(_pct(s), "transform:translate(%.1fpx,%.1fpx)"
              % (px(states[s]["lam"]), py(states[s]["latency"], lat_max)))
             for s in range(STEPS)]
    css.append(_kf("mark", [(0.0, stops[0][1])] + stops + [(100.0, stops[-1][1])]))
    css.append(".mark{animation:mark " + "%.1f" % DUR + "s linear infinite}")
    out.append('<g class="mark"><circle cx="0" cy="0" r="4" fill="%s"/></g>' % CRIMSON)

    # ── what it comes to ─────────────────────────────────────────────────
    end = states[-1]
    out.append('<path d="M48,%d H%d" stroke="%s" stroke-width="1.4" fill="none"/>'
               % (H - 46, W - 48, RULE))
    for k, (lab, val) in enumerate(
            (("AT FULL LOAD", "%d THREADS HELD" % round(end["threads"])),
             ("ACTUALLY WORKING", "%d OF THEM" % round(end["conns"])),
             ("THROUGHPUT", "%d/s, PINNED" % round(end["tput"])),
             ("LATENCY", "%dx THE IDLE FIGURE"
              % round(end["latency"] / (SERVICE * 1000.0))))):
        x = 48 + k * 296
        out.append(_txt(x, H - 26, lab, 8.6, FAINT, "700", "start", "1.5"))
        out.append(_txt(x + 160, H - 26, val, 11, INK, "800", "start", "0.6"))
    out.append(_txt(48, H - 8, "ADDING THREADS HERE MAKES IT WORSE · IT ACCEPTS MORE WORK TO "
                               "WAIT, NOT MORE WORK TO DO", 9, FAINT, "600", "start", "1.3"))
    out.append("</svg>")

    svg = "\n".join(out).replace("__STYLE__", "<style>\n" + "\n".join(css) + "\n</style>")
    with open(path_out, "w", encoding="utf-8") as f:
        f.write(svg)
    print("  wrote %s (%d steps, %d..%d req/s, capacity %d, latency %.0f..%.0f ms, %d KB)"
          % (path_out, STEPS, int(LAM_MIN), int(LAM_MAX), int(CAPACITY),
             states[0]["latency"], lat_max, len(svg) // 1024))
    return path_out


if __name__ == "__main__":
    build()
