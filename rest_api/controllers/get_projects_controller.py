from ..controller import *
from ..decorators.route import route
from ..models import Projects

@route("projects")
class CreateProjectController(Controller):
    #api/projects => PostRequest
    def process_post_request(self, request_object):
        projects = Projects.objects.all()
        resp = []
        for project in projects:
            project_data = {
                'projectId': str(project.project_id),
                'name': project.project_name,
                'description': project.description,
                'dateCreated': project.date_created.strftime("%Y-%m-%d %H:%M:%S") if project.date_created else None}
            resp.append(project_data)
                
                
        # resp = [{'projectId': '1234',
        #         'name': 'Project 1',
        #         'description': 'Project Description',
        #         'dateCreated': '2020-02-02 13:30:23'},  #"YYYY-MM-DD HH:mm:ss.SSS"
        #         {'projectId': '5678',
        #         'name': 'Waterbodies',
        #         'description': 'Project Description',
        #         'dateCreated': '2024-02-02'},
        #         {'projectId': '56783',
        #         'name': 'Building',
        #         'description': 'Project Description',
        #         'dateCreated': '2025-02-02'}
        #         ]
  
        return ok(resp)
    
    def process_put_request(self, request_object):
        pass

    def process_get_request(self,request_object):
        pass

    def process_delete_request(self,request_object):
        pass
