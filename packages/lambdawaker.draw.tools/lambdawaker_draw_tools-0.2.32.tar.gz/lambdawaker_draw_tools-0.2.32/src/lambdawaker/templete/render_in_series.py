#!/usr/bin/env python3
import argparse
import asyncio
from io import BytesIO
from typing import Tuple

import requests
from PIL import Image

from lambdawaker.draw import card_background as card_background_module
from lambdawaker.draw.color.generate_color import generate_hsluv_black_text_contrasting_color
from lambdawaker.file.path.ensure_directory import ensure_directory
from lambdawaker.reflection.query import select_random_function_from_module_and_submodules
from lambdawaker.templete.AsyncPlaywrightRenderer import AsyncPlaywrightRenderer


def fetch_available_templates(base_url: str) -> Tuple[str, ...]:
    available_templates_resp = requests.request("INFO", f"{base_url}/id_cards/", timeout=10)
    available_templates_resp.raise_for_status()
    available_templates = available_templates_resp.json()

    return tuple((
        t["name"] for t in available_templates if not t['name'].startswith("_")
    ))


async def render_single_card(
        renderer: AsyncPlaywrightRenderer,
        base_url: str,
        record_id: int,
        template_name: str,
        outdir: str,
):
    primary_color = generate_hsluv_black_text_contrasting_color()

    url = (
        f"{base_url}/render/id_cards/{template_name}/{record_id}"
        f"?primary_color={primary_color.to_hsl_tuple()}"
    )

    await renderer.page.goto(url)

    card = await renderer.page.wait_for_selector("#view-port")
    image_bytes = await card.screenshot(omit_background=True)

    background_paint_function = select_random_function_from_module_and_submodules(
        card_background_module,
        "generate_card_background_.*",
    )

    first_layer_image = Image.open(BytesIO(image_bytes))

    _, card_background_image = background_paint_function(
        first_layer_image.size,
        primary_color,
    )

    canvas = Image.new("RGBA", first_layer_image.size)
    for image in [card_background_image, first_layer_image]:
        canvas.paste(image, (0, 0), image)

    ensure_directory(outdir)
    canvas.save(f"{outdir.rstrip('/')}/{record_id}_{template_name}.png")


async def render(
        ds_range: Tuple[int, int] = (0, 5),
        *,
        base_url: str = "http://127.0.0.1:8001",
        headless: bool = True,
        outdir: str = "./output/img/",
):
    print("STATUS: RUNNING")
    renderer = AsyncPlaywrightRenderer()

    await renderer.start(headless=headless)

    start, end = ds_range

    try:
        available_templates = fetch_available_templates(base_url)
    except Exception as e:
        print(f"MESSAGE: Failed to fetch templates: {e}")
        print("STATUS: FAILED")
        await renderer.close()
        return

    try:
        local_count = 0
        for record_id in range(start, end):
            print(f"MESSAGE: Processing record {record_id}")
            for template_name in available_templates:
                await render_single_card(renderer, base_url, record_id, template_name, outdir)

            local_count += 1
            print(f"PROGRESS: {local_count}")

        print("STATUS: SUCCESS")
    except Exception as e:
        print(f"MESSAGE: Error during rendering: {e}")
        print("STATUS: FAILED")
    finally:
        await renderer.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Render id card images for a range of record IDs."
    )

    p.add_argument("--start", default=0, type=int, help="Start record id (inclusive)")
    p.add_argument("--end", default=5, type=int, help="End record id (exclusive)")

    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:8001",
        help="Base server URL (default: %(default)s)",
    )
    p.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run browser headless (default: %(default)s). Use --no-headless to show UI.",
    )
    p.add_argument(
        "--outdir",
        default="./output/img/",
        help="Output directory (default: %(default)s)",
    )

    return p


def main() -> int:
    args = build_parser().parse_args()
    ds_range = (args.start, args.end)

    asyncio.run(
        render(
            ds_range=ds_range,
            base_url=args.base_url,
            headless=args.headless,
            outdir=args.outdir,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
