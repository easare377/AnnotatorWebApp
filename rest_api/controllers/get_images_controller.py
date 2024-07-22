from ..controller import *
from ..decorators.route import route
from ..dbhelper import *


@route('projects/data')
class GetImagesController(Controller):
    def process_post_request(self, request_object):
        # return ok([{'imageId': '092cfa2c-371d-516e-8eb7-776931146f90',
        #             'originalFilename': 'DJI_0198_AS_0320_01.jpg',
        #             'imageUrl': 'http://localhost:8000/api/downloads/DJI_0198_AS_0320_01.JPG',
        #             'imageSize': {'width': 1920, 'height': 1080},
        #             'dateAdded': '2020-02-02 13:30:23',
        #             'dateModified': '2020-02-02 13:30:23'
        #             }])
        project_id = request_object.project_id
        image_infos = get_images(project_id)
        return ok(data=image_infos)
        # [{'imageId': '19699044-5ada-4a1b-8924-a523dac47618',
        #   'originalFilename': 'image.jpg',
        #   'imageUrl': 'https://s3.bucket/19699044-5ada-4a1b-8924-a523dac47618.png',
        #   'imageWidth': 3000,
        #   'imageHeight': 2000,
        #   'dateAdded': '2020-02-02 13:30:23',
        #   'dateModified': '2020-02-02 13:30:23'
        #   }]
        pass
