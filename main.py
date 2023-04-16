import asyncio
from bledom.device import BleLedDevice
from bleak import BleakScanner, BleakClient
import time
import random
import math

SPLINES = {
    'forest': ([[37, 89, 31], [25, 39, 13], [114, 96, 27], [37, 89, 31], [129, 140, 60], [89, 58, 14]], 10.0),
    'nightlife': ([[12, 5, 15], [48, 17, 61], [139, 35, 219], [34, 6, 46]], 0.9),
    'redgreen': ([[212, 0, 0], [212, 0, 0], [54, 156, 17], [54, 156, 17]], 5.0)
}


def color_space_to_pixel(color, gamma=1.2, low=4, high=255):
    pixels = [0.0, 0.0, 0.0]
    for i in range(3):
        comp = max(0, color[i])
        c = round((comp ** gamma) * (high - low + 1) + low - 0.5)
        c = min(high, max(low, c))
        pixels[i] = c
    return pixels


def random_circle_point():
    r = random.random() ** 0.5
    theta = random.random() * math.tau
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return [x, y]


def scale(obj, factor):
    if isinstance(obj, list):
        return [scale(x, factor) for x in obj]
    else:
        return obj * factor


def sample_cyclic_spline(spline_def, x):
    # Uniform Catmull-Rom
    charateristic = [
        [0, 1, 0, 0],
        [-0.5, 0, 0.5, 0],
        [1, -2.5, 2, -0.5],
        [-0.5, 1.5, -1.5, 0.5]
    ]

    whole = int(x)
    part = x - whole

    p_contrib_factors = [0.0, 0.0, 0.0, 0.0]
    for i in range(4):
        for u in range(4):
            p_contrib_factors[i] += charateristic[u][i] * pow(part, u)

    ans = [0.0] * len(spline_def[0])
    for point in range(0, 4):
        for component in range(len(ans)):
            point_component_value = spline_def[(whole + point - 1 + len(spline_def)) % len(spline_def)][component]
            contrib = point_component_value * p_contrib_factors[point]
            ans[component] += contrib
    return ans


async def logic(device):
    fps = 40.0  # approximate

    spline_def, duration = SPLINES['nightlife']
    spline_def = scale(spline_def, 1 / 255)

    await device.power_on()
    await device.set_brightness(75)
    while True:
        x = time.time() * len(spline_def) / duration
        c = sample_cyclic_spline(spline_def, x)
        c_px = color_space_to_pixel(c)
        await device.set_color(c_px[0], c_px[1], c_px[2])
        await asyncio.sleep(1 / fps)


async def main():
    devices = []
    for device in await BleakScanner.discover():
        if 'ELK-BLEDOM' in device.name.upper():
            devices.append(device)

    device = devices[0]
    print(device.name, device.address)
    client = BleakClient(device)
    await client.connect()

    try:
        device = await BleLedDevice.new(client)
        await logic(device)
    finally:
        # disconnect when we finish
        await client.disconnect()
        print('Exited gracefully')


if __name__ == '__main__':
    # spline = [[134, 217, 128], [97, 176, 65], [46, 87, 29], [50, 115, 99], [104, 171, 179], [165, 72, 189]]
    # for i in [0.0, 0.2, 0.7, 1.0, 1.5, 5.0, 6.0]:
    #    sample_cyclic_spline(spline, i)

    asyncio.run(main())
