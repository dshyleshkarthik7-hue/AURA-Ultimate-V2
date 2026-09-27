import time
import cv2

from aura.config import load_config
from aura.camera import Camera
from aura.perception import PerceptionEngine
from aura.voice import Voice


LANGUAGES = {
    "1": ("en", "English"),
    "2": ("hi", "Hindi"),
    "3": ("te", "Telugu"),
    "4": ("ta", "Tamil"),
    "5": ("gu", "Gujarati"),
}


def draw_panel(
    frame,
    title,
    subtitle="",
    color=(40, 200, 80),
):
    """
    Draw a modern top information panel.
    """

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (frame.shape[1], 125),
        (20, 20, 20),
        -1,
    )

    frame[:] = cv2.addWeighted(
        overlay,
        0.88,
        frame,
        0.12,
        0,
    )

    cv2.putText(
        frame,
        title,
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        color,
        2,
        cv2.LINE_AA,
    )

    if subtitle:
        cv2.putText(
            frame,
            subtitle,
            (30, 92),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )


def draw_footer(frame, language_name, paused):
    h, w = frame.shape[:2]

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (0, h - 90),
        (w, h),
        (15, 15, 15),
        -1,
    )

    frame[:] = cv2.addWeighted(
        overlay,
        0.9,
        frame,
        0.1,
        0,
    )

    status = "PAUSED" if paused else "SCANNING"

    cv2.putText(
        frame,
        f"Language: {language_name} | {status}",
        (25, h - 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "[L] Language   [R] Reset   [SPACE] Pause   [Q] Quit",
        (25, h - 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )


def draw_result_card(frame, result):
    """
    Large centered result card.
    """

    h, w = frame.shape[:2]

    card_w = int(w * 0.72)
    card_h = int(h * 0.42)

    x1 = (w - card_w) // 2
    y1 = (h - card_h) // 2

    x2 = x1 + card_w
    y2 = y1 + card_h

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (x1, y1),
        (x2, y2),
        (25, 25, 25),
        -1,
    )

    frame[:] = cv2.addWeighted(
        overlay,
        0.93,
        frame,
        0.07,
        0,
    )

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (60, 220, 100),
        2,
    )

    cv2.putText(
        frame,
        "OBJECT IDENTIFIED",
        (x1 + 30, y1 + 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (60, 220, 100),
        2,
        cv2.LINE_AA,
    )

    label = str(
        result.get(
            "label",
            "UNKNOWN",
        )
    ).upper().replace("_", " ")

    cv2.putText(
        frame,
        label,
        (x1 + 30, y1 + 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    confidence = float(
        result.get(
            "confidence",
            0.0,
        )
    ) * 100

    cv2.putText(
        frame,
        f"Confidence: {confidence:.1f}%",
        (x1 + 30, y1 + 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Verified Offline",
        (x1 + 30, y1 + 220),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (60, 220, 100),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Press R to scan again",
        (x1 + 30, y2 - 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )


def draw_language_menu(frame):
    h, w = frame.shape[:2]

    menu_w = int(w * 0.55)
    menu_h = int(h * 0.65)

    x1 = (w - menu_w) // 2
    y1 = (h - menu_h) // 2

    x2 = x1 + menu_w
    y2 = y1 + menu_h

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (x1, y1),
        (x2, y2),
        (15, 15, 15),
        -1,
    )

    frame[:] = cv2.addWeighted(
        overlay,
        0.95,
        frame,
        0.05,
        0,
    )

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (70, 150, 255),
        2,
    )

    cv2.putText(
        frame,
        "SELECT LANGUAGE",
        (x1 + 30, y1 + 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    items = [
        "1 - English",
        "2 - Hindi",
        "3 - Telugu",
        "4 - Tamil",
        "5 - Gujarati",
    ]

    y = y1 + 115

    for item in items:

        cv2.putText(
            frame,
            item,
            (x1 + 45, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

        y += 55

    cv2.putText(
        frame,
        "Press a number to select",
        (x1 + 30, y2 - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (150, 150, 150),
        1,
        cv2.LINE_AA,
    )


def main():

    cfg = load_config()

    camera_cfg = cfg["camera"]

    camera = Camera(
        source=camera_cfg.get("source", 0),
        width=camera_cfg.get("width", 1280),
        height=camera_cfg.get("height", 720),
        fps=camera_cfg.get("fps", 30),
    )

    print("\nOpening camera...")

    if not camera.open():

        print(
            "\nERROR: Could not open camera."
        )

        print(
            "Try changing camera.source in config.yaml"
        )

        return

    print(
        f"Camera opened using: "
        f"{camera.backend_name}"
    )

    engine = PerceptionEngine(cfg)

    voice_cfg = cfg.get("voice", {})

    voice = Voice(
        enabled=voice_cfg.get(
            "enabled",
            True,
        ),
        cooldown=voice_cfg.get(
            "cooldown_seconds",
            4,
        ),
    )

    current_language = cfg.get(
        "language",
        "en",
    )

    language_name = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "ta": "Tamil",
        "gu": "Gujarati",
    }.get(
        current_language,
        "English",
    )

    paused = False
    result_locked = False
    language_menu = False

    failure_count = 0

    window_name = "AURA Perception | Offline Indian Vision"

    cv2.namedWindow(
        window_name,
        cv2.WINDOW_NORMAL,
    )

    cv2.resizeWindow(
        window_name,
        1280,
        720,
    )

    print("\nAURA Controls:")
    print("L = Language")
    print("R = Reset")
    print("SPACE = Pause")
    print("Q = Quit")
    print("1-5 = Select language\n")

    try:

        while True:

            ok, frame = camera.read()

            if not ok:

                failure_count += 1

                if failure_count >= 5:

                    print(
                        "Camera connection problem. "
                        "Attempting reconnect..."
                    )

                    camera.reconnect()

                    failure_count = 0

                time.sleep(0.05)

                # Keep UI responsive.
                key = cv2.waitKey(1) & 0xFF

                if key in (
                    ord("q"),
                    ord("Q"),
                ):
                    break

                continue

            failure_count = 0

            display = frame.copy()

            result = None

            if not paused and not result_locked:

                result = engine.predict(frame)

                reason = result.get(
                    "reason",
                    "scanning",
                )

                if result.get("stable", False):

                    result_locked = True

                    label = result.get(
                        "label",
                        "unknown",
                    )

                    try:
                        voice.announce(
                            label,
                            current_language,
                        )
                    except TypeError:
                        # Compatibility with older Voice class.
                        voice.announce(label)

                if reason == "collecting_evidence":

                    draw_panel(
                        display,
                        "AURA PERCEPTION",
                        "Collecting visual evidence...",
                        (70, 170, 255),
                    )

                elif reason == "uncertain":

                    draw_panel(
                        display,
                        "AURA PERCEPTION",
                        "Object uncertain - adjusting...",
                        (0, 180, 255),
                    )

                else:

                    draw_panel(
                        display,
                        "AURA PERCEPTION",
                        "Offline recognition active",
                        (60, 220, 100),
                    )

            elif paused:

                draw_panel(
                    display,
                    "AURA PAUSED",
                    "Press SPACE to continue",
                    (0, 180, 255),
                )

            if result_locked and result is not None:

                draw_panel(
                    display,
                    "AURA PERCEPTION",
                    "Recognition verified",
                    (60, 220, 100),
                )

                draw_result_card(
                    display,
                    result,
                )

            draw_footer(
                display,
                language_name,
                paused,
            )

            if language_menu:
                draw_language_menu(display)

            cv2.imshow(
                window_name,
                display,
            )

            key = cv2.waitKey(1) & 0xFF

            # Q = Quit
            if key in (
                ord("q"),
                ord("Q"),
                27,
            ):
                break

            # L = Language menu
            elif key in (
                ord("l"),
                ord("L"),
            ):
                language_menu = True

            # R = Reset
            elif key in (
                ord("r"),
                ord("R"),
            ):
                result_locked = False
                paused = False
                language_menu = False

                try:
                    engine.temporal.clear()
                except Exception:
                    pass

                print("AURA reset. Scanning again...")

            # SPACE = Pause
            elif key == 32:

                if not result_locked:
                    paused = not paused

            # Language selection
            elif language_menu:

                char = chr(key) if key != 255 else ""

                if char in LANGUAGES:

                    current_language, language_name = (
                        LANGUAGES[char]
                    )

                    language_menu = False

                    print(
                        f"Language changed to: "
                        f"{language_name}"
                    )

    except KeyboardInterrupt:

        print("\nStopping AURA...")

    finally:

        print("Closing camera...")

        camera.release()

        try:
            voice.close()
        except Exception:
            pass

        cv2.destroyAllWindows()

        print("AURA stopped safely.")


if __name__ == "__main__":
    main()