"""
SAWS Google Earth Engine Client

Handles all interactions with Google Earth Engine API.
"""

import logging
import threading
from datetime import datetime
from typing import Any

import ee
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Thread-local storage for GEE initialization
_thread_local = threading.local()


class GeeClient:
    """
    Google Earth Engine client for satellite data fetching.

    Supports:
    - MODIS (MOD13Q1): 250m, daily
    - Landsat 8-9: 30m, 16-day
    - Sentinel-1: 5m SAR, 6-day
    - Sentinel-2: 10m, 5-day
    """

    def __init__(self):
        """Initialize GEE client."""
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """Ensure GEE is initialized (thread-safe)."""
        if not hasattr(_thread_local, "gee_initialized") or not _thread_local.gee_initialized:
            try:
                if settings.gee_service_account_key_path:
                    # Use service account authentication
                    credentials = ee.ServiceAccountCredentials(
                        email=None,  # Will be read from key file
                        key_file=settings.gee_service_account_key_path,
                    )
                    ee.Initialize(credentials)
                else:
                    # Use default authentication (for development)
                    ee.Initialize()

                _thread_local.gee_initialized = True
                logger.info("Google Earth Engine initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Google Earth Engine: {e}")
                raise

    def _geometry_to_ee(self, geometry: bytes) -> ee.Geometry.Polygon:
        """
        Convert PostGIS geometry to Earth Engine Geometry.

        Args:
            geometry: PostGIS geometry bytes (WKB format with SRID 4326)

        Returns:
            Earth Engine Polygon geometry with EPSG:4326 CRS
        """
        import shapely.wkb as shapely_wkb
        import shapely.geometry as shapely_geom

        # Parse WKB geometry
        shapely_geom_obj = shapely_wkb.loads(geometry)

        # Validate geometry is within Eastern Province bounds
        if not self._validate_eastern_province_bounds(shapely_geom_obj):
            logger.warning("Geometry extends outside Eastern Province bounds")

        # Convert to GeoJSON-like format
        if shapely_geom_obj.geom_type == "Polygon":
            coords = list(shapely_geom_obj.exterior.coords)
            # Convert to nested array format for GEE
            ee_geom = ee.Geometry.Polygon([coords])
            # Explicitly set CRS to EPSG:4326 (WGS84)
            return ee_geom.transform("EPSG:4326")
        else:
            raise ValueError(f"Unsupported geometry type: {shapely_geom_obj.geom_type}")

    def _validate_eastern_province_bounds(self, shapely_geom) -> bool:
        """
        Validate geometry is within Saudi Eastern Province bounds.

        Args:
            shapely_geom: Shapely geometry object

        Returns:
            True if geometry is within bounds, False otherwise
        """
        try:
            # Get geometry bounds
            bounds = shapely_geom.bounds  # (minx, miny, maxx, maxy)
            min_lon, min_lat, max_lon, max_lat = bounds

            # Eastern Province bounds
            ep_min_lon, ep_min_lat, ep_max_lon, ep_max_lat = settings.eastern_province_bounds

            # Check if geometry intersects with Eastern Province
            # Allow some tolerance for boundary cases (0.1 degree)
            tolerance = 0.1

            return not (
                max_lon < ep_min_lon - tolerance or
                min_lon > ep_max_lon + tolerance or
                max_lat < ep_min_lat - tolerance or
                min_lat > ep_max_lat + tolerance
            )
        except Exception as e:
            logger.error(f"Error validating bounds: {e}")
            return True  # Allow if validation fails

    def get_modis_images(
        self,
        geometry: bytes,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch MODIS MOD13Q1 imagery for a field.

        MODIS provides 250m resolution with 16-day composite.

        Args:
            geometry: Field boundary geometry
            start_date: Start date for imagery
            end_date: End date for imagery

        Returns:
            List of image data with NDVI, EVI, LST values
        """
        try:
            ee_geom = self._geometry_to_ee(geometry)

            # Create Eastern Province bounding rectangle for additional filtering
            ep_min_lon, ep_min_lat, ep_max_lon, ep_max_lat = settings.eastern_province_bounds
            ep_bbox = ee.Geometry.Rectangle([
                [ep_min_lon, ep_min_lat],
                [ep_max_lon, ep_min_lat],
                [ep_max_lon, ep_max_lat],
                [ep_min_lon, ep_max_lat],
            ])

            # Get MODIS MOD13Q1 collection (250m, 16-day)
            collection = (
                ee.ImageCollection(settings.modis_collection_id)
                .filterDate(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                .filterBounds(ee_geom)
                .filterBounds(ep_bbox)  # Additional EP bounds filter
            )

            # Get image count
            count = collection.size().getInfo()
            if count == 0:
                logger.warning("No MODIS images found for the given date range")
                return []

            # Process images
            images_data = []
            image_list = collection.toList(count)

            for i in range(count):
                try:
                    image = ee.Image(image_list.get(i))

                    # Get image metadata
                    image_id = image.get("system:index").getInfo()
                    acquisition_time = image.get("system:time_start").getInfo()
                    acquisition_date = datetime.fromtimestamp(acquisition_time / 1000)

                    # Calculate cloud cover (QA layer)
                    qa = image.select("SummaryQA")
                    cloud_score = self._calculate_modis_cloud_score(qa, ee_geom)

                    # Extract NDVI (scaled by 10000 in MODIS)
                    ndvi = (
                        image.select("NDVI")
                        .reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=ee_geom,
                            scale=250,
                            maxPixels=1e9,
                        )
                        .get("NDVI")
                    )
                    ndvi_value = ndvi.getInfo() / 10000 if ndvi.getInfo() else None

                    # Extract EVI
                    evi = (
                        image.select("EVI")
                        .reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=ee_geom,
                            scale=250,
                            maxPixels=1e9,
                        )
                        .get("EVI")
                    )
                    evi_value = evi.getInfo() / 10000 if evi.getInfo() else None

                    # Extract LST from thermal bands (if available)
                    lst_value = None  # Would need separate MOD11A2 product

                    images_data.append(
                        {
                            "image_id": image_id,
                            "acquisition_time": acquisition_date.isoformat(),
                            "image_time": acquisition_date.isoformat(),
                            "cloud_cover": cloud_score,
                            "ndvi": ndvi_value,
                            "evi": evi_value,
                            "lst": lst_value,
                            "quality_score": 1.0 - (cloud_score / 100),
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing MODIS image {i}: {e}")
                    continue

            return images_data

        except Exception as e:
            logger.error(f"Error fetching MODIS data: {e}")
            raise

    def get_landsat_images(
        self,
        geometry: bytes,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch Landsat 8-9 imagery for a field.

        Landsat provides 30m resolution with 16-day revisit.

        Args:
            geometry: Field boundary geometry
            start_date: Start date for imagery
            end_date: End date for imagery

        Returns:
            List of image data
        """
        try:
            ee_geom = self._geometry_to_ee(geometry)

            # Get Landsat Collection 2 Level-2
            collection = (
                ee.ImageCollection(settings.landsat_collection_id)
                .filterDate(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                .filterBounds(ee_geom)
                .filter(ee.Filter.lt("CLOUD_COVER", 50))  # Filter out cloudy images
            )

            count = collection.size().getInfo()
            if count == 0:
                logger.warning("No Landsat images found for the given date range")
                return []

            images_data = []
            image_list = collection.toList(count)

            for i in range(count):
                try:
                    image = ee.Image(image_list.get(i))

                    image_id = image.get("LANDSAT_PRODUCT_ID").getInfo()
                    acquisition_time = image.get("system:time_start").getInfo()
                    acquisition_date = datetime.fromtimestamp(acquisition_time / 1000)

                    cloud_cover = image.get("CLOUD_COVER").getInfo()

                    # Calculate NDVI from surface reflectance bands
                    ndvi = (
                        image.normalizedDifference(["NIR", "RED"])
                        .rename("NDVI")
                        .reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=ee_geom,
                            scale=30,
                            maxPixels=1e9,
                        )
                        .get("NDVI")
                    )
                    ndvi_value = ndvi.getInfo()

                    # Calculate EVI
                    evi = (
                        image.expression(
                            "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
                            {
                                "NIR": image.select("SR_B5"),
                                "RED": image.select("SR_B4"),
                                "BLUE": image.select("SR_B2"),
                            },
                        )
                        .reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=ee_geom,
                            scale=30,
                            maxPixels=1e9,
                        )
                        .get("EVI")
                    )
                    evi_value = evi.getInfo()

                    # Get thermal band for LST
                    lst_value = None  # Requires additional processing

                    images_data.append(
                        {
                            "image_id": image_id,
                            "acquisition_time": acquisition_date.isoformat(),
                            "image_time": acquisition_date.isoformat(),
                            "cloud_cover": cloud_cover,
                            "ndvi": ndvi_value,
                            "evi": evi_value,
                            "lst": lst_value,
                            "quality_score": 1.0 - (cloud_cover / 100),
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing Landsat image {i}: {e}")
                    continue

            return images_data

        except Exception as e:
            logger.error(f"Error fetching Landsat data: {e}")
            raise

    def get_sentinel1_images(
        self,
        geometry: bytes,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """
        Fetch Sentinel-1 SAR imagery for a field.

        Sentinel-1 provides radar imagery useful for soil moisture.

        Args:
            geometry: Field boundary geometry
            start_date: Start date for imagery
            end_date: End date for imagery

        Returns:
            List of image data
        """
        try:
            ee_geom = self._geometry_to_ee(geometry)

            # Get Sentinel-1 GRD
            collection = (
                ee.ImageCollection(settings.sentinel1_collection_id)
                .filterDate(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                .filterBounds(ee_geom)
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            )

            count = collection.size().getInfo()
            if count == 0:
                return []

            images_data = []

            for i in range(min(count, 50)):  # Limit to 50 images
                try:
                    image = ee.Image(collection.toList(count).get(i))

                    image_id = image.get("system:index").getInfo()
                    acquisition_time = image.get("system:time_start").getInfo()
                    acquisition_date = datetime.fromtimestamp(acquisition_time / 1000)

                    # Calculate backscatter for soil moisture
                    vh = (
                        image.select("VH")
                        .reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=ee_geom,
                            scale=10,
                            maxPixels=1e9,
                        )
                        .get("VH")
                    )
                    vh_value = vh.getInfo()

                    images_data.append(
                        {
                            "image_id": image_id,
                            "acquisition_time": acquisition_date.isoformat(),
                            "image_time": acquisition_date.isoformat(),
                            "cloud_cover": 0,  # SAR is not affected by clouds
                            "vh_backscatter": vh_value,
                            "quality_score": 1.0,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing Sentinel-1 image {i}: {e}")
                    continue

            return images_data

        except Exception as e:
            logger.error(f"Error fetching Sentinel-1 data: {e}")
            raise

    def calculate_index_for_image(
        self,
        image_id: str,
        geometry: bytes,
        index_type: str,
    ) -> float | None:
        """
        Calculate a vegetation index for a specific image.

        Args:
            image_id: Earth Engine image ID
            geometry: Field boundary geometry
            index_type: Type of index to calculate

        Returns:
            Calculated index value
        """
        try:
            ee_geom = self._geometry_to_ee(geometry)

            # This would require storing the original image collection
            # For now, return placeholder
            logger.warning(f"Index calculation for {image_id} not fully implemented")
            return None

        except Exception as e:
            logger.error(f"Error calculating index: {e}")
            return None

    def _calculate_modis_cloud_score(self, qa: ee.Image, geometry: ee.Geometry) -> float:
        """
        Calculate cloud score from MODIS QA band.

        Args:
            qa: QA band image
            geometry: Region of interest

        Returns:
            Cloud score (0-100)
        """
        try:
            # MODIS QA bits interpretation
            # Bits 0-1: Cloud state (00=clear, 01=cloudy, etc.)
            qa_value = (
                qa.reduceRegion(
                    reducer=ee.Reducer.mode(),
                    geometry=geometry,
                    scale=250,
                    maxPixels=1e9,
                )
                .get("SummaryQA")
            )

            if qa_value.getInfo() is None:
                return 0.0

            # Extract cloud state bits (0-1)
            cloud_state = qa_value.getInfo() & 0x03

            # Map to cloud score
            cloud_scores = {0: 0, 1: 25, 2: 50, 3: 100}
            return float(cloud_scores.get(cloud_state, 50))

        except Exception as e:
            logger.error(f"Error calculating cloud score: {e}")
            return 50.0  # Default to moderate cloud cover


def initialize_gee() -> None:
    """
    Initialize Google Earth Engine for the application.

    Should be called on application startup.
    """
    try:
        client = GeeClient()
        logger.info("Google Earth Engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Google Earth Engine: {e}")
        raise
