class PctConfig:
    def __init__(self, allow_overlapping: bool = False, tracking_multiple_sensors: bool = False,
                 segmentation_mode: bool = False):
        self.allow_overlapping = allow_overlapping
        self.tracking_multiple_sensors = tracking_multiple_sensors
        self.segmentation_mode = segmentation_mode

    def toDict(self):
        return {
            'allowOverlapping': self.allow_overlapping,
            'trackingMultipleSensors': self.tracking_multiple_sensors,
            'segmentationMode': self.segmentation_mode
        }
