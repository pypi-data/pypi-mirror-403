"""
MapView - A view for displaying geographic data on maps
"""

from typing import Optional, Dict, Any
from datetime import datetime

from ..core.base_view import BaseView
from ..types.models import GeoPoint, MapViewport, MapControls, MapMarker
from ..errors.exceptions import MissingRequiredParameterError


class MapView(BaseView):
    """View for displaying geographic data on maps"""

    def __init__(self, view_id: str, title: str, process_id: Optional[str] = None):
        super().__init__(
            {
                "id": view_id,
                "type": "Map",
                "process_id": process_id,
                "metadata": {
                    "version": "1.0.0",
                    "created_at": datetime.now(),
                },
            }
        )

        self.content = {
            "title": title,
            "intro": "",
            "markers": [],
            "viewport": None,
            "controls": {
                "zoom": True,
                "compass": True,
                "userLocation": False,
            },
            "overlays": [],
        }

    def set_intro(self, intro: str) -> "MapView":
        """Set the introduction text displayed before the map"""
        return self._set_intro_text("intro", intro)

    def set_viewport(
        self,
        center: GeoPoint,
        zoom: Optional[float] = None,
        bearing: Optional[float] = None,
        pitch: Optional[float] = None,
    ) -> "MapView":
        """Define the initial camera position for the map widget"""
        self.content["viewport"] = {
            "center": {"lat": center.lat, "lon": center.lon, "altitude": center.altitude, "precision": center.precision},
            "zoom": zoom,
            "bearing": bearing,
            "pitch": pitch,
        }
        return self

    def set_controls(self, controls: MapControls) -> "MapView":
        """Configure map UI toggles (zoom, compass, user location, ...)"""
        self.content["controls"] = {
            "zoom": controls.zoom,
            "compass": controls.compass,
            "userLocation": controls.user_location,
        }
        return self

    def add_marker(self, marker: MapMarker) -> "MapView":
        """Add a single marker to the map dataset"""
        if not marker.id:
            raise MissingRequiredParameterError("marker id")

        marker_dict = {
            "id": marker.id.strip(),
            "location": {
                "lat": marker.location.lat,
                "lon": marker.location.lon,
                "altitude": marker.location.altitude,
                "precision": marker.location.precision,
            },
            "title": marker.title.strip() if marker.title else None,
            "description": marker.description.strip() if marker.description else None,
            "icon": marker.icon,
        }

        if marker.meta:
            marker_dict["meta"] = marker.meta

        self.content["markers"].append(marker_dict)
        return self

    def add_markers(self, markers: list) -> "MapView":
        """Add multiple markers"""
        for marker in markers:
            if isinstance(marker, dict):
                map_marker = MapMarker(
                    id=marker["id"],
                    location=GeoPoint(
                        lat=marker["location"]["lat"],
                        lon=marker["location"]["lon"],
                        altitude=marker["location"].get("altitude"),
                        precision=marker["location"].get("precision"),
                    ),
                    title=marker.get("title"),
                    description=marker.get("description"),
                    icon=marker.get("icon"),
                    meta=marker.get("meta"),
                )
                self.add_marker(map_marker)
            else:
                self.add_marker(marker)
        return self

    def clear_markers(self) -> "MapView":
        """Remove all registered markers"""
        self.content["markers"] = []
        return self

    def add_overlay(self, id: str, data: Dict[str, Any]) -> "MapView":
        """Append a lightweight overlay record (heatmap, region...)"""
        overlays = self.content.get("overlays", [])
        overlays.append({"id": id.strip(), "data": data})
        self.content["overlays"] = overlays
        return self

    def set_overlays(
        self, overlays: list
    ) -> "MapView":
        """Replace the existing overlay list with a sanitized copy"""
        self.content["overlays"] = [
            {"id": overlay["id"].strip(), "data": dict(overlay["data"])}
            for overlay in overlays
        ]
        return self

    def get_content(self):
        """Get the map content"""
        return self.content

