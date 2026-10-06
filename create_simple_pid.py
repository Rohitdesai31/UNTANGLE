from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


OUTPUT = Path("samples/simple_pid.pdf")

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)


def draw_arrow(c, x, y):
    c.line(x - 10, y + 6, x, y)
    c.line(x - 10, y - 6, x, y)


def create_pid():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(
        str(OUTPUT),
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
    )

    c.setTitle("UNTANGLE Simple Test P&ID")

    # -------------------------------------------------
    # Title
    # -------------------------------------------------

    c.setFont("Helvetica-Bold", 18)
    c.drawString(
        40,
        PAGE_HEIGHT - 40,
        "UNTANGLE - Simple Test P&ID",
    )

    c.setFont("Helvetica", 9)
    c.drawString(
        40,
        PAGE_HEIGHT - 56,
        "Synthetic development fixture - not for engineering use",
    )

    # -------------------------------------------------
    # Main coordinates
    # -------------------------------------------------

    y = 390

    tank_x = 120
    pump_x = 300
    valve_x = 440
    reactor_x = 650
    outlet_x = 810

    # -------------------------------------------------
    # TK-101
    # -------------------------------------------------

    c.setLineWidth(2)

    c.rect(
        tank_x - 45,
        y - 70,
        90,
        140,
    )

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(
        tank_x,
        y + 88,
        "TK-101",
    )

    c.setFont("Helvetica", 9)
    c.drawCentredString(
        tank_x,
        y + 75,
        "Feed Tank",
    )

    # -------------------------------------------------
    # P-101
    # -------------------------------------------------

    c.circle(
        pump_x,
        y,
        30,
    )

    c.line(
        pump_x - 20,
        y - 20,
        pump_x + 20,
        y + 20,
    )

    c.line(
        pump_x - 20,
        y + 20,
        pump_x + 20,
        y - 20,
    )

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(
        pump_x,
        y + 50,
        "P-101",
    )

    c.setFont("Helvetica", 9)
    c.drawCentredString(
        pump_x,
        y + 37,
        "Feed Pump",
    )

    # -------------------------------------------------
    # FCV-101
    # -------------------------------------------------

    c.line(
        valve_x - 25,
        y + 20,
        valve_x,
        y,
    )

    c.line(
        valve_x - 25,
        y - 20,
        valve_x,
        y,
    )

    c.line(
        valve_x + 25,
        y + 20,
        valve_x,
        y,
    )

    c.line(
        valve_x + 25,
        y - 20,
        valve_x,
        y,
    )

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(
        valve_x,
        y + 50,
        "FCV-101",
    )

    c.setFont("Helvetica", 8)
    c.drawCentredString(
        valve_x,
        y + 38,
        "Control Valve",
    )

    # -------------------------------------------------
    # R-101
    # -------------------------------------------------

    c.circle(
        reactor_x,
        y,
        60,
    )

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(
        reactor_x,
        y + 5,
        "R-101",
    )

    c.setFont("Helvetica", 9)
    c.drawCentredString(
        reactor_x,
        y - 10,
        "Reactor",
    )

    # -------------------------------------------------
    # Process lines
    # -------------------------------------------------

    c.setLineWidth(2)

    # Tank -> Pump
    c.line(
        tank_x + 45,
        y,
        pump_x - 30,
        y,
    )

    # Pump -> Valve
    c.line(
        pump_x + 30,
        y,
        valve_x - 25,
        y,
    )

    # Valve -> Reactor
    c.line(
        valve_x + 25,
        y,
        reactor_x - 60,
        y,
    )

    # Reactor -> Outlet
    c.line(
        reactor_x + 60,
        y,
        outlet_x,
        y,
    )

    # Flow arrows
    draw_arrow(c, 220, y)
    draw_arrow(c, 375, y)
    draw_arrow(c, 545, y)
    draw_arrow(c, 735, y)

    # -------------------------------------------------
    # FT-101
    # -------------------------------------------------

    ft_x = 350
    ft_y = y + 120

    c.circle(
        ft_x,
        ft_y,
        23,
    )

    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(
        ft_x,
        ft_y + 3,
        "FT",
    )

    c.drawCentredString(
        ft_x,
        ft_y - 7,
        "101",
    )

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(
        ft_x,
        ft_y + 40,
        "FT-101",
    )

    c.line(
        ft_x,
        ft_y - 23,
        ft_x,
        y,
    )

    # -------------------------------------------------
    # FIC-101
    # -------------------------------------------------

    fic_x = 470
    fic_y = y + 120

    c.rect(
        fic_x - 25,
        fic_y - 23,
        50,
        46,
    )

    c.setFont("Helvetica-Bold", 8)

    c.drawCentredString(
        fic_x,
        fic_y + 4,
        "FIC",
    )

    c.drawCentredString(
        fic_x,
        fic_y - 7,
        "101",
    )

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(
        fic_x,
        fic_y + 40,
        "FIC-101",
    )

    c.line(
        fic_x,
        fic_y - 23,
        fic_x,
        y,
    )

    # -------------------------------------------------
    # TT-101
    # -------------------------------------------------

    tt_x = reactor_x
    tt_y = y - 120

    c.circle(
        tt_x,
        tt_y,
        23,
    )

    c.setFont("Helvetica-Bold", 8)

    c.drawCentredString(
        tt_x,
        tt_y + 3,
        "TT",
    )

    c.drawCentredString(
        tt_x,
        tt_y - 7,
        "101",
    )

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(
        tt_x,
        tt_y - 40,
        "TT-101",
    )

    c.line(
        tt_x,
        tt_y + 23,
        tt_x,
        y - 60,
    )

    # -------------------------------------------------
    # LT-101
    # -------------------------------------------------

    lt_x = reactor_x + 110
    lt_y = y + 10

    c.circle(
        lt_x,
        lt_y,
        23,
    )

    c.setFont("Helvetica-Bold", 8)

    c.drawCentredString(
        lt_x,
        lt_y + 3,
        "LT",
    )

    c.drawCentredString(
        lt_x,
        lt_y - 7,
        "101",
    )

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(
        lt_x,
        lt_y + 40,
        "LT-101",
    )

    c.line(
        lt_x - 23,
        lt_y,
        reactor_x + 60,
        y,
    )

    # -------------------------------------------------
    # Outlet
    # -------------------------------------------------

    c.setFont("Helvetica-Bold", 10)

    c.drawString(
        outlet_x + 10,
        y + 5,
        "OUTLET",
    )

    # -------------------------------------------------
    # Test information
    # -------------------------------------------------

    c.setFont("Helvetica-Bold", 10)

    c.drawString(
        40,
        90,
        "Test Process:",
    )

    c.setFont("Helvetica", 9)

    c.drawString(
        40,
        75,
        "TK-101 -> P-101 -> FCV-101 -> R-101 -> OUTLET",
    )

    c.drawString(
        40,
        60,
        "Instruments: FT-101, FIC-101, TT-101, LT-101",
    )

    c.drawString(
        40,
        45,
        "Intentional missing IO-list test tag: FT-999",
    )

    c.setFont("Helvetica-Oblique", 8)

    c.drawRightString(
        PAGE_WIDTH - 40,
        25,
        "UNTANGLE synthetic test fixture",
    )

    c.save()

    print("P&ID created successfully:")
    print(OUTPUT)


if __name__ == "__main__":
    create_pid()