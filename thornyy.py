# ========================================================
# AIR PURIFIER – Final Version
# MQ135 | OLED | Relay on GP19 | ECO/PWR/CLEAN modes
# Save this file as main.py on your Pico
# ========================================================

from machine import Pin, ADC, I2C
import time, ssd1306

# ---------- HARDWARE PINS ----------
mq135 = ADC(26)                     # Air sensor
relay = Pin(19, Pin.OUT)            # Relay IN -> GP19
btn_mode = Pin(9, Pin.IN, Pin.PULL_UP)
btn_select = Pin(10, Pin.IN, Pin.PULL_UP)

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# ---------- RELAY LOGIC ----------
RELAY_ACTIVE_LOW = True             # Set False if your relay needs HIGH to turn on

def relay_on():
    relay.value(0 if RELAY_ACTIVE_LOW else 1)

def relay_off():
    relay.value(1 if RELAY_ACTIVE_LOW else 0)

# ---------- CALIBRATION ----------
CLEAN_RAW = 18000   # ADC value when air is clean -> shows ~400 PPM
DIRTY_RAW = 35000   # ADC value in very polluted air -> ~1000 PPM
FAN_ON_PPM = 650    # Fan switches on above this PPM

mode = 0
modes = ["ECO", "PWR", "CLEAN"]
fan_state = False
clean_active = False
clean_start = 0

# ---------- PPM CALCULATION ----------
def raw_to_ppm(raw):
    if raw <= CLEAN_RAW:
        ppm = int((raw / CLEAN_RAW) * 400)
    elif raw >= DIRTY_RAW:
        ppm = int(1000 + (raw - DIRTY_RAW) * 0.1)
    else:
        ratio = (raw - CLEAN_RAW) / (DIRTY_RAW - CLEAN_RAW)
        ppm = int(400 + ratio * 600)
    return max(ppm, 0)

def read_sensor():
    total = 0
    for _ in range(10):
        total += mq135.read_u16()
        time.sleep(0.01)
    avg = total // 10
    return raw_to_ppm(avg), avg

# ---------- RAW CALIBRATION MODE (hold SELECT during boot) ----------
def raw_calibration_mode():
    oled.fill(0)
    oled.text("RAW CALIBRATION", 5, 5, 1)
    oled.hline(0, 15, 128, 1)
    oled.text("Press SEL to exit", 5, 50, 1)
    oled.text("Set CLEAN_RAW", 15, 57, 1)
    while True:
        raw = mq135.read_u16()
        ppm = raw_to_ppm(raw)
        oled.fill_rect(0, 20, 128, 25, 0)
        oled.text("RAW:" + str(raw), 10, 22, 1)
        oled.text("PPM:" + str(ppm), 10, 35, 1)
        oled.show()
        time.sleep(0.3)
        if not btn_select.value():
            time.sleep(0.5)
            break

# ---------- BOOT SELF-TEST ----------
def boot():
    oled.fill(0)
    oled.text("SYSTEM CHECK", 20, 10, 1)
    oled.show()
    time.sleep(1)

    # Fan test
    oled.fill(0)
    oled.text("FAN TEST", 30, 20, 1)
    oled.text("Relay ON...", 25, 35, 1)
    oled.show()
    relay_on()
    time.sleep(1.5)
    oled.text(" OK", 80, 35, 1)
    oled.show()
    time.sleep(0.5)

    oled.text("Relay OFF..", 25, 45, 1)
    relay_off()
    time.sleep(1)
    oled.text(" OK", 85, 45, 1)
    oled.show()
    time.sleep(1)

    # Sensor test
    oled.fill(0)
    oled.text("SENSOR TEST", 25, 20, 1)
    oled.show()
    ppm, raw = read_sensor()
    time.sleep(0.5)
    oled.text(str(ppm) + " PPM", 35, 30, 1)
    oled.text("Raw:" + str(raw), 35, 42, 1)
    oled.text("OK", 90, 30, 1)
    oled.show()
    time.sleep(3)

    if not btn_select.value():
        raw_calibration_mode()

    oled.fill(0)
    oled.text("ALL SYSTEMS", 20, 20, 1)
    oled.text("READY!", 45, 35, 1)
    oled.show()
    time.sleep(2)

# ---------- 5 SECOND MENU RETURN ----------
def return_to_menu():
    for i in range(5, 0, -1):
        oled.fill(0)
        oled.text("BACK TO MENU", 15, 20, 1)
        oled.text("WAIT " + str(i) + " SEC", 25, 35, 1)
        oled.show()
        time.sleep(1)
    mode_menu()

