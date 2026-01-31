import mimetypes
import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import yaml
from fastapi import FastAPI, HTTPException
from jinja2 import FileSystemLoader, select_autoescape
from starlette.requests import Request
from starlette.responses import Response, FileResponse
from starlette.staticfiles import StaticFiles

from lambdawaker.dataset.DiskDataset import DiskDataset
from lambdawaker.dataset.hadlers.DatasetSourceHandler import DataSetsHandler
from lambdawaker.dataset.hadlers.process_data_payload import process_data_payload
from lambdawaker.draw.color.HSLuvColor import to_hsluv_color
from lambdawaker.draw.color.generate_color import generate_hsluv_black_text_contrasting_color
from lambdawaker.templete.fields import field_generators
from lambdawaker.templete.server.FileMetadataHandler import FileMetadataHandler
from lambdawaker.templete.server.RelativeLoader import RelativeEnvironment


class TemplateServer:
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        if config_path:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config or {}

        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", 8001)
        self.workers = self.config.get("workers", 1)
        self.site_path = Path(self.config.get("site_path", "./site")).resolve()

        self.app = FastAPI()
        self._setup_jinja()
        self._setup_datasets()
        self._setup_routes()
        self._setup_static()

    def _setup_jinja(self):
        self.env = RelativeEnvironment(
            loader=FileSystemLoader(str(self.site_path)),
            autoescape=select_autoescape(["html", "xml", "svg"]),
        )

    def _setup_datasets(self):
        dataset_paths = self.config.get("datasets", [])
        datasets = [DiskDataset(path) for path in dataset_paths]

        self.dataset_handler = DataSetsHandler(datasets)

    def _setup_routes(self):
        self.handel_path_info = FileMetadataHandler(self.site_path)

        @self.app.get("/render/{template_type}/{variant}/{record_id:int}")
        def render_card_by_record(
                template_type: str,
                variant: str,
                record_id: int,
                request: Request,
                primary_color: Tuple[float, float, float, float] = (0, 0, 0, 1)
        ):
            path = os.path.join(template_type, variant, "index.html.j2")
            env_path = str(self.site_path.joinpath(template_type, variant, "meta", "common.json"))
            common = {}

            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    import json
                    common = json.load(f)

            return self.render_template(
                path,
                request,
                primary_color,
                data={
                    "data": {
                        "id": record_id
                    },
                    "common": common
                }
            )

        @self.app.get("/render/{template_type}/{variant}")
        def render_card_by_random_record(
                template_type: str,
                variant: str,
                request: Request,
                primary_color: Tuple[float, float, float, float] = (0, 0, 0, 1)
        ):
            path = os.path.join(template_type, variant, "index.html.j2")
            env_path = str(self.site_path.joinpath(template_type, variant, "meta", "common.json"))
            common = {}

            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    import json
                    common = json.load(f)

            return self.render_template(
                path,
                request,
                primary_color,
                data={
                    "data": {
                        "id": "random"
                    },
                    "common": common
                }
            )

        @self.app.get("/render/{path:path}")
        def serve_relative_to_site(path: str, request: Request):
            if path.endswith(".j2"):
                return render_jinja_any(path, request)

            result = str(self.site_path.joinpath(path))
            return FileResponse(path=result)

        @self.app.get("/ds/{path:path}")
        def server_dataset_resource(path: str):
            data = self.dataset_handler[path]
            content_type, data = process_data_payload(data)
            return Response(content=data, media_type=content_type)

        @self.app.get("/{path:path}")
        def render_jinja_any(path: str, request: Request):
            if path == "":
                path = "index.html.j2"

            if not path.endswith(".j2"):
                raise HTTPException(status_code=404)

            template_path = self.site_path / path
            if not template_path.exists():
                raise HTTPException(status_code=404)

            return self.render_template(path, request)

        @self.app.api_route("/{path:path}", methods=["INFO"])
        def handle_info(path: str):
            return self.handel_path_info(path)

    def _setup_static(self):
        self.app.mount("/", StaticFiles(directory=str(self.site_path)), name="site")

    def render_template(self, path: str, request: Request, primary_color=None, data=None) -> Response:
        data = data if data is not None else {}
        path = path.replace("\\", "/")

        primary_color = to_hsluv_color(primary_color) if primary_color is not None else generate_hsluv_black_text_contrasting_color()
        text_color_hex = to_hsluv_color((0, 0, 0, 1))

        default_env = {
            "theme": {
                "primary_color": primary_color,
                "text_color": text_color_hex
            }
        }

        output_name = path[:-3]  # remove ".j2"
        media_type, _ = mimetypes.guess_type(output_name)
        media_type = media_type or "text/plain"

        template = self.env.get_template(path)

        rendered = template.render(
            request=request,
            env=default_env,
            gen=field_generators,
            ds=self.dataset_handler,
            **data
        )

        return Response(
            content=rendered,
            media_type=media_type
        )

    def run(self):
        import uvicorn
        uvicorn.run(self.app, host=self.host, port=self.port, workers=self.workers)
