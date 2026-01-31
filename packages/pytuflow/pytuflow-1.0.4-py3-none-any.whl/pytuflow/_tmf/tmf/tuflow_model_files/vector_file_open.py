from collections import OrderedDict
import numpy as np

try:
    import shapely
except ImportError:
    shapely = None


class Geom:

    def __init__(self, geom):
        self.geom = geom
        self.geom_is_wkb = False
        if isinstance(geom, bytes):  # occurs if shapely is not installed
            self.geom_is_wkb = True

    def __repr__(self):
        return f'Geom({self.geom})'

    def points(self):
        if self.geom_is_wkb:
            # this means GDAL is installed and shapely is not
            from osgeo import ogr
            ogr_geom = ogr.CreateGeometryFromWkb(self.geom)
            if ogr_geom.GetGeometryType() == 1:  # wkbPoint
                x = ogr_geom.GetX()
                y = ogr_geom.GetY()
                return np.array([[x, y]])
            elif ogr_geom.GetGeometryType() == 4:  # wkbMultiPoint
                points = []
                for i in range(ogr_geom.GetGeometryCount()):
                    pt = ogr_geom.GetGeometryRef(i)
                    x = pt.GetX()
                    y = pt.GetY()
                    points.append([x, y])
                return np.array(points)
            elif ogr_geom.GetGeometryType() == 2:  # wkbLineString
                points = []
                for i in range(ogr_geom.GetPointCount()):
                    x, y, _ = ogr_geom.GetPoint(i)
                    points.append([x, y])
                return np.array(points)
            elif ogr_geom.GetGeometryType() == 5:  # wkbMultiLineString
                points = []
                for j in range(ogr_geom.GetGeometryCount()):
                    line = ogr_geom.GetGeometryRef(j)
                    for i in range(line.GetPointCount()):
                        x, y, _ = line.GetPoint(i)
                        points.append([x, y])
                return np.array(points)
            elif ogr_geom.GetGeometryType() == 3:  # wkbPolygon
                points = []
                ring = ogr_geom.GetGeometryRef(0)  # exterior ring
                for i in range(ring.GetPointCount()):
                    x, y, _ = ring.GetPoint(i)
                    points.append([x, y])
                return np.array(points)
            elif ogr_geom.GetGeometryType() == 6:  # wkbMultiPolygon
                points = []
                for k in range(ogr_geom.GetGeometryCount()):
                    poly = ogr_geom.GetGeometryRef(k)
                    ring = poly.GetGeometryRef(0)  # exterior ring
                    for i in range(ring.GetPointCount()):
                        x, y, _ = ring.GetPoint(i)
                        points.append([x, y])
                return np.array(points)
        else:
            # assume shapely is installed if we reach here
            if self.geom.geom_type == 'Point':
                x = self.geom.x
                y = self.geom.y
                return np.array([[x, y]])
            elif self.geom.geom_type == 'MultiPoint':
                points = []
                for pt in self.geom.geoms:
                    x = pt.x
                    y = pt.y
                    points.append([x, y])
                return np.array(points)
            elif self.geom.geom_type == 'LineString':
                points = []
                for x, y in self.geom.coords:
                    points.append([x, y])
                return np.array(points)
            elif self.geom.geom_type == 'MultiLineString':
                points = []
                for line in self.geom.geoms:
                    for x, y in line.coords:
                        points.append([x, y])
                return np.array(points)
            elif self.geom.geom_type == 'Polygon':
                points = []
                exterior = self.geom.exterior
                for x, y in exterior.coords:
                    points.append([x, y])
                return np.array(points)
            elif self.geom.geom_type == 'MultiPolygon':
                points = []
                for poly in self.geom.geoms:
                    exterior = poly.exterior
                    for x, y in exterior.coords:
                        points.append([x, y])
                return np.array(points)

    def lines(self):
        if self.geom_is_wkb:
            from osgeo import ogr
            ogr_geom = ogr.CreateGeometryFromWkb(self.geom)
            lines = []
            if ogr_geom.GetGeometryType() == 2:  # wkbLineString
                line_points = []
                for i in range(ogr_geom.GetPointCount()):
                    x, y, _ = ogr_geom.GetPoint(i)
                    line_points.append([x, y])
                lines.append(np.array(line_points))
            elif ogr_geom.GetGeometryType() == 5:  # wkbMultiLineString
                for j in range(ogr_geom.GetGeometryCount()):
                    line = ogr_geom.GetGeometryRef(j)
                    line_points = []
                    for i in range(line.GetPointCount()):
                        x, y, _ = line.GetPoint(i)
                        line_points.append([x, y])
                    lines.append(np.array(line_points))
            return lines
        else:
            lines = []
            if self.geom.geom_type == 'LineString':
                line_points = []
                for x, y in self.geom.coords:
                    line_points.append([x, y])
                lines.append(np.array(line_points))
            elif self.geom.geom_type == 'MultiLineString':
                for line in self.geom.geoms:
                    line_points = []
                    for x, y in line.coords:
                        line_points.append([x, y])
                    lines.append(np.array(line_points))
            return lines

    def polygons(self):
        if self.geom_is_wkb:
            from osgeo import ogr
            ogr_geom = ogr.CreateGeometryFromWkb(self.geom)
            polygons = []
            if ogr_geom.GetGeometryType() == 3:  # wkbPolygon
                poly_points = []
                ring = ogr_geom.GetGeometryRef(0)  # exterior ring
                for i in range(ring.GetPointCount()):
                    x, y, _ = ring.GetPoint(i)
                    poly_points.append([x, y])
                polygons.append(np.array(poly_points))
            elif ogr_geom.GetGeometryType() == 6:  # wkbMultiPolygon
                for k in range(ogr_geom.GetGeometryCount()):
                    poly = ogr_geom.GetGeometryRef(k)
                    poly_points = []
                    ring = poly.GetGeometryRef(0)  # exterior ring
                    for i in range(ring.GetPointCount()):
                        x, y, _ = ring.GetPoint(i)
                        poly_points.append([x, y])
                    polygons.append(np.array(poly_points))
            return polygons
        else:
            polygons = []
            if self.geom.geom_type == 'Polygon':
                poly_points = []
                exterior = self.geom.exterior
                for x, y in exterior.coords:
                    poly_points.append([x, y])
                polygons.append(np.array(poly_points))
            elif self.geom.geom_type == 'MultiPolygon':
                for poly in self.geom.geoms:
                    poly_points = []
                    exterior = poly.exterior
                    for x, y in exterior.coords:
                        poly_points.append([x, y])
                    polygons.append(np.array(poly_points))
            return polygons



