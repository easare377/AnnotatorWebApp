from ..controller import *
from ..decorators.route import route
from rest_api import dbhelper as dbh


@route('projects/data')
class GetImagesController(Controller):
    def process_post_request(self, request_object):
        project_id = request_object.project_id
        project_details = dbh.get_project_details(project_id)
        project_setup = dbh.get_project_setup(project_id)
        image_infos = dbh.get_images(project_id)
        resp = {'projectInfo': project_details, 'projectSetup': project_setup,
                'imageInfos': image_infos}
        # return ok(data=image_infos)
        # resp = {'annotationType': {'annotationId': '19649044-5ada-4a1b-8924-a523dac47618',
        #                            'annotationType': 'POLYGON'},
        #         'objectClasses': [{'setupId': '19696044-5ada-4a1b-8924-a523dac47618',
        #                            'className': 'Tree',
        #                            'color': '#FFFF00',
        #                            'description': 'Trees in Florida'}],
        #         'imageInfos': [{'imageId': '19699044-5ada-4a1b-8924-a523dac47618',
        #                         'originalFilename': 'image.jpg',
        #                         'imageUrl': 'https://s3.bucket/19699044-5ada-4a1b-8924-a523dac47618.png',
        #                         'imageWidth': 3000,
        #                         'imageHeight': 2000,
        #                         'dateAdded': '2020-02-02 13:30:23',
        #                         'dateModified': '2020-02-02 13:30:23'
        #                         }]}
        return ok(resp)
