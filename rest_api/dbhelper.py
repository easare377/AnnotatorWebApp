from .models import *
import uuid
import json
from django.http import JsonResponse
import time



def add_annotation_type_if_not_exist():
    # Define a namespace and a name (string) to generate the UUID
    namespace = uuid.NAMESPACE_DNS
    polygon_name = "POLYGON"
    bbox_name = "BBOX"
    AnnotationType(annotation_id=uuid.uuid5(namespace, polygon_name), annotation_type='POLYGON').save()
    AnnotationType(annotation_id=uuid.uuid5(namespace, bbox_name), annotation_type='BBOX').save()
    


def create_project(self, request_object):
    # project_name = project_info['name']
    # project_description = project_info['description']
    # projects = Projects(project_name=project_name, project_description)
    # projects.save()
    # image_url = image_info['url']
    
        # project_name = request_object['projectName']
        # return bad_request('Invalid Json')
        # return bad_request(request_object)
    if request_object:
       
       
        try:
            # data = json.loads(request_object)
            data=request_object
            print(data)
            # Create a new project
            project = Projects(
                project_name=data['project_name'],
                description=data['project_description'],
                date_created=timezone.now()
                # print(request_object)
            )
            project.save()

            # Create a new ImageInfo
            image_info = ImageInfo(
                project_id=project,
                original_filename=data['original_filename'],
                image_url='',  # Assuming you need to set this later
                image_width=0,  # Assuming you need to set this later
                image_height=0,  # Assuming you need to set this later
                date_added=timezone.now()
            )
            image_info.save()
            annotation_type_map = {
                "POLYGON": "092cfa2c-371d-516e-8eb7-776931146fd6",
                "BBOX": "858bdea9-94b8-5e1d-8339-03d14b75ca41"
            }
            annotation_type_key = data.get('annotation_type', 'POLYGON')  # Use 'POLYGON' as default
            annotation_type_uuid = annotation_type_map.get(annotation_type_key, annotation_type_map['POLYGON'])

            # Create or get the AnnotationType
            # annotation_type, created = AnnotationType.objects.get_or_create(
            #     annotation_type=data['annotation_type']
            # )
            annotation_type, created = AnnotationType.objects.get_or_create(
                annotation_id=annotation_type_uuid,
                defaults={'annotation_type': annotation_type_key}
            )

            # Create a new AnnotationSetup
            annotation_setup = AnnotationSetup(
                image_id=image_info,
                annotation_type=annotation_type
                
            )
           
            annotation_setup.save()

            # Create ObjectClass instances
            class_names = data.get('class_name', [])
            colors = data.get('color', [])
            description = data.get('description', '')
            print(class_names)
            # time.sleep(5)

            for class_name, color in zip(class_names, colors):
                print(class_name)
                object_class = ObjectClass(
                    setup_id=annotation_setup,
                    class_name=class_name,
                    color=color,
                    description=description  # Assuming single description for all
                )
                print(object_class)
                try:
                    object_class.save()
                except Exception as e:
                    print(f"An error occurred: {e}")
                

            return JsonResponse({'message': 'Project and related data created successfully'}, status=201)
        except KeyError as e:
            return JsonResponse({'error': f'Missing key: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method'}, status=400)
    
    
    
def update_project_with_details(self,request_object):
    # if request.method == 'POST':
    try:
        data = request_object
        project_id=data['project_id']
        

        # Fetch the project by project_id
        try:
            project = Projects.objects.get(project_id=project_id)
            
        except Projects.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # Update project fields
        project.project_name = data.get('project_name', project.project_name)
        project.description = data.get('project_description', project.description)
        project.last_modified = timezone.now()
        project.save()

        # Update ImageInfo (assuming one image per project for simplicity)
        try:
            image_info = ImageInfo.objects.get(project_id=project)
            image_info.original_filename = data.get('original_filename', image_info.original_filename)
            image_info.date_modified = timezone.now()
            image_info.save()
        except ImageInfo.DoesNotExist:
            return JsonResponse({'error': 'ImageInfo not found'}, status=404)

        # Handle annotation type
        annotation_type_map = {
            "POLYGON": "092cfa2c-371d-516e-8eb7-776931146fd6",
            "BBOX": "858bdea9-94b8-5e1d-8339-03d14b75ca41"
        }
        annotation_type_key = data.get('annotation_type', 'POLYGON')  # Use 'POLYGON' as default
        annotation_type_uuid = annotation_type_map.get(annotation_type_key, annotation_type_map['POLYGON'])
        print(annotation_type_uuid)

        # Get or create the AnnotationType
        annotation_type, created = AnnotationType.objects.get_or_create(
            annotation_id=annotation_type_uuid,
            defaults={'annotation_type': annotation_type_key}
        )
        print(annotation_type)

        # Update AnnotationSetup (assuming one setup per image for simplicity)
        try:
            annotation_setup = AnnotationSetup.objects.get(image_id=image_info)
            annotation_setup.annotation_type = annotation_type
            annotation_setup.save()
        except AnnotationSetup.DoesNotExist:
            return JsonResponse({'error': 'AnnotationSetup not found'}, status=404)

        # Update ObjectClass instances
        class_names = data.get('class_name', [])
        colors = data.get('color', [])
        description = data.get('description', '')

        # Clear existing ObjectClass instances
        ObjectClass.objects.filter(setup_id_id=annotation_setup).delete()

        # Create new ObjectClass instances
        for class_name, color in zip(class_names, colors):
            object_class = ObjectClass(
                setup_id=annotation_setup,
                class_name=class_name,
                color=color,
                description=description  # Assuming single description for all
            )
            object_class.save()

        return JsonResponse({'message': 'Project and related data updated successfully'}, status=200)
    except KeyError as e:
        return JsonResponse({'error': f'Missing key: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_project_details():
    
    pass


def delete_project_details(self,request_object):
    try:
        data = request_object
        project_id=data['project_id']
        
        try:
            project = Projects.objects.get(project_id=project_id)
            images = ImageInfo.objects.filter(project_id=project_id)
        except Exception as e:
            return e
        if len(images)==1:
            image=images[0]
            image.delete()
            print("Image deleted")
        project.delete()
        return JsonResponse({'message': 'Project deleted successfully'})
    except Projects.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)

#
# # image_info = ImageInfo()
#
# # def update_project(self, project_name, description=None):
# #     projects = Projects()
# #     projects.
#
# def get_projects_info(project_id):
#     projects = Projects.objects.all()
#     return projects
