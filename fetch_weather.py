import json, os, sys, time, datetime, urllib.request, urllib.error

with open(os.path.join(os.path.dirname(__file__), "_points_data.json")) as _f:
    POINTS = json.load(_f)

# Must match RIDER_RANGE_MIN/MAX in index.html (7*60 .. 18*60) — the rider time-slider
# never renders outside this window, so this is the full range we need hourly data for.
RIDER_HOUR_LO = 7
RIDER_HOUR_HI = 18

# 2026-09-12: temperature was being served by a coarser model than it needed to be.
# ItaliaMeteo ARPAE ICON-2I (2 km, Italy, the best available model for these Alpine
# points inside its 3-day range) does NOT publish precipitation_probability. Asking for
# precipitation_probability in the SAME call as temperature therefore forces best_match
# onto a model that carries all five variables — i.e. a coarse one. In the Dolomites that
# reads a valley point off a grid cell which averages in the surrounding 2000 m peaks, and
# comes out 2–3 °C too cold; confirmed as a stable, one-directional offset across 10+
# consecutive runs (stored consistently colder than a temperature-only live call).
#
# Splitting the request lets temperature/wind/weather_code use the highest-resolution
# model available, and fetches precipitation_probability on its own. Nothing is lost by
# separating it: precipitation probability only ever comes from a ~27 km ensemble anyway,
# so it was never going to benefit from the high-resolution model.
#
# Flip to False to revert to the previous single-call behaviour instantly, with no other
# code change — the old path is kept intact below.
SPLIT_PRECIP = True

# Second, independent suspect for the same symptom. The diagnostic panel's live check —
# the one returning the warmer, high-resolution-looking numbers — does NOT send
# &models=best_match at all, it just lets Open-Meteo default. Explicitly naming best_match
# may pin a different blend than the bare default does. Run the A/B/C URL test before
# touching this: if dropping precipitation_probability alone (test C) does NOT recover the
# warmer value, set this to False instead and re-test.
# Do not flip both at once — one change at a time, so the result stays attributable.
USE_BEST_MATCH_PARAM = True

MAIN_VARS = "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m"
LEGACY_VARS = MAIN_VARS + ",precipitation_probability"

