import os
import sys


def to_pascal_case(snake_str):
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


def create_controller(app_name, controller_name):
    # Convert controller name to PascalCase
    pascal_case_controller_name = to_pascal_case(controller_name)

    # Define the content of the controller file
    controller_content = f"""
from ..controller import *
from ..decorators.route import route


@route('{controller_name.lower()}')
class {pascal_case_controller_name}Controller(Controller):
    def process_post_request(self, request_object):
        pass
"""

    # Define the path to the controllers directory
    controllers_dir = os.path.join(app_name, 'controllers')

    # Create the controllers directory if it does not exist
    if not os.path.exists(controllers_dir):
        os.makedirs(controllers_dir)

    # Define the path to the new controller file
    controller_file_path = os.path.join(controllers_dir, f'{controller_name.lower()}_controller.py')

    # Write the content to the new controller file
    with open(controller_file_path, 'w') as controller_file:
        controller_file.write(controller_content)

    print(f'Controller {pascal_case_controller_name}Controller created at {controller_file_path}')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python generate_controller.py <app_name> c <controller_name>')
        sys.exit(1)

    app_name = sys.argv[1]
    flag = sys.argv[2]
    controller_name = sys.argv[3]

    if flag != 'c':
        print('Invalid flag. Use "c" for controller.')
        sys.exit(1)

    create_controller(app_name, controller_name)
