"""Draws the DFIP UML component diagram (SAD section 3, Figure 1) as a PNG.

Notation follows Lab 3: <<component>> boxes with the component icon, ports (small squares),
provided interfaces (ball), required interfaces (socket), assembly connectors, <<use>>
dependencies (dashed arrows) and tier frames.

    python docs/diagrams/make_component_diagram.py
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Rectangle

OUT = Path(__file__).with_name("dfip_component_diagram.png")

BG = "#faf7f0"
INK = "#222222"
GREEN = "#1f7a3d"
COLORS = {  # tier -> (fill, edge)
    "ui": ("#bcd4ee", "#3d6ea5"),
    "app": ("#f6d3a1", "#b9731c"),
    "ana": ("#d5e8c8", "#4f8a34"),
    "data": ("#e6d5ee", "#7a4f94"),
}

fig, ax = plt.subplots(figsize=(30, 18.6), dpi=110)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(-1.3, 30.2)
ax.set_ylim(-1.6, 17.0)
ax.set_aspect("equal")
ax.axis("off")

PORT = 0.2  # half size of a port square


def tier(x0, y0, x1, y1, label):
    ax.add_patch(
        FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.15",
                       fill=False, ec=INK, lw=1.8, ls=(0, (6, 4)), zorder=1)
    )
    ax.text(x0 - 0.55, (y0 + y1) / 2, label, fontsize=13, fontweight="bold", color=INK, va="center",
            ha="center", rotation=90, linespacing=1.2)


def component(cx, cy, w, h, name, kind):
    fill, edge = COLORS[kind]
    x0, y0 = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch((x0 + 0.08, y0 - 0.08), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                fc="#00000014", ec="none", zorder=2))
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                fc=fill, ec=edge, lw=2.2, zorder=3))
    # component icon (UML): two small rectangles on the left edge
    for dy in (0.28, 0.0):
        ax.add_patch(Rectangle((x0 - 0.22, y0 + h - 0.36 - dy - 0.22), 0.44, 0.22, fc="white", ec=edge, lw=1.6, zorder=5))
    ax.text(cx + 0.1, cy + 0.28, "«component»", fontsize=11, style="italic", ha="center", va="center",
            color=INK, zorder=6)
    ax.text(cx + 0.1, cy - 0.22, name, fontsize=14, fontweight="bold", ha="center", va="center",
            color=INK, zorder=6, linespacing=1.15)
    return dict(x0=x0, y0=y0, x1=x0 + w, y1=y0 + h, edge=edge)


def port(x, y, edge="#444444"):
    ax.add_patch(Rectangle((x - PORT, y - PORT), 2 * PORT, 2 * PORT, fc="white", ec=edge, lw=1.8, zorder=7))
    return (x, y)


def ball(x, y, r=0.2):
    ax.add_patch(Circle((x, y), r, fc="white", ec=INK, lw=1.9, zorder=9))


def socket(x, y, toward_deg, r=0.34):
    """Semicircle centred on the ball, convex side facing the requiring component."""
    ax.add_patch(Arc((x, y), 2 * r, 2 * r, theta1=toward_deg - 90, theta2=toward_deg + 90,
                     ec=INK, lw=2.0, zorder=9))


def assembly(provider, requirer, name, proto, label_side=1, pos=0.5, off=0.62):
    """Assembly connector: provider port -o)- requirer port, with name and protocol labels."""
    (px, py), (rx, ry) = provider, requirer
    ax.plot([px, rx], [py, ry], color=INK, lw=1.7, zorder=4, solid_capstyle="round")
    mx, my = px + (rx - px) * pos, py + (ry - py) * pos
    ang = math.degrees(math.atan2(ry - my, rx - mx))  # direction from the ball towards the requirer
    ball(mx, my)
    socket(mx, my, ang)
    dx, dy = rx - px, ry - py
    n = math.hypot(dx, dy)
    nx, ny = -dy / n, dx / n  # unit normal
    offs = off * label_side
    ha = "left" if nx * label_side > 0.2 else ("right" if nx * label_side < -0.2 else "center")
    tx, ty = mx + nx * offs, my + ny * offs
    ax.text(tx, ty + 0.15, name, fontsize=11.5, style="italic", fontweight="bold", ha=ha, va="center",
            color=INK, zorder=10, bbox=dict(fc=BG, ec="none", pad=1.2))
    ax.text(tx, ty - 0.22, proto, fontsize=9.5, style="italic", ha=ha, va="center", color="#555555",
            zorder=10, bbox=dict(fc=BG, ec="none", pad=1.0))


def use_dep(a, b):
    ax.annotate("", xy=b, xytext=a, zorder=6,
                arrowprops=dict(arrowstyle="-|>", ls=(0, (6, 3)), color=GREEN, lw=1.9,
                                shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- title
ax.text(0.6, 16.5, "Demand Forecasting & Inventory Planning System (DFIP)", fontsize=26, fontweight="bold",
        color=INK, va="center")
ax.text(0.6, 15.75, "UML Component Diagram — Layered Modular Architecture (SAD Figure 1)", fontsize=16,
        style="italic", color="#555555", va="center")
ax.text(29.4, 16.2, "HTTPS/TLS (DFIP-SR-005) protects every browser-to-API call;\n"
        "RBAC (IAuthentication) is checked on each request.", fontsize=10.5, style="italic",
        color="#555555", ha="right", va="center")

# ---------------------------------------------------------------- tiers
tier(0.5, 13.1, 29.5, 15.3, "Presentation\nTier")
tier(0.5, 4.9, 29.5, 12.3, "Application Tier\n(FastAPI REST API)")
tier(9.0, 0.7, 23.5, 4.2, "Analytics\nTier")
tier(0.5, 0.7, 7.9, 4.2, "Data\nTier")

W, H = 4.2, 1.7
UPPER, LOWER, AN_Y = 9.6, 6.1, 2.45
UX = dict(auth=3.0, prod=8.2, sales=13.4, plan=18.6, dash=25.0)

# ---------------------------------------------------------------- components
ui = component(14.8, 14.2, 26.8, 1.6, "Web UI / Dashboard (React single-page app)", "ui")
auth = component(UX["auth"], UPPER, W, H, "Authentication\n& RBAC", "app")
prod = component(UX["prod"], UPPER, W, H, "Product / Inventory\nService", "app")
sales = component(UX["sales"], UPPER, W, H, "Sales Data\nService", "app")
plan = component(UX["plan"], UPPER, W, H, "Inventory Planning\nService", "app")
dash = component(UX["dash"], UPPER, W, H, "Dashboard / Report\nService", "app")
sett = component(20.6, LOWER, 3.8, H, "Administration /\nSettings Service", "app")
audit = component(26.6, LOWER, 3.8, H, "Audit & Logging\nService", "app")
valid = component(12.4, AN_Y, 4.2, 1.7, "Data Validation /\nPreprocessing", "ana")
fcst = component(19.6, AN_Y, 4.2, 1.7, "Demand Forecasting\nEngine", "ana")
db = component(4.5, AN_Y, 5.6, 1.7, "Relational Database\n(SQLite / SQL, SQLAlchemy ORM)", "data")

# ---------------------------------------------------------------- UI -> services (5 assemblies, vertical)
svc = dict(auth=auth, prod=prod, sales=sales, plan=plan, dash=dash)
svc_x = dict(auth=UX["auth"], prod=UX["prod"], sales=UX["sales"], plan=17.7, dash=UX["dash"])
labels = dict(
    auth=("IAuthentication", "login / logout (REST, HTTPS)"),
    prod=("IProductInventory", "products, stock (REST, HTTPS)"),
    sales=("ISalesData", "sales, CSV import (REST, HTTPS)"),
    plan=("IPlanning", "forecasts, plans (REST, HTTPS)"),
    dash=("IDashboardReport", "KPIs, alerts, reports (REST)"),
)
for key in svc:
    prov = port(svc_x[key], svc[key]["y1"], COLORS["app"][1])
    req = port(svc_x[key], ui["y0"], COLORS["ui"][1])
    assembly(prov, req, *labels[key], label_side=-1, pos=0.42)

# ---------------------------------------------------------------- Sales -> Validation
p_val_top = port(13.4, valid["y1"], COLORS["ana"][1])
r_sales = port(13.4, sales["y0"], COLORS["app"][1])
assembly(p_val_top, r_sales, "IValidation", "validate rows (Python call)", label_side=1, pos=0.5)

# ---------------------------------------------------------------- Forecast -> Validation
p_val_r = port(valid["x1"], AN_Y, COLORS["ana"][1])
r_fc_l = port(fcst["x0"], AN_Y, COLORS["ana"][1])
assembly(p_val_r, r_fc_l, "ITimeSeries", "clean series (Python call)", label_side=1, pos=0.5)

# ---------------------------------------------------------------- Planning -> Forecast
p_fc_top = port(17.9, fcst["y1"], COLORS["ana"][1])
r_plan_b = port(17.9, plan["y0"], COLORS["app"][1])
assembly(p_fc_top, r_plan_b, "IForecast", "forecast (Python call)", label_side=1, pos=0.5)

# ---------------------------------------------------------------- Planning -> Settings
p_set_top = port(20.0, sett["y1"], COLORS["app"][1])
r_plan_b2 = port(20.0, plan["y0"], COLORS["app"][1])
assembly(p_set_top, r_plan_b2, "ISettings", "planning defaults (Python call)", label_side=-1, pos=0.72)

# ---------------------------------------------------------------- Dashboard -> Planning
p_plan_r = port(plan["x1"], UPPER, COLORS["app"][1])
r_dash_l = port(dash["x0"], UPPER, COLORS["app"][1])
assembly(p_plan_r, r_dash_l, "IRisk", "risk, reorder qty (Python call)", label_side=1, pos=0.5, off=1.45)

# ---------------------------------------------------------------- Settings -> Audit
p_aud_l = port(audit["x0"], LOWER, COLORS["app"][1])
r_set_r = port(sett["x1"], LOWER, COLORS["app"][1])
assembly(p_aud_l, r_set_r, "IAudit", "record action (Python call)", label_side=-1, pos=0.5, off=1.3)

# ---------------------------------------------------------------- <<use>> dependencies to the database
db_p1 = port(3.6, db["y1"], COLORS["data"][1])
db_p2 = port(5.9, db["y1"], COLORS["data"][1])
a_auth = port(3.6, auth["y0"], COLORS["app"][1])
a_prod = port(6.5, prod["y0"], COLORS["app"][1])
use_dep(a_auth, db_p1)
use_dep(a_prod, db_p2)
ax.text(4.2, 5.55, "«use» IPersistence\n(SQL via SQLAlchemy ORM)", fontsize=10.5, style="italic",
        color=GREEN, ha="left", va="center", zorder=10, bbox=dict(fc=BG, ec="none", pad=1.5))

note = ("«use» IPersistence: every application service reads and\n"
        "writes the database through the same interface. Sales, Planning,\n"
        "Dashboard, Settings and Audit follow the dependency drawn for\n"
        "Authentication and Product; only two arrows are drawn to keep\n"
        "the diagram readable.")
ax.add_patch(FancyBboxPatch((23.8, 0.9), 6.0, 3.0, boxstyle="round,pad=0,rounding_size=0.1", fc="white",
                            ec=GREEN, lw=1.3, ls=(0, (4, 3)), zorder=2))
ax.text(24.0, 2.4, note, fontsize=8.6, style="italic", color=GREEN, va="center", zorder=10)

# ---------------------------------------------------------------- legend
lx, ly = 0.6, -1.2
ax.add_patch(FancyBboxPatch((lx, ly), 25.0, 1.9, boxstyle="round,pad=0,rounding_size=0.12", fc="white",
                            ec="#999999", lw=1.6, zorder=2))
ax.text(lx + 0.4, ly + 1.5, "Legend", fontsize=13, fontweight="bold", va="center", color=INK)
y = ly + 0.62
ax.add_patch(FancyBboxPatch((lx + 0.7, y - 0.3), 1.6, 0.6, boxstyle="round,pad=0,rounding_size=0.06",
                            fc=COLORS["app"][0], ec=COLORS["app"][1], lw=1.6, zorder=3))
for dy in (0.15, -0.1):
    ax.add_patch(Rectangle((lx + 0.55, y + dy - 0.07), 0.3, 0.14, fc="white", ec=COLORS["app"][1], lw=1.2, zorder=5))
ax.text(lx + 2.55, y, "«component»", fontsize=10.5, va="center")
ball(lx + 6.0, y, 0.18)
ax.text(lx + 6.45, y, "Provided interface (ball)", fontsize=10.5, va="center")
socket(lx + 10.9, y, 180, 0.24)
ax.text(lx + 11.35, y, "Required interface (socket)", fontsize=10.5, va="center")
ax.add_patch(Rectangle((lx + 15.3 - PORT, y - PORT), 2 * PORT, 2 * PORT, fc="white", ec="#444444", lw=1.6, zorder=5))
ax.text(lx + 15.75, y, "Port", fontsize=10.5, va="center")
ax.plot([lx + 17.3, lx + 18.2], [y, y], color=INK, lw=1.6)
ball(lx + 17.75, y, 0.14)
socket(lx + 17.75, y, 0, 0.22)
ax.text(lx + 18.5, y, "Assembly connector", fontsize=10.5, va="center")
ax.annotate("", xy=(lx + 22.6, y), xytext=(lx + 21.1, y),
            arrowprops=dict(arrowstyle="-|>", ls=(0, (6, 3)), color=GREEN, lw=1.7))
ax.text(lx + 22.8, y, "«use» dependency", fontsize=10.5, va="center", color=GREEN)

ax.text(0.6, -1.5, "11 components • 11 interfaces (IAuthentication, IProductInventory, ISalesData, IPlanning, "
        "IDashboardReport, IValidation, ITimeSeries, IForecast, ISettings, IRisk, IAudit) + IPersistence dependency",
        fontsize=10, style="italic", color="#555555", va="center")

fig.savefig(OUT, dpi=110, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
print("wrote", OUT)