# ---------- MODE SELECTION ----------
def mode_menu():
    global mode
    selected = mode
    last_btn = True

    while True:
        oled.fill(0)
        oled.text("SELECT MODE:", 10, 2, 1)
        oled.hline(0, 12, 128, 1)

        for i in range(3):
            y = 20 + (i * 14)
            if i == selected:
                oled.fill_rect(15, y-1, 100, 10, 1)
                oled.text("> " + modes[i], 20, y, 0)
            else:
                oled.text("  " + modes[i], 20, y, 1)

        oled.hline(0, 55, 128, 1)
        oled.text("MODE:Next SEL:OK", 2, 56, 1)
        oled.show()
        time.sleep(0.05)

        if not btn_mode.value() and last_btn:
            selected = (selected + 1) % 3
            last_btn = False
            time.sleep(0.2)
        elif btn_mode.value():
            last_btn = True

        if not btn_select.value():
            mode = selected
            break

    oled.fill(0)
    oled.text("MODE: " + modes[mode], 25, 15, 1)
    oled.text("WAIT 5 SEC...", 20, 30, 1)
    oled.show()
    time.sleep(5)

    oled.fill(0)
    oled.text("STARTING", 35, 25, 1)
    oled.text(modes[mode] + " MODE", 30, 38, 1)
    oled.show()
    time.sleep(2)

# ---------- DASHBOARD ----------
def show_dashboard(ppm_val):
    oled.fill(0)
    oled.text(modes[mode], 50, 2, 1)
    oled.hline(0, 12, 128, 1)

    oled.text("PPM:", 10, 18, 1)
    oled.text(str(ppm_val), 50, 18, 1)

    oled.text("STAT:", 10, 30, 1)
    if ppm_val <= 400:
        status = "GOOD"
    elif ppm_val <= 650:
        status = "OK"
    else:
        status = "BAD"
    oled.text(status, 60, 30, 1)

    oled.hline(0, 42, 128, 1)
    oled.text("FAN:", 10, 48, 1)
    if fan_state:
        oled.text("ON", 50, 48, 1)
        oled.fill_rect(75, 48, 8, 8, 1)
    else:
        oled.text("OFF", 50, 48, 1)
        oled.rect(75, 48, 8, 8, 1)
    oled.show()

# ---------- MAIN LOOP ----------
def main():
    global fan_state, clean_active, clean_start
    boot()
    mode_menu()

    hold_timer = 0
    holding = False

    while True:
        # Long press SELECT (3 sec) → back to menu
        if not btn_select.value():
            if not holding:
                holding = True
                hold_timer = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), hold_timer) > 3000:
                return_to_menu()
                holding = False
                clean_active = False
                time.sleep(0.3)
        else:
            holding = False

        ppm, raw = read_sensor()

        # CLEAN MODE (fan always on for 60 sec)
        if mode == 2:
            if not clean_active:
                clean_active = True
                clean_start = time.ticks_ms()
                relay_on()
                fan_state = True

            elapsed = time.ticks_diff(time.ticks_ms(), clean_start)
            remaining = max(0, 60 - elapsed // 1000)

            oled.fill(0)
            oled.text("CLEAN MODE", 25, 10, 1)
            oled.hline(0, 20, 128, 1)
            timer_str = str(remaining) + " SEC"
            x = 64 - (len(timer_str) * 3)
            oled.text(timer_str, x, 30, 1)

            progress = int((elapsed / 60000) * 100)
            oled.rect(14, 48, 100, 8, 1)
            oled.fill_rect(15, 49, int(progress * 0.96), 6, 1)
            oled.show()

            if elapsed >= 60000:
                relay_off()
                fan_state = False
                clean_active = False
                return_to_menu()
            time.sleep(0.2)
            continue

        # ECO / PWR modes
        if ppm > FAN_ON_PPM:
            relay_on()
            fan_state = True
        else:
            relay_off()
            fan_state = False

        show_dashboard(ppm)
        time.sleep(0.3)

# ---------- RUN ----------
try:
    main()
except KeyboardInterrupt:
    relay_off()
    oled.fill(0)
    oled.text("GOODBYE!", 40, 28, 1)
    oled.show()
    time.sleep(1)
    oled.fill(0)
    oled.show()