class Feature:

    def __init__(self, geom, attrs: OrderedDict):
        self.geom = Geom(geom)
        self.attrs = attrs

    def __repr__(self):
        return f'Feature(geom={self.geom}, attrs={self.attrs})'

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.attrs[item]
        elif isinstance(item, int):
            key = list(self.attrs.keys())[item]
            return self.attrs[key]
        else:
            raise KeyError(f'Invalid key type: {type(item)}')

    def __len__(self):
        return len(self.attrs)

    def field_index(self, field_name: str) -> int:
        keys = [x.lower() for x in self.attrs.keys()]
        if field_name.lower() in keys:
            return keys.index(field_name.lower())
        return -1


class VectorLayerOpen:

    def __init__(self, path, mode):
        self.fpath = path
        self.mode = mode
        self.driver = None
        self.ds = None
        self.lyr = None
        self.fmt = None
        self.geometry_type = None
        self.open(path, mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __iter__(self):
        return self.__next__()

    def get_feature(self, index: int) -> Feature:
        for i, feat in enumerate(self):
            if i == index:
                return feat
        raise IndexError('Feature index out of range')

    def geometry_types(self) -> list[str]:
        return []

    def open(self, path, mode):
        pass

    def close(self):
        pass


class OGROpen(VectorLayerOpen):

    def __next__(self):
        from .gis import GisFormat, ogr_geom_type_to_string
        for feat in self.lyr:
            if self.fmt == GisFormat.MIF:
                self.geometry_type = ogr_geom_type_to_string(feat.GetGeometryRef().GetGeometryType())
            geom = feat.GetGeometryRef()
            attrs = OrderedDict()
            for i in range(feat.GetFieldCount()):
                field_defn = feat.GetFieldDefnRef(i)
                field_name = field_defn.GetName()
                field_value = feat.GetField(i)
                attrs[field_name] = field_value
            if shapely is not None:
                geom = shapely.from_wkb(bytes(geom.ExportToWkb()))
            else:
                geom = bytes(geom.ExportToWkb())
            feat = Feature(geom, attrs)
            yield feat

    def geometry_types(self) -> list[str]:
        from .gis import ogr_geom_type_to_string
        return [ogr_geom_type_to_string(x) for x in self.lyr.GetGeometryTypes()]

    def open(self, path, mode):
        from .gis import ogr_format, ogr, get_driver_name_from_gis_format, GisFormat, ogr_geom_type_to_string
        self.fmt = ogr_format(self.fpath)
        driver_name = get_driver_name_from_gis_format(self.fmt)
        self.driver = ogr.GetDriverByName(driver_name)
        if self.mode == 'r':
            if not path.exists():
                raise FileExistsError(f'Could not open {path} for reading')
            self.ds = self.driver.Open(str(path.dbpath))
        else:
            if os.path.exists(path.dbpath):
                self.ds = self.driver.Open(str(path.dbpath), 1)
            else:
                self.ds = self.driver.CreateDataSource(str(path.dbpath))
        if self.ds is None:
            raise Exception(f'Could not open {path.dbpath}')
        self.lyr = self.ds.GetLayer(path.lyrname)
        if mode == 'w' and self.lyr is not None:
            self.ds.DeleteLayer(path.lyrname)
            self.lyr = None
        if mode == 'w' or mode == 'r+' and self.lyr is None:
            self.lyr = self.ds.CreateLayer(path.lyrname)
        if self.lyr is None:
            raise Exception(f'Could not open layer {path.lyrname}')
        if mode == 'r' and self.fmt != GisFormat.MIF:
            self.geometry_type = ogr_geom_type_to_string(self.lyr.GetGeomType())

    def close(self):
        for k, v in globals().copy().items():
            if v == self.lyr or v == self.ds:
                del globals()[k]
        self.ds, self.lyr = None, None


class PyOGRIOOpen(VectorLayerOpen):

    def __next__(self):
        from .gis import GisFormat
        for _, feat in self.lyr.iterrows():
            if self.fmt == GisFormat.MIF:
                self.geometry_type = feat.geometry.geom_type
            attrs = OrderedDict()
            for col in self.lyr.columns:
                if col != 'geometry':
                    attrs[col] = feat[col]
            geom = feat.geometry
            feat = Feature(geom, attrs)
            yield feat

    def geometry_types(self) -> list[str]:
        return [x for x in self.lyr.geometry.geom_type.unique().tolist() if x is not None]

    def open(self, path, mode):
        import geopandas as gpd
        from .gis import ogr_format
        self.fmt = ogr_format(self.fpath)
        if self.mode == 'r':
            if not path.exists():
                raise FileExistsError(f'Could not open {path} for reading')
            self.ds = gpd.read_file(str(path), layer=path.lyrname)
        else:
            raise NotImplementedError('Writing not supported with GeoPandas backend.')
        self.lyr = self.ds
        if not self.lyr.empty:
            self.geometry_type = self.lyr.geometry.geom_type.unique()[0]