def _request(url):
    req = urllib.request.Request(url, headers={"User-Agent": "trd-weather-bot"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def _url(p, hourly):
    u = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
         "&hourly=%s&timezone=auto&start_date=%s&end_date=%s"
         % (p["lat"], p["lon"], hourly, p["date"], p["date"]))
    if USE_BEST_MATCH_PARAM:
        u += "&models=best_match"
    return u

def hour_slice(H, idx):
    return {"temp": round(H["temperature_2m"][idx]),
            "code": H["weather_code"][idx],
            "wind": round(H["wind_speed_10m"][idx]),
            "windDeg": round(H["wind_direction_10m"][idx]),
            "rain": H["precipitation_probability"][idx] or 0}

def fetch_precip(p, times):
    """Second, SOFT-failing call. Returns a list aligned to `times`, or None on failure.

    Deliberately does not raise: a precipitation outage must never cost us the
    temperature we already successfully fetched. main() carries the previous run's
    rain values forward when this returns None, so a failure here is invisible
    rather than silently showing 0% ("no rain expected") in the mountains.
    """
    try:
        H = _request(_url(p, "precipitation_probability"))["hourly"]
    except Exception as e:
        sys.stderr.write("precip %s: %s (temperature unaffected)\n" % (p["key"], e))
        return None
    by_time = dict(zip(H["time"], H.get("precipitation_probability", [])))
    return [by_time.get(t) for t in times]

def open_meteo(p):
    if SPLIT_PRECIP:
        H = _request(_url(p, MAIN_VARS))["hourly"]
        pr = fetch_precip(p, H["time"])
        precip_ok = pr is not None
        H["precipitation_probability"] = pr if precip_ok else [None] * len(H["time"])
    else:
        H = _request(_url(p, LEGACY_VARS))["hourly"]
        precip_ok = True
    times = H["time"]
    target = "%sT%02d:00" % (p["date"], p["hour"])
    idx = times.index(target) if target in times else p["hour"]
    result = hour_slice(H, idx)
    # Full hourly breakdown across the rider-slider window — same response, just kept
    # instead of discarded. Missing hours (e.g. outside Open-Meteo's returned day) are
    # simply omitted rather than guessed.
    hourly = {}
    for hr in range(RIDER_HOUR_LO, RIDER_HOUR_HI + 1):
        t = "%sT%02d:00" % (p["date"], hr)
        if t in times:
            hourly[str(hr)] = hour_slice(H, times.index(t))
    result["hourly"] = hourly
    result["_precip_ok"] = precip_ok   # stripped in main(), never written to weather.json
    return result

def fetch_point(p, tries=5):
    for a in range(tries):
        try:
            return open_meteo(p)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                # date is outside Open-Meteo's forecast horizon — this won't change on retry
                sys.stderr.write("skip %s: HTTP 400 (date out of forecast range)\n" % p["key"])
                return None
            sys.stderr.write("retry %d %s: HTTP %d\n" % (a, p["key"], e.code)); time.sleep(2)
        except Exception as e:
            sys.stderr.write("retry %d %s: %s\n" % (a, p["key"], e)); time.sleep(2)
    return None

def carry_rain(new, old):
    """Keep the previous run's rain figures when this run's precipitation call failed.

    Never touches temp/wind/code — those came from a successful fetch and are current.
    """
    if not old:
        return new
    if "rain" in old:
        new["rain"] = old["rain"]
    for hr, sl in new.get("hourly", {}).items():
        o = old.get("hourly", {}).get(hr)
        if o and "rain" in o:
            sl["rain"] = o["rain"]
    return new

def main():
    prev = {}
    if os.path.exists("weather.json"):
        try: prev = json.load(open("weather.json")).get("data", {})
        except Exception: pass
    # Carry forward only keys that are still in the current point list. This preserves the
    # failed-fetch protection intact — a current point whose fetch fails this run keeps its
    # previous value, because its key survives this filter — while dropping orphans left
    # behind by retired point schemes (e.g. the old 3-point "0-2" finish index and the old
    # A/B "2-1b"/"5-1b" midpoints). Without this, weather.json only ever grew: nothing
    # removed a key just because it stopped being generated.
    current_keys = {p["key"] for p in POINTS}
    dropped = sorted(k for k in prev if k not in current_keys)
    out = {k: v for k, v in prev.items() if k in current_keys}
    if dropped:
        print("dropped %d stale key(s): %s" % (len(dropped), ", ".join(dropped)))
    failed = []
    precip_degraded = []
    for p in POINTS:
        wx = fetch_point(p)
        if wx:
            if not wx.pop("_precip_ok", True):
                wx = carry_rain(wx, prev.get(p["key"]))
                precip_degraded.append(p["key"])
            out[p["key"]] = wx
        else:
            failed.append(p["key"])
        time.sleep(0.4)
    payload = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "data": out}
    json.dump(payload, open("weather.json", "w"), ensure_ascii=False)
    print("wrote weather.json:", len(out), "points")
    if precip_degraded:
        # Not fatal: temperature/wind are current, only rain% fell back to the last run.
        print("precip carried forward for %d point(s): %s"
              % (len(precip_degraded), ", ".join(precip_degraded)))
    if failed:
        # Fail the job *after* writing whatever succeeded, so the run shows red in the Actions
        # tab instead of looking identical to a clean run -- previously nothing signalled a
        # failure beyond stderr lines nobody was watching, so even a 100%-failed run stayed
        # green. A failed point here still keeps its carried-forward value in weather.json
        # above (or is simply absent if it has never once succeeded) -- this exit code only
        # affects whether the run gets flagged, never whether data gets written.
        sys.stderr.write("FAILED to fetch %d/%d point(s): %s\n" % (len(failed), len(POINTS), ", ".join(failed)))
        sys.exit(1)

if __name__ == "__main__":
    main()
