from abc import ABC
from ..controller import Controller, ok, bad_request
from ..decorators.route import route
from rest_framework.decorators import api_view
from datetime import datetime
import json
from ..models import Projects
from django.http import JsonResponse
from ..dbhelper import create_project,update_project_with_details,get_project_details,delete_project_details




@route('project')
# @api_view(['POST'])
class CreateProjectController(Controller):
    def process_post_request(self, request_object):
        # print("kkk"+ self)
        create_project(self,request_object=request_object)
        # update_project_with_details(request_object,"6d9ae90d-4164-480b-80cf-02d35984b938")
        
        return ok(request_object)
    def process_put_request(self, request_object):#update
        
        update_project_with_details(self,request_object=request_object)
        
        
        return ok(request_object)
    def process_get_request(self, request_object):
        
        get_project_details(self,request_object=request_object)
        
        return ok(request_object)
    
    def process_delete_request(self, request_object):
        
        delete_project_details(self,request_object=request_object)
        
        return ok(request_object)#
       
        
        # return super().process_put_request(request_object)
        # return 
    
