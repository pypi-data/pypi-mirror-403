import requests


def get_os_colors(
    type: str, kleur: str, aantal: str | int, invert: bool = False
) -> list[str]:
    """_summary_

    Args:
        type (str): type of (oplopend, uiteenlopend, discreet)
        kleur (str):
            oplopend:
                'blauw' |
                'paars' |
                'groen' |
                'roze' |
                'lichtblauw' |
                'oranje' |
                'lichtgroen' |
                'grijs'
            uiteenlopend:
                'stoplicht (1-7)' |
                'blauw - grijs - groen (1-9)' |
                'paars - grijs - lichtblauw (1-9)' |
                'blauw - geel - groen (1-9)' |
                'rood - geel - lichtblauw (1-9)'
            discreet:
                'discreet (1-9)' |
                'fruitig (1-9)' |
                'fruitig (1-9, anders gesorteerd)' |
                'waterkant (1-9)' |
                'waterkant (1-9, anders gesorteerd)' |
                'zonsondergang (1-9)'
        aantal (str): number of colors returned
        invert (bool, optional): invert colors. Defaults to False.

    Returns:
        list[str]: list with colors
    """
    url = "https://gitlab.com/os-amsterdam/tools-onderzoek-en-statistiek/-/raw/main/references/OS_colors.json"
    colors = requests.get(url).json()

    colors = colors[type][kleur][str(aantal)]

    if invert:
        colors = colors[::-1]

    return colors
