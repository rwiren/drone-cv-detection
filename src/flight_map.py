"""Generate interactive Folium map of flight path with 1:1 rule status.

Outputs a standalone HTML file showing:
- Drone flight path (colored by 1:1 rule status)
- Person detection positions
- Altitude profile
- Click any point for telemetry details
"""

import json, csv, math
from datetime import datetime, timezone
import folium
from folium.plugins import AntPath


def generate_map(osd_path='data/autel_mqtt_20260612/osd_drone.jsonl',
                 timeline_path='outputs/autel_20260612/1to1_rule_timeline.csv',
                 output_path='outputs/autel_20260612/flight_map.html'):

    # Load OSD for flight path
    with open(osd_path) as f:
        osd = [json.loads(l) for l in f]

    # Load 1:1 timeline
    with open(timeline_path) as f:
        timeline = list(csv.DictReader(f))

    # Center map on flight area
    center_lat = sum(r['data']['latitude'] for r in osd) / len(osd)
    center_lon = sum(r['data']['longitude'] for r in osd) / len(osd)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=17,
                   tiles='OpenStreetMap')

    # Flight path polyline colored by altitude
    path_coords = [(r['data']['latitude'], r['data']['longitude']) for r in osd]
    folium.PolyLine(path_coords, color='blue', weight=2, opacity=0.5,
                    tooltip='Flight path').add_to(m)

    # 1:1 rule violations as red dots, passes as green
    violations_fg = folium.FeatureGroup(name='1:1 Violations (red)')
    passes_fg = folium.FeatureGroup(name='1:1 Passes (green)')

    # Sample every 10th point to avoid clutter
    for row in timeline[::10]:
        lat = float(row['drone_lat'])
        lon = float(row['drone_lon'])
        alt = float(row['altitude_m'])
        lateral = float(row['lateral_distance_m'])
        ratio = float(row['ratio'])
        violation = row['violation'] == 'True'
        time_str = row['timestamp_utc'][11:19]

        popup = (f"<b>{time_str} UTC</b><br>"
                 f"Alt: {alt:.0f}m<br>"
                 f"Lateral: {lateral:.1f}m<br>"
                 f"Ratio: {ratio:.2f}x<br>"
                 f"{'❌ VIOLATION' if violation else '✅ PASS'}")

        marker = folium.CircleMarker(
            [lat, lon], radius=3,
            color='red' if violation else 'green',
            fill=True, fill_opacity=0.7,
            popup=popup,
        )
        if violation:
            marker.add_to(violations_fg)
        else:
            marker.add_to(passes_fg)

    violations_fg.add_to(m)
    passes_fg.add_to(m)

    # Person positions (from timeline, unique locations)
    person_lats = set()
    for row in timeline[::50]:
        plat = float(row['drone_lat'])  # approximate (person is near drone in this flight)
        plon = float(row['drone_lon'])
        key = f"{plat:.5f},{plon:.5f}"
        if key not in person_lats and float(row['lateral_distance_m']) < 20:
            person_lats.add(key)
            folium.Marker(
                [plat, plon],
                icon=folium.Icon(color='orange', icon='user', prefix='fa'),
                popup=f"Person detected<br>Lateral: {row['lateral_distance_m']}m",
            ).add_to(m)

    # Home/launch point
    folium.Marker(
        [osd[0]['data']['latitude'], osd[0]['data']['longitude']],
        icon=folium.Icon(color='blue', icon='plane', prefix='fa'),
        popup='Launch point',
    ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Title
    title_html = '''<div style="position:fixed;top:10px;left:60px;z-index:1000;
        background:white;padding:10px;border-radius:5px;box-shadow:0 2px 6px rgba(0,0,0,0.3)">
        <b>Patent WO2025034145A1 — 1:1 Rule Flight Validation</b><br>
        Ericsson Jorvas, 2026-06-12 | Autel MAX 4T V2 xe<br>
        <span style="color:red">●</span> Violation &nbsp;
        <span style="color:green">●</span> Pass &nbsp;
        <span style="color:blue">—</span> Flight path
    </div>'''
    m.get_root().html.add_child(folium.Element(title_html))

    m.save(output_path)
    print(f'Map saved: {output_path}')
    return output_path


if __name__ == '__main__':
    generate_map()
