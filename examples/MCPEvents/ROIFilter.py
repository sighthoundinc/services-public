from shapely import geometry
import json

class ROIFilter:
    class ROIRegion:
        def __init__(self, polygon, name, classes, id):
            self.polygon = polygon
            self.name = name
            self.classes = classes
            self.id = id

    @staticmethod
    def convert_points_to_polygon(points):
        x_div = 1
        y_div = 1
        points_list = []
        for p in points:
            points_list.extend(list(p.values()))
        if max(points_list) > 1.0:
            print("Non-normalized coordinates specified, assuming 1920x1080 coordinates and normalizing")
            x_div = 1920
            y_div = 1080
        normalized_points = ([[p["x"]/x_div, p["y"]/y_div] for p in points])
        try:
            return geometry.Polygon(normalized_points)
        except Exception as e:
            print("ROI Filter point conversion error: ", e)

    def __init__(self, file):
        self.regions = {}
        with open(file,'r') as f:
            self.sensors = json.loads(f.read())
            for data in self.sensors['presenceSensors']:
                polygon = self.convert_points_to_polygon(data['polygon'])
                name = data['name']
                classes = data['classes']
                id = data['id']
                self.regions[id] = ROIFilter.ROIRegion(polygon, name, classes, id)

    def get_object_region_map(self, data):
        region_map = {}
        metaclasses = data['metaClasses']
        frame_dimensions = data['frameDimensions']
        for metaclass in metaclasses.keys():
            for obj_id in metaclasses[metaclass].keys():
                obj_dict = metaclasses[metaclass][obj_id]
                obj_class = obj_dict['class']
                if 'box' in obj_dict:
                    # Generate a point which is the bottom right corner of the bounding box
                    point = geometry.Point((obj_dict['box']['x']+obj_dict['box']['width'])/frame_dimensions['w'],
                                            (obj_dict['box']['y']+obj_dict['box']['height'])/frame_dimensions['h'])
                    for region_id in self.regions:
                        region = self.regions[region_id]
                        if metaclass in region.classes or obj_class in region.classes:
                            if region.polygon.contains(point):
                                if not region.name in region_map:
                                    region_map[obj_id] = []
                                region_map[obj_id].append(region.name)
        return region_map


    def objects_in_roi(self, data):
        return len(self.get_object_region_map(data).keys()) > 0

    def get_roi_region(self, id):
        return self.regions.get(id, None)
    def get_regions(self):
        return self.regions.values()

